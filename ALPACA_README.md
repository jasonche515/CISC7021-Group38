# Alpaca released-recipe experiment: shared evidence

This package supports the additional matched-budget section in the reviewed report.
It is separate from the historical Phi-2 Part 3 and question-aware Qwen Part 4.

## Verify the reported numbers without models or a GPU

From the extracted package root, with Python 3.10 or newer:

```bash
python3 part3_llmlingua/verify_author_full150.py
```

No third-party package is required for that command. It checks SHA256 manifests,
the original frozen source/data hashes, full source/setting coverage, questions and
reference answers, all 600 stored answer scores, compression/evaluation consistency
and the recorded per-pair token gaps. It recomputes means and approximate paired
95% intervals from the predictions rather than trusting the stored summary.
The hash manifest detects content changes; it is not a cryptographic signature.
Recorded token counts/loading/source-preservation flags are not independently
re-executed without the tokenizer and model environment.

Expected results (150 questions per setting):

| Requested | LL F1 | matched head-tail F1 | LL mean prompt tokens | achieved ratio | LL minus HT, approximate 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| 2x | 0.2396 | 0.3875 | 1966.4 | 3.5375 | -0.1479 [-0.1912, -0.1046] |
| 4x | 0.2174 | 0.3494 | 1113.4 | 5.9006 | -0.1320 [-0.1731, -0.0909] |

There are 288 exactly matched prompt budgets and 12 head-tail prompts one token
shorter. Ratios are means of per-example original/compressed whole-prompt counts.
The intervals are approximate and unadjusted exploratory intervals.

## Files

- `shared/samples.json`: all 150 source documents, questions and references.
- `part3_llmlingua/author_full150_compressed.json`: 300 compressed inputs with
  settings, selected context units and model-loading audit fields.
- `part3_llmlingua/author_full150_results.json`: 300 LLMLingua predictions.
- `part3_llmlingua/author_full150_matched_headtail.json`: 300 matched predictions.
- `part3_llmlingua/author_full150_status.json`: completion, pilot reuse provenance
  and the original frozen code/data hashes. The snapshot path is the original
  machine's recorded provenance, not a portable path requirement.
- `part3_llmlingua/author_full150_analysis/`: stored detailed analysis and CSV.
- `part3_llmlingua/FROZEN_FULL_EXPERIMENT.md`: fixed method and boundaries.
- `part3_llmlingua/author_full150_report_contribution.md`: report-ready text.
- `ALPACA_MANIFEST.json`: SHA256 for each bundled file other than itself.
- `recorded_runtime.json`: versions recorded inside the experiment output.

Inference, analysis, prompt and scoring source files are included in their original
repository-relative locations. Historical Part 1-4 result JSONs are included only
because the original analysis script uses them as explicitly labelled references.
Only the completed full-run JSON exports are required; duplicate JSONL files,
pilot files, virtual environments, cache directories and model weights are omitted.
The full exports already contain the verified reused pilot rows.

## Optional: rerun inference on a compatible Apple Silicon MPS environment

This step is not needed to check report arithmetic. The recorded versions are
Torch 2.15.0, Transformers 4.46.3 and LLMLingua 0.2.2. Other Python dependencies
used by the runners include accelerate, sentencepiece, tiktoken, safetensors,
huggingface-hub, numpy and nltk. Consult the imports when recreating that environment.
The old Part 3 requirements pinning Transformers 4.38.2 are not this Alpaca run.
Model download access, compatible dependencies and sufficient accelerator memory
are required; the package contains no model weights or caches.

Run in a separate environment/extracted copy to retain the original evidence:

```bash
python3 part3_llmlingua/run_author_pilot.py --all-samples --prefix author_reproduction
```

The new prefix preserves `author_full150_*`. The command downloads the pinned
compressor, uses MPS, and runs compression, target generation, matched head-tail,
analysis and contribution generation. It does not depend on omitted pilot files;
the seed-prefix list is empty by default. Exact floating-point outputs may vary
with hardware and library builds. A fresh run need not reproduce the old latency.

## Interpretation

Compressor: `vicgalle/alpaca-7b`, revision
`c98caccd9a60bc04b92c07e93966a72ee5173a95`, fp16 without quantization;
`rank_method=llmlingua`, `context_budget=*2`, `iterative_size=100`, paragraph
units of at most 512 compressor tokens, separate instruction/context/question.
Target: `unsloth/Llama-3.2-3B-Instruct`, fp16, greedy, at most 64 new tokens.
The trained legacy output head is restored and checked exactly by the loader.

This is a transfer evaluation of a released inference recipe, not an exact
recreation of all original-paper datasets, targets or alignment training. Achieved
compression overshoots the requested labels; its precise cause is unresolved.
The 7B compressor is larger than the 3B target. Timing includes reused pilot rows
and varying system conditions and is not a controlled speed benchmark.

## GitHub integration

The package mirrors repository paths. Add these evidence and source files to the
report-review branch together with the revised report. Keep the historical result
filenames/labels unchanged. Include this README as a sharing guide and preserve
the completed `author_full150_status.json` provenance. A ZIP alone is convenient
for transfer; checking in the individual JSON and source files makes review easier.
