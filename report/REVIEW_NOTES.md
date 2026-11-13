# Report numerical review and additional evidence

The canonical report is now `report/final_report_revised.tex`, as confirmed by
the group. Previously verified corrections from `report/final.tex` have been
integrated into that file, preserving the revised report's structure, existing
figures and answer-position analysis. The seven historical result rows remain
distinct from the added Alpaca experiment. The old `final.tex` is retained in
this review branch for history only; it is not the submission source.

Corrections include prompt-length median 7,023; head-tail 2x latency reduction
43.5%; maximum historical/rerun F1 discrepancy rounded to 0.0076; baseline
cross-environment mean F1 difference rounded to 0.0053; and separate stage
processes rather than a single process. The complete same-environment per-id
JSONs are preserved; the older Markdown export is stale. Empty context fields
do not prevent recomputing EM/F1 from stored answers and references.

Method wording now identifies Phi-2 as a resource-constrained adaptation,
records its disabled coarse filter, removes unsupported chunking-effect bounds,
and distinguishes nominal from achieved budgets. Discussion and conclusion are
restricted to the tested setting. The additional released-recipe Alpaca run is
not presented as an exact recreation of the full original-paper protocol.

Raw Alpaca inputs and predictions, the matched head-tail answers, frozen source
files, source questions/references, completion provenance and verifier accompany
the new results. Consult ALPACA_README.md. Caches, model weights, virtualenvs,
invalid/interrupted pilots, duplicate JSONL exports and old draft ZIPs are omitted.

Verification (from repository root):

```bash
python3 part3_llmlingua/verify_author_full150.py
python3 'Final Report/cross_check_report.py'
python3 'Final Report/verify_revised_report.py'
```

The first verifier requires only the Python standard library. The report audit
also checks that historical data blobs match the pinned reviewed commit. The
second/third commands write local audit JSON under `Final Report/`. They do not
run any models. All 600 added answer scores and actual prompt-budget pairs are
verified; reported paired intervals use mean difference ± 1.96 SE.

The numeric audit passes 5,227 checks over 2,400 recorded answers. The canonical
report verifier passes 221 checks, including the seven historical rows, five
same-environment rows, twelve paired contrasts, actual whole-prompt ratios,
additional Alpaca results, position-zone means and source references.

`report/final_report_revised.tex` compiled successfully with the desktop compiler
on 2026-11-13. The project root must be the repository root and the selected main
file `report/final_report_revised.tex`, so the compiler can access `figures/`.
Existing PDF exports are unchanged; an exported PDF still needs visual layout
review before submission. Compilation evidence and the source hash are saved in
`Final Report/review_revised_20261113/`.

Position-zone counts and means were independently recomputed from the CSV and
checked against the prediction JSONs. Bootstrap bounds match the committed
`report/answer_position_stats.tex`, but the generating script, seed and replicate
count are unavailable. This limitation is disclosed in the report. Comparisons
with the uncompressed baseline now use exactly the same subset of ids, and no
causal decomposition of truncation losses is claimed.

The current Part 2 runner is preserved, including the group's answer-position
logging. Its head_tail_truncate function was checked for AST identity against
the experiment dependency snapshot; only that function is used by the matched runner.
