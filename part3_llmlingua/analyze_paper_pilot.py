"""Compare the fixed length-stratified pilot and audit coarse context selection."""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import mean, stdev
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from part3_llmlingua.run_llmlingua_paper import split_natural_units
from shared.config import SAMPLES_PATH
from shared.metrics import normalize_answer, score
PART = Path(__file__).resolve().parent
PILOT_INDICES = [17, 75, 130, 125, 23]
def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
def contains_gold(text: str, answers: list[str]) -> bool:
    normalized = " " + normalize_answer(text) + " "
    return any(normalize_answer(answer) and " " + normalize_answer(answer) + " " in normalized for answer in answers)
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compressed", type=Path, default=PART / "paper_pilot5_compressed.json")
    parser.add_argument("--results", type=Path, default=PART / "paper_pilot5_results.json")
    parser.add_argument("--out-dir", type=Path, default=PART / "paper_pilot5_analysis")
    parser.add_argument("--all-samples", action="store_true", help="analyze all shared samples instead of the fixed five-sample pilot")
    parser.add_argument("--sample-indices", nargs="+", type=int, default=None)
    parser.add_argument("--matched-baseline", type=Path, default=None)
    args = parser.parse_args()
    from transformers import AutoTokenizer
    samples = read(SAMPLES_PATH)["samples"]
    if args.all_samples and args.sample_indices is not None:
        parser.error("Choose either --all-samples or --sample-indices")
    indices = list(range(len(samples))) if args.all_samples else (args.sample_indices or PILOT_INDICES)
    selected = {str(samples[index]["id"]): (index, samples[index]) for index in indices}
    sample_count = len(selected)
    compressed_payload = read(args.compressed)
    author_recipe = compressed_payload.get("recipe") == "author_release"
    current_label = "Author-recipe LLMLingua" if author_recipe else "Official-API LLMLingua"
    results_payload = read(args.results)
    matched_path = args.matched_baseline or args.results.with_name(args.results.stem.removesuffix("_results") + "_matched_headtail.json")
    matched = read(matched_path) if author_recipe and matched_path.exists() else None
    compressed = {(str(row["id"]), int(row["target_compression_ratio"])): row for row in compressed_payload["results"]}
    results = {(str(row["id"]), int(row["target_compression_ratio"])): row for row in results_payload["results"]}
    expected = {(sid, ratio) for sid in selected for ratio in (2, 4)}
    if set(compressed) != expected or set(results) != expected or len(results_payload["results"]) != len(expected) or len(compressed_payload["results"]) != len(expected):
        raise ValueError("Results must contain exactly the selected source ids at both ratios")
    tokenizer = AutoTokenizer.from_pretrained(compressed_payload["compressor_model"], revision=compressed_payload.get("compressor_revision") or "main", use_fast=not author_recipe, local_files_only=True)
    audit = []
    for key in sorted(expected, key=lambda item: (indices.index(selected[item[0]][0]), item[1])):
        index, sample = selected[key[0]]
        source, result = compressed[key], results[key]
        if any(row["question"] != sample["question"] or row["answers"] != sample["answers"] for row in (source, result)):
            raise ValueError(f"Question/reference differs from the shared source: {key}")
        if author_recipe and source.get("compressor_loading_verified") is not True:
            raise ValueError("Author-recipe results require verified compressor weight loading")
        if not source["source_text_preserved"] or source["preprocessing_version"] != "preserve_source_v2":
            raise ValueError("Unexpected preprocessing")
        units = split_natural_units(tokenizer, sample["docs"], source["context_unit_tokens"])
        assert "".join(units) == sample["docs"]
        chosen = source["selected_context_indices"]
        if len(chosen) != len(set(chosen)) or any(i < 0 or i >= len(units) for i in chosen):
            raise ValueError("Invalid selected context indices")
        for metric, value in score(result["answer"], sample["answers"]).items():
            if abs(result[metric] - value) > 1e-10:
                raise ValueError(f"Stored {metric} differs from shared metric: {key}")
        audit.append({
            "sample_index": index, "id": key[0], "ratio": key[1],
            "question": sample["question"], "answers": sample["answers"],
            "prediction": result["answer"], "em": result["em"], "f1": result["f1"],
            "prompt_tokens": result["prompt_tokens"], "actual_prompt_ratio": result["compression_ratio"],
            "context_units": len(units), "selected_units": len(chosen),
            "compressor_context_budget": source.get("context_budget_audit", {}).get("fine_context_target"),
            "actual_compressor_context_tokens": len(tokenizer(source["compressed_docs"], add_special_tokens=False)["input_ids"]),
            "selected_context_indices": chosen,
            "gold_phrase_in_source": contains_gold(sample["docs"], sample["answers"]),
            "gold_phrase_after_context_filter": contains_gold("\n\n".join(units[i] for i in chosen), sample["answers"]),
            "gold_phrase_after_token_filter": contains_gold(source["compressed_docs"], sample["answers"]),
        })
    specifications = [
        ("Uncompressed", 1, ROOT / "part1_uncompressed/results_member1.json"),
        ("Head-tail 2x", 2, ROOT / "part2_truncation/results_member2_2x.json"),
        ("Head-tail 4x", 4, ROOT / "part2_truncation/results_member2_4x.json"),
        ("Phi-2 chunked 2x", 2, PART / "results_member3.json"),
        ("Phi-2 chunked 4x", 4, PART / "results_member3.json"),
        ("Part 4 enhanced 2x", 2, ROOT / "part4_llmlingua_enhanced/results_member4.json"),
        ("Part 4 enhanced 4x", 4, ROOT / "part4_llmlingua_enhanced/results_member4.json"),
        (f"{current_label} 2x", 2, args.results),
        (f"{current_label} 4x", 4, args.results),
    ]
    if author_recipe and set(selected) <= {str(row["id"]) for row in read(PART / "paper_pilot5_results.json")["results"]}:
        specifications[7:7] = [("Previous API-default 2x", 2, PART / "paper_pilot5_results.json"), ("Previous API-default 4x", 4, PART / "paper_pilot5_results.json")]
    if matched:
        specifications += [("Head-tail matched budget (2x setting)", 2, matched_path), ("Head-tail matched budget (4x setting)", 4, matched_path)]
    summary, comparisons = [], {}
    for label, ratio, path in specifications:
        rows = [r for r in read(path)["results"] if str(r["id"]) in selected and int(r.get("target_compression_ratio", ratio)) == ratio]
        if len(rows) != sample_count or len({r["id"] for r in rows}) != sample_count:
            raise ValueError(f"Incomplete comparison: {path} at {ratio}x")
        comparisons[label] = {r["id"]: r for r in rows}
        summary.append({"method": label, "n": len(rows), "em": mean(r["em"] for r in rows), "f1": mean(r["f1"] for r in rows), "prompt_tokens": mean(r["prompt_tokens"] for r in rows)})
    from datetime import datetime, timedelta, timezone
    finished = datetime.fromisoformat(results_payload["finished_at"]).astimezone(timezone(timedelta(hours=8)))
    lines = [
        f"# Original LLMLingua API: {sample_count}-sample evaluation", "",
        f"Completed on {finished:%Y-%m-%d %H:%M}, Asia/Shanghai. " + ("This covers the full shared test split." if args.all_samples else "This is a feasibility and error-analysis pilot, not the 150-sample result."), "",
        "## Fixed sample selection", "",
        ("All 150 shared sample ids are included at both ratios." if args.all_samples else f"Fixed source indices: {indices}. These ids were fixed before this evaluation; no examples were selected or removed based on the new answers. This is a feasibility check, not a random or representative quality estimate." if author_recipe else "Indices 17, 75, 130, 125, 23 are the minimum, lower quartile, median, upper quartile and maximum of the 150 documents sorted by Llama-2 compressor-token length. Selection was fixed before observing pilot answers. This is length-stratified, not a random or representative quality estimate."), "",
        "## Method and reproduction scope", "",
        ("Uses the official reproduction FAQ recipe: LLMLingua 0.2.2, `rank_method=llmlingua`, `vicgalle/alpaca-7b` (the Alpaca checkpoint named in the Microsoft demo), `context_budget=*2`, `iterative_size=100`, separate instruction/context/question arguments, context-level and iterative token filtering. Instruction and question are verified unchanged in the API output and removed only from that output wrapper before the shared target prompt is rendered, so they appear exactly once. Paper instruction/question rates 0.85/0.9 are not independently implemented by this API recipe." if author_recipe else "Uses LLMLingua 0.2.2's `rank_method=llmlingua`, base `NousResearch/Llama-2-7b-hf`, `context_budget=+100`, and `iterative_size=200`. These API defaults do not match the original paper's experimental configuration."), "",
        "Source paragraphs are packed into at most 512 compressor-token context units; every source character is retained before filtering. The selected unit ids are recorded without changing the library's selection algorithm. No LongLLMLingua conditioning, context reordering or retrieval is added. This transfers the released inference algorithm to LongBench/Llama-3.2 chat evaluation; it does not recreate the paper's datasets, target models or completion-mode protocol. No new alignment training is performed; an Alpaca-family checkpoint is used only in the author-recipe run, with its model revision recorded. That checkpoint is referenced by the authors' demo but is not independently proven to be the exact weights used for every paper table.", "",
        "References: [original paper](https://aclanthology.org/2023.emnlp-main.825/), [official reproduction FAQ](https://github.com/microsoft/LLMLingua/blob/main/Transparency_FAQ.md), [author demo checkpoint examples](https://huggingface.co/spaces/microsoft/LLMLingua/blob/main/app.py).", "",
        "Runtime: " + ", ".join(f"{k}={v}" for k, v in compressed_payload["runtime_versions"].items()) + ". Compressor and target run in separate processes on MPS.", "",
        f"## Quality on the same {sample_count} ids", "",
        "Historical baselines use their existing runs on other hardware. Quality and prompt-token counts are shown; cross-machine latency comparisons are intentionally omitted. Differences here are descriptive, with no significance claim.", "",
        "| Method | n | EM | F1 | Mean prompt tokens |", "| --- | ---: | ---: | ---: | ---: |",
    ]
    lines += [f"| {r['method']} | {r['n']} | {r['em']:.4f} | {r['f1']:.4f} | {r['prompt_tokens']:.1f} |" for r in summary]
    contrasts = []
    if args.all_samples:
        lines += ["", "## Paired F1 contrasts", "", "Differences are original-API LLMLingua minus each comparison, paired by source id. Intervals use mean difference plus/minus 1.96 times the paired standard error, matching the project's existing analysis. Compression ratios are nominal; achieved prompt lengths differ. These are unadjusted exploratory intervals across historical runs, not evidence that one implementation factor caused the difference.", "", "| Ratio | Comparison | Mean difference | Approx. 95% CI |", "| ---: | --- | ---: | --- |"]
        for ratio in (2, 4):
            current = comparisons[f"{current_label} {ratio}x"]
            labels = ["Uncompressed", f"Head-tail {ratio}x", f"Phi-2 chunked {ratio}x", f"Part 4 enhanced {ratio}x"]
            if matched:
                labels.append(f"Head-tail matched budget ({ratio}x setting)")
            for label in labels:
                differences = [current[sid]["f1"] - comparisons[label][sid]["f1"] for sid in selected]
                delta = mean(differences)
                margin = 1.96 * stdev(differences) / len(differences) ** 0.5
                contrasts.append({"ratio": ratio, "comparison": label, "mean_delta_f1": delta, "ci_low": delta - margin, "ci_high": delta + margin})
                lines.append(f"| {ratio}x | {label} | {delta:+.4f} | [{delta - margin:+.4f}, {delta + margin:+.4f}] |")
    lines += ["", "## Paired per-sample F1", "", "| Source index | Ratio | Uncompressed | Head-tail | Phi-2 | Part 4 | Current recipe | Actual prompt ratio | Units kept |", "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in audit:
        sid, ratio = row["id"], row["ratio"]
        values = [comparisons[label][sid]["f1"] for label in ["Uncompressed", f"Head-tail {ratio}x", f"Phi-2 chunked {ratio}x", f"Part 4 enhanced {ratio}x", f"{current_label} {ratio}x"]]
        lines.append(f"| {row['sample_index']} | {ratio}x | " + " | ".join(f"{v:.4f}" for v in values) + f" | {row['actual_prompt_ratio']:.3f}x | {row['selected_units']}/{row['context_units']} |")
    if author_recipe:
        two_x = [r for r in audit if r["ratio"] == 2]
        fully_retained = sum(r["selected_units"] == r["context_units"] for r in two_x)
        lines += ["", "## Budget adherence", "", f"The API's requested rate does not guarantee the achieved ratio on long inputs. At the 2x setting, {fully_retained}/{len(two_x)} examples retain every context unit before token filtering. Outputs substantially below their recorded fine-stage targets indicate overcompression in the released token-filtering path; the difference is not solely a target-tokenizer counting effect. Achieved ratios must be reported alongside requested settings. No rate was tuned on QA scores.", "", "| Source | Setting | Fine context target | Actual compressor context tokens | Actual whole-prompt ratio |", "| ---: | ---: | ---: | ---: | ---: |"]
        lines += [f"| {r['sample_index']} | {r['ratio']}x | {r['compressor_context_budget']:.1f} | {r['actual_compressor_context_tokens']} | {r['actual_prompt_ratio']:.3f}x |" for r in audit]
    if matched:
        paired = {(r["id"], r["target_compression_ratio"]): r for r in matched["results"]}
        if set(paired) != expected or len(matched["results"]) != len(expected) or any(not 0 <= r["budget_gap_tokens"] <= 2 for r in paired.values()):
            raise ValueError("Matched baseline has invalid coverage or budget gaps")
        for key, row in paired.items():
            target_budget = results[key]["prompt_tokens"]
            if row["matched_prompt_budget"] != target_budget or row["budget_gap_tokens"] != target_budget - row["prompt_tokens"]:
                raise ValueError(f"Recorded matched budget differs from actual result: {key}")
            sample = selected[key[0]][1]
            if row["question"] != sample["question"] or row["answers"] != sample["answers"]:
                raise ValueError(f"Matched baseline differs from the shared source: {key}")
            for metric, value in score(row["answer"], sample["answers"]).items():
                if abs(row[metric] - value) > 1e-10:
                    raise ValueError(f"Matched baseline {metric} differs from the shared scorer: {key}")
        lines += ["", "## Same-machine baseline at the achieved budgets", "", "Part 2's 50/50 head-tail function is reused, with its retained length chosen only from prompt token counts. The target model, MPS device, dtype, generation limit and metric implementation match the new run. Each baseline prompt is at most two tokens shorter than the corresponding compressed prompt. This controls the severe budget mismatch without changing or tuning the LLMLingua recipe.", "", "| Source | Setting | LLMLingua tokens | Head-tail tokens | LLMLingua F1 | Head-tail F1 |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
        for r in audit:
            other = paired[(r["id"], r["ratio"])]
            lines.append(f"| {r['sample_index']} | {r['ratio']}x | {r['prompt_tokens']} | {other['prompt_tokens']} | {r['f1']:.4f} | {other['f1']:.4f} |")
    lines += ["", "## Answer phrase audit", "", "These are normalized whole-phrase matches, not semantic evidence checks. An absent phrase does not prove that a question is unanswerable; paraphrases, equations and split phrases can defeat this diagnostic.", "", "| Source index | Ratio | In source | After context filter | After token filter |", "| ---: | ---: | --- | --- | --- |"]
    lines += [f"| {r['sample_index']} | {r['ratio']}x | {r['gold_phrase_in_source']} | {r['gold_phrase_after_context_filter']} | {r['gold_phrase_after_token_filter']} |" for r in audit]
    lines += ["", "## Predictions and references", ""]
    for r in audit:
        lines += [f"### Source {r['sample_index']}, {r['ratio']}x", "", "Question: " + r["question"], "", "References: " + json.dumps(r["answers"], ensure_ascii=False), "", "Prediction: " + r["prediction"], ""]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (args.out_dir / "audit.json").write_text(json.dumps({"sample_indices": indices, "summary": summary, "paired_contrasts": contrasts, "audit": audit}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print(json.dumps(summary, indent=2))
    print(f"Report: {args.out_dir / 'report.md'}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
