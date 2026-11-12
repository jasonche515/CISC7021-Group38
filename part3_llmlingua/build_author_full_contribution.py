"""Build report-ready material only from a complete frozen 150-id evaluation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
PART = Path(__file__).resolve().parent
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default="author_full150")
    args = parser.parse_args()
    def artifact(suffix):
        return PART / f"{args.prefix}_{suffix}"
    compressed = read(artifact("compressed.json"))
    results = read(artifact("results.json"))
    baseline = read(artifact("matched_headtail.json"))
    analysis = read(artifact("analysis") / "audit.json")
    if analysis["sample_indices"] != list(range(150)):
        raise ValueError("Report contribution requires all 150 source ids")
    for payload in (compressed, results, baseline):
        if len(payload["results"]) != 300 or len({(r["id"], r["target_compression_ratio"]) for r in payload["results"]}) != 300:
            raise ValueError("Report contribution requires 300 unique rows in each stage")
    newer = {(r["id"], r["target_compression_ratio"]): r for r in results["results"]}
    older = {(r["id"], r["target_compression_ratio"]): r for r in baseline["results"]}
    if newer.keys() != older.keys() or any(abs(newer[k]["prompt_tokens"] - older[k]["prompt_tokens"]) > 2 for k in newer):
        raise ValueError("Matched baseline coverage or prompt budgets differ")
    if any(r.get("compressor_loading_verified") is not True for r in compressed["results"]):
        raise ValueError("Unverified compressor outputs cannot enter the report")
    finished = max(datetime.fromisoformat(results["finished_at"]), datetime.fromisoformat(baseline["finished_at"])).astimezone(timezone(timedelta(hours=8)))
    primary = {r["ratio"]: r for r in analysis["paired_contrasts"] if r["comparison"].startswith("Head-tail matched budget")}
    if set(primary) != {2, 4}:
        raise ValueError("Primary paired contrasts are missing")
    lines = [
        "# Member 3 report contribution: frozen LLMLingua inference evaluation", "",
        f"Evaluation completed {finished:%Y-%m-%d %H:%M} Asia/Shanghai. All values below are generated from the full result files.", "",
        "## Method", "",
        "We evaluated the released original LLMLingua inference algorithm in a resource-constrained long-context QA setting. We followed the authors' published reproduction recipe with `context_budget=*2`, `iterative_size=100`, original LLMLingua ranking, and separate instruction, context and question inputs. The compressor was `vicgalle/alpaca-7b`, the Alpaca-family checkpoint referenced in Microsoft's demonstration, pinned to revision `c98caccd9a60bc04b92c07e93966a72ee5173a95`. Both models used float16, with no compressor quantization. Before filtering, paragraphs were packed into context units of at most 512 compressor tokens while preserving every source character. This is an explicit adaptation of the dataset's single-document inputs to the context-list interface.", "",
        "The old checkpoint's output head is stored under `base_model.model.lm_head.weight`, whereas modern Transformers expects `lm_head.weight`. Our loader restores that exact checkpoint tensor and verifies equality; any unresolved missing, unexpected or mismatched model weight aborts execution. The negative padding sentinel is replaced with the tokenizer's EOS id for compatibility. Perplexity is evaluated on unpadded single sequences. The invalid first loading attempt is quarantined and excluded from every result here.", "",
        "## Experimental protocol", "",
        "We used all 150 shared LongBench multifieldqa_en source ids and nominal retention rates 0.5 and 0.25, producing 300 compressed contexts and answers. The target was unsloth/Llama-3.2-3B-Instruct with the shared chat template, greedy decoding, a 64-token generation limit, and the shared EM/token-F1 implementation. The compressor and target ran sequentially in separate MPS processes. Existing verified pilot rows were reused with the same recipe; no setting or sample was selected on the full-run scores. Source, prompt, metric and inference code hashes were frozen when the run started.", "",
        "The requested rate did not reliably determine the achieved rate on long inputs. We therefore report actual target-token prompt lengths and additionally evaluated the existing Part 2 50/50 head-tail algorithm at each LLMLingua output's achieved prompt budget. Baseline lengths were selected using token counts only. Both methods used the same MPS target model and generation settings. Any difference greater than two prompt tokens fails the budget-match check. This paired baseline evaluates quality at comparable achieved budgets without changing the LLMLingua recipe.", "",
        "## Full-test results", "",
        "| Requested setting | n | LLMLingua EM | LLMLingua F1 | Matched head-tail F1 | Mean LLMLingua prompt tokens | Mean per-example achieved ratio |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ratio in (2, 4):
        current, other = results["summary"][f"{ratio}x"], baseline["summary"][f"{ratio}x"]
        lines.append(f"| {ratio}x | 150 | {current['mean_em']:.4f} | {current['mean_f1']:.4f} | {other['mean_f1']:.4f} | {current['mean_prompt_tokens']:.1f} | {current['mean_achieved_compression_ratio']:.4f}x |")
    lines += ["", "## Paired comparisons", "", "Differences below are LLMLingua minus head-tail at matched achieved prompt budgets. Approximate 95% confidence intervals use the paired mean plus/minus 1.96 standard errors. They are unadjusted exploratory intervals. The complete comparison table also reports historical Part 1-4 quality numbers; those older runs do not provide a common-hardware latency comparison for this experiment.", ""]
    for ratio in (2, 4):
        contrast = primary[ratio]
        differences = [newer[k]["f1"] - older[k]["f1"] for k in newer if k[1] == ratio]
        wins, ties, losses = sum(d > 1e-10 for d in differences), sum(abs(d) <= 1e-10 for d in differences), sum(d < -1e-10 for d in differences)
        relation = "lower" if contrast["mean_delta_f1"] < 0 else "higher" if contrast["mean_delta_f1"] > 0 else "equal"
        lines.append(f"At the {ratio}x requested setting, LLMLingua's mean F1 is {relation}: paired delta {contrast['mean_delta_f1']:+.4f}, CI [{contrast['ci_low']:+.4f}, {contrast['ci_high']:+.4f}]. Per-id wins/ties/losses are {wins}/{ties}/{losses}.")
        lines.append("")
    lines += ["## Illustrative cases", "", "For each requested ratio, the lowest and highest paired F1 differences are selected deterministically for error analysis. These are illustrative extrema, not estimates of how often a failure mechanism occurs. Gold references are used only for evaluation and diagnostics, never for compression or budget selection.", ""]
    for ratio in (2, 4):
        keys = sorted((k for k in newer if k[1] == ratio), key=lambda k: (newer[k]["f1"] - older[k]["f1"], k[0]))
        for label, key in [("Largest disadvantage", keys[0]), ("Largest advantage", keys[-1])]:
            row, other = newer[key], older[key]
            case = {"id": key[0], "requested_ratio": ratio, "question": row["question"], "references": row["answers"], "llmlingua_prediction": row["answer"], "head_tail_prediction": other["answer"], "llmlingua_f1": row["f1"], "head_tail_f1": other["f1"], "llmlingua_prompt_tokens": row["prompt_tokens"], "head_tail_prompt_tokens": other["prompt_tokens"]}
            quote = lambda value: json.dumps(" ".join(value.split()), ensure_ascii=False)
            lines += [f"### {label}, {ratio}x setting", "", f"For the question {quote(row['question'])}, the reference answer was {json.dumps(row['answers'], ensure_ascii=False)}. LLMLingua answered {quote(row['answer'])}, while head-tail answered {quote(other['answer'])}. Their F1 scores were {row['f1']:.4f} and {other['f1']:.4f}, using {row['prompt_tokens']} and {other['prompt_tokens']} prompt tokens, respectively.", ""]
    lines += [
        "## Reproduction scope and limitations", "",
        "This is a transfer evaluation of the released inference recipe, not an exact recreation of every paper table. The original paper used different datasets, target models and a completion-mode protocol. Our shared target uses chat mode, which the authors identify as more sensitive to token compression. The public Alpaca checkpoint is referenced by the authors' demo but has not been independently established as the exact weights used for every original result. No new alignment training toward Llama-3.2 was performed.", "",
        "The released recipe preserves instruction and question text rather than independently implementing the paper's initial component rates 0.85 and 0.9. Actual long-input compression can substantially exceed the requested ratio. The matched head-tail baseline controls prompt length for the main quality comparison but does not remove every implementation or transfer-setting limitation. Any unfavorable outcome should be stated as a result for this released implementation and evaluation setup, not as general evidence against LLMLingua.", "",
        "The 7B compressor is larger than the 3B target, unlike the small-compressor/large-target relationship motivating the paper. We therefore make no claim that this setup reproduces its end-to-end speedup. Compression and generation latencies include pilot reuse and varying system memory pressure; historical runs were on other hardware. The existing same-environment Parts 1-3 benchmark remains a separate experiment and must not be used as the new method's latency measurement.", "",
        "References: [original paper](https://aclanthology.org/2023.emnlp-main.825/), [author reproduction recipe](https://github.com/microsoft/LLMLingua/blob/main/Transparency_FAQ.md), [Microsoft demo checkpoint examples](https://huggingface.co/spaces/microsoft/LLMLingua/blob/main/app.py).", "",
        "## Source artifacts", "",
        f"- `{args.prefix}_compressed.json`: contexts, budgets, selected units and loading audit.",
        f"- `{args.prefix}_results.json`: all 300 LLMLingua answers and metrics.",
        f"- `{args.prefix}_matched_headtail.json`: all 300 matched-baseline answers and metrics.",
        f"- `{args.prefix}_analysis/report.md` and `audit.json`: combined table, paired contrasts, per-id predictions and diagnostics.",
        f"- `{args.prefix}_status.json`: run state, seed provenance and frozen code/data hashes.", "",
    ]
    artifact("report_contribution.md").write_text("\n".join(lines), encoding="utf-8")
    tex = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{lrrrr}", r"\hline", r"Setting & $n$ & LLMLingua F1 & Head-tail F1 & Tokens \\", r"\hline"]
    for ratio in (2, 4):
        current, other = results["summary"][f"{ratio}x"], baseline["summary"][f"{ratio}x"]
        tex.append(f"{ratio}x target & 150 & {current['mean_f1']:.4f} & {other['mean_f1']:.4f} & {current['mean_prompt_tokens']:.1f} " + r"\\")
    tex += [r"\hline", r"\end{tabular}", r"\caption{Full-test F1 at matched achieved prompt budgets. Compression settings are nominal; achieved ratios are reported separately.}", r"\label{tab:author-matched-budget}", r"\end{table}"]
    artifact("results_table.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"Report contribution: {artifact('report_contribution.md')}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
