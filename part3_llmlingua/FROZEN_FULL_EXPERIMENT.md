# Frozen full-test evaluation

**Completed 2026-11-10 05:49 Asia/Shanghai.** All stages completed successfully,
including full coverage, 600 independently recomputed answer scores, verified
model loading and unchanged frozen hashes. Of 300 paired prompt budgets,
288 match exactly and the other 12 differ by one token. Full-test LLMLingua F1
is 0.2396 / 0.2174; matched head-tail F1 is 0.3875 / 0.3494. Current report-ready
material is in [author_full150_report_contribution.md](./author_full150_report_contribution.md).

The agreed final experiment evaluates all 150 shared LongBench multifieldqa_en
ids, at both requested rates, using the verified author-published LLMLingua
inference recipe. The scientific claim is a transfer evaluation on
Llama-3.2-3B-Instruct, not an exact recreation of all original paper settings.

## Frozen method

- Compressor: `vicgalle/alpaca-7b`, revision
  `c98caccd9a60bc04b92c07e93966a72ee5173a95`, float16, no quantization.
- Author recipe: `rank_method=llmlingua`, `context_budget=*2`,
  `iterative_size=100`, separate instruction/context/question, no sentence filter.
- Preprocessing: source-preserving paragraph packing, 512 compressor tokens
  per context unit, preprocessing version `preserve_source_v2`.
- Loading: the checkpoint's legacy output-head key is restored and checked
  tensor-for-tensor. Unresolved missing/unexpected/mismatched weights abort.
- Target: `unsloth/Llama-3.2-3B-Instruct`, float16, shared chat template,
  greedy generation, at most 64 new tokens, shared EM and token-F1 metrics.
- Data: every shared id in original order; every id is evaluated at both rates.
- Baseline: existing Part 2 50/50 head-tail algorithm, evaluated on the same
  MPS target and paired to each achieved prompt budget within two tokens.

The first 10 ids plus the three earlier diagnostic ids provide 26 previously
verified rows per stage. They are reused without filtering on scores. All
remaining rows are computed with the same recipe. The three-id attempt with
an uninitialized output head and the interrupted base-Llama run are excluded.

## Execution

```bash
/usr/bin/caffeinate -i .venv-member3/bin/python \
  part3_llmlingua/run_author_pilot.py --offline --all-samples \
  --prefix author_full150 --seed-prefixes author_pilot10 author_pilot3
```

`caffeinate -i` prevents idle sleep only while the process is alive. Models are
already cached. Compression and answer generation run sequentially in separate
processes, with MPS idle cache released between compression jobs. Each job is
checkpointed. Re-running the same command resumes by `(id, ratio)`.

The pipeline finishes compression, target evaluation, token-matched baseline,
analysis, and report contribution in order. No QA-driven rate calibration,
model replacement or method tuning is part of this run.

## Completion checks

- Exactly 300 unique `(id, ratio)` rows in each of the three computational stages.
- Full id coverage at both requested rates.
- Compressor checkpoint, recipe, revision, loading audit and source preservation
  verified on every reused or new compression row.
- Stored answer metrics recomputed with the shared scoring implementation.
- Matched baseline prompt budgets differ by at most two target tokens.
- Frozen inference, prompt, metric and data hashes unchanged during execution.
- Paired per-id F1 contrasts, achieved compression ratios, and qualitative
  cases reported without dropping unfavorable samples.

## Artifacts

All outputs use the `author_full150_` prefix and preserve previous experiments:

- `author_full150_status.json`: authoritative current stage and completion state,
  seed provenance, and frozen source/data hashes.
- `author_full150_compressed.jsonl` / `.json`: contexts and compression audit.
- `author_full150_results.jsonl` / `.json`: 300 LLMLingua predictions and metrics.
- `author_full150_matched_headtail.jsonl` / `.json`: 300 baseline predictions.
- `author_full150_analysis/report.md`, `audit.json`, `summary.csv`: complete
  quality tables, paired contrasts, token budgets and per-id cases.
- `author_full150_report_contribution.md`: report-ready English methods,
  full-test results, selected cases and limitations.
- `author_full150_results_table.tex`: table fragment for the group's ACL report.
- `_author_full150.log`: execution history.

## Interpretation boundaries

Requested rates can overshoot on long inputs, so achieved prompt ratios are
mandatory results. The matched baseline supports a quality comparison at those
achieved budgets. The 7B compressor is larger than the 3B target, so this setup
does not recreate the paper's small-compressor/large-target efficiency regime.
Historical Part 1-4 results and the older same-machine benchmark are distinct
experiments; their latencies cannot be substituted for this method's timing.

The released API keeps instruction and question text rather than independently
implementing the paper's initial 0.85/0.9 component rates. No new target-specific
alignment is trained. Dataset, target model, completion/chat mode and context
segmentation differ from the original paper. These limitations must accompany
the results regardless of their ranking.
