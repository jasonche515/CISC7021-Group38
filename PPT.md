# PPT + video 分工

## Canva 
https://canva.link/jg5zomq5v69zlje

- 以下按「PPT 三段內容 → 各自 screen record 配旁述 → 合併」分工，每人約 1/3（約 1 分 40 秒）：

**成員 1（基準與截斷）**
- 負責 PPT 段：問題背景、RQ1–RQ3、共用實驗設定（樣本索引、prompt 模板、EM/F1）、不壓縮基準、頭尾截斷 2x/4x 結果與 token 節省。
- 錄製：講動機與 baseline 表、accuracy–compression 圖左半。

**成員 2（LLMLingua 與切塊缺陷）**
- 負責 PPT 段：LLMLingua 兩階段流程、296/300 切塊問題、F1 大幅下降、質性成功/失敗案例。
- 錄製：講壓縮流程圖、Part 3 結果列與案例對照。

**成員 3（RQ3 延遲、結論）**
- 負責 PPT 段：LLMLingua-Enhanced（單次通過、問題感知、0 切塊）、+0.0444/+0.0587 回升但仍輸截斷、同環境延遲（截斷 −44%/−66%、LLMLingua 2x 慢 44%）、限制與結論。
- 錄製：講 Part 4 對照、延遲表與結論。

**合併流程**
1. 先定 PPT 模板與每段頁數（S1–S5 / S6–S8 / S9–S11，共 11 頁），統一術語與數字口徑（品質用 per-part、延遲用同機 rerun）。
2. 各自錄製約 1 分 30 秒–1 分 50 秒 MP4。
3. 用剪輯軟體串接、總長控制在 5 分鐘內。
4. 上傳公開網站、填共用表單。

---

# Canva AI 生成用：逐頁簡報內容

用法：Canva →「Docs」貼上下面「整份貼上版」全部文字 → 右上「轉換為簡報」；
或 Magic Design 貼上同一段，選 16:9、學術簡約模板。生成後只要微調配色與圖表即可。

**三個必須遵守的規則（也寫進 Canva prompt 裡）**
- 每頁最多 6 個 bullet，每個 bullet 不超過 12 個英文字。
- 所有數字**照抄不改**，不要四捨五入、不要改寫單位（Canva 很愛自動改數字）。
- 投影片只用英文；中文只出現在講稿，不要放上投影片。

## 全域設計指令（先貼這段，再貼逐頁內容）

```
Create an 11-slide 16:9 academic conference deck for a course project.
Minimal, clean layout: white background, thin accent rules, generous margins.
Headings in Inter Bold, body in Inter Regular, body text 18 pt or larger.
Palette: blue #1F6FB4, orange #D9772E, teal #1E8A78, purple #7A4FA3,
grey #8C8C8C, pale blue #D8E5F2, pale orange #F7E2D0, pale teal #D5EBE6.
No stock photos, no clip-art, no gradients, no drop shadows, no 3D icons.
Each slide has a small section label at top-left and the page number bottom-right.
Reproduce every number exactly as written in the outline; do not round or rephrase.
Keep all text in English.
```

## 整份貼上版（可直接丟給 Canva）

