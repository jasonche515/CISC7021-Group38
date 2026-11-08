# Part 4 — LLMLingua-Enhanced (Member 4)

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

This folder holds the **LLMLingua-enhanced** experiment. It repeats the
LLMLingua run of Part 3 under exactly the same evaluation protocol and changes
only the compressor: a long-context model compresses every document in a single
pass, with the question visible to the ranker, so no sample is ever chunked.

> 這個資料夾是 **LLMLingua 改善版**實驗。它沿用 Part 3 的 LLMLingua 流程，評估方式完全
> 不變，只更換壓縮器：改用長上下文模型，每份文件一次過壓縮，而且排序時看得見問題，
> 因此不會有任何樣本被切塊。

## Why this part exists

Part 3 compressed each document with `microsoft/phi-2`, whose context window is
2,048 positions. The mean raw prompt is 6,967 tokens, so the pipeline had to cut
each document into fixed 1,400-token chunks before compression. In the Part 3
result file, **296 of 300 rows (98.7%) were chunked**, with a mean of 6.28 chunks
and a maximum of 13. Two distortions follow:

1. each chunk is ranked without seeing the question, so tokens that matter for
   this particular question are not preferred;
2. each chunk is compressed to its own budget, so boundaries are decided by text
   position rather than by information value.

Part 3 therefore scored F1 0.2626 (2x) and 0.2207 (4x), which is *worse* than the
0.3990 / 0.3633 of plain head-and-tail truncation in Part 2 — the opposite of
what the LLMLingua paper predicts. Part 4 tests the natural explanation: the
loss came from chunking, not from LLMLingua itself.

> Part 3 用 `microsoft/phi-2` 壓縮，但它的上下文只有 2,048 個位置，而原始 prompt 平均
> 6,967 個 token，所以必須先把文件切成固定的 1,400-token 區塊。Part 3 的結果檔中，
> **300 筆有 296 筆（98.7%）被切塊**，平均 6.28 塊、最多 13 塊。這帶來兩個扭曲：
> 每個區塊排序時看不到問題；每個區塊各自壓到自己的預算，切點由文字位置而非資訊價值決定。
> 因此 Part 3 的 F1 只有 0.2626（2x）與 0.2207（4x），反而比 Part 2 的
> head-and-tail 截斷（0.3990 / 0.3633）更差，與 LLMLingua 論文的預期相反。
> Part 4 就是驗證「損失來自切塊，而不是 LLMLingua 本身」這個解釋。

## What changed relative to Part 3

| Item | Part 3 | Part 4 |
| --- | --- | --- |
| Compressor | `microsoft/phi-2` (2,048 positions) | `Qwen/Qwen2.5-1.5B-Instruct` (32,768 positions) |
| Chunking | 1,400-token chunks, 98.7% of rows chunked | single pass, `chunked_count = 0` |
| Question in ranking | not passed (`question=""`) | passed, `condition_in_question="after_condition"` |
| Rank method | `"llmlingua"` | `"longllmlingua"` |
| Sentence filter | off | `use_sentence_level_filter=True` |
| Samples / prompt / target model / metrics / ratios | — | unchanged |

> | 項目 | Part 3 | Part 4 |
> | --- | --- | --- |
> | 壓縮器 | `microsoft/phi-2`（2,048 位置） | `Qwen/Qwen2.5-1.5B-Instruct`（32,768 位置） |
> | 切塊 | 1,400-token 區塊，98.7% 樣本被切 | 一次過壓縮，`chunked_count = 0` |
> | 排序是否看問題 | 沒有（`question=""`） | 有，`condition_in_question="after_condition"` |
> | 排序方法 | `"llmlingua"` | `"longllmlingua"` |
> | 句級過濾 | 關閉 | `use_sentence_level_filter=True` |
> | 樣本／prompt／目標模型／指標／壓縮率 | — | 完全不變 |

## How the compressor is configured

`compress_prompt` is called once per document with:

