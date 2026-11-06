# Requirement Checklist — CISC7021 Group 38

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

Verification baseline: experiment outputs verified through commit `f321a6c`,
checked against [project.md](./project.md) and [plan.md](./plan.md) on
2026-11-06. All numbers in this file were recomputed from the result JSON files,
not copied from the READMEs.

> 核對基準：實驗輸出已核對至 commit `f321a6c`，並於 2026-11-06 對照
> [project.md](./project.md) 與 [plan.md](./plan.md)。本檔所有數字均由結果 JSON
> 重新計算，非抄自 README。

## 1. Status at a glance

| Requirement | Weight | Due | State |
| --- | ---: | --- | --- |
| Task 1 — Review report | 15% | 10 Oct (passed) | ✅ Done |
| Task 2 — Final report (ACL two-column) | 30% | 17 Nov 23:55 | ⚠️ Member 3 contribution drafted; group report not assembled |
| Task 3 — Pre-recorded presentation | 30% (with Task 4) | 17 Nov | ⚠️ 1 of 4 items ready |
| Task 4 — In-class presentation | | 17 / 24 Nov | ⬜ Not started |
| System implementation (the three methods) | 20% | 17 Nov | ✅ Done |

### 1.1 Experiment and programming audit (2026-11-06)

| Technical item | Evidence | State |
| --- | --- | --- |
| Shared samples, prompt template, and EM/F1 metrics | [shared/](./shared) | ✅ Complete |
| Uncompressed pipeline | [part1_uncompressed/](./part1_uncompressed) — 150 results | ✅ Complete |
| Head-tail 2x and 4x pipelines | [part2_truncation/](./part2_truncation) — 150 results per ratio | ✅ Complete |
| LLMLingua 2x and 4x pipeline | [part3_llmlingua/](./part3_llmlingua) — 300 results | ✅ Complete |
| Accuracy–compression plotting code and figure | [plot script](./part3_llmlingua/plot_accuracy_compression.py) · [figure](./figures/accuracy_compression_tradeoff.pdf) | ✅ Complete |
| Reproducible qualitative-case analysis | [script](./part3_llmlingua/build_qualitative_cases.py) · [cases](./part3_llmlingua/qualitative_cases.md) | ✅ Complete |
| One generated table covering all five settings | [make_table.py](./part2_truncation/make_table.py) | ⚠️ Incomplete — currently only three rows |
| Systematic answer-position analysis | Part 2 plan | ⚠️ Partial — one qualitative example exists, but no systematic implementation |
| Cross-method latency comparison | Result JSONs from three machines | ⚠️ Unresolved — absolute times are not directly comparable |
| Part 2 result documentation | [part2 README](./part2_truncation/README.md) | ⬜ Six placeholders remain |

> 三個方法的主程式與完整結果均已完成，Member 3 的圖表和可重現案例分析也已完成。
> 剩餘編程／實驗整合工作是：五列總表、Part 2 位置分析、Part 2 README 清理，
> 以及決定不同硬體下 latency 應如何報告。

**Deadline trap:** "Implementation & All Materials" is listed as *17 November
2026, 12:00 AM*, which is midnight at the **start** of 17 Nov — effectively the
end of 16 Nov. That is roughly 24 hours earlier than the report deadline.

> 截止時間陷阱：Implementation & All Materials 寫 11 月 17 日 12:00 AM，即 17 日
> 凌晨零時，實際等於 16 日結束前，比報告截止早約 24 小時。

## 2. Phase 1 — Review report (Task 1, 15%)

| Required content | Where | State |
| --- | --- | --- |
| List of papers read, with references | [acl_latex.tex](./acl_latex.tex) §Papers Reviewed | ✅ |
| Main methodologies previously used | §Existing Methodologies | ✅ |
| Experimental results of reviewed works | §Experimental Results in Previous Work | ✅ |
| Project idea and preliminary strategy | §Research Gap, §Proposed Project | ✅ |
| Tentative schedule | §Tentative Schedule | ✅ |
| Two-column ACL format, submitted as PDF | [CISC7021_course_project_review_report.pdf](./CISC7021_course_project_review_report.pdf) | ✅ |

> 第一階段回顧報告的五項內容全部齊備，且已有 ACL 兩欄格式 PDF，此項已完成。

## 3. Phase 2 — Final report (Task 2, 30%)

