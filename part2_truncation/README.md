# Part 2 — Head-and-Tail Truncation

Non-semantic compression baseline: keep the first and last tokens of the
document, drop the middle. The instruction and the question are never
truncated. Uses the same sample index, prompt template, metrics and model
loader as Part 1.

> 無語意壓縮基準：保留文章開頭與結尾的 token，丟棄中間。指令與問題不會被
> 截斷。使用與 Part 1 相同的樣本索引、prompt 模板、評分方式與模型載入器。

## Method

For a document of `n` tokens and a target ratio `r`, the budget is
`b = round(n / r)`. The first `floor(b * head_frac)` and the last
`b - floor(b * head_frac)` tokens are kept (default `head_frac = 0.5`).
Documents already shorter than the budget are left unchanged. Token counts use
the Llama-3.2 tokenizer. The compression ratio is measured on the document
only, not on the full prompt; both are recorded.

> 文章共 `n` 個 token、目標壓縮比 `r` 時，保留預算 `b = round(n / r)`，頭尾
> 各取一部分（預設各 50%）。文章本來就比預算短則不處理。壓縮比以文章部分計算，
> 結果同時記錄整個 prompt 的壓縮比。

## Files

| File | Description |
| --- | --- |
| `run_truncation.py` | Truncation + generation + scoring pipeline |
| `results_member2_2x.json` | Final results at 2x (summary + per-sample records) |
| `results_member2_4x.json` | Final results at 4x |
| `make_table.py` | Builds the comparison table from all result files |

## Quick start

```powershell
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 2 --limit 5 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 2 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 4 --dtype float16
```

Colab (T4 GPU): clone the repo, `pip install -r part1_uncompressed/requirements.txt`,
mount Google Drive, then pass `--out-dir` so checkpoints survive a disconnect:


> 在 Colab T4 上執行：clone 專案、安裝套件、掛載 Google Drive，並用
> `--out-dir` 讓進度寫入 Drive，斷線後重跑同一指令即可接續。

## Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--ratio` | 2.0 | Target compression ratio on the document |
| `--head-frac` | 0.5 | Share of the kept tokens taken from the head |
| `--limit` | all | Only run the first N samples |
| `--model` | `MODEL_ID` | Use `unsloth/Llama-3.2-3B-Instruct` if the gated model is unavailable |
| `--dtype` | auto | Use the same dtype as Part 1 (`float16`) |
| `--out-dir` | this folder | Where `.jsonl` / `.json` are written |
| `--chunk-size` / `--chunk-threshold` | 2048 / 4096 | Chunked prefill for long prompts |
| `--no-resume` | off | Ignore the existing `.jsonl` checkpoint |

## Output format

Same structure as Part 1: `results_member2_<r>x.jsonl` is a per-sample
checkpoint written after every sample (re-running the same command resumes);
`results_member2_<r>x.json` is written at the end with a `summary` block and
all `results`. Extra fields compared with Part 1: `orig_docs_tokens`,
`retained_docs_tokens`, `compression_ratio` (document), `prompt_compression_ratio`
(full prompt), `compression_latency`, `head_frac`.

> 輸出格式與 Part 1 相同：`.jsonl` 為每題即時存檔的檢查點，`.json` 為跑完後
> 產生的最終結果（含 `summary` 與全部 `results`）。

## Implementation notes

- Greedy decoding (`do_sample=False`), `max_new_tokens` from `shared/config.py`.
- A warm-up generation is run before timing.
- `total_latency` covers truncation, prompt rendering and generation.
- On a free Colab T4 (about 15 GB), very long prompts ran out of memory in
  the attention step. Prompts longer than `--chunk-threshold` tokens are
  therefore prefilled in chunks of `--chunk-size` tokens. Shorter prompts use
  the same path as Part 1.
- If a sample still runs out of memory it is skipped, not written to the
  checkpoint (so a re-run retries it), and listed in `oom_skipped_ids` in the
  final JSON.

> 實作說明：貪婪解碼；計時前先暖機；`total_latency` 含截斷、組 prompt 與生成。
> 免費 Colab T4 上，很長的 prompt 在 attention 階段會記憶體不足，因此超過門檻
> 的 prompt 改為分段預讀；仍然失敗的題目會被跳過並記錄在 `oom_skipped_ids`。

## Results

| Setting | n | EM | F1 | Mean doc ratio | Mean total latency (s) |
| --- | --- | --- | --- | --- | --- |
| Uncompressed (Part 1) | 150 | 0.0933 | 0.4296 | 1.00 | [X] |
| Head-tail 2x | [150] | [0.0733] | [0.4065] | [2.00] | [5.82] |
| Head-tail 4x | [150] | [0.0667] | [0.3620] | [4.00] | [3.55s] |

Skipped (OOM) samples: [X].

## Known limitations

- Only one dataset (`multifieldqa_en`), one model, one `head_frac`.
- Answer-position analysis uses character offsets as an approximation of
  token offsets, and only covers answers found verbatim in the document.
- Environment: Colab T4, `float16`, transformers [版本], torch [版本].

> 限制：單一資料集、單一模型、單一 `head_frac`；答案位置分析以字元位置近似，
> 且僅涵蓋在原文中逐字出現的答案。