- `rate = 1 / target_ratio` — 0.5 for 2x, 0.25 for 4x;
- `condition_in_question="after_condition"` — the question is prepended as a
  conditioning prefix and its perplexity contribution is removed afterwards, so
  the returned prompt still starts with the original instruction;
- `rank_method="longllmlingua"` — re-ranking plus fine-grained token selection
  for long inputs (`llmlingua` asserts that this rank method receives a
  question);
- `use_sentence_level_filter=True` — sentences are pre-filtered to 1.4x the
  budget, then token-level compression trims to the exact target;
- `concate_question=False` — the original prompt structure is preserved.

`--no-question-aware` switches `condition_in_question` to `"none"` and is only
meant for an ablation; the question must still be supplied because
`longllmlingua` requires it.

> `compress_prompt` 每份文件只呼叫一次，參數如下：
> `rate = 1 / 目標壓縮率`（2x → 0.5，4x → 0.25）；
> `condition_in_question="after_condition"`（把問題當作前置條件，之後再扣掉它的困惑度貢獻，
> 回傳的 prompt 仍以原本的指令開頭）；`rank_method="longllmlingua"`（長文本重排序加細粒度
> 選 token，此方法必須提供問題）；`use_sentence_level_filter=True`（先按句子篩到預算的
> 1.4 倍，再於 token 層收窄到目標）；`concate_question=False`（保留原本 prompt 結構）。
> `--no-question-aware` 會把 `condition_in_question` 設為 `"none"`，只供消融實驗使用，
> 問題本身仍然必須提供。

## Comparability with Parts 1–3

The following are deliberately identical to Part 1–3 so that the numbers can be
placed in the same table:

- samples: `shared/samples.json`, the fixed 150 LongBench `multifieldqa_en`
  records;
- prompt: `shared/prompt_template.py`, the same template and document order;
- target model: `unsloth/Llama-3.2-3B-Instruct` loaded in `float16`;
- decoding: greedy, `max_new_tokens = 64`;
- metrics: `shared/metrics.py` Strict EM and token-level F1;
- ratios: 2x and 4x (`target_compression_ratio` 2 / 4);
- token accounting: prompt lengths are measured with the *target* tokenizer so
  `prompt_tokens` is comparable with the other parts.

> 以下各項刻意與 Part 1–3 完全相同，數字才能放進同一張表：樣本用 `shared/samples.json`
> 固定的 150 筆 LongBench `multifieldqa_en`；prompt 用 `shared/prompt_template.py` 相同模板
> 與文件順序；目標模型是 `unsloth/Llama-3.2-3B-Instruct`，以 `float16` 載入；解碼採貪心、
> `max_new_tokens = 64`；指標用 `shared/metrics.py` 的 Strict EM 與 token-level F1；
> 壓縮率為 2x 與 4x；token 長度一律用目標模型的 tokenizer 量度，因此 `prompt_tokens`
> 與其他部分可直接比較。

## Files

| File | Purpose |
| --- | --- |
| `run_llmlingua_enhanced.py` | both stages: `compress` and `evaluate` |
| `make_table.py` | standalone Part 1–4 comparison table and paired F1 contrasts |
| `requirements.txt` | dependencies for both stages |
| `README.md` | this document |
| `results_member4_compressed.jsonl` | written by `compress`, one row per (sample, ratio) |
| `results_member4_compressed.json` | summary of the compression stage |
| `results_member4.jsonl` | written by `evaluate`, checkpoint after every sample |
| `results_member4.json` | final per-ratio summary and per-sample rows |
| `results_table.md` / `.csv` | written by `make_table.py` |

> `run_llmlingua_enhanced.py` 包含兩個階段（`compress` 與 `evaluate`）；
> `make_table.py` 產生 Part 1–4 的比較總表與配對 F1 差異；`requirements.txt` 為依賴清單；
> `results_member4_compressed.*` 是壓縮階段的中繼檔；`results_member4.jsonl` 與
> `results_member4.json` 是最終答案與分數。中繼檔可安全刪除，重跑 `compress` 會重新產生。