```
# Slide 1 - Title
Section: CISC7021 Applied Natural Language Processing
Title: Reproducing LLMLingua
Subtitle: Accuracy-Efficiency Trade-offs in Long-Context Prompt Compression
Meta: Group 38 | University of Macau | Course Project Final Report
Visual: thin horizontal rule under the title, one small blue square accent

# Slide 2 - Why compress prompts at all
Section: Background
Title: Long prompts are expensive, and mostly redundant
- Retrieved documents, examples and articles push thousands of tokens per call
- Longer prompt means more prefill, more memory, slower first token
- Context is repetitive, and models use long windows unevenly
- RQ1: does the ratio change answer accuracy?
- RQ2: does LLMLingua beat truncation at equal budget?
- RQ3: does compression cut end-to-end latency?
Visual: three short question chips (RQ1, RQ2, RQ3) across the lower third

# Slide 3 - What we compare
Section: Method
Title: Four settings, seven result rows
- Uncompressed: full context, the reference row
- Head-and-tail: drop one middle span, no model, question-blind
- LLMLingua: token-level deletion per 1,400-token chunk, question-blind
- LLMLingua-Enhanced: whole document, question-aware ranking
- Each compressed method run at nominal 2x and 4x
- 150 examples per setting, Identical prompt template and metrics
Visual: 4-column comparison strip; grey icon crosses for "question-blind", blue check for "question-aware"

# Slide 4 - Setup
Section: Method
Title: One frozen harness behind every number
- Data: LongBench multifieldqa_en, all 150 official test examples
- Target model: Llama-3.2-3B-Instruct, greedy, 64 new tokens, fp16
- Compressors: Phi-2 (2,048 positions) and Qwen2.5-1.5B (32,768 positions)
- Metrics: Exact Match and token F1, SQuAD normalisation
- One sample index, one prompt template, one metric module, one config
- Statistics: paired per-sample differences with 95% confidence intervals
Visual: six small labelled blocks in a row under the bullets

# Slide 5 - RQ1: accuracy falls with the ratio
Section: Results
Title: Monotone loss, but the slope differs 7x by method
- Truncation F1: 0.4296 -> 0.4065 (2x) -> 0.3620 (4x)
- LLMLingua F1: 0.4296 -> 0.2626 (2x) -> 0.2207 (4x)
- LLMLingua-Enhanced F1: 0.4296 -> 0.3070 (2x) -> 0.2794 (4x)
- Relative F1 loss: 5.4% / 15.7%, then 38.9% / 48.6%, then 28.5% / 35.0%
- Same samples, same target model, same token budgets
- Answer to RQ1: yes, and the size of the effect is a property of the method
Visual: line chart, x = achieved prompt ratio (1.0, 1.97, 3.82, 2.09, 3.51, 2.14, 4.13), y = token F1; blue circles for truncation, orange dashed squares for LLMLingua, teal dotted triangles for Enhanced, purple star at (1.00, 0.4296)

# Slide 6 - RQ2: truncation wins
Section: Results
Title: At the same token budget, LLMLingua loses 0.14 F1
- Truncation -> LLMLingua at 2x: -0.1440, 95% CI [-0.186, -0.102]
- Truncation -> LLMLingua at 4x: -0.1414, 95% CI [-0.183, -0.100]
- Both intervals exclude zero; the loss is not sampling noise
- Exact Match collapses from 14 hits to 1-2 hits out of 150
- F1 stays at 0.22-0.31: answer words survive, exact spans do not
- Answer to RQ2: no, in both variants and at both ratios
Visual: two horizontal error bars anchored at zero, both clearly left of zero, annotated with the deltas

# Slide 7 - Why it happens
Section: Analysis
Title: Perplexity is not question relevance
- A year is highly predictable in a paper, so it looks deletable, even when it is the answer
- Truncation keeps grammatical passages; token deletion leaves fragments a 3B model handles worse
- A document is retrieved because it holds the answer, so at 4x we delete evidence, not redundancy
- Case "7 March 2023": LLMLingua returns "7 March" or "not present"; truncation scores 1.000
- Case "The Wallace electorate": LLMLingua returns "Clutha-Southland", F1 0.15
- Genuine win: evidence at 65.1% of the document, LLMLingua 0.667 / 0.788, truncation 0.182
Visual: three-row case table, winner column in blue or orange; no images

# Slide 8 - The chunking defect
Section: Analysis
Title: The compressor could not see the document
- Phi-2 has 2,048 positions; the mean prompt is 6,967 tokens
- So documents were cut into 1,400-token chunks and compressed separately
- 296 of 300 rows chunked (98.7%), mean 6.28 chunks, maximum 13
- Chunking bypasses the global budget controller: every chunk gets the same rate
- Is chunking the cause of the 0.14 F1 gap? That needs a fourth setting
Visual: long document bar cut into six chunk blocks, all compressed to the same ratio; the 2,048-position limit marked as a hard ceiling

# Slide 9 - Part 4: fixing the defect
Section: Analysis
Title: De-chunking recovers a third to two fifths, not all
- Replace only the compressor: Qwen2.5-1.5B, 32,768 positions, whole document in one pass
- Question-aware ranking, sentence-level filter, 4-bit weights
- 0 of 300 rows chunked
- Gain over LLMLingua: +0.0444 at 2x [+0.013, +0.076], +0.0587 at 4x [+0.025, +0.093]
- That is 31% and 42% of the gap, not 100%
- Still 0.0995 and 0.0827 F1 below truncation, intervals excluding zero
Visual: gap bar from LLMLingua to truncation, one segment filled for the recovered part, the rest hatched

# Slide 10 - RQ3: latency
Section: Results
Title: Only truncation actually gets faster
- Measured in one rerun: one RTX 3060, one process, Parts 1-3 only
- Truncation: compression 0.02 s, total latency -43.6% at 2x, -65.7% at 4x
- LLMLingua: +43.9% at 2x and +14.1% at 4x
- At 2x, generation saves 3.37 s but compression costs 7.50 s, net +4.13 s
- Break-even needs compression to cost less than the generation time it saves
- A 2.7B compressor over a 7k-token prompt does not break even on one GPU
Visual: stacked bar chart, generation in pale blue, compression in orange, total label above each bar

# Slide 11 - Conclusion
Section: Conclusion
Title: A negative result with a diagnosed cause
- RQ1: accuracy falls monotonically; the slope is a property of the method
- RQ2: no; de-chunking recovers 31-42% of the deficit, not all of it
- RQ3: only truncation reduces end-to-end latency
- A frozen evaluation contract is worth more than a method
- Measure the end-to-end quantity you claim to improve, on one machine
- Every number in this deck traces to a committed result file
Visual: three large answer cards for RQ1-RQ3 above a single takeaway line
```

