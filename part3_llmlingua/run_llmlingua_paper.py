"""Run audited LLMLingua API variants on the shared samples.

This keeps the question outside compression, divides each long document into
natural context units for the paper's budget controller, and then applies the
paper's iterative token-level compression globally to the selected units.
Existing Phi-2 outputs are never overwritten.
"""
from __future__ import annotations
import argparse
import gc
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from part3_llmlingua.run_llmlingua import append_jsonl, load_jsonl, load_samples, numeric_mean, resolve_device, synchronize, utc_now, write_json
from shared.config import MIRROR_MODEL_ID, SAMPLES_PATH
from shared.prompt_template import SYSTEM_PROMPT, USER_TEMPLATE, render_input_ids
PART_DIR = Path(__file__).resolve().parent
DEFAULT_COMPRESSED_JSONL = PART_DIR / "paper_compressed_member3.jsonl"
DEFAULT_COMPRESSED_JSON = PART_DIR / "paper_compressed_member3.json"
DEFAULT_COMPRESSOR = "NousResearch/Llama-2-7b-hf"
DEFAULT_MEASUREMENT_TOKENIZER = MIRROR_MODEL_ID
METHOD = "llmlingua_paper_coarse_to_fine"
def release_mps_cache(torch, device: str) -> None:
    if device == "mps":
        synchronize(torch, device)
        gc.collect()
        torch.mps.empty_cache()
def split_natural_units(tokenizer, text: str, max_tokens: int) -> list[str]:
    """Preserve source characters while packing paragraphs into bounded units."""
    if max_tokens <= 0:
        raise ValueError("--context-unit-tokens must be greater than zero")
    boundaries = [0] + [match.end() for match in re.finditer(r"(?:\n\s*\n)+", text)]
    boundaries.append(len(text))
    parts = [text[start:end] for start, end in zip(boundaries, boundaries[1:]) if end > start]
    units: list[str] = []
    current = ""
    def length(value: str) -> int:
        return len(tokenizer(value, add_special_tokens=False)["input_ids"])
    for part in parts:
        if current and length(current + part) > max_tokens:
            units.append(current)
            current = ""
        while length(part) > max_tokens:
            # Character boundaries avoid losing multi-byte characters when a
            # paragraph exceeds the limit. Every source character is retained.
            low, high, split = 1, len(part), 0
            while low <= high:
                middle = (low + high) // 2
                if length(part[:middle]) <= max_tokens:
                    split = middle
                    low = middle + 1
                else:
                    high = middle - 1
            if split == 0:
                raise ValueError("Context unit budget cannot encode one source character")
            units.append(part[:split])
            part = part[split:]
        current += part
    if current:
        units.append(current)
    return units or [text]
def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["target_compression_ratio"])].append(row)
    result: dict[str, Any] = {}
    for ratio, group in sorted(grouped.items()):
        result[f"{ratio}x"] = {
            "num_samples": len(group),
            "mean_original_prompt_tokens": numeric_mean(group, "original_prompt_tokens"),
            "mean_prompt_tokens": numeric_mean(group, "prompt_tokens"),
            "mean_achieved_compression_ratio": numeric_mean(group, "compression_ratio"),
            "mean_compression_latency": numeric_mean(group, "compression_latency"),
            "mean_context_units": numeric_mean(group, "num_context_units"),
        }
    return result
def build_model_config(torch, device: str, revision: str | None) -> dict[str, Any]:
    config: dict[str, Any] = {"trust_remote_code": True}
    if revision:
        config["revision"] = revision
    if device in {"cuda", "mps"}:
        config["torch_dtype"] = torch.float16
    return config
