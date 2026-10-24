"""Part 1 - Uncompressed baseline (Member 1).

Full-context prompting with no compression: every retrieved document, the
question and the instruction are concatenated and sent to
Llama-3.2-3B-Instruct. Produces one result record per sample in the shared
JSON format so the three methods can be merged into a single table.

Examples
--------
Local HF (CPU / GPU):
    python part1_uncompressed/run_baseline.py --limit 5

Full run, resumable:
    python part1_uncompressed/run_baseline.py

Against a Colab / vLLM OpenAI-compatible server:
    python part1_uncompressed/run_baseline.py --backend openai \
        --base-url http://127.0.0.1:8000/v1 --model meta-llama/Llama-3.2-3B-Instruct
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows consoles default to cp1252/cp950 and crash on characters outside the
# code page (e.g. Arabic, CJK, emoji in model output). Never let logging kill a
# multi-hour run: replace unencodable characters instead.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import (  # noqa: E402
    MAX_NEW_TOKENS,
    MAX_PROMPT_TOKENS,
    MODEL_ID,
    SAMPLES_PATH,
    TEMPERATURE,
)
from shared.metrics import mean_metrics, score  # noqa: E402
from shared.prompt_template import build_messages, build_with_budget  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results_member1.json"


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #
class HFBackend:
    """Local transformers backend (CPU or CUDA)."""

    def __init__(self, model_id: str, device: str, dtype: str):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        if dtype == "auto":
            dtype = "bfloat16" if device == "cuda" else "float32"
        self.torch_dtype = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }[dtype]

        print(f"[hf] loading {model_id} on {device} ({dtype})", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # transformers 5 renamed ``torch_dtype`` to ``dtype``.
        dtype_kwarg = (
            "dtype"
            if int(transformers.__version__.split(".")[0]) >= 5
            else "torch_dtype"
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, **{dtype_kwarg: self.torch_dtype}
        )
        self.model.to(device)
        self.model.eval()

    def prompt_tokens(self, docs: str, question: str, max_prompt_tokens: int):
        return build_with_budget(
            self.tokenizer, docs, question, max_prompt_tokens
        )

    def clear_cache(self) -> None:
        if self.device == "cuda":
            self.torch.cuda.empty_cache()

    def generate(self, input_ids, max_new_tokens: int):
        torch = self.torch
        ids = torch.tensor([input_ids], device=self.device)
        attention_mask = torch.ones_like(ids)
        start = time.perf_counter()
        with torch.inference_mode():
            output = self.model.generate(
                input_ids=ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id
                or self.tokenizer.eos_token_id,
            )
        latency = time.perf_counter() - start
        new_tokens = output[0][ids.shape[1] :]
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        return text.strip(), latency


class OpenAIBackend:
    """Any OpenAI-compatible chat endpoint (vLLM, TGI, Colab server, ...)."""

    def __init__(self, model_id: str, base_url: str, api_key: str):
        self.model_id = model_id
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key

    def prompt_tokens(self, docs: str, question: str, max_prompt_tokens: int):
        # No local tokenizer: send the full prompt and let the server report
        # the token count. Truncation is therefore not applied client-side.
        return docs, None, {
            "original_prompt_tokens": None,
            "prompt_tokens": None,
            "truncated": False,
            "docs_chars_used": len(docs),
        }

    def generate(self, docs: str, question: str, max_new_tokens: int, temperature: float):
        import requests

        payload = {
            "model": self.model_id,
            "messages": build_messages(docs, question),
            "max_tokens": max_new_tokens,
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        start = time.perf_counter()
        response = requests.post(self.url, json=payload, headers=headers, timeout=600)
        response.raise_for_status()
        latency = time.perf_counter() - start
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        prompt_tokens = (data.get("usage") or {}).get("prompt_tokens")
        return text, latency, prompt_tokens


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def load_samples(path: Path, limit: int | None):
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    samples = payload["samples"] if isinstance(payload, dict) else payload
    return samples[:limit] if limit else samples


def load_done_ids(jsonl_path: Path) -> set:
    done = set()
    if not jsonl_path.exists():
        return done
    with open(jsonl_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def load_jsonl(jsonl_path: Path):
    rows = []
    if not jsonl_path.exists():
        return rows
    with open(jsonl_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def write_json(path: Path, payload) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def run(args) -> int:
    samples = load_samples(args.samples, args.limit)
    if not samples:
        print("[error] no samples found; run `python shared/prepare_samples.py`")
        return 1

    done = load_done_ids(args.jsonl) if args.resume else set()
    if not args.resume:
        args.jsonl.unlink(missing_ok=True)

    if args.backend == "hf":
        if args.temperature > 0:
            print(
                "[warn] --temperature is ignored by the hf backend "
                "(greedy decoding is required for the baseline)",
                flush=True,
            )
        backend = HFBackend(args.model, args.device, args.dtype)
        max_prompt_tokens = args.max_prompt_tokens
        print(
            f"[hf] {len(samples)} samples, {len(done)} already done, "
            f"prompt budget {max_prompt_tokens} tokens",
            flush=True,
        )
    else:
        backend = OpenAIBackend(args.model, args.base_url, args.api_key)
        max_prompt_tokens = None
        print(f"[openai] {len(samples)} samples -> {backend.url}", flush=True)

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    processed = 0

    with open(args.jsonl, "a", encoding="utf-8") as sink:
        for index, sample in enumerate(samples, start=1):
            if sample["id"] in done:
                continue

            total_start = time.perf_counter()
            docs = sample["docs"]
            question = sample["question"]

            if args.backend == "hf":
                docs, input_ids, info = backend.prompt_tokens(
                    docs, question, max_prompt_tokens
                )
                try:
                    answer, generation_latency = backend.generate(
                        input_ids, args.max_new_tokens
                    )
                except Exception as exc:  # noqa: BLE001 - OOM fallback
                    if not _is_oom(exc):
                        raise
                    backend.clear_cache()
                    reduced = max(64, (max_prompt_tokens or 0) // 2)
                    print(
                        f"[oom] {sample['id']}: retry with budget {reduced}",
                        flush=True,
                    )
                    docs, input_ids, info = backend.prompt_tokens(
                        docs, question, reduced
                    )
                    answer, generation_latency = backend.generate(
                        input_ids, args.max_new_tokens
                    )
                    info["oom_fallback"] = True
            else:
                answer, generation_latency, reported_tokens = backend.generate(
                    docs, question, args.max_new_tokens, args.temperature
                )
                info = {
                    "original_prompt_tokens": reported_tokens,
                    "prompt_tokens": reported_tokens,
                    "truncated": False,
                    "docs_chars_used": len(docs),
                }

            total_latency = time.perf_counter() - total_start
            scores = score(answer, sample["answers"])
            record = {
                "id": sample["id"],
                "question": question,
                "docs": docs if args.save_context else None,
                "prompt_tokens": info["prompt_tokens"],
                "original_prompt_tokens": info["original_prompt_tokens"],
                "truncated": info["truncated"],
                "docs_chars_used": info["docs_chars_used"],
                "compression_ratio": 1.0,
                "compression_latency": 0.0,
                "answer": answer,
                "answers": sample["answers"],
                "em": scores["em"],
                "f1": scores["f1"],
                "generation_latency": generation_latency,
                "total_latency": total_latency,
                "method": "uncompressed",
                "model": args.model,
            }
            if info.get("oom_fallback"):
                record["oom_fallback"] = True

            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
            processed += 1

            print(
                f"[{index}/{len(samples)}] id={sample['id']} "
                f"tokens={record['prompt_tokens']} "
                f"{'TRUNC ' if record['truncated'] else ''}"
                f"em={record['em']:.2f} f1={record['f1']:.3f} "
                f"gen={generation_latency:.1f}s "
                f"pred={answer[:60]!r}",
                flush=True,
            )

    rows = load_jsonl(args.jsonl)
    summary = mean_metrics(rows)
    summary["truncated_samples"] = sum(1 for row in rows if row.get("truncated"))
    payload = {
        "method": "uncompressed",
        "model": args.model,
        "dataset": "multifieldqa_en",
        "samples_file": str(args.samples),
        "backend": args.backend,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "max_prompt_tokens": max_prompt_tokens,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "num_results": len(rows),
        "summary": summary,
        "results": rows,
    }
    write_json(args.output, payload)
    print(
        f"\n[done] {processed} new samples -> {args.output}\n"
        f"[summary] n={summary.get('num_samples')} "
        f"em={summary.get('mean_em', 0):.4f} "
        f"f1={summary.get('mean_f1', 0):.4f} "
        f"prompt_tokens={summary.get('mean_prompt_tokens', 0):.1f} "
        f"total_latency={summary.get('mean_total_latency', 0):.1f}s",
        flush=True,
    )
    return 0


def _is_oom(exc: Exception) -> bool:
    name = type(exc).__name__
    return (
        isinstance(exc, MemoryError)
        or "OutOfMemory" in name
        or "out of memory" in str(exc).lower()
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, default=SAMPLES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=DEFAULT_OUTPUT.with_suffix(".jsonl"),
        help="checkpoint file, one JSON record per line",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--backend", choices=["hf", "openai"], default="hf")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument(
        "--dtype",
        choices=["auto", "float32", "float16", "bfloat16"],
        default="auto",
    )
    parser.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    parser.add_argument("--max-prompt-tokens", type=int, default=MAX_PROMPT_TOKENS)
    parser.add_argument("--temperature", type=float, default=TEMPERATURE)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument(
        "--save-context",
        action="store_true",
        help="store the (possibly truncated) context in the results file",
    )
    parser.set_defaults(resume=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