## 逐頁講稿與時間分配（不上投影片）

| 頁 | 內容 | 成員 | 秒數 | 口播重點（一句） |
|---|---|---|---|---|
| S1 | 標題 | 1 | 6 | 組別、題目、這是一個 reproduction + 診斷的研究 |
| S2 | 動機與 RQ | 1 | 26 | 長 prompt 貴且冗餘，但壓縮器本身也要跑，所以有三個問題 |
| S3 | 四方法 / 七行 | 1 | 22 | 關鍵差異是「有沒有看問題」和「壓縮單位」 |
| S4 | 共用設定 | 1 | 26 | 除了壓縮那一步，其他全部凍結，所以七行可以放同一張表 |
| S5 | RQ1 | 1 | 28 | 三個家族都單調下降，但斜率差 7 倍，方法比 budget 重要 |
| S6 | RQ2 | 2 | 30 | 同 budget 下 LLMLingua 輸 0.14，CI 不含 0；EM 幾乎歸零 |
| S7 | 為何失敗 | 2 | 32 | perplexity 不等於問題相關性；用三個案例說明 |
| S8 | 切塊缺陷 | 2 | 26 | Phi-2 只有 2048 位置，被迫切塊，global budget 被繞過 |
| S9 | Part 4 | 3 | 34 | 去切塊 + 問題感知，回升 31–42%，但仍輸截斷 |
| S10 | RQ3 | 3 | 32 | 只有截斷變快；壓縮 7.5 秒 > 生成省下的 3.4 秒 |
| S11 | 結論 | 3 | 26 | 三個答案 + 兩個 lesson；負面結果有診斷就是結果 |

合計 288 秒（4 分 48 秒），留約 10 秒轉場；S1–S5 約 108 秒、S6–S8 約 88 秒、S9–S11 約 92 秒。

## 數字對照（出圖／報數前先核對，全部來自已提交的 result JSON）

- 主表 F1：0.4296 / 0.4065 / 0.3620 / 0.2626 / 0.2207 / 0.3070 / 0.2794
- 主表 EM：0.0933 / 0.0733 / 0.0667 / 0.0067 / 0.0133 / 0.0000 / 0.0067
- 平均 prompt tokens：6,966.8 / 3,523.1 / 1,801.2 / 3,308.1 / 1,961.6 / 3,254.1 / 1,663.0
- 達成比例：1.000 / 1.969 / 3.820 / 2.094 / 3.508 / 2.144 / 4.133
- 同機延遲（秒）：9.43 / 5.32 / 3.23 / 13.57 / 10.76
- 配對差：−0.1440、−0.1414、+0.0444、+0.0587、−0.0995、−0.0827

**不要做的事**：不要把四個 part 的延遲數字放在同一句比較（四部機）；不要用 EM 決定任何比較；
不要說 LLMLingua-Enhanced 追平截斷；不要說 Part 4 的增益純粹來自去切塊（同時改了五樣）。