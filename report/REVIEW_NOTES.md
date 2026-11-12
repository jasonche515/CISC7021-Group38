# Report numerical review and additional evidence

This branch reviews `report/final.tex` on top of main at 60b95f3. It preserves
the group's newer video and Q&A additions. The seven historical result rows and
the existing inline TeX plots remain distinct from the added Alpaca experiment.

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
python3 'Final Report/verify_final_tex.py'
```

The first verifier requires only the Python standard library. The report audit
also checks that historical data blobs match the pinned reviewed commit. The
second/third commands write local audit JSON under `Final Report/`. They do not
run any models. All 600 added answer scores and actual prompt-budget pairs are
verified; reported paired intervals use mean difference ± 1.96 SE.

The same report/final.tex bytes compiled successfully with the desktop compiler.
Existing PDF exports are unchanged; a newly exported PDF still needs visual layout
review before submission.
The separate fuzzy answer-position bootstrap analysis is not a numeric table
in this final.tex and is not claimed independently reproduced here.

The current Part 2 runner is preserved, including the group's answer-position
logging. Its head_tail_truncate function was checked for AST identity against
the experiment dependency snapshot; only that function is used by the matched runner.
