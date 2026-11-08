"""Part 4 - LLMLingua-enhanced prompt compression (Member 4).

Part 3 compressed every LongBench sample with ``microsoft/phi-2``, a 2k-context
model.  Almost every document (98.7% of the rows) therefore had to be cut into
several independent chunks before compression, and each chunk was ranked without
seeing the rest of the document or the question.  The resulting F1 (0.2626 at 2x,
0.2207 at 4x) was *worse* than plain head-and-tail truncation (0.4065 / 0.3620),
which contradicts the LLMLingua paper.

Part 4 keeps the experiment identical in every other respect (same 150 samples,
same prompt template, same target model, same metrics, same 2x / 4x ratios) and
changes exactly one thing: the compressor.  A long-context model
(``Qwen/Qwen2.5-1.5B-Instruct``, 32k positions) compresses the *whole* document in
a single pass with question-aware ranking, so no sample is chunked.

The experiment stays split into two commands so the compressor and the target LLM
never occupy GPU memory at the same time.

Examples
--------
Compress three samples at 2x and 4x (smoke test):
    python part4_llmlingua_enhanced/run_llmlingua_enhanced.py compress --limit 3

Answer and score every compressed row produced by the first command:
    python part4_llmlingua_enhanced/run_llmlingua_enhanced.py evaluate

Both stages append to JSONL checkpoints after every sample and resume by default.
Use ``--no-resume`` when intentionally starting a fresh run.
"""

from __future__ import annotations

import argparse
import json
import os
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
DEFAULT_COMPRESSED_JSONL = PART_DIR / "results_member4_compressed.jsonl"
DEFAULT_COMPRESSED_JSON = PART_DIR / "results_member4_compressed.json"
DEFAULT_RESULTS_JSONL = PART_DIR / "results_member4.jsonl"
DEFAULT_RESULTS_JSON = PART_DIR / "results_member4.json"

# Long-context compressor.  Part 3 used microsoft/phi-2 (2,048 positions), which
# forced chunking; this model has 32,768 positions, more than any sample needs.
DEFAULT_COMPRESSOR = "Qwen/Qwen2.5-1.5B-Instruct"
# Prompt lengths are measured with the *target* tokenizer so the reported token
# counts are directly comparable with Part 1-3 rows in the combined table.
DEFAULT_MEASUREMENT_TOKENIZER = MIRROR_MODEL_ID
METHOD = "llmlingua_enhanced"


# --------------------------------------------------------------------------- #
# Third-party compatibility shims
# --------------------------------------------------------------------------- #
def install_transformers_cache_patch() -> bool:
    """Make llmlingua's legacy KV-cache code work with modern transformers.

    ``llmlingua==0.2.2`` stores the KV cache as a list of ``[key, value]`` pairs
    and indexes it (``past_key_values[0][0]``).  Modern transformers returns a
    ``DynamicCache`` object, which is not subscriptable, so token-level
    compression crashes on the second step of its sliding window.  The wrapper
    converts in both directions and is a no-op on transformers 4.x, where the
    cache is already a legacy tuple.
    """
    try:
        import llmlingua
        from transformers import DynamicCache
    except Exception as exc:  # pragma: no cover - dependency missing
        print(f"[warn] cannot install transformers cache patch: {exc}")
        return False

    if getattr(llmlingua.PromptCompressor, "_part4_cache_patch", False):
        return True

    def is_cache_object(value: Any) -> bool:
        return hasattr(value, "get_seq_length")

    def to_legacy(cache: Any) -> Any:
        if not is_cache_object(cache):
            return cache
        if hasattr(cache, "layers"):
            return [[layer.keys, layer.values] for layer in cache.layers]
        if hasattr(cache, "to_legacy_cache"):
            return [[pair[0], pair[1]] for pair in cache.to_legacy_cache()]
        return [[k, v] for k, v in zip(cache.key_cache, cache.value_cache)]

    def from_legacy(legacy: Any) -> Any:
        if is_cache_object(legacy):
            return legacy
        cache = DynamicCache()
        for index, layer in enumerate(legacy):
            cache.update(layer[0], layer[1], index)
        return cache

    original_init = llmlingua.PromptCompressor.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        original_forward = self.model.forward

        def forward(*fargs, past_key_values=None, **fkwargs):
            if past_key_values is not None:
                past_key_values = from_legacy(past_key_values)
            output = original_forward(
                *fargs, past_key_values=past_key_values, **fkwargs
            )
            if getattr(output, "past_key_values", None) is not None:
                output.past_key_values = to_legacy(output.past_key_values)
            return output

        self.model.forward = forward

        original_get_ppl = self.get_ppl

        def get_ppl(*gargs, **gkwargs):
            result = original_get_ppl(*gargs, **gkwargs)
            if (
                gkwargs.get("return_kv")
                and isinstance(result, tuple)
                and len(result) == 2
            ):
                return result[0], to_legacy(result[1])
            return result

        self.get_ppl = get_ppl

    llmlingua.PromptCompressor.__init__ = patched_init
    llmlingua.PromptCompressor._part4_cache_patch = True
    return True


