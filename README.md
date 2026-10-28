# CISC7021-Group38
CISC7021 Group38 Course Project

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

## Project

Study of prompt-compression methods for long-context QA with
`Llama-3.2-3B-Instruct` on LongBench `multifieldqa_en`. Three methods are compared
under an identical sample index, prompt template and metric implementation
(see [plan.md](./plan.md) for the full division of work):

| Part | Method | Owner | Status |
| --- | --- | --- | --- |
| [part1_uncompressed](./part1_uncompressed) | No compression (full context baseline) | Member 1 | Done — 150/150, EM 0.0933 / F1 0.4296 |
| [part2_truncation](./part2_truncation) | Head-and-tail truncation (2x / 4x) | Member 2 | Done — 150/150 at both ratios, EM 0.0733 / 0.0667, F1 0.4065 / 0.3620 |
| [part3_llmlingua](./part3_llmlingua) | LLMLingua (2x / 4x) | Member 3 | Pipeline done — verified 5-sample pilot at both ratios; full 150-sample run pending |

> 本專案比較三種 prompt 壓縮方法 —— 在 LongBench
> `multifieldqa_en` 上以 `Llama-3.2-3B-Instruct` 做長文本問答。三人使用完全相同
> 的樣本索引、prompt 模板與評分實作，確保三份結果可互相對照（分工見
> [plan.md](./plan.md)）。Part 1 已完成 150/150 筆（EM 0.0933 / F1 0.4296）；
> Part 2 的 2x 與 4x 亦各完成 150/150 筆（EM 0.0733 / 0.0667，F1 0.4065 /
> 0.3620）；Part 3 已完成兩階段 LLMLingua pipeline 並在 Colab T4 上通過 5 筆
> pilot 驗證，但 150 筆完整實驗（`results_member3.json`）尚未產生。

## Key results

All numbers below are read from the committed result files, not re-typed by hand.

