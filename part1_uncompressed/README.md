# Part 1 — Uncompressed Baseline

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

Member 1's pipeline: **no compression**. The full retrieved context, the question
and the instruction are packed into one prompt and sent to
`meta-llama/Llama-3.2-3B-Instruct`. This is the reference point that Parts 2 and
3 are compared against.

> Member 1 的流程**不做任何壓縮** —— 把檢索到的完整上下文、問題與
> 指示全部塞進同一個 prompt，送給 `meta-llama/Llama-3.2-3B-Instruct`，作為
> Part 2、Part 3 的比較基準。

## Files

| File | Purpose |
| --- | --- |
| `run_baseline.py` | Runs inference, scores EM/F1, writes results |
| `requirements.txt` | Python dependencies |
| `results_member1.json` | Final output (created by the run) |
| `results_member1.jsonl` | Per-sample checkpoint, enables `--resume` |

Shared assets live in [`../shared`](../shared) (Member 1 owns the sample index):

| File | Purpose |
| --- | --- |
| [`shared/prepare_samples.py`](../shared/prepare_samples.py) | Downloads LongBench `multifieldqa_en`, builds the fixed sample index |
| [`shared/samples.json`](../shared/samples.json) | Fixed sample index used by **all three members** (150 = full test split) |
| [`shared/prompt_template.py`](../shared/prompt_template.py) | Unified prompt + chat template + token-budget fallback |
| [`shared/metrics.py`](../shared/metrics.py) | SQuAD-style Exact Match / token F1 |
| [`shared/config.py`](../shared/config.py) | Model, seed, token budgets shared by everyone |

> `run_baseline.py` 負責推論、算 EM/F1 並輸出結果；
> `results_member1.json` 是最終結果，`results_member1.jsonl` 是逐筆 checkpoint
> （中斷後可續跑）。`../shared/` 放三人共用的東西：`samples.json` 是固定的樣本
> 索引（三人都用同一份，150 筆等於官方完整測試集）、`prompt_template.py` 是統一
> prompt 與 chat template、`metrics.py` 是 SQuAD 式 EM / token F1、
> `config.py` 是 model / seed / token 預算。

## Setup

```powershell
# Project-local environment (keeps your global Python untouched)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r part1_uncompressed\requirements.txt
```

`requirements.txt` pulls the default PyPI `torch`, which is the CUDA build on
Windows. For a CPU-only machine use instead:

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

For an NVIDIA GPU (tested on an RTX 3060 12 GB, driver 560.94 / CUDA 12.6):

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu126
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --device cuda --dtype float16
```

> 用專案專屬的 `.venv`，不會動到全域 Python 環境。
> `requirements.txt` 裝的是 PyPI 預設版 `torch`（Windows 上即 CUDA 版）；
> 純 CPU 機器改用 `torch --index-url https://download.pytorch.org/whl/cpu`；
> 有 NVIDIA 顯卡（本機 RTX 3060 12 GB、driver 560.94 / CUDA 12.6 實測可用）改用
> `cu126` 版，並在執行時加上 `--device cuda --dtype float16`。

### Dataset size

`multifieldqa_en` in LongBench v1 contains only **150** test examples, so the
shared index keeps all 150 instead of the 300–500 planned. This is the complete
official split, which keeps EM/F1 comparable with published LongBench numbers.
`shared/prepare_samples.py --num-samples N` still supports smaller subsets for
quick experiments (the index is seed-fixed and identical for all members).

> LongBench v1 的 `multifieldqa_en` 只有 **150** 筆測試資料，所以
> 共用索引保留全部 150 筆（而非原先規劃的 300–500 筆）。這是官方完整測試集，
> EM/F1 才能與論文數字對照；若只做小規模實驗，仍可用
> `shared/prepare_samples.py --num-samples N` 產生子集（索引由固定 seed 產生，
> 三人完全一致）。

## Usage

```powershell
# 1) Build the shared sample index once (downloads ~110 MB)
.\.venv\Scripts\python.exe shared/prepare_samples.py

# 2) Smoke test on 5 samples
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --limit 5

# 3) Full run (resumable: re-running skips finished ids)
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py
```

Useful flags: `--model`, `--device cpu|cuda|auto`, `--dtype auto|float32|float16|bfloat16`,
`--max-new-tokens`, `--max-prompt-tokens`, `--no-resume`, `--save-context`.

> 第一步只需執行一次，會下載約 110 MB 的 LongBench 資料並產生共用
> 樣本索引；第二步先跑 5 筆確認環境正常；第三步跑完整 150 筆，中斷後重跑會自動
> 跳過已完成的 id（續跑）。有 GPU 時在第三步加上 `--device cuda --dtype float16`。

### Running on a remote GPU / OpenAI-compatible server

Part 1 does not have to run on this laptop. Any OpenAI-compatible server
(vLLM, TGI, llama.cpp server, Ollama, …) works:

```powershell
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --backend openai `
  --base-url http://127.0.0.1:8000/v1 `
  --model meta-llama/Llama-3.2-3B-Instruct
