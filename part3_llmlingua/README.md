# Part 3 — LLMLingua (Member 3)

This folder reproduces the original **LLMLingua** method at nominal 2x and 4x
compression on the shared LongBench `multifieldqa_en` samples. The target LLM,
prompt template, sample order and EM/F1 implementation are identical to Part 1.

## 中文進度摘要

這個資料夾是 Member 3 負責的 LLMLingua 部分。目前已在 Google Colab
Tesla T4 上完成可運行的兩階段 pipeline：先用 LLMLingua 壓縮 prompt，釋放
compressor 後，再載入 `Llama-3.2-3B-Instruct` 生成答案並計算 EM、token-level
F1 和延遲。這樣可以避免 compressor 與 target model 同時佔用 GPU 而造成 OOM。

目前完成的五樣本 pilot 使用固定索引 `[17, 29, 126, 85, 112]`，每個樣本均測試
2x 和 4x 壓縮。2x 的平均 F1 為 0.352、平均總延遲為 3.549 秒；4x 的平均 F1
為 0.086、平均總延遲為 2.384 秒。初步結果顯示，更高壓縮率可以減少 token
數量和推理時間，但答案品質會明顯下降。

現階段結果只用來證明流程可行，不能當作最終結論。完整實驗會把長文本切成
固定的1,400-token區塊，各區塊獨立壓縮後按原順序合併，避免超過Phi-2
compressor的context limit。接下來需要跑完150題，並與uncompressed和
head-and-tail truncation使用相同樣本及設定進行正式比較。

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

The Mac run is useful for a one-sample smoke test. Colab is recommended for the
reported experiment because all members can use the same CUDA environment.

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

Official resources:

- https://github.com/microsoft/LLMLingua
- https://pypi.org/project/llmlingua/
- https://huggingface.co/microsoft/phi-2