| Method | n | EM | F1 | Mean prompt tokens | Doc ratio | Compression (s) | Generation (s) | Total (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uncompressed (Part 1) | 150 | 0.0933 | 0.4296 | 6 966.8 | 1.000 | 0.000 | 4.634 | 4.647 |
| Head-tail 2x (Part 2) | 150 | 0.0733 | 0.4065 | 3 523.1 | 2.000 | 0.019 | 5.793 | 5.822 |
| Head-tail 4x (Part 2) | 150 | 0.0667 | 0.3620 | 1 801.2 | 4.000 | 0.018 | 3.523 | 3.546 |
| LLMLingua 2x (Part 3, pilot) | 5 | 0.000 | 0.3523 | 727.8 | 2.339 | 1.699 | 1.835 | 3.549 |
| LLMLingua 4x (Part 3, pilot) | 5 | 0.000 | 0.0860 | 449.8 | 3.823 | 1.325 | 1.056 | 2.384 |

Sources: [Part 1](./part1_uncompressed/results_member1.json) ·
[Part 2 2x](./part2_truncation/results_member2_2x.json) ·
[Part 2 4x](./part2_truncation/results_member2_4x.json) ·
[Part 3 pilot](./part3_llmlingua/pilot5_results.json) ·
[combined table](./part2_truncation/results_table.md).

- Head-and-tail truncation loses 5.4% relative F1 at 2x and 15.7% at 4x while
  removing 49% and 74% of the prompt tokens. All 150 samples were truncated in
  both settings, as intended, so Part 1 really is the uncompressed reference.
- Part 2 reports two ratios: the **document** ratio (achieved 2.000 / 4.000) and
  the **whole-prompt** ratio (1.969 / 3.820), because the instruction and the
  question are always kept.
- The LLMLingua rows are a five-sample pilot on the five shortest shared samples
  (indices 17, 29, 126, 85, 112). They are **not** comparable with the
  150-sample rows, and EM is not meaningful at n = 5.
- Latencies come from different hardware — Part 1 on a local RTX 3060, Parts 2
  and 3 on a Colab T4, all `float16` — so compare token counts and quality
  across parts, not absolute seconds.

> 上表數字直接取自各結果檔（非人手抄錄）。頭尾截斷在 2x 只損失 5.4% 相對 F1、
> 4x 損失 15.7%，但分別減少 49% 與 74% 的 prompt token；兩個設定的 150 筆全部
> 有截斷，符合方法設計，因此 Part 1 確實是完全不壓縮的基準。Part 2 同時記錄
> 「文章壓縮比」（實得 2.000 / 4.000）與「整個 prompt 壓縮比」（1.969 /
> 3.820），因為指令與問題一律保留。LLMLingua 兩列只是 5 筆 pilot（共用索引中
> 最短的 5 題：17、29、126、85、112），不可與 150 筆的結果直接比較，n = 5 時
> EM 也沒有統計意義。延遲來自不同硬體（Part 1 本機 RTX 3060、Part 2/3 Colab
> T4，皆 `float16`），跨部分請比較 token 數與品質，不要比較絕對秒數。

## Repository layout

| Path | Description |
| --- | --- |
| [shared/](./shared) | Sample index, prompt template, metrics and config shared by all members |
| [part1_uncompressed/](./part1_uncompressed) | Uncompressed baseline pipeline + 150-sample results ([README](./part1_uncompressed/README.md)) |
| [part2_truncation/](./part2_truncation) | Head-and-tail truncation + 2x/4x results ([README](./part2_truncation/README.md), [table](./part2_truncation/results_table.md)) |
| [part3_llmlingua/](./part3_llmlingua) | Two-stage LLMLingua compress/evaluate pipeline + pilots ([README](./part3_llmlingua/README.md)) |
| [acl_latex.tex](./acl_latex.tex) | ACL two-column review report (Phase 1) |
| [plan.md](./plan.md) | Work split and shared interface |
| [project.md](./project.md) | Course project requirements |

> `shared/` 是三人共用的樣本索引、prompt 模板、評分方式與參數設定；
> `part1_uncompressed/` 是不壓縮基準流程與 150 筆結果；`part2_truncation/` 是
> 頭尾截斷與 2x/4x 結果；`part3_llmlingua/` 是兩階段 LLMLingua 流程與 pilot；
> `acl_latex.tex` 為 ACL 格式回顧報告；`plan.md` 為分工與共用介面；
> `project.md` 為課程專案要求。

## Quick start

Parts 1 and 2 share one environment; Part 3 needs two environments because
LLMLingua 0.2.2 pins an older `transformers` than Llama 3.2 requires.

```powershell
# Shared setup: project-local venv + shared sample index
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r part1_uncompressed\requirements.txt
.\.venv\Scripts\python.exe shared/prepare_samples.py
```

```powershell
# Part 1 — uncompressed baseline (≈12 min for 150 samples on an RTX 3060)
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --limit 5 --device cuda --dtype float16
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --device cuda --dtype float16

# Part 2 — head-and-tail truncation at 2x and 4x, then rebuild the table
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 2 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 4 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\make_table.py

# Part 3 — LLMLingua: compress first, then evaluate (separate requirements)
python -m pip install -r part3_llmlingua\requirements.txt
python part3_llmlingua\run_llmlingua.py compress --device cuda --compressor-chunk-tokens 1400
python -m pip install -r part3_llmlingua\requirements_evaluate.txt
python part3_llmlingua\run_llmlingua.py evaluate --device cuda --dtype float16
```

Every runner is resumable: it writes one `.jsonl` record per sample and skips
completed ids on re-run (pass `--no-resume` to start over). Full flags and output
formats are in [Part 1](./part1_uncompressed/README.md),
[Part 2](./part2_truncation/README.md) and
[Part 3](./part3_llmlingua/README.md). On a CPU-only machine install
`torch --index-url https://download.pytorch.org/whl/cpu` and drop
`--device cuda --dtype float16` (≈152 s/sample instead of ≈4.6 s). Part 3 needs
Python 3.10–3.12 and follows the Colab T4 instructions in its own README.

> 建立專案專屬 `.venv`（不動到全域 Python）、安裝相依套件、下載並建立共用樣本
> 索引，先跑 5 筆確認環境正常，再跑完整 150 筆。Part 1、Part 2 共用同一環境；
> Part 3 因為 LLMLingua 0.2.2 綁定較舊的 `transformers`，所以壓縮與評估分兩個
> 環境（兩條指令各自在獨立 Python 程序執行）。所有 runner 都支援續跑：每題寫入
> 一筆 `.jsonl`，重跑會跳過已完成的 id（`--no-resume` 可從頭開始）。完整參數與
> 輸出格式見 Part 1、Part 2、Part 3 各自的 README。純 CPU 環境請改裝
> `torch --index-url https://download.pytorch.org/whl/cpu`，並去掉
> `--device cuda --dtype float16`（每筆約 152 秒，而非 4.6 秒）；Part 3 需
> Python 3.10–3.12，並依其 README 在 Colab T4 上執行。

## Open items

| Item | State |
| --- | --- |
| Part 1: 150-sample uncompressed results | Done |
| Part 2: 150 samples at 2x and 4x | Done |
| Part 3: two-stage LLMLingua pipeline | Done and verified on Colab T4 |
| Part 3: full 150-sample 2x/4x run | **Pending** — only the 5-sample pilot is committed; `results_member3.json` does not exist yet |
| Part 2: answer-position failure analysis | **Pending** — requested in `plan.md`, but `run_truncation.py` does not compute answer positions yet |
| Combined table across all three methods | **Partial** — `make_table.py` covers Parts 1–2 only; add Part 3 when its full run exists |

> 目前狀態：Part 1 與 Part 2 的 150 筆結果已完成；Part 3 的兩階段 pipeline 已在
> Colab T4 驗證，但只提交了 5 筆 pilot，尚未產生 `results_member3.json`。
> `plan.md` 要求的「答案位於中間時的失敗案例分析」在 Part 2 仍未實作。
> 合併表格目前只涵蓋 Part 1–2，待 Part 3 完整結果產生後再補上。

