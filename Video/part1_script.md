# Part 1 script — Slides 1–4 (member 1)

## Slide 1 — Reproducing LLMLingua

> Hi everyone. This is our project, Reproducing LLMLingua: accuracy-efficiency
> trade-offs in long-context prompt compression. We are Group 38.

> 大家好，這是我們的專題：重現 LLMLingua —— 長上下文 prompt 壓縮下的準確度與
> 效率取捨。我們是第 38 組。

[Pause. Let the title and subtitle stay on screen.]

## Slide 2 — Why compress prompts at all

> Why do we care about prompt compression? Today we give the model a long
> context: many documents, many examples, one big prompt. That is expensive. It
> uses more GPU memory, and every answer is slower. And a lot of the text
> repeats itself.
>
> But there is a catch. The compressor is also a model, and it also needs time.
> So we ask three questions. Does the ratio hurt accuracy? Does LLMLingua beat
> simple truncation? And does it really save end-to-end time?

> 為什麼要關心 prompt 壓縮？現在我們給模型的上下文很長：很多文件、很多範例、
> 一個很大的 prompt。這很貴，佔更多 GPU 記憶體，每個回答也更慢。而且很多文字
> 是重複的。
>
> 但有一個陷阱：壓縮器本身也是模型，也需要時間。所以我們問三個問題：壓縮比
> 會不會損害準確度？LLMLingua 打得贏簡單的截斷嗎？它真的能節省端到端時間嗎？

## Slide 3 — Four settings, seven result rows

> We compare four settings. One, uncompressed. The full context. This is our
> reference row.
>
> Two, head-and-tail truncation. We keep the start and the end, and we cut the
> middle. It uses no model, and it never reads the question.
>
> Three, LLMLingua. It deletes tokens that look unimportant, chunk by chunk. It
> also never reads the question.
>
> Four, LLMLingua-Enhanced. It reads the whole document, and it does read the
> question.
>
> The last three run at 2x and 4x, so we get seven result rows.

> 我們比較四種設定。第一，不壓縮，用完整上下文，這是我們的基準列。
>
> 第二，頭尾截斷：保留開頭和結尾，切掉中間。它不用任何模型，也完全不看問題。
>
> 第三，LLMLingua：它會刪掉看起來不重要的 token，而且是逐塊處理。它同樣不看
> 問題。
>
> 第四，LLMLingua-Enhanced：它一次讀完整份文件，並且會看問題。
>
> 後三個方法各跑 2x 和 4x，所以總共有七個結果列。

## Slide 4 — One frozen harness behind every number

> All our numbers come from one frozen setup. Data is LongBench multi-field QA,
> all 150 official test examples. The target model is Llama 3.2 3B, greedy
> decoding, 64 new tokens. The compressors are Phi-2 for Part 3 and Qwen2.5 1.5B
> for Part 4. We score with Exact Match and token F1.
>
> And one rule: we never compare averages. We compare the same 150 samples, one
> by one, with 95 percent intervals.

> 我們所有數字都來自同一套凍結的設定。資料是 LongBench 的多欄位問答，全部 150
> 題官方測試集。目標模型是 Llama 3.2 3B，貪婪解碼，最多 64 個新 token。壓縮器
> 在 Part 3 是 Phi-2，在 Part 4 是 Qwen2.5 1.5B。評分用 Exact Match 和 token F1。
>
> 還有一個原則：我們從不比較平均值，而是逐筆比較同樣這 150 題，並給出 95% 信賴
> 區間。

[Hand over to Part 2.]
