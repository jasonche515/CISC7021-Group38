"""Part 3 - LLMLingua prompt compression (Member 3).

The experiment is deliberately split into two separate commands so the
compressor and target LLM never have to occupy GPU memory at the same time.

Examples
--------
Compress one verified short sample at 2x (quick pilot):
    python part3_llmlingua/run_llmlingua.py compress --sample-indices 17 --ratios 2

Evaluate every compressed row produced by the first command:
    python part3_llmlingua/run_llmlingua.py evaluate

Both stages write JSONL checkpoints after every sample and resume by default.
Use ``--no-resume`` when intentionally starting a fresh run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import (  # noqa: E402
    MAX_NEW_TOKENS,
    MIRROR_MODEL_ID,
    SAMPLES_PATH,
)
from shared.metrics import score  # noqa: E402
from shared.prompt_template import render_input_ids  # noqa: E402

PART_DIR = Path(__file__).resolve().parent
DEFAULT_COMPRESSED_JSONL = PART_DIR / "compressed_member3.jsonl"
DEFAULT_COMPRESSED_JSON = PART_DIR / "compressed_member3.json"
DEFAULT_RESULTS_JSONL = PART_DIR / "results_member3.jsonl"
DEFAULT_RESULTS_JSON = PART_DIR / "results_member3.json"
DEFAULT_COMPRESSOR = "microsoft/phi-2"
DEFAULT_MEASUREMENT_TOKENIZER = "NousResearch/Llama-2-7b-hf"


# --------------------------------------------------------------------------- #
# Generic helpers
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_samples(
    path: Path,
    limit: int | None,
    indices: list[int] | None = None,
) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    samples = payload["samples"] if isinstance(payload, dict) else payload
    if indices is not None:
        invalid = [index for index in indices if index < 0 or index >= len(samples)]
        if invalid:
            raise IndexError(
                f"sample indices out of range for {len(samples)} samples: {invalid}"
            )
        samples = [samples[index] for index in indices]
    return samples[:limit] if limit else samples


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[warn] ignoring invalid JSONL line {line_number}: {path}")
    return rows


def append_jsonl(handle, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    temporary.replace(path)


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def synchronize(torch, device: str) -> None:
    """Synchronize asynchronous accelerators before latency measurements."""
    if device == "cuda":
        torch.cuda.synchronize()
    elif device == "mps" and hasattr(torch, "mps"):
        torch.mps.synchronize()


def numeric_mean(rows: Iterable[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def summarize_compression(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["target_compression_ratio"])].append(row)
    by_ratio: dict[str, Any] = {}
    for ratio, group in sorted(grouped.items()):
        by_ratio[f"{ratio}x"] = {
            "num_samples": len(group),
            "mean_original_prompt_tokens": numeric_mean(
                group, "original_prompt_tokens"
            ),
            "mean_prompt_tokens": numeric_mean(group, "prompt_tokens"),
            "mean_achieved_compression_ratio": numeric_mean(
                group, "compression_ratio"
            ),
            "mean_compression_latency": numeric_mean(
                group, "compression_latency"
            ),
        }
    return by_ratio


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["target_compression_ratio"])].append(row)
    by_ratio: dict[str, Any] = {}
    for ratio, group in sorted(grouped.items()):
        by_ratio[f"{ratio}x"] = {
            "num_samples": len(group),
            "mean_em": numeric_mean(group, "em"),
            "mean_f1": numeric_mean(group, "f1"),
            "mean_original_prompt_tokens": numeric_mean(
                group, "original_prompt_tokens"
            ),
            "mean_prompt_tokens": numeric_mean(group, "prompt_tokens"),
            "mean_achieved_compression_ratio": numeric_mean(
                group, "compression_ratio"
            ),
            "mean_compression_latency": numeric_mean(
                group, "compression_latency"
            ),
            "mean_generation_latency": numeric_mean(
                group, "generation_latency"
            ),
            "mean_total_latency": numeric_mean(group, "total_latency"),
        }
    return by_ratio


# --------------------------------------------------------------------------- #
# Stage 1: prompt compression
# --------------------------------------------------------------------------- #
def run_compress(args: argparse.Namespace) -> int:
    samples = load_samples(args.samples, args.limit, args.sample_indices)
    if not samples:
        print(f"[error] no samples found in {args.samples}")
        return 1

    invalid_ratios = [ratio for ratio in args.ratios if ratio <= 1]
    if invalid_ratios:
        raise ValueError(f"compression ratios must be greater than 1: {invalid_ratios}")

    if not args.resume:
        args.jsonl.unlink(missing_ok=True)
        args.output.unlink(missing_ok=True)

    existing = load_jsonl(args.jsonl) if args.resume else []
    done = {
        (str(row["id"]), int(row["target_compression_ratio"]))
        for row in existing
        if "id" in row and "target_compression_ratio" in row
    }

    import torch
    from llmlingua import PromptCompressor
    from transformers import AutoTokenizer

    device = resolve_device(args.device)
    model_config: dict[str, Any] = {"trust_remote_code": True}
    if device in {"cuda", "mps"}:
        model_config["torch_dtype"] = torch.float16

    print(
        f"[compress] loading {args.compressor_model} on {device}; "
        f"measurement tokenizer={args.tokenizer_model}",
        flush=True,
    )
    measurement_tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_model)
    compressor = PromptCompressor(
        model_name=args.compressor_model,
        device_map=device,
        model_config=model_config,
    )

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    new_rows = 0
    total_jobs = len(samples) * len(args.ratios)

    with open(args.jsonl, "a", encoding="utf-8") as sink:
        job_number = 0
        for sample in samples:
            original_prompt_tokens = len(
                render_input_ids(
                    measurement_tokenizer, sample["docs"], sample["question"]
                )
            )
            for target_ratio in args.ratios:
                job_number += 1
                key = (str(sample["id"]), int(target_ratio))
                if key in done:
                    print(
                        f"[{job_number}/{total_jobs}] skip id={sample['id']} "
                        f"target={target_ratio}x",
                        flush=True,
                    )
                    continue

                rate = 1.0 / float(target_ratio)
                synchronize(torch, device)
                started = time.perf_counter()
                compressed = compressor.compress_prompt(
                    sample["docs"],
                    instruction="",
                    question="",
                    rate=rate,
                    iterative_size=args.iterative_size,
                    use_context_level_filter=False,
                    use_sentence_level_filter=False,
                    use_token_level_filter=True,
                    rank_method="llmlingua",
                    concate_question=False,
                )
                synchronize(torch, device)
                compression_latency = time.perf_counter() - started

                compressed_docs = compressed["compressed_prompt"].strip()
                if not compressed_docs:
                    raise RuntimeError(
                        f"compressor returned empty text for id={sample['id']} "
                        f"at {target_ratio}x"
                    )
                prompt_tokens = len(
                    render_input_ids(
                        measurement_tokenizer, compressed_docs, sample["question"]
                    )
                )
                achieved_ratio = (
                    original_prompt_tokens / prompt_tokens if prompt_tokens else 0.0
                )
                row = {
                    "id": sample["id"],
                    "question": sample["question"],
                    "answers": sample["answers"],
                    "compressed_docs": compressed_docs,
                    "target_compression_ratio": int(target_ratio),
                    "target_rate": rate,
                    "original_prompt_tokens": original_prompt_tokens,
                    "prompt_tokens": prompt_tokens,
                    "retained_fraction": (
                        prompt_tokens / original_prompt_tokens
                        if original_prompt_tokens
                        else 0.0
                    ),
                    "compression_ratio": achieved_ratio,
                    "compression_latency": compression_latency,
                    "compressor_origin_tokens": compressed.get("origin_tokens"),
                    "compressor_compressed_tokens": compressed.get(
                        "compressed_tokens"
                    ),
                    "compressor_reported_ratio": compressed.get("ratio"),
                    "compressor_model": args.compressor_model,
                    "tokenizer_model": args.tokenizer_model,
                    "target_model": MIRROR_MODEL_ID,
                    "method": "llmlingua",
                }
                append_jsonl(sink, row)
                done.add(key)
                new_rows += 1
                print(
                    f"[{job_number}/{total_jobs}] id={sample['id']} "
                    f"target={target_ratio}x tokens={original_prompt_tokens}"
                    f"->{prompt_tokens} actual={achieved_ratio:.2f}x "
                    f"compress={compression_latency:.1f}s",
                    flush=True,
                )

    rows = load_jsonl(args.jsonl)
    payload = {
        "stage": "compression",
        "method": "llmlingua",
        "dataset": "multifieldqa_en",
        "compressor_model": args.compressor_model,
        "tokenizer_model": args.tokenizer_model,
        "target_model": MIRROR_MODEL_ID,
        "device": device,
        "target_compression_ratios": args.ratios,
        "iterative_size": args.iterative_size,
        "started_at": started_at,
        "finished_at": utc_now(),
        "num_results": len(rows),
        "summary": summarize_compression(rows),
        "results": rows,
    }
    write_json(args.output, payload)
    print(f"\n[done] {new_rows} new compressed rows -> {args.output}")
    _print_summary(payload["summary"])
    return 0


# --------------------------------------------------------------------------- #
# Stage 2: answer generation and evaluation
# --------------------------------------------------------------------------- #
class TargetModel:
    def __init__(self, model_id: str, device: str, dtype: str):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.device = resolve_device(device)
        if dtype == "auto":
            dtype = "float16" if self.device in {"cuda", "mps"} else "float32"
        self.dtype_name = dtype
        torch_dtype = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }[dtype]

        print(f"[evaluate] loading {model_id} on {self.device} ({dtype})")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        dtype_kwarg = (
            "dtype"
            if int(transformers.__version__.split(".")[0]) >= 5
            else "torch_dtype"
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            low_cpu_mem_usage=True,
            **{dtype_kwarg: torch_dtype},
        )
        self.model.to(self.device)
        self.model.eval()

    def generate(self, docs: str, question: str, max_new_tokens: int):
        input_ids = render_input_ids(self.tokenizer, docs, question)
        ids = self.torch.tensor([input_ids], device=self.device)
        attention_mask = self.torch.ones_like(ids)
        synchronize(self.torch, self.device)
        started = time.perf_counter()
        with self.torch.inference_mode():
            output = self.model.generate(
                input_ids=ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id
                or self.tokenizer.eos_token_id,
            )
        synchronize(self.torch, self.device)
        latency = time.perf_counter() - started
        new_tokens = output[0][ids.shape[1] :]
        answer = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        return answer, latency, len(input_ids)


def run_evaluate(args: argparse.Namespace) -> int:
    compressed_rows = load_jsonl(args.input)
    if args.limit:
        # ``--limit`` means N source samples, therefore keep both ratio rows.
        allowed_ids: list[str] = []
        for row in compressed_rows:
            sample_id = str(row["id"])
            if sample_id not in allowed_ids:
                allowed_ids.append(sample_id)
            if len(allowed_ids) >= args.limit:
                break
        compressed_rows = [
            row for row in compressed_rows if str(row["id"]) in set(allowed_ids)
        ]
    if not compressed_rows:
        print(f"[error] no compressed rows found in {args.input}")
        return 1

    if not args.resume:
        args.jsonl.unlink(missing_ok=True)
        args.output.unlink(missing_ok=True)
    existing = load_jsonl(args.jsonl) if args.resume else []
    done = {
        (str(row["id"]), int(row["target_compression_ratio"]))
        for row in existing
        if "id" in row and "target_compression_ratio" in row
    }

    target = TargetModel(args.model, args.device, args.dtype)
    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    new_rows = 0

    with open(args.jsonl, "a", encoding="utf-8") as sink:
        for index, source in enumerate(compressed_rows, start=1):
            key = (str(source["id"]), int(source["target_compression_ratio"]))
            if key in done:
                continue

            evaluation_started = time.perf_counter()
            answer, generation_latency, measured_prompt_tokens = target.generate(
                source["compressed_docs"],
                source["question"],
                args.max_new_tokens,
            )
            evaluation_latency = time.perf_counter() - evaluation_started
            scores = score(answer, source["answers"])
            row = {
                "id": source["id"],
                "question": source["question"],
                "docs": source["compressed_docs"] if args.save_context else None,
                "prompt_tokens": measured_prompt_tokens,
                "original_prompt_tokens": source["original_prompt_tokens"],
                "target_compression_ratio": source["target_compression_ratio"],
                "retained_fraction": (
                    measured_prompt_tokens / source["original_prompt_tokens"]
                    if source["original_prompt_tokens"]
                    else 0.0
                ),
                "compression_ratio": (
                    source["original_prompt_tokens"] / measured_prompt_tokens
                    if measured_prompt_tokens
                    else 0.0
                ),
                "compression_latency": source["compression_latency"],
                "answer": answer,
                "answers": source["answers"],
                "em": scores["em"],
                "f1": scores["f1"],
                "generation_latency": generation_latency,
                "evaluation_latency": evaluation_latency,
                "total_latency": source["compression_latency"]
                + evaluation_latency,
                "method": f"llmlingua_{source['target_compression_ratio']}x",
                "compressor_model": source["compressor_model"],
                "model": args.model,
            }
            append_jsonl(sink, row)
            done.add(key)
            new_rows += 1
            print(
                f"[{index}/{len(compressed_rows)}] id={source['id']} "
                f"target={source['target_compression_ratio']}x "
                f"tokens={measured_prompt_tokens} em={scores['em']:.2f} "
                f"f1={scores['f1']:.3f} gen={generation_latency:.1f}s "
                f"pred={answer[:60]!r}",
                flush=True,
            )

    rows = load_jsonl(args.jsonl)
    payload = {
        "stage": "evaluation",
        "method": "llmlingua",
        "dataset": "multifieldqa_en",
        "model": args.model,
        "device": target.device,
        "dtype": target.dtype_name,
        "max_new_tokens": args.max_new_tokens,
        "started_at": started_at,
        "finished_at": utc_now(),
        "num_results": len(rows),
        "summary": summarize_results(rows),
        "results": rows,
    }
    write_json(args.output, payload)
    print(f"\n[done] {new_rows} new evaluated rows -> {args.output}")
    _print_summary(payload["summary"])
    return 0


def _print_summary(summary: dict[str, Any]) -> None:
    for condition, values in summary.items():
        pieces = [f"n={values['num_samples']}"]
        for key in (
            "mean_achieved_compression_ratio",
            "mean_em",
            "mean_f1",
            "mean_compression_latency",
            "mean_generation_latency",
        ):
            value = values.get(key)
            if value is not None:
                pieces.append(f"{key.removeprefix('mean_')}={value:.4f}")
        print(f"[summary:{condition}] " + " ".join(pieces))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress = subparsers.add_parser(
        "compress", help="run LLMLingua and save compressed contexts"
    )
    compress.add_argument("--samples", type=Path, default=SAMPLES_PATH)
    compress.add_argument("--limit", type=int, default=None)
    compress.add_argument(
        "--sample-indices",
        nargs="+",
        type=int,
        default=None,
        help="zero-based source-sample indices to run (for example: 17)",
    )
    compress.add_argument("--ratios", nargs="+", type=int, default=[2, 4])
    compress.add_argument("--compressor-model", default=DEFAULT_COMPRESSOR)
    compress.add_argument(
        "--tokenizer-model",
        "--target-model",
        dest="tokenizer_model",
        default=DEFAULT_MEASUREMENT_TOKENIZER,
        help=(
            "tokenizer used only to measure prompt lengths; --target-model is "
            "retained as a backwards-compatible alias"
        ),
    )
    compress.add_argument(
        "--device", choices=["auto", "cpu", "cuda", "mps"], default="auto"
    )
    compress.add_argument("--iterative-size", type=int, default=200)
    compress.add_argument("--jsonl", type=Path, default=DEFAULT_COMPRESSED_JSONL)
    compress.add_argument("--output", type=Path, default=DEFAULT_COMPRESSED_JSON)
    compress.add_argument("--no-resume", dest="resume", action="store_false")
    compress.set_defaults(resume=True, handler=run_compress)

    evaluate = subparsers.add_parser(
        "evaluate", help="generate answers from previously compressed contexts"
    )
    evaluate.add_argument("--input", type=Path, default=DEFAULT_COMPRESSED_JSONL)
    evaluate.add_argument("--limit", type=int, default=None)
    evaluate.add_argument("--model", default=MIRROR_MODEL_ID)
    evaluate.add_argument(
        "--device", choices=["auto", "cpu", "cuda", "mps"], default="auto"
    )
    evaluate.add_argument(
        "--dtype",
        choices=["auto", "float32", "float16", "bfloat16"],
        default="auto",
    )
    evaluate.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    evaluate.add_argument("--jsonl", type=Path, default=DEFAULT_RESULTS_JSONL)
    evaluate.add_argument("--output", type=Path, default=DEFAULT_RESULTS_JSON)
    evaluate.add_argument("--no-resume", dest="resume", action="store_false")
    evaluate.add_argument("--save-context", action="store_true")
    evaluate.set_defaults(resume=True, handler=run_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
