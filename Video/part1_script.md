# Part 1 script — Slides 1–4 (member 1)

## Slide 1 — Reproducing LLMLingua

> Hi everyone. We are Group 38. This is our project: Reproducing LLMLingua — long-context prompt compression.

> 大家好，我們是第 38 組。這是我們的專題。題目是「重現 LLMLingua：長上下文 prompt 壓縮」。

## Slide 2 — Why compress prompts at all

> Why do we care about prompt compression? Today we give the model a long context: 
> one big prompt. That is expensive. It
> uses more GPU memory and it is slower.
> But the compressor is also a model, and it also needs time. So
> we ask three questions:
>
> - Does the compression hurt the accuracy?
> - Does LLMLingua beat simple truncation?
> - Does it really save end-to-end time?

> 我們為什麼在意 prompt 壓縮？現在我們給模型很長的上下文：
> 很大的 prompt。這很昂貴：佔用更多 GPU 記憶體，而且每次回答都更
> 慢。而且很多文字其實是重複的。但壓縮器本身也是一個模型，也需要時間。所以我們
> 問三個問題：
>
> - 壓縮會不會傷害準確度？
> - LLMLingua 能勝過簡單的截斷嗎？
> - 它真的能節省端到端的時間嗎？

## Slide 3 — Four settings, seven result rows

> We compare four settings:
>
> 1. First, uncompressed. The full context. This is our reference row.
> 2. Second, head-and-tail truncation. We keep the start and the end, and cut
>    the middle.
> 3. Third, LLMLingua. It deletes tokens that look unimportant, chunk by chunk.
> 4. Fourth, LLMLingua-Enhanced. It reads the whole document.

> 我們比較四種設定：
>
> 1. 第一，不壓縮。完整的上下文，這是我們的參考列。
> 2. 第二，頭尾截斷。保留開頭與結尾，切掉中間。
> 3. 第三，LLMLingua。它會逐塊刪除看起來不重要的 token。
> 4. 第四，LLMLingua-Enhanced。它會讀完整份文件。

## Slide 4 — One frozen harness behind every number

> All our results come from the same setup. Data is LongBench multi-field QA,
> all one-hundred-and-fifty samples. The target model is Llama three-point-two, greedy
> decoding, sixty-four new tokens. The compressors are Phi-two and Qwen two-point-five. We score with
> Exact Match and token F1, by comparing the samples one by one.

> 我們所有數字都來自同一套凍結的設定。資料是 LongBench 的多欄位問答，全部 150
> 題官方測試範例。目標模型是 Llama 3.2，貪婪解碼，輸出 64 個新 token。壓縮器
> 是 Phi-2 與 Qwen2.5。評分用 Exact Match 與 token F1，逐題配對比較。
