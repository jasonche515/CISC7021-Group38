"""Evaluate Part 2's head-tail algorithm at the author's achieved prompt budgets."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from part2_truncation.run_truncation import head_tail_truncate
from part3_llmlingua.run_llmlingua import TargetModel, append_jsonl, load_jsonl, utc_now, write_json, summarize_results
from shared.config import MIRROR_MODEL_ID, SAMPLES_PATH, MAX_NEW_TOKENS
from shared.metrics import score
from shared.prompt_template import render_input_ids
PART = Path(__file__).resolve().parent
def matched_context(tokenizer, docs: str, question: str, target_tokens: int):
    original_ids = tokenizer(docs, add_special_tokens=False)["input_ids"]
    def candidate(budget):
        text, _, _ = head_tail_truncate(tokenizer, docs, len(original_ids) / budget, 0.5)
        return text, len(render_input_ids(tokenizer, text, question))
    low, high, best_budget = 1, len(original_ids), 0
    best_text, best_tokens = "", len(render_input_ids(tokenizer, "", question))
    if best_tokens >= target_tokens:
        raise ValueError("Target budget does not leave document room")
    while low <= high:
        middle = (low + high) // 2
        text, tokens = candidate(middle)
        if tokens <= target_tokens:
            if tokens > best_tokens:
                best_text, best_tokens, best_budget = text, tokens, middle
            low = middle + 1
        else:
            high = middle - 1
    for budget in range(max(1, best_budget - 16), min(len(original_ids), best_budget + 16) + 1):
        text, tokens = candidate(budget)
        if best_tokens < tokens <= target_tokens:
            best_text, best_tokens = text, tokens
    if target_tokens - best_tokens > 2:
        raise RuntimeError("Cannot closely match target prompt budget")
    return best_text, best_tokens
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PART / "author_pilot3_results.json")
    parser.add_argument("--jsonl", type=Path, default=PART / "author_pilot3_matched_headtail.jsonl")
    parser.add_argument("--output", type=Path, default=PART / "author_pilot3_matched_headtail.json")
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    samples = {s["id"]: s for s in json.loads(SAMPLES_PATH.read_text())["samples"]}
    destination = args.jsonl
    existing = load_jsonl(destination)
    reference_by_key = {(row["id"], row["target_compression_ratio"]): row for row in source["results"]}
    for row in existing:
        key = (row["id"], row["target_compression_ratio"])
        if key not in reference_by_key or row["matched_prompt_budget"] != reference_by_key[key]["prompt_tokens"]:
            raise ValueError("Matched baseline checkpoint belongs to a different input/budget")
    done = {(row["id"], row["target_compression_ratio"]) for row in existing}
    target = TargetModel(MIRROR_MODEL_ID, "mps", "float16")
    started = utc_now()
    with destination.open("a", encoding="utf-8") as sink:
        for reference in source["results"]:
            key = (reference["id"], reference["target_compression_ratio"])
            if key in done:
                continue
            sample = samples[reference["id"]]
            docs, tokens = matched_context(target.tokenizer, sample["docs"], sample["question"], reference["prompt_tokens"])
            prediction, latency, actual_tokens = target.generate(docs, sample["question"], MAX_NEW_TOKENS)
            assert tokens == actual_tokens
            metrics = score(prediction, sample["answers"])
            row = {"id": sample["id"], "target_compression_ratio": reference["target_compression_ratio"], "question": sample["question"], "answers": sample["answers"], "answer": prediction, "docs": docs, "prompt_tokens": tokens, "matched_prompt_budget": reference["prompt_tokens"], "budget_gap_tokens": reference["prompt_tokens"] - tokens, "original_prompt_tokens": reference["original_prompt_tokens"], "compression_ratio": reference["original_prompt_tokens"] / tokens, "generation_latency": latency, "method": "head_tail_matched_author_budget", "model": MIRROR_MODEL_ID, "head_frac": 0.5, **metrics}
            append_jsonl(sink, row)
            done.add(key)
            print(f"[matched] id={key[0]} setting={key[1]}x tokens={tokens}/{reference['prompt_tokens']} f1={metrics['f1']:.4f}", flush=True)
    rows = load_jsonl(destination)
    if len(rows) != len(source["results"]) or done != {(r["id"], r["target_compression_ratio"]) for r in source["results"]}:
        raise RuntimeError("Matched baseline coverage differs")
    write_json(args.output, {"method": "head_tail_matched_author_budget", "started_at": started, "finished_at": utc_now(), "model": MIRROR_MODEL_ID, "device": "mps", "dtype": "float16", "num_results": len(rows), "summary": summarize_results(rows), "results": rows})
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
