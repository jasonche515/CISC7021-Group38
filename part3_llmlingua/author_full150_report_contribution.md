# Member 3 report contribution: frozen LLMLingua inference evaluation

Evaluation completed 2026-11-10 05:48 Asia/Shanghai. All values below are generated from the full result files.

## Method

We evaluated the released original LLMLingua inference algorithm in a resource-constrained long-context QA setting. We followed the authors' published reproduction recipe with `context_budget=*2`, `iterative_size=100`, original LLMLingua ranking, and separate instruction, context and question inputs. The compressor was `vicgalle/alpaca-7b`, the Alpaca-family checkpoint referenced in Microsoft's demonstration, pinned to revision `c98caccd9a60bc04b92c07e93966a72ee5173a95`. Both models used float16, with no compressor quantization. Before filtering, paragraphs were packed into context units of at most 512 compressor tokens while preserving every source character. This is an explicit adaptation of the dataset's single-document inputs to the context-list interface.

The old checkpoint's output head is stored under `base_model.model.lm_head.weight`, whereas modern Transformers expects `lm_head.weight`. Our loader restores that exact checkpoint tensor and verifies equality; any unresolved missing, unexpected or mismatched model weight aborts execution. The negative padding sentinel is replaced with the tokenizer's EOS id for compatibility. Perplexity is evaluated on unpadded single sequences. The invalid first loading attempt is quarantined and excluded from every result here.

## Experimental protocol

We used all 150 shared LongBench multifieldqa_en source ids and nominal retention rates 0.5 and 0.25, producing 300 compressed contexts and answers. The target was unsloth/Llama-3.2-3B-Instruct with the shared chat template, greedy decoding, a 64-token generation limit, and the shared EM/token-F1 implementation. The compressor and target ran sequentially in separate MPS processes. Existing verified pilot rows were reused with the same recipe; no setting or sample was selected on the full-run scores. Source, prompt, metric and inference code hashes were frozen when the run started.

The requested rate did not reliably determine the achieved rate on long inputs. We therefore report actual target-token prompt lengths and additionally evaluated the existing Part 2 50/50 head-tail algorithm at each LLMLingua output's achieved prompt budget. Baseline lengths were selected using token counts only. Both methods used the same MPS target model and generation settings. Any difference greater than two prompt tokens fails the budget-match check. This paired baseline evaluates quality at comparable achieved budgets without changing the LLMLingua recipe.

## Full-test results

| Requested setting | n | LLMLingua EM | LLMLingua F1 | Matched head-tail F1 | Mean LLMLingua prompt tokens | Mean per-example achieved ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2x | 150 | 0.0000 | 0.2396 | 0.3875 | 1966.4 | 3.5375x |
| 4x | 150 | 0.0067 | 0.2174 | 0.3494 | 1113.4 | 5.9006x |

## Paired comparisons

Differences below are LLMLingua minus head-tail at matched achieved prompt budgets. Approximate 95% confidence intervals use the paired mean plus/minus 1.96 standard errors. They are unadjusted exploratory intervals. The complete comparison table also reports historical Part 1-4 quality numbers; those older runs do not provide a common-hardware latency comparison for this experiment.

At the 2x requested setting, LLMLingua's mean F1 is lower: paired delta -0.1479, CI [-0.1912, -0.1046]. Per-id wins/ties/losses are 29/24/97.

At the 4x requested setting, LLMLingua's mean F1 is lower: paired delta -0.1320, CI [-0.1731, -0.0909]. Per-id wins/ties/losses are 35/30/85.

## Illustrative cases

For each requested ratio, the lowest and highest paired F1 differences are selected deterministically for error analysis. These are illustrative extrema, not estimates of how often a failure mechanism occurs. Gold references are used only for evaluation and diagnostics, never for compression or budget selection.

### Largest disadvantage, 2x setting