```

> Part 1 不一定要在本機跑。任何 OpenAI 相容伺服器（vLLM、TGI、
> llama.cpp server、Ollama 等）都可以，用 `--backend openai --base-url ...` 指定。

### Gated model

`meta-llama/Llama-3.2-3B-Instruct` is license-gated on Hugging Face. Either run
`huggingface-cli login` with an account that accepted the licence, or use the
ungated mirror `unsloth/Llama-3.2-3B-Instruct` via `--model`.

> `meta-llama/Llama-3.2-3B-Instruct` 在 Hugging Face 上需要接受授權
> 才能下載。做法二選一：用已接受授權的帳號執行 `huggingface-cli login`，或改用
> 無閘門鏡像 `unsloth/Llama-3.2-3B-Instruct`（以 `--model` 指定）。本專案的
> 結果就是用後者跑出來的，兩者權重相同。

## Output format

One record per sample, exactly as agreed in [`../plan.md`](../plan.md):

```json
{
  "id": "…",
  "question": "…",
  "docs": null,
  "prompt_tokens": 3721,
  "answer": "…",
  "em": 0.0,
  "f1": 0.4,
  "compression_latency": 0.0,
  "generation_latency": 42.1,
  "total_latency": 42.6
}
```

Extra diagnostic fields: `original_prompt_tokens`, `truncated`,
`docs_chars_used`, `compression_ratio` (always `1.0` for this method),
`answers`, `method`, `model`. `prompt_tokens` counts the **chat-templated**
prompt, so all members must use `shared.prompt_template` to stay comparable.

`results_member1.json` = `{meta, summary, results}` where `summary` contains
mean EM/F1, mean prompt tokens and mean latencies.

> 每筆樣本一筆紀錄，欄位與 [`../plan.md`](../plan.md) 的約定一致
> （`id`、`question`、`docs`、`prompt_tokens`、`answer`、`em`、`f1`、
> `compression_latency`、`generation_latency`、`total_latency`）。另有診斷欄位
> `original_prompt_tokens`、`truncated`、`docs_chars_used`、`compression_ratio`
> （本方法固定為 `1.0`）、`answers`、`method`、`model`。
> `prompt_tokens` 算的是**套用 chat template 後**的長度，所以三人務必都用
> `shared.prompt_template`，結果才可比。`results_member1.json` 的結構是
> `{meta, summary, results}`，`summary` 放平均 EM/F1、平均 prompt 長度與平均耗時。

## Protocol

- Greedy decoding (`do_sample=False`), `max_new_tokens=64`
- Prompt budget `MAX_PROMPT_TOKENS = 32768 - 64 - 32 = 32672`
- **No truncation in practice**: Llama-3.2-3B-Instruct is natively 128k
  (`max_position_embeddings=131072`, `rope_scaling.type="llama3"`), so the 32k
  budget is a self-imposed cap that bounds the fp16 KV cache on a 12 GB card.
  The longest sample here is 15 026 tokens, so **all 150 samples run
  untruncated** (`truncated_samples: 0`) — which is exactly what an
  "uncompressed" baseline must be able to claim.
- **Over-length fallback**: if a future sample did not fit, `docs` would be
  truncated from the **tail** (head kept) via binary search so the question and
  `Answer:` suffix always survive; `truncated: true` and
  `original_prompt_tokens` record how much was dropped. A CUDA OOM triggers one
  retry with a halved prompt budget and sets `oom_fallback: true`.

> 解碼採 greedy（`do_sample=False`），`max_new_tokens=64`。
> Prompt 預算是 `MAX_PROMPT_TOKENS = 32768 - 64 - 32 = 32672`。
> Llama-3.2-3B-Instruct 原生支援 128k（`max_position_embeddings=131072`、
> `rope_scaling.type="llama3"`），32k 只是為了在 12 GB 顯卡上控制 fp16 KV cache
> 而自訂的上限；本資料最長樣本 15 026 tokens，因此**150 筆全部完整送入、0 筆被
> 截斷**（`truncated_samples: 0`），符合「uncompressed」基準的要求。
> 若日後遇到超長樣本，會從**尾端**二分搜尋截斷（保留頭部），確保問題與
> `Answer:` 結尾一定留存，並以 `truncated: true` 與 `original_prompt_tokens`
> 記錄被砍掉多少；CUDA OOM 時會將 prompt 預算減半重試一次，並標記
> `oom_fallback: true`。

## Results (local RTX 3060, fp16)

`results_member1.json`, 150/150 samples, 0 truncated:

| Metric | Value |
| --- | --- |
| mean EM | 0.0933 |
| mean F1 | 0.4296 |
| mean prompt tokens | 6 966.8 |
| mean generation latency | 4.63 s |
| mean total latency | 4.65 s |

Wall clock for the full split is ≈12 min on the GPU versus ≈6.3 h on CPU
(fp32, ≈152 s/sample), so Parts 2 and 3 should also use `--device cuda
--dtype float16`.

> `results_member1.json` 為 150/150 筆、0 筆截斷的結果 ——
> 平均 EM 0.0933（14 題完全命中）、平均 F1 0.4296（中位數 0.381）、平均 prompt
> 長度 6 966.8 tokens（最長 15 026）、平均生成時間 4.63 秒、平均總時間 4.65 秒，
> 沒有空答案。全跑 GPU 約 12 分鐘，純 CPU（fp32）約 6.3 小時，因此 Part 2、Part 3
> 建議也用 `--device cuda --dtype float16`。

## Notes for the other members

Parts 2 and 3 only need `shared/samples.json` and `shared/prompt_template.py`.
They must not modify `shared/samples.json`, `shared/config.py` or
`shared/prompt_template.py`; raise changes in the weekly sync instead, otherwise
the three result files stop being comparable.

> Part 2、Part 3 只需要 `shared/samples.json` 與
> `shared/prompt_template.py`。請**不要**修改 `shared/samples.json`、
> `shared/config.py`、`shared/prompt_template.py`；若要調整，請在每週會議提出，
> 由三人一起改，否則三份結果就無法比較。