`project.md` requires at least three sections. The group report has not been
assembled, but a Member 3 methods/results contribution has been drafted.

| Required section | Content required | State |
| --- | --- | --- |
| Introduction | Motivation, achievements, brief literature review, conclusions drawn | ⬜ |
| Detailed Description | Design, implementation, testing, evaluation, diagrams / flowcharts | ⬜ |
| Conclusion | Lessons learned, problems and difficulties, future improvements | ⬜ |

Supporting evidence that already exists for the main comparison:

| Evidence | File | State |
| --- | --- | --- |
| Uncompressed baseline, 150/150 | [results_member1.json](./part1_uncompressed/results_member1.json) | ✅ |
| Head-tail 2x and 4x, 150/150 each | [2x](./part2_truncation/results_member2_2x.json) · [4x](./part2_truncation/results_member2_4x.json) | ✅ |
| LLMLingua 2x and 4x, 150/150 each (300 rows) | [results_member3.json](./part3_llmlingua/results_member3.json) | ✅ |
| Shared sample index, prompt template, metrics | [shared/](./shared) | ✅ |
| Combined Markdown table | [results_table.md](./part2_truncation/results_table.md) | ⚠️ Parts 1–2 only |
| Accuracy–compression figure | [PNG](./figures/accuracy_compression_tradeoff.png) · [PDF](./figures/accuracy_compression_tradeoff.pdf) | ✅ |
| Reproducible qualitative examples | [Markdown](./part3_llmlingua/qualitative_cases.md) · [CSV](./part3_llmlingua/qualitative_cases.csv) | ✅ |
| Member 3 report contribution | [final_report_contribution.md](./part3_llmlingua/final_report_contribution.md) | ⚠️ Draft; not yet assembled into the group report |

> 小組總報告尚未組裝，但 Member 3 的方法與結果文字已有草稿。實驗證據、圖表與
> 質性案例均已齊；合併表格目前仍只涵蓋 Part 1–2。

Blocking gaps for the report (details in §6):

| # | Gap | Blocks which section |
| --- | --- | --- |
| 1 | Combined 5-row table missing Part 3 | Detailed Description (results table) |
| 2 | Standard deviations and paired CIs are computed in this checklist but not integrated into the generated table/report | Detailed Description |
| 3 | Systematic answer-position failure analysis not implemented; only one reproducible qualitative example exists | Planned contribution for RQ2 / position bias |
| 4 | Cross-machine latency framing is unresolved | RQ3 and Detailed Description |

## 4. Phase 2 — Pre-recorded presentation (Task 3, part of 30%)

| Required item | State |
| --- | --- |
| Slides file, 5 minutes, all members participate | ⬜ Missing |
| Source code zip (optional) | ⚠️ Code ready in repo, zip not built |
| Final results | ✅ Four result JSONs; ⚠️ five-row combined table pending |
| Presentation video uploaded to a public site + shared form | ⬜ Missing |

> 投影片、影片與共用表單均未做；原始碼已在 repo 內，只需打包成 zip；結果檔已齊。

## 5. Phase 2 — In-class presentation (Task 4)

| Required item | State |
| --- | --- |
| PowerPoint submitted by 14:00, 17 Nov | ⬜ Missing |
| 4 min talk + 1 min Q&A by one representative | ⬜ Not prepared |
| Mandatory attendance (deduction if absent) | ⬜ Pending |

> 課堂報告的 PPT 需於 11 月 17 日 14:00 前提交，簡報與出席均未處理。

## 6. Internal commitments from plan.md

| Commitment | Owner | State |
| --- | --- | --- |
| Fixed 150-sample index in `shared/samples.json` | M1 | ✅ 150 ids, `seed=42` |
| Single shared prompt template | M1 | ✅ `render_input_ids` used by all three runners |
| Temperature zero, fixed max new tokens | M1 | ✅ `do_sample=False`, `max_new_tokens=64` |
| EM and token-level F1 | M1 | ✅ `shared/metrics.py` |
| Head-and-tail at 2x and 4x | M2 | ✅ Both ratios, 150/150 |
| Achieved compression ratio recorded | M2 | ✅ Document 2.000 / 4.000, prompt 1.969 / 3.820 |
| **Failure analysis when the answer sits in the middle** | M2 | ⚠️ **Partial** — one reproducible qualitative case is at 65.1%, but `run_truncation.py` has no systematic answer-position logic |
| LLMLingua at 2x and 4x | M3 | ✅ Both ratios, 150/150 |
| Two-stage compress / evaluate to avoid OOM | M3 | ✅ Separate processes |
| Accuracy–compression curve | M3 | ✅ [PNG](./figures/accuracy_compression_tradeoff.png) · [PDF](./figures/accuracy_compression_tradeoff.pdf) |
| Successful / failed compression cases | M3 | ✅ Reproducible [script](./part3_llmlingua/build_qualitative_cases.py), [CSV](./part3_llmlingua/qualitative_cases.csv), and [write-up](./part3_llmlingua/qualitative_cases.md) |
| Combined table answering RQ1–RQ3 | All | ⚠️ README summary only; script covers Parts 1–2 |