## Environment

```bash
python -m pip install -r part4_llmlingua_enhanced/requirements.txt
```

llmlingua 0.2.2 is from the Transformers 4.x era: it stores the KV cache as a
list of `[key, value]` pairs and slices it during token-level compression.
Modern Transformers returns a `DynamicCache` object instead, which is not
subscriptable. The script installs a small in-process shim
(`install_transformers_cache_patch`) that converts the cache in both directions,
so no Transformers downgrade is required and both stages can run in one
environment.

On Windows the script retries checkpoint loading with `disable_mmap=True`. A
memory-mapped 3 GB shard can fail with
`OSError: [WinError 1455] The paging file is too small`; the retry reads the
shard into RAM instead, which only needs commit charge rather than a working
memory map. The mmap path is tried first because `safetensors.torch.load(bytes)`
can raise `pyo3_runtime.PanicException` on some safetensors/torch combinations,
so the fallback is the exception, not the default.

The compressor needs a Hugging Face download of about 3.1 GB on first run.

> 安裝方式為 `python -m pip install -r part4_llmlingua_enhanced/requirements.txt`。
> llmlingua 0.2.2 屬 Transformers 4.x 年代，它把 KV cache 當成 `[key, value]` 串列來取值，
> 新版 Transformers 則回傳不可下標的 `DynamicCache`。腳本內建
> `install_transformers_cache_patch` 做雙向轉換，因此不必降級 Transformers，兩個階段可共用
> 同一個環境。Windows 上以記憶體映射載入權重失敗時（pagefile 偏小時會出現 `WinError 1455`）
> 會自動改用 `disable_mmap=True` 重試，把分片讀進記憶體；預設仍先走映射，因為部分
> safetensors/torch 版本組合在 `safetensors.torch.load(bytes)` 會丟出
> `pyo3_runtime.PanicException`。壓縮器首次執行需下載約 3.1 GB 的權重。

### Low-memory hosts

`--load-in-4bit` loads the compressor in NF4 instead of float16, which needs
about a quarter of the weight memory (roughly 1.2 GB instead of 4.5 GB for
`Qwen2.5-1.5B-Instruct`). It requires `bitsandbytes` and CUDA.

Before either stage loads a model, the script prints the host RAM and commit
headroom and aborts with a clear message when it is below what the checkpoint
needs (4 GiB for a 4-bit compressor, 6 GiB for float16, 8 GiB for the target
model). Runaway paging while safetensors maps a multi-GB shard otherwise
freezes the whole desktop instead of raising an error. `--skip-memory-check`
bypasses the guard.

> 記憶體吃緊的機器可加 `--load-in-4bit`，以 NF4 載入壓縮器，權重記憶體約為 float16 的四分之一
> （`Qwen2.5-1.5B-Instruct` 約 1.2 GB 而非 4.5 GB），需另裝 `bitsandbytes` 且需 CUDA。
> 兩個階段在載入模型前都會先印出可用 RAM 與 commit 空間，不足時直接中止並提示
> （4-bit 壓縮器需 4 GiB、float16 需 6 GiB、目標模型需 8 GiB）；否則在記憶體不足時
> 邊映射邊置換會讓整個桌面卡死。要略過檢查可用 `--skip-memory-check`。

## Running the experiment

Both stages resume by default: each finished (sample, ratio) pair is appended to
the JSONL checkpoint, so an interrupted run continues where it stopped. Use
`--no-resume` to start over.

Smoke test first — three samples, one ratio:

```bash
python part4_llmlingua_enhanced/run_llmlingua_enhanced.py compress --limit 3 --ratios 2
```

If the machine has little free commit charge, add `--load-in-4bit`:

```bash
python part4_llmlingua_enhanced/run_llmlingua_enhanced.py compress --limit 3 --ratios 2 --load-in-4bit
```

