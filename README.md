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
| [part2_truncation](./part2_truncation) | Head-and-tail truncation | Member 2 | To do |
| [part3_llmlingua](./part3_llmlingua) | LLMLingua (2x / 4x) | Member 3 | To do |

> 本專案比較三種 prompt 壓縮方法 —— 在 LongBench
> `multifieldqa_en` 上以 `Llama-3.2-3B-Instruct` 做長文本問答。三人使用完全相同
> 的樣本索引、prompt 模板與評分實作，確保三份結果可互相對照（分工見
> [plan.md](./plan.md)）。Part 1 已完成 150/150 筆，EM 0.0933 / F1 0.4296；
> Part 2（頭尾截斷）、Part 3（LLMLingua 2x / 4x）尚待完成。

## Repository layout

| Path | Description |
| --- | --- |
| [shared/](./shared) | Sample index, prompt template, metrics and config shared by all members |
| [part1_uncompressed/](./part1_uncompressed) | Uncompressed baseline pipeline ([README](./part1_uncompressed/README.md)) |
| [plan.md](./plan.md) | Work split and shared interface |
| [project.md](./project.md) | Course project requirements |

> `shared/` 是三人共用的樣本索引、prompt 模板、評分方式與參數設定；
> `part1_uncompressed/` 是不壓縮基準流程；`plan.md` 為分工與共用介面；
> `project.md` 為課程專案要求。

## Quick start (Part 1)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r part1_uncompressed\requirements.txt
.\.venv\Scripts\python.exe shared/prepare_samples.py
.\.venv\Scripts\python.exe part1_uncompressed\run_baseline.py --limit 5 --device cuda --dtype float16
```

Full details, flags and the output format are in
[part1_uncompressed/README.md](./part1_uncompressed/README.md). On a CPU-only
machine install `torch --index-url https://download.pytorch.org/whl/cpu` and drop
`--device cuda --dtype float16` (≈152 s/sample instead of ≈4.6 s).

> 建立專案專屬 `.venv`（不動到全域 Python）、安裝相依套件、下載並
> 建立共用樣本索引，先跑 5 筆確認環境正常。完整說明、參數與輸出格式見
> [part1_uncompressed/README.md](./part1_uncompressed/README.md)。純 CPU 環境請改裝
> `torch --index-url https://download.pytorch.org/whl/cpu`，並去掉
> `--device cuda --dtype float16`（每筆約 152 秒，而非 4.6 秒）。

