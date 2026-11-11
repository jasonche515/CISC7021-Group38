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


| File                                            | Description                                                                                                            |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `run_truncation.py`                             | Truncation + generation + scoring pipeline                                                                             |
| `run_truncation_result.ipynb`                   | Analysis notebook: optional re-run (Colab-safe, resumable), result tables, answer-position analysis, ACL-ready figures |
| `results_member2_2x.json`                       | Final results at 2x (summary + per-sample records)                                                                     |
| `results_member2_4x.json`                       | Final results at 4x                                                                                                    |
| `make_table.py`                                 | Builds the comparison table from all result files                                                                      |
| `part2_summary_table.csv` / `.tex`              | Main metrics table exported by the notebook                                                                            |
| `answer_position_analysis.csv`                  | Per-sample answer location, match type and zone (2x and 4x)                                                            |
| `answer_position_stats.csv` / `.tex`            | Mean F1 and 95% bootstrap CI for kept / partial / dropped answers                                                      |
| `figures/fig_answer_position_scatter.(pdf,png)` | Figure A: F1 vs. relative answer position, with the dropped region shaded                                              |
| `figures/fig_f1_by_answer_zone.(pdf,png)`       | Figure B: mean F1 by answer zone with 95% CI                                                                           |
| `figures/fig_zone_share.(pdf,png)`              | Figure C: share of samples per answer zone                                                                             |




## Quick start

```powershell
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 2 --limit 5 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 2 --dtype float16
.\.venv\Scripts\python.exe part2_truncation\run_truncation.py --ratio 4 --dtype float16
```

Colab (T4 GPU): clone the repo, `pip install -r part1_uncompressed/requirements.txt`,
mount Google Drive, then pass `--out-dir` so checkpoints survive a disconnect:

```bash
python part2_truncation/run_truncation.py --ratio 2 --dtype float16 \
  --model unsloth/Llama-3.2-3B-Instruct \
  --out-dir /content/drive/MyDrive/cisc7021/results
```

> 在 Colab T4 上執行：clone 專案、安裝套件、掛載 Google Drive，並用
> `--out-dir` 讓進度寫入 Drive，斷線後重跑同一指令即可接續。



### Analysis notebook

Open `run_truncation_result.ipynb` from the repository (it locates the repo root
automatically). Set `RERUN = True` in the first cell to regenerate the results
(GPU required, resumable); leave it `False` to only read the existing JSON files.
The notebook reuses `shared/` (config, metrics, prompt template) and
`part1_uncompressed/` (sample loader, I/O helpers) so that numbers stay
comparable with the other parts.

> 分析 notebook：`RERUN = False` 只讀取既有結果；`True` 則重新跑（需要 GPU，可斷點續跑）。
> Notebook 重用 `shared/` 與 `part1_uncompressed/`，確保與其他 Part 可比較。



## Options


| Flag                                 | Default     | Meaning                                                                                                  |
| ------------------------------------ | ----------- | -------------------------------------------------------------------------------------------------------- |
| `--ratio`                            | 2.0         | Target compression ratio on the document                                                                 |
| `--head-frac`                        | 0.5         | Share of the kept tokens taken from the head                                                             |
| `--limit`                            | all         | Only run the first N samples                                                                             |
| `--model`                            | `MODEL_ID`  | Use `unsloth/Llama-3.2-3B-Instruct` if the gated model is unavailable (this is what the Colab runs used) |
| `--dtype`                            | auto        | Use the same dtype as Part 1 (`float16`)                                                                 |
| `--out-dir`                          | this folder | Where `.jsonl` / `.json` are written                                                                     |
| `--chunk-size` / `--chunk-threshold` | 2048 / 4096 | Chunked prefill for long prompts                                                                         |
| `--no-resume`                        | off         | Ignore the existing `.jsonl` checkpoint                                                                  |




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
- The meta-llama checkpoint is gated on Hugging Face; the runs use the public
mirror `unsloth/Llama-3.2-3B-Instruct`. Make sure every part reports the same
model.

> 實作說明：貪婪解碼；計時前先暖機；`total_latency` 含截斷、組 prompt 與生成。
> 免費 Colab T4 上，很長的 prompt 在 attention 階段會記憶體不足，因此超過門檻
> 的 prompt 改為分段預讀；仍然失敗的題目會被跳過並記錄在 `oom_skipped_ids`。
> Meta 官方模型需授權，實驗改用公開鏡像 `unsloth/Llama-3.2-3B-Instruct`。



## Results


| Setting               | n   | EM     | F1     | Mean doc ratio | Mean total latency (s) |
| --------------------- | --- | ------ | ------ | -------------- | ---------------------- |
| Uncompressed (Part 1) | 150 | 0.0933 | 0.4296 | 1.00           | [X]                    |
| Head-tail 2x          | 150 | 0.0733 | 0.4065 | 2.00           | 5.82                   |
| Head-tail 4x          | 150 | 0.0667 | 0.3620 | 4.00           | 3.55                   |


Prompt tokens: 6,966.8 (uncompressed), 3,523.1 (2x, -49.4%), 1,801.2 (4x, -74.1%).
Skipped (OOM) samples: [X — check `oom_skipped_ids`].