Full compression stage (150 samples x 2 ratios):

```bash
python part4_llmlingua_enhanced/run_llmlingua_enhanced.py compress
```

Evaluation stage, after the compressor process has exited:

```bash
python part4_llmlingua_enhanced/run_llmlingua_enhanced.py evaluate
```

Useful flags:

- `--compressor-model` — swap the compressor (default `Qwen/Qwen2.5-1.5B-Instruct`);
- `--compressor-dtype {float16,bfloat16,float32}` — default `float16`;
- `--load-in-4bit` — load the compressor in NF4 (needs `bitsandbytes` + CUDA);
- `--ratios 2 4` — restrict the ratios;
- `--sample-indices 17` — run a single source sample;
- `--iterative-size` — context window used for token-level refinement;
- `--device {auto,cpu,cuda,mps}` — default `auto`;
- `--skip-memory-check` — load anyway when commit headroom looks too small.

> 兩個階段預設都會續跑：每完成一組（樣本, 壓縮率）就寫入 JSONL，行程中斷後可接續，
> 要重新開始請加 `--no-resume`。先做小規模測試：
> `compress --limit 3 --ratios 2`；正式壓縮用 `compress`；壓縮行程結束後再跑 `evaluate`，
> 確保壓縮器與目標模型不會同時佔用 GPU。常用旗標包括 `--compressor-model`、
> `--compressor-dtype`、`--load-in-4bit`（NF4 載入，需 `bitsandbytes` 與 CUDA）、
> `--ratios`、`--sample-indices`、`--iterative-size`、`--device` 與 `--skip-memory-check`。

### Comparison table

`make_table.py` builds the Part 1–4 table from the JSON artifacts of every part:

```bash
python part4_llmlingua_enhanced/make_table.py
python part4_llmlingua_enhanced/make_table.py --rerun-dir results_same_machine
```

It reads only result files and imports no Part 1–3 module, so a missing part is
skipped with a warning and the script already works before
`results_member4.json` exists. Output goes to `results_table.md` and
`results_table.csv` in this folder; `--out` changes the destination. The table
carries the Chunked count column that Part 3 and Part 4 are compared on, followed
by paired F1 contrasts with 95% confidence intervals.

> `make_table.py` 由各部分的 JSON 結果檔產生 Part 1–4 總表：不加參數時讀各 part
> 資料夾，加 `--rerun-dir results_same_machine` 時讀同環境重跑的攤平檔案。它只讀結果檔，
> 不 import Part 1–3 任何模組，因此缺少某一部分時只印出警告並跳過，在
> `results_member4.json` 尚未產生前也能執行。輸出為本資料夾的 `results_table.md` 與
> `results_table.csv`，可用 `--out` 指定其他位置；表中包含用於比較 Part 3 與 Part 4 的
> Chunked count 欄，以及配對 F1 差異與 95% 信賴區間。

## Output files and schema

`results_member4_compressed.jsonl` — one JSON object per line with `id`,
`target_compression_ratio`, `compressed_prompt`, `num_compression_chunks` (always
1), `chunked` (always `false`), `compressor_input_tokens`,
`compressor_max_position_embeddings`, `exceeds_compressor_context`,
`condition_on_question`, `rank_method`, `compressor_dtype`,
`compressor_load_in_4bit`, plus the Part 1–3
compatibility fields `original_prompt_tokens`, `prompt_tokens`,
`compression_ratio`, `retained_fraction`, `compression_latency`.

`results_member4.json` — `stage`, `method`, `dataset`, `model`, `device`,
`dtype`, `max_new_tokens`, `started_at`, `finished_at`, `num_results`, plus:

- `summary["2x"]` / `summary["4x"]`: `num_samples`, `mean_em`, `mean_f1`,
  `mean_original_prompt_tokens`, `mean_prompt_tokens`,
  `mean_achieved_compression_ratio`, `mean_compression_latency`,
  `mean_generation_latency`, `mean_total_latency`, `chunked_count`,
  `mean_num_compression_chunks`, `max_num_compression_chunks`,
  `condition_on_question`, `rank_method`;