def install_safetensors_mmap_bypass() -> bool:
    """Fall back to a RAM read when memory-mapping a shard fails.

    Windows refuses to memory-map a multi-gigabyte safetensors shard when the
    pagefile is small (``OSError: [WinError 1455] The paging file is too small``).
    The default load path is kept because mapping costs no extra commit charge;
    only when it fails do we retry with ``disable_mmap=True``, which reads the
    shard into a buffer and therefore needs free physical memory instead.
    """
    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoModelForTokenClassification,
        )
    except Exception as exc:  # pragma: no cover - dependency missing
        print(f"[warn] cannot install safetensors mmap bypass: {exc}")
        return False

    for auto_class in (AutoModelForCausalLM, AutoModelForTokenClassification):
        if getattr(auto_class, "_part4_mmap_bypass", False):
            continue
        original = auto_class.from_pretrained.__func__

        def wrapper(cls_, *fargs, __original=original, **fkwargs):
            try:
                return __original(cls_, *fargs, **fkwargs)
            except BaseException as exc:
                if fkwargs.get("disable_mmap"):
                    raise
                print(
                    "[warn] memory-mapped weight load failed "
                    f"({type(exc).__name__}); retrying with disable_mmap=True",
                    flush=True,
                )
                fkwargs["disable_mmap"] = True
                return __original(cls_, *fargs, **fkwargs)

        auto_class.from_pretrained = classmethod(wrapper)
        auto_class._part4_mmap_bypass = True
    return True


def build_4bit_config(compute_dtype: Any) -> Any:
    """Build a bitsandbytes 4-bit config for the compressor model.

    The compressor only needs to score tokens, but it still has to hold the whole
    document, so quantizing the weights frees VRAM for the KV cache.  ``nf4`` with
    double quantization is the usual quality-preserving default.
    """
    try:
        import torch
    except Exception as exc:  # pragma: no cover - dependency missing
        raise RuntimeError(f"4-bit loading needs torch: {exc}") from exc
    try:
        from transformers import BitsAndBytesConfig
    except Exception as exc:  # pragma: no cover - dependency missing
        raise RuntimeError(
            "4-bit loading needs transformers.BitsAndBytesConfig"
        ) from exc
    try:
        import bitsandbytes  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "4-bit loading needs bitsandbytes; install it with "
            "`pip install bitsandbytes>=0.43`"
        ) from exc
    if compute_dtype is torch.float32:
        compute_dtype = torch.float16
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )


def ensure_nltk_sentence_tokenizer() -> None:
    """llmlingua splits sentences with ``nltk.sent_tokenize`` (Punkt data)."""
    try:
        import nltk
    except Exception:  # pragma: no cover - dependency missing
        return
    for resource in ("punkt_tab", "punkt"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception as exc:  # pragma: no cover - offline
                print(f"[warn] could not download nltk '{resource}': {exc}")


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


def memory_headroom() -> dict[str, float] | None:
    """Return RAM/commit headroom in GiB (Windows only); ``None`` elsewhere."""
    if os.name != "nt":
        return None
    import ctypes

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    gib = float(2**30)
    return {
        "ram_avail_gib": status.ullAvailPhys / gib,
        # On Windows the commit limit = RAM + pagefile, and mmap/load needs commit.
        "commit_avail_gib": status.ullAvailPageFile / gib,
    }


def check_memory_headroom(required_gib: float, label: str) -> None:
    """Fail fast when the host cannot commit enough memory to load a model.

    Without this guard Windows pages itself to death while safetensors maps a
    multi-GB shard, which freezes the whole desktop instead of raising a clean
    error.
    """
    info = memory_headroom()
    if info is None:
        return
    if info["commit_avail_gib"] >= required_gib:
        print(
            f"[memory] {label}: {info['commit_avail_gib']:.1f} GiB commit free, "
            f"{info['ram_avail_gib']:.1f} GiB RAM free",
            flush=True,
        )
        return
    raise SystemExit(
        f"[memory] not enough commit charge to load {label}: "
        f"{info['commit_avail_gib']:.1f} GiB free, {required_gib:.1f} GiB needed. "
        "Close memory-hungry apps or raise the pagefile, or run Part 4 on Colab. "
        "Pass --skip-memory-check to bypass this guard."
    )


def numeric_mean(rows: Iterable[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def chunk_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Report how many rows needed more than one compressor pass.

    Part 4 targets ``chunked_count = 0``: every document is compressed in a
    single call, so the distortion Part 3 suffered cannot happen here.
    """
    counts = [int(row.get("num_compression_chunks") or 1) for row in rows]
    if not counts:
        return {
            "chunked_count": 0,
            "mean_num_compression_chunks": None,
            "max_num_compression_chunks": 0,
        }
    return {
        "chunked_count": sum(1 for count in counts if count > 1),
        "mean_num_compression_chunks": sum(counts) / len(counts),
        "max_num_compression_chunks": max(counts),
    }


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
            "mean_compressor_input_tokens": numeric_mean(
                group, "compressor_input_tokens"
            ),
            **chunk_statistics(group),
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
            **chunk_statistics(group),
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
    if args.iterative_size <= 0:
        raise ValueError("--iterative-size must be greater than zero")

    if not args.resume:
        args.jsonl.unlink(missing_ok=True)
        args.output.unlink(missing_ok=True)

    existing = load_jsonl(args.jsonl) if args.resume else []
    done = {
        (str(row["id"]), int(row["target_compression_ratio"]))
        for row in existing
        if "id" in row and "target_compression_ratio" in row
    }

    install_transformers_cache_patch()
    install_safetensors_mmap_bypass()
    ensure_nltk_sentence_tokenizer()

    import torch
    from llmlingua import PromptCompressor
    from transformers import AutoTokenizer

    device = resolve_device(args.device)
    dtype = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[args.compressor_dtype]
    model_config: dict[str, Any] = {"trust_remote_code": True}
    if device in {"cuda", "mps"}:
        model_config["torch_dtype"] = dtype
    if args.load_in_4bit:
        model_config["quantization_config"] = build_4bit_config(dtype)

    print(
        f"[compress] loading {args.compressor_model} on {device}"
        f"{' (4-bit NF4)' if args.load_in_4bit else ''}; "
        f"measurement tokenizer={args.tokenizer_model}",
        flush=True,
    )
    if not args.skip_memory_check:
        check_memory_headroom(
            4.0 if args.load_in_4bit else 6.0,
            f"compressor {args.compressor_model}",
        )
    measurement_tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_model)
    compressor = PromptCompressor(
        model_name=args.compressor_model,
        device_map=device,
        model_config=model_config,
    )
    compressor_context_limit = int(
        getattr(compressor, "max_position_embeddings", 0) or 0
    )
    print(
        "[compress] compressor context window = "
        f"{compressor_context_limit} positions; "
        "every document is compressed in a single pass",
        flush=True,
    )

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    new_rows = 0
    total_jobs = len(samples) * len(args.ratios)

    with open(args.jsonl, "a", encoding="utf-8") as sink:
        job_number = 0
        for sample in samples:
            question = sample["question"]
            original_prompt_tokens = len(
                render_input_ids(measurement_tokenizer, sample["docs"], question)
            )
            compressor_input_tokens = len(
                compressor.tokenizer(sample["docs"], add_special_tokens=False)[
                    "input_ids"
                ]
            )
            exceeds_compressor_context = bool(
                compressor_context_limit
                and compressor_input_tokens >= compressor_context_limit
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
                    question=question,
                    rate=rate,
                    iterative_size=args.iterative_size,
                    use_context_level_filter=False,
                    use_sentence_level_filter=True,
                    use_token_level_filter=True,
                    condition_in_question=(
                        "after_condition" if args.condition_on_question else "none"
                    ),
                    rank_method="longllmlingua",
                    concate_question=False,
                )
                synchronize(torch, device)
                compression_latency = time.perf_counter() - started

                compressed_docs = (compressed["compressed_prompt"] or "").strip()
                if not compressed_docs:
                    raise RuntimeError(
                        f"compressor returned empty text for id={sample['id']} "
                        f"at {target_ratio}x"
                    )
                prompt_tokens = len(
                    render_input_ids(measurement_tokenizer, compressed_docs, question)
                )
                achieved_ratio = (
                    original_prompt_tokens / prompt_tokens if prompt_tokens else 0.0
                )
                compressor_origin_tokens = int(compressed.get("origin_tokens") or 0)
                compressor_compressed_tokens = int(
                    compressed.get("compressed_tokens") or 0
                )
                row = {
                    "id": sample["id"],
                    "question": question,
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
                    "compressor_origin_tokens": compressor_origin_tokens,
                    "compressor_compressed_tokens": compressor_compressed_tokens,
                    "compressor_reported_ratio": (
                        compressor_origin_tokens / compressor_compressed_tokens
                        if compressor_compressed_tokens
                        else None
                    ),
                    "compressor_input_tokens": compressor_input_tokens,
                    "compressor_max_position_embeddings": compressor_context_limit,
                    "exceeds_compressor_context": exceeds_compressor_context,
                    # Part 4 always compresses the full document in one pass.
                    "num_compression_chunks": 1,
                    "chunked": False,
                    "condition_on_question": bool(args.condition_on_question),
                    "rank_method": "longllmlingua",
                    "compressor_model": args.compressor_model,
                    "compressor_dtype": args.compressor_dtype,
                    "compressor_load_in_4bit": bool(args.load_in_4bit),
                    "tokenizer_model": args.tokenizer_model,
                    "target_model": MIRROR_MODEL_ID,
                    "method": METHOD,
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
        "method": METHOD,
        "dataset": "multifieldqa_en",
        "compressor_model": args.compressor_model,
        "compressor_dtype": args.compressor_dtype,
        "compressor_load_in_4bit": bool(args.load_in_4bit),
        "compressor_max_position_embeddings": compressor_context_limit,
        "condition_on_question": bool(args.condition_on_question),
        "rank_method": "longllmlingua",
        "tokenizer_model": args.tokenizer_model,
        "target_model": MIRROR_MODEL_ID,
        "device": device,
        "target_compression_ratios": args.ratios,
        "iterative_size": args.iterative_size,
        "started_at": started_at,
        "finished_at": utc_now(),
        "num_results": len(rows),
        "chunked_count": chunk_statistics(rows)["chunked_count"],
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
        allowed = set(allowed_ids)
        compressed_rows = [
            row for row in compressed_rows if str(row["id"]) in allowed
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

    if not args.skip_memory_check:
        check_memory_headroom(8.0, f"target model {args.model}")
    target = TargetModel(args.model, args.device, args.dtype)
    source_samples = {
        str(sample["id"]): sample for sample in load_samples(args.samples, limit=None)
    }
    missing_sample_ids = sorted(
        {str(row["id"]) for row in compressed_rows} - source_samples.keys()
    )
    if missing_sample_ids:
        raise KeyError(
            "compressed rows contain ids missing from the source samples: "
            + ", ".join(missing_sample_ids[:5])
        )
    original_prompt_tokens_by_id: dict[str, int] = {}
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
            sample_id = str(source["id"])
            if sample_id not in original_prompt_tokens_by_id:
                original_sample = source_samples[sample_id]
                original_prompt_tokens_by_id[sample_id] = len(
                    render_input_ids(
                        target.tokenizer,
                        original_sample["docs"],
                        original_sample["question"],
                    )
                )
            original_prompt_tokens = original_prompt_tokens_by_id[sample_id]
            evaluation_latency = time.perf_counter() - evaluation_started
            scores = score(answer, source["answers"])
            row = {
                "id": source["id"],
                "question": source["question"],
                "docs": source["compressed_docs"] if args.save_context else None,
                "prompt_tokens": measured_prompt_tokens,
                "original_prompt_tokens": original_prompt_tokens,
                "compression_measurement_original_prompt_tokens": source[
                    "original_prompt_tokens"
                ],
                "target_compression_ratio": source["target_compression_ratio"],
                "retained_fraction": (
                    measured_prompt_tokens / original_prompt_tokens
                    if original_prompt_tokens
                    else 0.0
                ),
                "compression_ratio": (
                    original_prompt_tokens / measured_prompt_tokens
                    if measured_prompt_tokens
                    else 0.0
                ),
                "compression_latency": source["compression_latency"],
                "num_compression_chunks": int(
                    source.get("num_compression_chunks") or 1
                ),
                "chunked": bool(int(source.get("num_compression_chunks") or 1) > 1),
                "compressor_input_tokens": source.get("compressor_input_tokens"),
                "answer": answer,
                "answers": source["answers"],
                "em": scores["em"],
                "f1": scores["f1"],
                "generation_latency": generation_latency,
                "evaluation_latency": evaluation_latency,
                "total_latency": source["compression_latency"] + evaluation_latency,
                "method": f"{METHOD}_{source['target_compression_ratio']}x",
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
        "method": METHOD,
        "dataset": "multifieldqa_en",
        "model": args.model,
        "device": target.device,
        "dtype": target.dtype_name,
        "max_new_tokens": args.max_new_tokens,
        "started_at": started_at,
        "finished_at": utc_now(),
        "num_results": len(rows),
        "chunked_count": chunk_statistics(rows)["chunked_count"],
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
        pieces.append(f"chunked={values.get('chunked_count', 0)}")
        print(f"[summary:{condition}] " + " ".join(pieces))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress = subparsers.add_parser(
        "compress", help="run the long-context LLMLingua compressor"
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
        "--compressor-dtype",
        choices=["float16", "bfloat16", "float32"],
        default="float16",
    )
    compress.add_argument(
        "--load-in-4bit",
        action="store_true",
        help=(
            "load the compressor in 4-bit NF4 instead of float16; needs "
            "bitsandbytes and roughly a quarter of the weights memory"
        ),
    )
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
    compress.add_argument(
        "--no-question-aware",
        dest="condition_on_question",
        action="store_false",
        help=(
            "disable question-aware ranking (condition_in_question='none'); "
            "the question is still required by rank_method='longllmlingua'"
        ),
    )
    compress.add_argument("--jsonl", type=Path, default=DEFAULT_COMPRESSED_JSONL)
    compress.add_argument("--output", type=Path, default=DEFAULT_COMPRESSED_JSON)
    compress.add_argument("--no-resume", dest="resume", action="store_false")
    compress.add_argument(
        "--skip-memory-check",
        action="store_true",
        help="load the compressor even if host commit charge looks too small",
    )
    compress.set_defaults(
        resume=True, condition_on_question=True, handler=run_compress
    )

    evaluate = subparsers.add_parser(
        "evaluate", help="generate answers from previously compressed contexts"
    )
    evaluate.add_argument("--input", type=Path, default=DEFAULT_COMPRESSED_JSONL)
    evaluate.add_argument("--samples", type=Path, default=SAMPLES_PATH)
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
    evaluate.add_argument(
        "--skip-memory-check",
        action="store_true",
        help="load the target model even if host commit charge looks too small",
    )
    evaluate.add_argument("--save-context", action="store_true")
    evaluate.set_defaults(resume=True, handler=run_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
