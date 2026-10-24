# 三人分工方案

本項目有三個主要方法需要比較：uncompressed prompt、head-and-tail truncation、以及 LLMLingua。為確保三人可同時獨立工作、互不阻塞，每位成員負責一個完整方法由頭到尾的 pipeline，包括數據準備、方法實作、模型推理、指標計算。三人共用同一份固定樣本索引（fixed sample indices）同同一個 target model（Llama-3.2-3B-Instruct），確保結果可直接比較。接口統一用固定 JSON 格式：每條樣本輸出 `{id, question, docs, prompt_tokens, answer, em, f1, compression_latency, generation_latency, total_latency}`，三人各自產生一份，最後合併成同一張表。

## Member 1 — Uncompressed Baseline

Member 1 負責最完整的 baseline：不做任何壓縮，直接將全部檢索文件、問題、指令組成 prompt，送入 Llama-3.2-3B-Instruct 生成答案。工作包括：

- 下載並預處理 LongBench `multifieldqa_en`，固定 **150** 條樣本索引（官方 test split 全部樣本），存成共用 JSON `shared/samples.json`，供三人使用。
- 實作 full-context prompt template，確保三人用同一格式。
- 在 Colab T4 上跑 inference，使用 temperature zero、固定 max new tokens。
- 計算 Exact Match、token-level F1。
- 記錄原始 prompt token 數、generation latency、total latency，作為其他兩個方法的對照基準。
- 處理 OOM fallback：如 full context 超長，記錄實際 truncate 到模型上限的做法，保持透明。

Member 1 的輸出係整個項目的參考點，其他兩人直接用同一份樣本索引，不需等 Member 1 完成推理。

## Member 2 — Truncation Baseline

Member 2 負責 head-and-tail truncation：保留 prompt 頭尾各一部分，中間丟棄，令 token 數降到同 LLMLingua 相近的水平。工作包括：

- 重用 Member 1 的固定樣本索引同 prompt template。
- 實作 head-and-tail 策略，參數化保留比例，令實際 token 數對齊 2× 同 4× 壓縮目標。
- 跑 Llama-3.2-3B-Instruct inference，計 EM、F1。
- 記錄 retained token 數、achieved compression ratio、truncation latency（近乎零）、generation latency、total latency。
- 分析 truncation 在答案位於中間時的失敗案例，作為 position bias 的間接證據。

Member 2 只依賴共用樣本索引同 prompt template，不依賴 Member 1 或 3 的進度。

## Member 3 — LLMLingua

Member 3 負責 LLMLingua 壓縮方法，係技術含量最高的一組。工作包括：

- 重用共用樣本索引同 prompt template。
- 在 Colab 安裝 `llmlingua`，載入官方 compressor（如 `NousResearch/Llama-2-7b-hf` 4-bit，或 fallback 到 `gpt2`）。
- 跑 LLMLingua 2× 同 4× 壓縮，記錄 retained token 數同 achieved compression ratio。
- 採用分階段處理避免 OOM：先載入 compressor 做壓縮、卸載，再載入 Llama-3.2-3B-Instruct 做 generation。
- 計 EM、F1、compression latency、generation latency、total latency。
- 整理 accuracy–compression 曲線同成功／失敗的壓縮案例。

Member 3 的壓縮步驟獨立於 Member 1、2，三人可同時在 Colab 或本機跑，只需共用同一份樣本索引同 prompt template。

## 共用接口與同步

- **共用檔案**：`shared/samples.json`（固定索引）、`shared/prompt_template.py`（統一 prompt 格式）、`shared/metrics.py`（EM/F1 計算）、`shared/config.py`（模型與 token 上限）。
- **各自輸出**：`results_member1.json`、`results_member2.json`、`results_member3.json`，格式一致。
- **同步方式**：每週一次短會，對齊樣本索引、prompt 格式、tokenizer 版本、max new tokens。其餘時間各自獨立開發。
- **合併階段**：三人輸出合併成同一張表，比較三種方法在 accuracy、retained tokens、compression ratio、compression latency、generation latency、total latency 的差異，回答 RQ1–RQ3。

此分工令三人由第一日起即可並行工作，無需等待彼此完成，同時保證最終結果可在同一控制條件下直接比較。