- `chunked_count`: top-level total, expected to be 0;
- `results`: per-row `id`, `target_compression_ratio`, `output`, `answers`,
  `em`, `f1`, the latency fields and the same chunking metadata.

`mean_prompt_tokens` is measured with the target tokenizer, so it can be placed
next to Part 1–3 rows in the combined table.

> `results_member4_compressed.jsonl` 每行一筆，記錄壓縮後 prompt、`num_compression_chunks`
> （固定為 1）、`chunked`（固定為 `false`）、壓縮器輸入 token 數與其上下文上限、是否超出上限、
> 以及與前三個部分相容的 token 與延遲欄位。`results_member4.json` 除了一般中繼資料，
> 另有 `summary["2x"]` / `summary["4x"]`（含 `mean_f1`、`mean_em`、延遲、
> `chunked_count` 等）與 `results` 逐筆結果；`chunked_count` 應為 0，正是這一版要證明的重點。
> `mean_prompt_tokens` 以目標模型 tokenizer 量度，可直接與 Part 1–3 並列。

## Expected result

The hypothesis is that removing chunking restores the ordering predicted by the
LLMLingua paper. Target values at 150 samples:

| Setting | Part 2 head-and-tail F1 | Part 3 LLMLingua F1 | Part 4 target F1 |
| --- | --- | --- | --- |
| 2x | 0.3990 | 0.2626 | ≈ 0.415 |
| 4x | 0.3633 | 0.2207 | ≈ 0.380 |

(Part 2 / Part 3 values above are from the same-environment rerun in
`results_same_machine/`.)

These are targets, not results. Until `results_member4.json` exists this folder
makes no claim about the outcome; if the measured F1 stays below the Part 2
numbers, the chunking explanation is falsified and the remaining suspects are
the sentence-level filter and the compressor's own ranking quality.

> 假設是：取消切塊之後，結果會回到 LLMLingua 論文預期的排序。150 筆樣本的目標值為
> 2x ≈ 0.415、4x ≈ 0.380（對照 Part 2 的 0.3990 / 0.3633 與 Part 3 的 0.2626 / 0.2207）。
> 這些是**目標**而非結果：在 `results_member4.json` 產生之前，本資料夾不對結論作任何宣稱。
> 若實測 F1 仍低於 Part 2，就代表切塊解釋被否證，剩下的疑點是句級過濾與壓縮器本身的排序品質。

## Cost

Approximate local cost on an RTX 3060 12 GB, 150 samples x 2 ratios:

- download: about 3.1 GB for the compressor weights;
- compression: dominated by the per-sentence perplexity pass; expect roughly
  20-40 s per (sample, ratio), i.e. 2-4 hours for the full stage;
- evaluation: about 3 s per row with the 3B target model, i.e. 15-20 minutes.

The compressor and target model are never resident at the same time, so 12 GB of
VRAM is enough for both stages. Compression runs comfortably in 8 GB.

> 在 RTX 3060 12 GB 上，150 筆 × 2 個壓縮率的大約成本：壓縮器權重下載約 3.1 GB；
> 壓縮階段主要受逐句困惑度計算限制，每組（樣本, 壓縮率）約 20-40 秒，全階段約 2-4 小時；
> 評估階段每筆約 3 秒，合計 15-20 分鐘。壓縮器與目標模型不同時駐留，12 GB VRAM 足夠，
> 壓縮階段 8 GB 已可運行。

## Limitations

- The comparison isolates one variable (the compressor). Part 3 and Part 4 use
  different compressor families, so a difference in F1 cannot be attributed to
  chunking alone; the ablation flag `--no-question-aware` narrows this down but
  does not remove it.
- `longllmlingua` with the sentence filter runs one forward pass per sentence,
  so compression latency is higher than Part 3 by design. Latency is reported
  for transparency, not as a claim of efficiency.