Head-tail truncation keeps most of the baseline F1 at 2x (0.4065 vs 0.4296) and
loses more at 4x (0.3620). Greedy decoding is not bit-exact across GPUs, and the
Uncompressed vs. Head-tail 2x significance changes between runs, so the 2x loss
is reported as marginal.

> 結果摘要：2x 幾乎保住基準 F1，4x 下降較多；2x 與基準的顯著性在不同 run 之間會翻轉，
> 因此視為「邊際性損失」。



## Answer-position analysis

**Question.** Head-tail truncation removes the middle of the document. Does F1
drop when the gold answer lies in the removed part?

**Method.** For every sample the gold answer is located in the *original*
document and mapped to token offsets (tokenizer offset mapping, not character
approximations). The span is compared with the kept head and tail ranges:


| Zone                      | Meaning                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| `kept_head` / `kept_tail` | An occurrence of the answer lies fully inside the kept head / tail |
| `partial`                 | An occurrence overlaps a kept region but is cut at the boundary    |
| `dropped_middle`          | Every occurrence lies in the removed middle                        |
| `not_found`               | The answer could not be located (e.g. yes/no or inferred answers)  |


Matching has two levels, recorded in `match_type`:

- `exact`: the normalised answer string (lower-case, punctuation removed) is found verbatim.
- `fuzzy`: no verbatim match; the best sliding window of the document by content-word
overlap with the answer is used (overlap >= 0.6). The location is approximate.
- `none`: no match.

Many MultiFieldQA-en gold answers are annotator-written sentences rather than
spans of the document, so a verbatim-only search finds only 18 of 150 samples.
With normalisation and fuzzy matching: 46 exact, 87 fuzzy, 17 none (identical at
2x and 4x, because matching does not depend on the ratio).

**Results (all 150 samples, exact + fuzzy + none).**


| Ratio | Zone           | n   | Mean F1 | Mean EM |
| ----- | -------------- | --- | ------- | ------- |
| 2x    | kept_head      | 85  | 0.4921  | 0.1176  |
| 2x    | kept_tail      | 16  | 0.3768  | 0.0000  |
| 2x    | partial        | 1   | 0.2069  | 0.0000  |
| 2x    | dropped_middle | 31  | 0.2259  | 0.0323  |
| 2x    | not_found      | 17  | 0.3481  | 0.0000  |
| 4x    | kept_head      | 63  | 0.5109  | 0.1587  |
| 4x    | kept_tail      | 11  | 0.3762  | 0.0000  |
| 4x    | partial        | 3   | 0.3501  | 0.0000  |
| 4x    | dropped_middle | 56  | 0.2006  | 0.0000  |
| 4x    | not_found      | 17  | 0.3351  | 0.0000  |


Pooling head and tail, the mean F1 is about 0.47 (n=101) when the answer is kept
and 0.23 (n=31) when it is dropped at 2x; at 4x it is about 0.49 (n=74) versus
0.20 (n=56). 95% bootstrap confidence intervals are in `answer_position_stats.csv`.
[Paste CI values here after running the notebook.]

**Findings.**

1. F1 is clearly lower when the gold answer falls in the removed middle, at both ratios.
2. The share of dropped-middle samples grows from 31 to 56 of 150 (21% to 37%) when going
  from 2x to 4x, which accounts for most of the F1 loss at 4x; F1 inside each group changes little.
3. Most answers are near the start of the document (`kept_head` is the largest group), which
  explains why a simple head-and-tail baseline stays competitive.
4. Kept-answer F1 (about 0.47-0.49) is close to the uncompressed baseline (0.4296), so F1 is
  limited by the generator and the F1 metric itself, not only by truncation.

**How to read it.** The analysis is correlational: questions whose answers appear early
may also be easier. Group sizes for `partial` (1-3) and exact-only `dropped_middle` (8 at 2x)
are too small for conclusions; report `n` with every number.

> 答案位置分析：答案落在被刪除的中間時 F1 明顯較低（約 0.20-0.23 vs 0.47-0.49）；
> 4x 較差主要因為「答案被刪」的樣本比例由 21% 升到 37%。這是相關性分析，且 fuzzy 定位為近似。



## Known limitations

- Only one dataset (`multifieldqa_en`, 150 samples), one model, one `head_frac`.
- Answer-position analysis uses token offsets, but 87 of 150 locations come from fuzzy
matching (approximate), 17 answers cannot be located, and `partial` / `kept_tail` groups are very small.
An exact-only robustness check should be reported alongside the pooled result.
- Position results are correlational and not causal.
- F1 is word overlap, not semantic correctness, so even retained answers rarely reach F1 = 1;
EM is near zero for most groups and is not used for the position analysis.
- Greedy decoding is not bit-exact across GPUs (a few answers differ between machines).
- Environment: Colab T4, `float16`, Python 3.13, transformers [version], torch [version]
(the Colab log showed torch 2.11.0+cu130; please confirm both versions).

> 限制：單一資料集、單一模型、單一 `head_frac`；答案位置分析使用 token 位置，但有 87/150 為
> 近似的 fuzzy 定位、17 筆無法定位；結果為相關性而非因果；F1 為詞彙重疊而非語意正確性。

