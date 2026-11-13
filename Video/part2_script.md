# Part 2 script — Truncation baseline (member 2)

## Opening

> Hi everyone, I'm Kin Meng, and I'll talk about Part 2, the truncation baseline.

> 大家好，我是 Kin Meng，我負責講 Part 2，也就是截斷基準。

## Method — keep the start and the end

> The idea is very simple. We keep the start of the document, keep the end, and
> cut the middle. The question and the instructions are never touched. At 2x we
> keep half of the document, and at 4x we keep a quarter. The cutting step
> doesn't need any extra model, so it costs almost nothing

> 想法很簡單：保留文件的開頭、保留結尾，切掉中間。問題和指令永遠不會被動到。
> 2x 時我們保留文件的一半，4x 時保留四分之一。切這一步不需要任何額外模型，所以
> 幾乎不花成本。

## Results — accuracy and speed

> Now the results. Without compression, we get an F1 of 0.43. With 2x truncation,
> it's 0.41, so we lose very little. With 4x, it's 0.36. But look at the speed.
> On the same GPU, each question goes from 9.4 seconds to 5.3 seconds at 2x, and
> 3.2 seconds at 4x. That's 44 and 66 percent faster.

> 現在看結果。不壓縮時 F1 是 0.43；2x 截斷是 0.41，所以損失很小；4x 則是 0.36。
> 但看速度：在同一張 GPU 上，每題從 9.4 秒降到 2x 的 5.3 秒，以及 4x 的 3.2 秒，
> 也就是快了 44% 與 66%。

## Why 4x loses more — where the answer sits

> So why does 4x lose more? We checked where the answer sits in the document.
> When the answer is in the part we keep, F1 is around 0.47 to 0.49. When the
> answer is in the part we cut, it falls to around 0.2. At 2x, about 21 percent of
> answers get cut. At 4x, it's 37 percent. So most of the loss simply comes from
> cutting out the answer. The small lines show how uncertain each average is.
> They don't overlap, so the gap is real.

> 那為什麼 4x 損失更多？我們檢查了答案在文件中的位置。當答案落在我們保留的部分，
> F1 約 0.47 到 0.49；當答案落在被切掉的部分，F1 掉到約 0.2。2x 時約 21% 的答案
> 被切掉，4x 時是 37%。所以大部分損失就是因為把答案切掉了。圖上的小線段表示每個
> 平均值的不確定程度，它們沒有重疊，所以這個差距是真的。

## Closing

> This is just a pattern, not proof, but it shows a simple baseline is hard to
> beat. Thank you.

> 這只是一個模式，不是證明，但它說明一個簡單的基準其實很難打敗。謝謝。