- 4x compression leaves roughly 1,740 target tokens out of 6,967; answer quality
  on the hardest multi-hop samples may still be limited by the target model, as
  in Parts 1–3.
- Numbers are only comparable with the Part 1–3 rows produced in the same
  environment; see `results_same_machine/` for the latency baseline.

> 本實驗只隔離一個變因（壓縮器）。Part 3 與 Part 4 使用不同家族的壓縮器，因此 F1 差異
> 不能完全歸因於切塊；`--no-question-aware` 消融可收窄範圍，但無法完全排除。
> `longllmlingua` 搭配句級過濾會逐句做一次前向傳播，壓縮延遲本來就比 Part 3 高，
> 延遲只用於透明揭露，並非效率主張。4x 壓縮後約餘 1,740 個目標模型 token（原始 6,967），
> 最難的多跳樣本仍受目標模型能力限制。數字只可與同環境產生的 Part 1–3 結果比較，
> 延遲基準見 `results_same_machine/`。

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `OSError: [WinError 1455]` while loading weights | pagefile too small for a memory-mapped shard | the script retries with `disable_mmap=True`; if it still fails, free system memory or enlarge the pagefile |
| `MemoryError` right after the retry | the shard cannot be committed to RAM either | free memory, or move the run to a host with more commit charge (see Colab below) |
| `torch.OutOfMemoryError` during warm-up | the GPU is shared with other programs | close them, lower `--compressor-dtype bfloat16`, or use `--load-in-4bit` |
| `TypeError: 'DynamicCache' object is not subscriptable` | cache shim not installed | make sure `compress` is run through this script, not a copied snippet |
| `LookupError: punkt` / `punkt_tab` | NLTK sentence data missing | the script downloads it; offline machines need `python -m nltk.downloader punkt_tab` |
| `AssertionError` on `rank_method` | `longllmlingua` used without a question | keep the question; do not pass `--no-question-aware` in the main run |

> 疑難排解：載入權重時出現 `WinError 1455` 表示 pagefile 不足，腳本會自動以
> `disable_mmap=True` 重試；若重試後出現 `MemoryError`，代表連把分片放進記憶體都不夠，
> 請釋放記憶體或改到 commit 空間較大的機器（見下方 Colab 說明）；出現 `OutOfMemoryError`
> 表示 GPU 被其他程式佔用，可改用 `--compressor-dtype bfloat16` 或 `--load-in-4bit`；
> 出現 `'DynamicCache' object is not subscriptable` 表示未經本腳本執行；缺少 NLTK 句子資料時
> 腳本會自動下載，離線環境需先執行 `python -m nltk.downloader punkt_tab`。

### Running on Google Colab

If the local host cannot commit the checkpoint (the memory guard aborts, or the
mmap retry ends in `MemoryError`), run both stages on a Colab GPU runtime. Nothing
in the script is platform specific: install `requirements.txt`, point
`--samples`/`--jsonl`/`--output` at a Drive folder so `--resume` survives a
disconnect, and run `compress` followed by `evaluate` in two separate cells so
the compressor is released before the target model loads. Copy
`results_member4.json` back into this folder afterwards; `make_table.py` in this
folder then folds it into the Part 1–4 table.

> 若本機無法配置足夠的 commit 空間（記憶體檢查中止，或映射重試後出現 `MemoryError`），
> 請改在 Colab GPU 執行這兩個階段。腳本本身不依賴平台：安裝 `requirements.txt`，
> 把 `--samples`/`--jsonl`/`--output` 指向 Drive 資料夾讓 `--resume` 能跨斷線續跑，
> 並在兩個不同 cell 分別執行 `compress` 與 `evaluate`，確保目標模型載入前壓縮器已釋放。
> 完成後把 `results_member4.json` 複製回本資料夾，本資料夾的 `make_table.py`
> 就會把它納入 Part 1–4 總表。