For the question "What was Hugh H. Goodwin's rank in the United States Navy?", the reference answer was ["Vice Admiral."]. LLMLingua answered "The text does not mention a person named Hugh H. Goodwin. It mentions Hughton Goodwin.", while head-tail answered "Vice Admiral.". Their F1 scores were 0.0000 and 1.0000, using 1088 and 1088 prompt tokens, respectively.

### Largest advantage, 2x setting

For the question "Besides the Boeing C-17, what other transport aircraft is the IAF considering for acquisition?", the reference answer was ["The IAF is considering the acquisition of the Airbus A330 MRTT (Multi-Role Tanker Transport) besides the Boeing C-17."]. LLMLingua answered "Besides the Boeing C-17, the IAF is considering the Airbus A330 MRTT (Multi-Role Transport Tanker) for acquisition.", while head-tail answered "The text does not explicitly mention another transport aircraft besides the Boeing C-17 that the IAF is considering for acquisition. However, it does mention the IL-76, which is being upgraded by Russia, and the IL-76MDM, which is a modified version of the IL-76.". Their F1 scores were 0.9286 and 0.3600, using 1992 and 1992 prompt tokens, respectively.

### Largest disadvantage, 4x setting

For the question "In which electorate was Simon English elected to the New Zealand Parliament?", the reference answer was ["The Wallace electorate."]. LLMLingua answered "The text does not mention Simon English being elected to the New Zealand Parliament.", while head-tail answered "The Wallace electorate.". Their F1 scores were 0.0000 and 1.0000, using 822 and 822 prompt tokens, respectively.

### Largest advantage, 4x setting

For the question "When was McPherson County established as a county?", the reference answer was ["McPherson County was established as a county in 1867."]. LLMLingua answered "McPherson County was established as a county in 1867.", while head-tail answered "The text does not explicitly state when McPherson County was established as a county. However, it does mention that the Kansas Territory was organized in 1854, and Kansas became the 34th U.S. state in 1861.". Their F1 scores were 1.0000 and 0.3590, using 691 and 691 prompt tokens, respectively.

## Reproduction scope and limitations

This is a transfer evaluation of the released inference recipe, not an exact recreation of every paper table. The original paper used different datasets, target models and a completion-mode protocol. Our shared target uses chat mode, which the authors identify as more sensitive to token compression. The public Alpaca checkpoint is referenced by the authors' demo but has not been independently established as the exact weights used for every original result. No new alignment training toward Llama-3.2 was performed.

The released recipe preserves instruction and question text rather than independently implementing the paper's initial component rates 0.85 and 0.9. Actual long-input compression can substantially exceed the requested ratio. The matched head-tail baseline controls prompt length for the main quality comparison but does not remove every implementation or transfer-setting limitation. Any unfavorable outcome should be stated as a result for this released implementation and evaluation setup, not as general evidence against LLMLingua.

The 7B compressor is larger than the 3B target, unlike the small-compressor/large-target relationship motivating the paper. We therefore make no claim that this setup reproduces its end-to-end speedup. Compression and generation latencies include pilot reuse and varying system memory pressure; historical runs were on other hardware. The existing same-environment Parts 1-3 benchmark remains a separate experiment and must not be used as the new method's latency measurement.

References: [original paper](https://aclanthology.org/2023.emnlp-main.825/), [author reproduction recipe](https://github.com/microsoft/LLMLingua/blob/main/Transparency_FAQ.md), [Microsoft demo checkpoint examples](https://huggingface.co/spaces/microsoft/LLMLingua/blob/main/app.py).

## Source artifacts

- `author_full150_compressed.json`: contexts, budgets, selected units and loading audit.
- `author_full150_results.json`: all 300 LLMLingua answers and metrics.
- `author_full150_matched_headtail.json`: all 300 matched-baseline answers and metrics.
- `author_full150_analysis/report.md` and `audit.json`: combined table, paired contrasts, per-id predictions and diagnostics.
- `author_full150_status.json`: run state, seed provenance and frozen code/data hashes.