> 三個方法、Member 3 圖表及質性案例均已交付。尚未完成的功能性整合是五列總表；
> Member 2 的答案位置分析只有個別案例，尚無系統化程式。

## 7. Comparability audit (verified 2026-11-06)

Checks recomputed directly from the JSON files:

| Check | Result |
| --- | --- |
| Sample ids identical across all four result files and `samples.json` | ✅ 150 / 150 match |
| Target model identical | ✅ `unsloth/Llama-3.2-3B-Instruct` in all files |
| Row count per result file | ✅ 150, 150, 150, 300 rows, no duplicate ids |
| Empty answers | ✅ 0 |
| Gold `answers` field present | ✅ 0 missing |
| `docs` field populated | ⚠️ Empty in **all** files, so `plan.md`'s declared interface `{… docs …}` is not met, although all three parts are equally empty and therefore comparable |

Recomputed metrics:

| Method | n | EM hits | EM | F1 | F1 sd | Mean prompt tokens | Token reduction vs Part 1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uncompressed | 150 | 14 | 0.0933 | 0.4296 | 0.2910 | 6 966.8 | — |
| Head-tail 2x | 150 | 11 | 0.0733 | 0.4065 | 0.2931 | 3 523.1 | 49.4% |
| Head-tail 4x | 150 | 10 | 0.0667 | 0.3620 | 0.2978 | 1 801.2 | 74.1% |
| LLMLingua 2x | 150 | 1 | 0.0067 | 0.2626 | 0.2675 | 3 308.1 | 52.5% |
| LLMLingua 4x | 150 | 2 | 0.0133 | 0.2207 | 0.2396 | 1 961.6 | 71.8% |

Paired F1 differences on the same 150 samples (95% CI, paired by id). This is
the statistical form the report should use; it is much tighter than comparing
independent means:

| Contrast | Mean ΔF1 | 95% CI | Verdict |
| --- | ---: | --- | --- |
| Uncompressed → Head-tail 2x | −0.0231 | [−0.057, +0.011] | **Not significant** |
| Uncompressed → Head-tail 4x | −0.0676 | [−0.107, −0.029] | Significant |
| Uncompressed → LLMLingua 2x | −0.1670 | [−0.208, −0.127] | Significant |
| Uncompressed → LLMLingua 4x | −0.2090 | [−0.250, −0.168] | Significant |
| Head-tail 2x → LLMLingua 2x | −0.1440 | [−0.186, −0.102] | Significant |
| Head-tail 4x → LLMLingua 4x | −0.1414 | [−0.183, −0.100] | Significant |

> 三人樣本 id 完全一致、模型一致、無重複、無空答案。唯一介面偏差是 `docs`
> 欄位全部為空，但三人一致，故比較仍然公平。配對檢定顯示：頭尾 2x 與不壓縮
> **沒有顯著差異**；4x 顯著下降；LLMLingua 兩個比例都大幅顯著下降，且顯著
> 劣於同預算的頭尾截斷。

## 8. Issues to resolve before or while writing

