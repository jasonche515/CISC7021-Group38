"""Part 2: head-and-tail truncation (Member 2).

Keeps the first and last tokens of the document and drops the middle so the
document has about 1/ratio of its tokens. Instruction and question are never
truncated. Output format mirrors part1_uncompressed/run_baseline.py.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import MAX_NEW_TOKENS, MODEL_ID, SAMPLES_PATH  # noqa: E402
from shared.metrics import mean_metrics, score  # noqa: E402
from shared.prompt_template import render_input_ids  # noqa: E402
from part1_uncompressed.run_baseline import (  # noqa: E402
    HFBackend,
    load_done_ids,
    load_jsonl,
    load_samples,
    write_json,
)

import json  # noqa: E402


def head_tail_truncate(tokenizer, docs, ratio, head_frac):
    ids = tokenizer(docs, add_special_tokens=False, verbose=False)["input_ids"]
    n_orig = len(ids)
    budget = max(1, round(n_orig / ratio))
    if budget >= n_orig:
        return docs, n_orig, n_orig
    head_n = int(budget * head_frac)
    tail_n = budget - head_n
    kept = ids[:head_n] + (ids[-tail_n:] if tail_n > 0 else [])
    text = tokenizer.decode(kept, skip_special_tokens=True)
    return text, n_orig, len(kept)


def run(args) -> int:
    tag = f"{args.ratio:g}x" + ("" if args.head_frac == 0.5 else f"_h{args.head_frac:g}")
    out_dir = args.out_dir or Path(__file__).resolve().parent
    output = out_dir / f"results_member2_{tag}.json"
    jsonl = output.with_suffix(".jsonl")
    method = f"head_tail_{args.ratio:g}x"

    samples = load_samples(args.samples, args.limit)
    if not samples:
        print("[error] no samples found; run `python shared/prepare_samples.py`")
        return 1

    done = load_done_ids(jsonl) if args.resume else set()
    if not args.resume:
        jsonl.unlink(missing_ok=True)

    backend = HFBackend(args.model, args.device, args.dtype)
    tok = backend.tokenizer
    print(
        f"[trunc] {len(samples)} samples, {len(done)} already done, "
        f"ratio={args.ratio:g}, head_frac={args.head_frac}",
        flush=True,
    )

    backend.generate(render_input_ids(tok, "warm up text", "Say hi."), 2)

    jsonl.parent.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    processed = 0

    with open(jsonl, "a", encoding="utf-8") as sink:
        for index, sample in enumerate(samples, start=1):
            if sample["id"] in done:
                continue

            question = sample["question"]
            original_prompt_tokens = len(render_input_ids(tok, sample["docs"], question))

            t0 = time.perf_counter()
            docs_c, n_orig, n_kept = head_tail_truncate(
                tok, sample["docs"], args.ratio, args.head_frac
            )
            compression_latency = time.perf_counter() - t0

            input_ids = render_input_ids(tok, docs_c, question)
            answer, generation_latency = backend.generate(input_ids, args.max_new_tokens)
            total_latency = time.perf_counter() - t0

            scores = score(answer, sample["answers"])
            record = {
                "id": sample["id"],
                "question": question,
                "docs": docs_c if args.save_context else None,
                "prompt_tokens": len(input_ids),
                "original_prompt_tokens": original_prompt_tokens,
                "truncated": n_kept < n_orig,
                "docs_chars_used": len(docs_c),
                "orig_docs_tokens": n_orig,
                "retained_docs_tokens": n_kept,
                "compression_ratio": n_orig / max(n_kept, 1),
                "prompt_compression_ratio": original_prompt_tokens / len(input_ids),
                "compression_latency": compression_latency,
                "answer": answer,
                "answers": sample["answers"],
                "em": scores["em"],
                "f1": scores["f1"],
                "generation_latency": generation_latency,
                "total_latency": total_latency,
                "method": method,
                "head_frac": args.head_frac,
                "model": args.model,
            }
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
            processed += 1

            print(
                f"[{index}/{len(samples)}] id={sample['id']} "
                f"docs {n_orig}->{n_kept} tokens={record['prompt_tokens']} "
                f"em={record['em']:.2f} f1={record['f1']:.3f} "
                f"gen={generation_latency:.1f}s pred={answer[:60]!r}",
                flush=True,
            )

    rows = load_jsonl(jsonl)
    summary = mean_metrics(rows)
    summary["truncated_samples"] = sum(1 for r in rows if r.get("truncated"))
    for key in ("compression_ratio", "prompt_compression_ratio", "compression_latency"):
        vals = [r[key] for r in rows if r.get(key) is not None]
        if vals:
            summary[f"mean_{key}"] = sum(vals) / len(vals)

    payload = {
        "method": method,
        "model": args.model,
        "dataset": "multifieldqa_en",
        "samples_file": str(args.samples),
        "target_ratio": args.ratio,
        "head_frac": args.head_frac,
        "max_new_tokens": args.max_new_tokens,
        "dtype": args.dtype,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "num_results": len(rows),
        "summary": summary,
        "results": rows,
    }
    write_json(output, payload)
    print(
        f"\n[done] {processed} new samples -> {output}\n"
        f"[summary] n={summary.get('num_samples')} "
        f"em={summary.get('mean_em', 0):.4f} f1={summary.get('mean_f1', 0):.4f} "
        f"prompt_tokens={summary.get('mean_prompt_tokens', 0):.1f} "
        f"doc_ratio={summary.get('mean_compression_ratio', 0):.2f} "
        f"total_latency={summary.get('mean_total_latency', 0):.2f}s",
        flush=True,
    )
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--samples", type=Path, default=SAMPLES_PATH)
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--ratio", type=float, default=2.0)
    p.add_argument("--head-frac", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--model", default=MODEL_ID)
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--dtype", choices=["auto", "float32", "float16", "bfloat16"], default="auto")
    p.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.add_argument("--save-context", action="store_true")
    p.set_defaults(resume=True)
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))