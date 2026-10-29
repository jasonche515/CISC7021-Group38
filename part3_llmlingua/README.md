# Part 3 — LLMLingua (Member 3)

This folder reproduces the original **LLMLingua** method at nominal 2x and 4x
compression on the shared LongBench `multifieldqa_en` samples. The target LLM,
prompt template, sample order and EM/F1 implementation are identical to Part 1.

## 中文進度摘要

這個資料夾是 Member 3 負責的 LLMLingua 部分。兩階段 pipeline 先用
LLMLingua 壓縮 prompt，釋放 compressor 後，再載入
`Llama-3.2-3B-Instruct` 生成答案並計算 EM、token-level F1 和延遲，避免兩個
模型同時佔用記憶體。

正式實驗已於 2026 年 10 月 29 日在 Apple M5 Pro（MPS）上完成全部 150 條
LongBench `multifieldqa_en` 樣本。每條樣本均測試 2x 和 4x，共 300 筆評估。
長文本會切成固定的 1,400-token 區塊，各區塊獨立壓縮後按原順序合併，避免
超過 Phi-2 compressor 的 context limit。2x 的平均 F1 為 0.2626；4x 的平均
F1 為 0.2207，但平均 generation latency 由 3.017 秒降至 2.130 秒，呈現清楚的
準確率與效率取捨。正式結果保存在 `results_member3.json`。

The pipeline has two independent stages so the compressor and target LLM are
never loaded at the same time:

1. `compress`: use `microsoft/phi-2` to compress each document and save it;
2. `evaluate`: load `Llama-3.2-3B-Instruct`, answer the questions and calculate
   EM/F1.

Both stages append one JSON record after every job and resume automatically.

## Recommended: Google Colab with a T4 GPU

Open `member3_colab.ipynb` in Colab, select **Runtime > Change runtime type >
T4 GPU**, and run the cells in order. Start with the verified short sample at
index 17 and a 2x target. This is a smoke test of the compression stage, not the
final experiment.

Equivalent terminal commands are:

```bash
python -m pip install -r part3_llmlingua/requirements.txt
python part3_llmlingua/run_llmlingua.py compress --sample-indices 17 --ratios 2 --device cuda
python -m pip install -r part3_llmlingua/requirements_evaluate.txt
python part3_llmlingua/run_llmlingua.py evaluate --device cuda --dtype float16
```

The Transformers upgrade between the commands is intentional. LLMLingua 0.2.2
uses a legacy model-cache interface, whereas Llama 3.2 requires a newer
Transformers release. Each command runs in its own Python process, so changing
the package version between stages is safe and keeps the experiment
reproducible.

The compression environment uses `NousResearch/Llama-2-7b-hf` only as a
compatible tokenizer for counting prompt tokens. It does not load Llama 2 for
answer generation. The evaluation stage still uses
`unsloth/Llama-3.2-3B-Instruct` as the target LLM.

`microsoft/phi-2`, the LLMLingua compressor used here, has a much shorter
working context than most raw LongBench samples. For the full run, each
document is therefore split into ordered, non-overlapping chunks of at most
1,400 measurement-tokenizer tokens. Every chunk is compressed at the same
target rate, then the outputs are concatenated in their original order. This
is a resource-constrained, chunked reproduction of LLMLingua and is recorded
explicitly in every result row. A fresh full run uses:

```bash
python part3_llmlingua/run_llmlingua.py compress --device cuda --compressor-chunk-tokens 1400 --no-resume
python part3_llmlingua/run_llmlingua.py evaluate --device cuda --dtype float16 --no-resume
```

## Local Mac test

The project must use Python 3.10–3.12 rather than the system Python 3.14. On the
current Apple Silicon Mac:

```bash
python3.12 -m venv .venv-member3
source .venv-member3/bin/activate
python -m pip install -U pip
python -m pip install -r part3_llmlingua/requirements.txt
python part3_llmlingua/run_llmlingua.py compress --sample-indices 17 --ratios 2 --device mps
python -m pip install -r part3_llmlingua/requirements_evaluate.txt
python part3_llmlingua/run_llmlingua.py evaluate --limit 1 --device mps --dtype float16
```

The complete reported Part 3 experiment was run successfully on an Apple M5 Pro
with MPS. Colab remains an alternative for reproducing the pipeline in a shared
CUDA environment.

## Output files

| File | Contents |
| --- | --- |
| `compressed_member3.jsonl` | resumable compression checkpoint |
| `compressed_member3.json` | compression-only summary and rows |
| `results_member3.jsonl` | resumable answer/evaluation checkpoint |
| `results_member3.json` | final 2x/4x EM, F1, tokens and latency summary |