def run(args: argparse.Namespace) -> int:
    recipe = getattr(args, "recipe", "legacy_api")
    method = "llmlingua_author_recipe_alpaca" if recipe == "author_release" else METHOD
    samples = load_samples(args.samples, args.limit, args.sample_indices)
    if not samples:
        raise SystemExit(f"No samples found in {args.samples}")
    if any(ratio <= 1 for ratio in args.ratios):
        raise ValueError("Compression ratios must be greater than one")
    if not args.resume:
        args.jsonl.unlink(missing_ok=True)
        args.output.unlink(missing_ok=True)
    existing = load_jsonl(args.jsonl) if args.resume else []
    for row in existing:
        if row.get("preprocessing_version") != "preserve_source_v2":
            raise ValueError("Checkpoint uses different preprocessing; select a new --jsonl and --output")
        expected = {"compressor_model": args.compressor_model, "tokenizer_model": args.tokenizer_model, "context_unit_tokens": args.context_unit_tokens, "context_budget": args.context_budget, "iterative_size": args.iterative_size}
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError("Checkpoint settings differ from this run; select new output paths")
        if row.get("recipe", "legacy_api") != recipe or row.get("compressor_revision") != args.revision:
            raise ValueError("Checkpoint recipe or revision differs; select new output paths")
        if recipe == "author_release" and row.get("compressor_loading_verified") is not True:
            raise ValueError("Checkpoint lacks a verified compressor weight-loading audit")
    done = {(str(row["id"]), int(row["target_compression_ratio"])) for row in existing}
    import torch
    import importlib.metadata
    from llmlingua import PromptCompressor
    from transformers import AutoTokenizer
    class AuditedCompressor(PromptCompressor):
        def load_model(self, model_name, device_map="cuda", model_config=None):
            if recipe != "author_release":
                return super().load_model(model_name, device_map, model_config or {})
            # This 2023 checkpoint declares pad_token_id=-1. Modern tokenizers
            # reject that sentinel; padding is unused for the single-row PPL
            # calls, so use its real EOS id without changing any model weight.
            from transformers import AutoConfig, AutoModelForCausalLM
            options = dict(model_config or {})
            dtype = options.pop("torch_dtype", torch.float32)
            config = AutoConfig.from_pretrained(model_name, **options)
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False, **options)
            self.original_pad_token_id = config.pad_token_id
            if config.pad_token_id is None or config.pad_token_id < 0:
                config.pad_token_id = tokenizer.eos_token_id
            tokenizer.padding_side = "left"
            tokenizer.pad_token_id = config.pad_token_id
            self.model, loading = AutoModelForCausalLM.from_pretrained(model_name, config=config, device_map=device_map, torch_dtype=dtype, use_safetensors=True, output_loading_info=True, **options)
            missing, unexpected = set(loading["missing_keys"]), set(loading["unexpected_keys"])
            source_head = "base_model.model.lm_head.weight"
            self.lm_head_key_remapped = False
            if missing == {"lm_head.weight"} and unexpected == {source_head}:
                from huggingface_hub import hf_hub_download
                from safetensors import safe_open
                index_path = hf_hub_download(model_name, "model.safetensors.index.json", revision=args.revision, cache_dir=os.environ.get("TRANSFORMERS_CACHE"), local_files_only=True)
                index = json.loads(Path(index_path).read_text())
                shard_path = hf_hub_download(model_name, index["weight_map"][source_head], revision=args.revision, cache_dir=os.environ.get("TRANSFORMERS_CACHE"), local_files_only=True)
                with safe_open(shard_path, framework="pt", device="cpu") as shard:
                    head = shard.get_tensor(source_head)
                weight = self.model.get_output_embeddings().weight
                if head.shape != weight.shape:
                    raise RuntimeError("Checkpoint output-head shape differs from model")
                expected_head = head.to(device=weight.device, dtype=weight.dtype)
                with torch.no_grad():
                    weight.copy_(expected_head)
                synchronize(torch, device_map)
                if not torch.equal(weight, expected_head):
                    raise RuntimeError("Restored output head differs from checkpoint tensor")
                del head, expected_head
                missing.remove("lm_head.weight")
                unexpected.remove(source_head)
                self.lm_head_key_remapped = True
                print("[author-load] restored checkpoint output head from legacy key; tensor equality verified", flush=True)
            if missing or unexpected or loading.get("mismatched_keys") or loading.get("error_msgs"):
                raise RuntimeError(f"Unresolved compressor weights: {loading}")
            self.loading_verified = True
            print("[author-load] all model weights verified; no unresolved missing/unexpected keys", flush=True)
            self.model.eval()
            self.tokenizer = tokenizer
            self.device = device_map
            self.context_idxs = []
            self.max_position_embeddings = config.max_position_embeddings
        def control_context_budget(self, *values, **options):
            result = super().control_context_budget(*values, **options)
            self.selected_context_indices = list(result[2])
            self.context_budget_audit = {
                "fine_context_target": float(values[2]),
                "context_lengths": list(values[1]),
                "selected_context_tokens": sum(values[1][i] for i in result[2]),
            }
            return result
    device = resolve_device(args.device)
    print(f"[paper] loading {args.compressor_model} on {device}", flush=True)
    measurement_tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_model)
    compressor = AuditedCompressor(model_name=args.compressor_model, device_map=device, model_config=build_model_config(torch, device, args.revision))
    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    runtime_versions = {package: importlib.metadata.version(package) for package in ("torch", "transformers", "llmlingua")}
    release_mps_cache(torch, device)
    total_jobs = len(samples) * len(args.ratios)
    new_rows = 0
    with open(args.jsonl, "a", encoding="utf-8") as sink:
        job = 0
        for sample in samples:
            units = split_natural_units(compressor.tokenizer, sample["docs"], args.context_unit_tokens)
            if "".join(units) != sample["docs"]:
                raise RuntimeError(f"Preprocessing changed source text for id={sample['id']}")
            original_prompt_tokens = len(render_input_ids(measurement_tokenizer, sample["docs"], sample["question"]))
            for target_ratio in args.ratios:
                job += 1
                key = (str(sample["id"]), int(target_ratio))
                if key in done:
                    print(f"[{job}/{total_jobs}] skip id={sample['id']} target={target_ratio}x", flush=True)
                    continue
                synchronize(torch, device)
                started = time.perf_counter()
                instruction = (SYSTEM_PROMPT + "\n\n" + USER_TEMPLATE.split("{docs}")[0].strip()) if recipe == "author_release" else ""
                question = ("Question: " + sample["question"] + "\n\nAnswer:") if recipe == "author_release" else ""
                concatenate_question = recipe == "author_release"
                component_lengths = {
                    "instruction": compressor.get_token_length(instruction),
                    "question": compressor.get_token_length(question),
                    "contexts": sum(compressor.get_token_length(unit) for unit in units),
                }
                expected_context_target = sum(component_lengths.values()) / target_ratio - component_lengths["instruction"] - (component_lengths["question"] if concatenate_question else 0)
                if expected_context_target <= 0:
                    raise ValueError("Requested compression leaves no positive context budget")
                compressed = compressor.compress_prompt(
                    units,
                    instruction=instruction,
                    question=question,
                    rate=1.0 / float(target_ratio),
                    iterative_size=args.iterative_size,
                    use_context_level_filter=True,
                    use_sentence_level_filter=False,
                    use_token_level_filter=True,
                    context_budget=args.context_budget,
                    rank_method="llmlingua",
                    concate_question=concatenate_question,
                )
                synchronize(torch, device)
                compression_latency = time.perf_counter() - started
                selected_units = list(compressor.selected_context_indices)
                compressed_docs = (compressed.get("compressed_prompt") or "").strip()
                if recipe == "author_release":
                    prefix, suffix = instruction + "\n\n", "\n\n" + question
                    if not compressed_docs.startswith(prefix) or not compressed_docs.endswith(suffix):
                        raise RuntimeError("API no longer preserves instruction/question boundaries")
                    compressed_docs = compressed_docs[len(prefix):-len(suffix)].strip()
                    audited_target = compressor.context_budget_audit["fine_context_target"]
                    if abs(audited_target - expected_context_target) > 1e-8:
                        raise RuntimeError("Actual context target differs from the released API budget equation")
                if not compressed_docs:
                    raise RuntimeError(f"Empty compressed prompt for id={sample['id']} at {target_ratio}x")
                release_mps_cache(torch, device)
                prompt_tokens = len(render_input_ids(measurement_tokenizer, compressed_docs, sample["question"]))
                achieved_ratio = original_prompt_tokens / prompt_tokens
                row = {
                    "id": sample["id"],
                    "question": sample["question"],
                    "answers": sample["answers"],
                    "compressed_docs": compressed_docs,
                    "target_compression_ratio": int(target_ratio),
                    "target_rate": 1.0 / float(target_ratio),
                    "original_prompt_tokens": original_prompt_tokens,
                    "prompt_tokens": prompt_tokens,
                    "retained_fraction": prompt_tokens / original_prompt_tokens,
                    "compression_ratio": achieved_ratio,
                    "compression_latency": compression_latency,
                    "compressor_origin_tokens": int(compressed.get("origin_tokens") or 0),
                    "compressor_compressed_tokens": int(compressed.get("compressed_tokens") or 0),
                    "num_context_units": len(units),
                    "selected_context_indices": selected_units,
                    "source_text_preserved": "".join(units) == sample["docs"],
                    "preprocessing_version": "preserve_source_v2",
                    "context_unit_tokens": args.context_unit_tokens,
                    "context_budget": args.context_budget,
                    "context_budget_audit": dict(compressor.context_budget_audit),
                    "component_token_lengths": component_lengths,
                    "coarse_context_budget": expected_context_target * 2 if recipe == "author_release" else None,
                    "iterative_size": args.iterative_size,
                    "use_context_level_filter": True,
                    "use_sentence_level_filter": False,
                    "use_token_level_filter": True,
                    "question_compressed": False,
                    "condition_in_question": "none",
                    "distribution_alignment_trained": False,
                    "pretrained_alignment": "alpaca_instruction_tuned" if recipe == "author_release" else "none",
                    "instruction_compressed": False,
                    "instruction_question_policy": "preserved_by_released_api",
                    "paper_component_rates_implemented": False,
                    "recipe": recipe,
                    "compressor_revision": args.revision,
                    "compressor_original_pad_token_id": getattr(compressor, "original_pad_token_id", compressor.model.config.pad_token_id),
                    "compressor_effective_pad_token_id": compressor.model.config.pad_token_id,
                    "compressor_loading_verified": getattr(compressor, "loading_verified", False),
                    "compressor_lm_head_key_remapped": getattr(compressor, "lm_head_key_remapped", False),
                    "mps_cache_cleared_between_jobs": device == "mps",
                    "rank_method": "llmlingua",
                    "compressor_model": args.compressor_model,
                    "tokenizer_model": args.tokenizer_model,
                    "target_model": MIRROR_MODEL_ID,
                    "method": method,
                }
                append_jsonl(sink, row)
                done.add(key)
                new_rows += 1
                print(f"[{job}/{total_jobs}] id={sample['id']} target={target_ratio}x units={len(units)} tokens={original_prompt_tokens}->{prompt_tokens} actual={achieved_ratio:.2f}x compress={compression_latency:.1f}s", flush=True)
    rows = load_jsonl(args.jsonl)
    payload = {
        "stage": "compression",
        "method": method,
        "recipe": recipe,
        "compressor_revision": args.revision,
        "dataset": "multifieldqa_en",
        "compressor_model": args.compressor_model,
        "tokenizer_model": args.tokenizer_model,
        "target_model": MIRROR_MODEL_ID,
        "device": device,
        "target_compression_ratios": args.ratios,
        "context_unit_tokens": args.context_unit_tokens,
        "context_budget": args.context_budget,
        "iterative_size": args.iterative_size,
        "preprocessing_version": "preserve_source_v2",
        "runtime_versions": runtime_versions,
        "mps_cache_cleared_between_jobs": device == "mps",
        "sample_indices": args.sample_indices,
        "started_at": started_at,
        "finished_at": utc_now(),
        "num_results": len(rows),
        "summary": summarize(rows),
        "results": rows,
    }
    write_json(args.output, payload)
    print(f"[done] {new_rows} new rows -> {args.output}")
    return 0
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, default=SAMPLES_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample-indices", nargs="+", type=int, default=None)
    parser.add_argument("--ratios", nargs="+", type=int, default=[2, 4])
    parser.add_argument("--compressor-model", default=DEFAULT_COMPRESSOR)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--tokenizer-model", default=DEFAULT_MEASUREMENT_TOKENIZER)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    parser.add_argument("--iterative-size", type=int, default=200)
    parser.add_argument("--context-unit-tokens", type=int, default=512)
    parser.add_argument("--context-budget", default="+100")
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_COMPRESSED_JSONL)
    parser.add_argument("--output", type=Path, default=DEFAULT_COMPRESSED_JSON)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.set_defaults(resume=True)
    return parser
def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))
if __name__ == "__main__":
    sys.exit(main())
