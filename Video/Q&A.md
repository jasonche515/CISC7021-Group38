# Q&A preparation

## Q1 — Why did LLMLingua lose to simple truncation?

> "We have hypotheses, but we did not test them directly. LLMLingua removes words
> one by one, so sentences become broken. A 3B model has a hard time
> understanding broken text. Truncation keeps whole passages, so what it keeps is
> clean. Also, most answers in this dataset are near the start, which helps
> truncation."

> 「我們有一些假設，但沒有直接驗證。LLMLingua 是逐詞刪除，句子會變得破碎，3B
> 模型很難理解破碎的文字。截斷保留完整段落，留下的內容是乾淨的。另外，這個資料集
> 多數答案都靠近開頭，這對截斷有利。」

> 中文提示：這是假設，不是已證明的原因。

## Q2 — Part 4 was meant to beat truncation. Why did it fail?

> "Part 4 fixed the chunking problem and made the compressor question-aware. F1
> went up by 0.044 and 0.059, but it is still about 0.08 to 0.10 below truncation.
> We changed five things at once, so we cannot say which one helped. Also, the
> compressor was slow, 15 to 17 seconds per question, which hurts speed."

> 「Part 4 修好了切塊問題，並讓壓縮器看問題。F1 上升了 0.044 與 0.059，但仍比
> 截斷低約 0.08 到 0.10。我們一次改了五樣東西，所以無法斷定是哪一項有用。另外，
> 壓縮器很慢，每題 15 到 17 秒，拖累了速度。」

## Q3 — How do you know the loss at 4x comes from the answer being cut?

> "We located each gold answer in the original document. When the answer is kept,
> F1 is about 0.47 to 0.49. When it is cut, F1 is about 0.20. The share of cut
> answers goes from 21% to 37% at 4x. But this is only a pattern. Questions with
> early answers might also be easier, and 87 of 150 answer locations are
> approximate."

> 「我們在原始文件中定位每一個標準答案。答案被保留時 F1 約 0.47 到 0.49，被切掉時
> 約 0.20；被切掉的比例從 21% 上升到 4x 的 37%。但這只是模式：答案靠前的題目本身
> 可能也比較容易，而且 150 題中有 87 題的答案位置只是近似值。」

## Q4 — F1 is only 0.43 without compression. Is the model just weak?

> "F1 measures word overlap, not meaning. Gold answers are often full sentences
> written by people, and the model may answer correctly with different words. A 3B
> model also limits the score. Other models on this task get similar numbers, for
> example 36.8 for Llama2-7B-chat in the LongBench paper. So we focus on the
> change relative to the baseline, not the absolute value."

> 「F1 衡量的是詞語重疊，不是語意。標準答案常常是人寫的完整句子，模型可能用不同
> 詞語答對；3B 模型本身也限制了分數。其他模型在這個任務上拿到相近的數字，例如
> LongBench 論文中 Llama2-7B-chat 為 36.8。所以我們看的是相對基準的變化，而非
> 絕對數值。」

> 中文提示：這題引用的 36.8 來自我先前查到的 LongBench 結果，請在報告中確認出處
> 後再用。

## Q5 — Is the latency result reliable? Why do the numbers differ between tables?

> "Our four parts ran on four different machines, so we only compare latency from
> one rerun on a single RTX 3060: 9.4 seconds uncompressed, 5.3 for 2x, 3.2 for
> 4x. The main table shows per-part latencies on different machines, so they
> should not be compared with each other. Part 4 has no same-machine measurement,
> so we do not make a speed ratio for it."

> 「我們四個部分跑在四台不同的機器上，所以延遲只比較同一台 RTX 3060 上的重跑結果：
> 不壓縮 9.4 秒、2x 為 5.3 秒、4x 為 3.2 秒。主表列的是各部分在不同機器上的延遲，
> 彼此不應比較。Part 4 沒有同機測量，所以我們不為它計算加速比。」

## 備用題（如果還有時間準備）

### Is the 2x loss real?

> "In our main run, no. The confidence interval includes zero. In the same-machine
> rerun it was marginal. We call it a small loss at the edge of significance."

> 「在主實驗中不是：信賴區間包含零。在同機重跑中則是邊緣顯著。我們稱它為一個在
> 顯著性邊緣上的小幅損失。」

### Why only one dataset and one model?

> "Time and compute limits. We say clearly that the ranking is shown only for this
> setup."

> 「時間與算力限制。我們明確說明這個排序只適用於此設定。」

### Did you use AI tools?

> 報告有寫 Use of Generative AI 一節，回答時與該節一致：AI 用於整理文獻、潤稿、
> 格式和除錯，沒有用來生成實驗結果。