The final rows use the shared interface and additionally record
`target_compression_ratio`, `retained_fraction` and the actually achieved
`compression_ratio`. Actual ratios can differ from exactly 2x/4x because
LLMLingua and the target Llama model use different tokenizers.

## Reproducibility notes

- Compressor: `microsoft/phi-2`, an option documented by the official project.
- Compression measurement tokenizer: `NousResearch/Llama-2-7b-hf`. This avoids
  a tokenizer-file incompatibility between Llama 3.2 and the legacy
  Transformers version required by LLMLingua 0.2.2.
- Target generation model: `unsloth/Llama-3.2-3B-Instruct`, matching the
  completed Part 1 run and avoiding the gated Meta download.
- Decoding: greedy (`do_sample=False`), `max_new_tokens=64`.
- LLMLingua settings: token-level filtering, `iterative_size=200`, rates 0.5
  (2x target) and 0.25 (4x target).
- Token counts and achieved ratios are measured with the declared measurement
  tokenizer, not copied from LLMLingua's internal Phi-2 tokenizer. The same
  tokenizer must be used for all three methods when results are merged.

## Verified pilot (26 October 2026)

On a Colab Tesla T4, shared sample index 17 completed successfully at a nominal
2x target. Compression measured with the Llama-2 tokenizer reduced 1,439 prompt
tokens to 652 (2.207x) in 2.528 seconds. Llama-3.2 subsequently measured 621
prompt tokens, generated the answer in 3.140 seconds, and obtained EM 0.000 and
token-level F1 0.261 for this single sample. The compression and end-to-end
outputs are saved as `pilot_short.json` and `pilot_short_evaluated.json`.
This establishes that the full pipeline works; the one-sample scores are not a
final result, and long-input handling remains to be completed.

## Five-sample pilot (27 October 2026)

A second Colab T4 pilot used the five shortest shared samples, with fixed
indices `[17, 29, 126, 85, 112]`. Selecting short samples avoided exceeding
the compressor's context limit while preserving an identical sample set for
the 2x and 4x conditions.

| Target | Achieved ratio | Mean prompt tokens | EM | Token F1 | Compression latency (s) | Generation latency (s) | Total latency (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2x | 2.339 | 727.8 | 0.000 | 0.352 | 1.699 | 1.835 | 3.549 |
| 4x | 3.823 | 449.8 | 0.000 | 0.086 | 1.325 | 1.056 | 2.384 |

The achieved ratios in this table are measured with the target model's
tokenizer during evaluation. Compared with 2x compression, the 4x setting used
fewer prompt tokens and reduced generation and end-to-end latency, but mean F1
dropped substantially. This provides preliminary evidence of the expected
accuracy--efficiency trade-off. Exact Match is zero in both conditions because
it is strict and the pilot contains only five samples; it should not be treated
as a stable final estimate. The outputs are saved in `pilot5_compressed.json`
and `pilot5_results.json`, with their resumable JSONL checkpoints retained for
reproducibility.

## Full 150-sample experiment (29 October 2026)

The complete run evaluated all 150 shared samples at both nominal compression
targets, producing 300 result rows. Compression used `microsoft/phi-2`; answer
generation used `unsloth/Llama-3.2-3B-Instruct` with greedy decoding on Apple
M5 Pro MPS. The reported achieved ratios below use the target model tokenizer,
which is also used by the other project methods.

| Target | Achieved ratio | Mean prompt tokens | EM | Token F1 | Compression latency (s) | Generation latency (s) | Total latency (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2x | 2.094 | 3308.1 | 0.0067 | 0.2626 | 10.816 | 3.017 | 13.839 |
| 4x | 3.508 | 1961.6 | 0.0133 | 0.2207 | 9.846 | 2.130 | 11.980 |

Compared with 2x, the 4x condition reduced mean generation latency by about
29.4% and mean total latency by about 13.4%, while mean token F1 decreased by
about 16.0%. Exact Match is very strict for generated long-form answers and is
based on only one exact match at 2x and two at 4x, so the F1 difference is the
more informative accuracy result. These results are for the documented
resource-constrained chunked reproduction and should be compared with the
uncompressed and truncation outputs under the same shared configuration.

Official resources:

- https://github.com/microsoft/LLMLingua
- https://pypi.org/project/llmlingua/
- https://huggingface.co/microsoft/phi-2