| # | Severity | Issue | Suggested action |
| --- | --- | --- | --- |
| 1 | 🔴 High | LLMLingua's drop is far larger than published results (−38.9% / −48.6% relative F1). 296 of 300 rows were **chunked** (mean 6.3 chunks, max 13) because the phi-2 compressor has a short context, so this is not the original whole-prompt LLMLingua. | ✅ Documented in the Member 3 README, qualitative analysis, and report draft; retain it as a limitation |
| 2 | 🔴 High | Latencies come from three different machines (RTX 3060, Colab T4, Apple M5 Pro MPS), but RQ3 asks about end-to-end latency | Only compare latencies **within** a part, or re-run generation on one machine for the RQ3 table |
| 3 | 🟠 Medium | `make_table.py` cannot read `results_member3.json` (summary nested under `2x` / `4x`) | Extend the script so the combined table is generated, not hand-typed |
| 4 | 🟠 Medium | 6 unfilled placeholders in [part2_truncation/README.md](./part2_truncation/README.md) lines 94–105 (`[X]`, `[150]`, `[0.0733]`, `[版本]`) | Fill from the verified table in §7 |
| 5 | 🟠 Medium | Standard deviations and paired CIs are computed in §7 but are absent from the generated combined table | Add sd/CI columns or a statistical-results table to the final report |
| 6 | 🟡 Low | Systematic answer-position analysis missing (planned Part 2 contribution); one qualitative example is available | Implement the systematic analysis or limit the report to the observed case |
| 7 | 🟡 Low | `docs` field empty in all outputs, deviating from the `plan.md` interface | Record as a known deviation, or backfill with `--save-context` |
| 8 | 🟡 Low | [part2_truncation/run_truncation_result.ipynb](./part2_truncation/run_truncation_result.ipynb) (190 KB) is a Colab artifact with embedded outputs | Keep if used as evidence, otherwise drop from the zip |
| 9 | 🟡 Low | `plan.md` still says Colab T4; actual runs are local GPU / Colab / M5 Pro | Leave `plan.md` as the original plan; describe the actual setup in the report |

## 9. What can be written now

- **Introduction**: motivation, literature, and the three research questions — [acl_latex.tex](./acl_latex.tex) §Papers Reviewed / §Existing Methodologies can be condensed directly.
- **Detailed Description — Method**: the shared harness, the three methods, and the comparability contract are fully documented in [README.md](./README.md), [part1](./part1_uncompressed/README.md), [part2](./part2_truncation/README.md), [part3](./part3_llmlingua/README.md).
- **Detailed Description — Results**: the metrics in §7, accuracy–compression figure, and reproducible qualitative cases are ready; only the generated five-row table and systematic position analysis are missing.
- **Conclusion — difficulties**: the gated model, Windows console encoding crash at sample 87, the compressor context limit forcing chunking, and the Colab T4 OOM forcing chunked prefill are all real, documented difficulties.

> 現在即可動筆：Introduction、方法、結果、圖表、質性案例，以及困難與經驗都已有
> 證據。技術上仍缺五列總表、系統化位置分析與 latency 比較口徑。

## 10. Suggested order of work

| Order | Task | Owner | Effort |
| ---: | --- | --- | --- |
| 1 | Extend `make_table.py` to emit all 5 rows + sd columns | M2 | ~1 h |
| 2 | Fill the 6 placeholders in `part2_truncation/README.md` | M2 | ~15 min |
| 3 | ✅ Accuracy–compression figure from the 5 rows | M3 | Done |
| 4 | ✅ Reproducible qualitative success / failure examples | M3 | Done |
| 5 | Answer-position analysis for Part 2, or remove the claim | M2 | ~3 h |
| 6 | Decide the RQ3 latency framing (within-part only, or re-run) | All | ~1 h meeting |
| 7 | Write the ACL final report | All | ~3 days |
| 8 | Slides, 5-minute video, source zip, in-class PPT | All | ~2 days |

> 建議順序：先補齊表格與文件小錯（1–2 小時），再做圖與案例，最後才動筆寫報告；
> RQ3 的延遲比較方式需要三人一起決定，因為三台機器不同。

## 11. RQ coverage

| RQ | Question | Evidence status |
| --- | --- | --- |
| RQ1 | How does the compression ratio affect QA accuracy? | ✅ Answerable — monotone F1 decline at 2x and 4x for both methods |
| RQ2 | Does LLMLingua beat simple truncation at the same token budget? | ✅ Answerable — no; truncation is significantly better at both ratios (ΔF1 ≈ −0.14, CI excludes 0) |
| RQ3 | Does compression reduce end-to-end latency after compression overhead? | ⚠️ Only within-part; cross-machine absolute seconds are not comparable |

> RQ1、RQ2 目前已可完整回答；RQ3 只能在同一個 part 內比較，因為三台機器不同，
> 需要決定寫法或補一次統一機器的生成實驗。
