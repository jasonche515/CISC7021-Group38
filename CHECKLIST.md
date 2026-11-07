# Requirement Checklist — CISC7021 Group 38

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

Verification baseline: experiment outputs verified through commit `4c0310b`,
checked against [project.md](./project.md) and [plan.md](./plan.md) on
2026-11-07. All numbers in this file were recomputed from the result JSON files,
not copied from the READMEs.

Two result sets now exist: the **per-part runs** on three different machines
(§7.1) and the **same-environment rerun** produced by `run_all.py` (§7.2).
Quality is reported from the per-part runs because that is what each member's
README documents; every latency claim must come from §7.2.

> 核對基準：實驗輸出已核對至 commit `4c0310b`，並於 2026-11-07 對照
> [project.md](./project.md) 與 [plan.md](./plan.md)。本檔所有數字均由結果 JSON
> 重新計算，非抄自 README。目前存在兩組結果：§7.1 的各 part 原始跑（三台不同
> 機器）與 §7.2 由 `run_all.py` 產生的同環境重跑。品質指標採各 part 原始跑
> （各成員 README 記錄的即是此組）；延遲一律引用 §7.2。

## 1. Status at a glance

| Requirement | Weight | Due | State |
| --- | ---: | --- | --- |
| Task 1 — Review report | 15% | 10 Oct (passed) | ✅ Done |
| Task 2 — Final report (ACL two-column) | 30% | 17 Nov 23:55 | ⚠️ Member 3 contribution drafted; group report not assembled |
| Task 3 — Pre-recorded presentation | 30% (with Task 4) | 17 Nov | ⚠️ 1 of 4 items ready |
| Task 4 — In-class presentation | | 17 / 24 Nov | ⬜ Not started |
| System implementation (the three methods) | 20% | 17 Nov | ✅ Done |

### 1.1 Experiment and programming audit (2026-11-07)

| Technical item | Evidence | State |
| --- | --- | --- |
| Shared samples, prompt template, and EM/F1 metrics | [shared/](./shared) | ✅ Complete |
| Uncompressed pipeline | [part1_uncompressed/](./part1_uncompressed) — 150 results | ✅ Complete |
| Head-tail 2x and 4x pipelines | [part2_truncation/](./part2_truncation) — 150 results per ratio | ✅ Complete |
| LLMLingua 2x and 4x pipeline | [part3_llmlingua/](./part3_llmlingua) — 300 results | ✅ Complete |
| Accuracy–compression plotting code and figure | [plot script](./part3_llmlingua/plot_accuracy_compression.py) · [figure](./figures/accuracy_compression_tradeoff.pdf) | ✅ Complete |
| Reproducible qualitative-case analysis | [script](./part3_llmlingua/build_qualitative_cases.py) · [cases](./part3_llmlingua/qualitative_cases.md) | ✅ Complete |
| One generated table covering all five settings | [make_table.py](./part2_truncation/make_table.py) · [numbers](./results_same_machine/README.md) | ✅ All five settings, but the script must be run with `--rerun-dir results_same_machine` to reflect the rerun |
| Systematic answer-position analysis | Part 2 plan | ⚠️ Partial — one qualitative example exists, but no systematic implementation |
| Cross-method latency comparison | [run_all.py](./run_all.py) · [results_same_machine/](./results_same_machine) | ✅ Complete — all five settings rerun on one GPU |
| Part 2 result documentation | [part2 README](./part2_truncation/README.md) | ✅ Placeholders filled from the per-part summaries |

> 三個方法的主程式與完整結果均已完成，Member 3 的圖表與可重現案例分析已完成，
> 五列總表與同機器延遲比較亦已就緒。剩餘的編程工作只有 Part 2 的系統化答案
> 位置分析（目前僅有個別案例）。

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
| Combined table, all five settings | [same-environment numbers](./results_same_machine/README.md) · [generated export](./results_same_machine/results_table.md) | ⚠️ The generated export is stale — see the warning at the top of that file |
| Accuracy–compression figure | [PNG](./figures/accuracy_compression_tradeoff.png) · [PDF](./figures/accuracy_compression_tradeoff.pdf) | ✅ |
| Reproducible qualitative examples | [Markdown](./part3_llmlingua/qualitative_cases.md) · [CSV](./part3_llmlingua/qualitative_cases.csv) | ✅ |
| Member 3 report contribution | [part3 README](./part3_llmlingua/README.md) · [qualitative cases](./part3_llmlingua/qualitative_cases.md) | ⚠️ Narrative lives inside the Part 3 README and the case write-up; no standalone `final_report_contribution.md` was ever created |

> 小組總報告尚未組裝，但 Member 3 的方法與結果文字已有草稿，散見於 Part 3 的
> README 與質性案例檔（先前指向的 `final_report_contribution.md` 並不存在）。
> 實驗證據、圖表、質性案例與五個設定的合併表格均已齊備。

Blocking gaps for the report (details in §6):

| # | Gap | Blocks which section |
| --- | --- | --- |
| 1 | Systematic answer-position failure analysis not implemented; only one reproducible qualitative example exists | Planned contribution for RQ2 / position bias |
| 2 | The committed `results_same_machine/results_table.md` was generated from the per-part files, so it does not match the JSON files beside it | Detailed Description (results table) |
| 3 | The significance verdict for Uncompressed → Head-tail 2x differs between the two runs | Detailed Description / Conclusion |

## 4. Phase 2 — Pre-recorded presentation (Task 3, part of 30%)

| Required item | State |
| --- | --- |
| Slides file, 5 minutes, all members participate | ⬜ Missing |
| Source code zip (optional) | ⚠️ Code ready in repo, zip not built |
| Final results | ✅ Five result JSON sets (per-part + same-environment) and a combined table |
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
| Combined table answering RQ1–RQ3 | All | ✅ [make_table.py](./part2_truncation/make_table.py) covers all five settings; latency from [run_all.py](./run_all.py) |

> 三個方法、Member 3 圖表、質性案例、五列總表與同機器延遲比較均已交付。尚未
> 完成的功能性整合只剩 Member 2 的系統化答案位置分析（目前僅有個別案例）。

## 7. Comparability audit (verified 2026-11-07)

### 7.1 Per-part runs (three machines)

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
| Uncompressed → Head-tail 2x | −0.0231 | [−0.057, +0.011] | **Not significant** — but this flips in §7.2 |
| Uncompressed → Head-tail 4x | −0.0676 | [−0.107, −0.029] | Significant |
| Uncompressed → LLMLingua 2x | −0.1670 | [−0.208, −0.127] | Significant |
| Uncompressed → LLMLingua 4x | −0.2090 | [−0.250, −0.168] | Significant |
| Head-tail 2x → LLMLingua 2x | −0.1440 | [−0.186, −0.102] | Significant |
| Head-tail 4x → LLMLingua 4x | −0.1414 | [−0.183, −0.100] | Significant |

> 三人樣本 id 完全一致、模型一致、無重複、無空答案。唯一介面偏差是 `docs`
> 欄位全部為空，但三人一致，故比較仍然公平。配對檢定顯示：頭尾 2x 與不壓縮
> **沒有顯著差異**；4x 顯著下降；LLMLingua 兩個比例都大幅顯著下降，且顯著
> 劣於同預算的頭尾截斷。

### 7.2 Same-environment rerun (single RTX 3060)

`run_all.py` replays all five settings back to back on one GPU with a single
`transformers` install, so the absolute second counts become comparable. Source:
[results_same_machine/](./results_same_machine), documented in
[its README](./results_same_machine/README.md).

| Method | n | EM | F1 | Mean prompt tokens | Mean generation s | Mean compression s | Mean total s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uncompressed | 150 | 0.1000 | 0.4350 | 6 966.8 | 9.403 | — | 9.43 |
| Head-tail 2x | 150 | 0.0733 | 0.3990 | 3 523.1 | 5.291 | 0.020 | 5.32 |
| Head-tail 4x | 150 | 0.0667 | 0.3633 | 1 801.2 | 3.209 | 0.019 | 3.23 |
| LLMLingua 2x | 150 | 0.0067 | 0.2569 | 3 309.1 | 6.032 | 7.496 | 13.57 |
| LLMLingua 4x | 150 | 0.0067 | 0.2221 | 1 962.8 | 4.034 | 6.711 | 10.76 |

Paired F1 contrasts from the same rerun:

| Contrast | Mean ΔF1 | 95% CI | Verdict |
| --- | ---: | --- | --- |
| Uncompressed → Head-tail 2x | −0.0360 | [−0.069, −0.003] | **Significant**, barely |
| Uncompressed → Head-tail 4x | −0.0717 | [−0.110, −0.033] | Significant |
| Uncompressed → LLMLingua 2x | −0.1781 | [−0.220, −0.137] | Significant |
| Uncompressed → LLMLingua 4x | −0.2128 | [−0.256, −0.170] | Significant |
| Head-tail 2x → LLMLingua 2x | −0.1421 | [−0.183, −0.101] | Significant |
| Head-tail 4x → LLMLingua 4x | −0.1412 | [−0.184, −0.098] | Significant |

Replication check: all five settings reproduce within 0.0075 F1 of §7.1, so the
qualitative conclusions hold. Two things do not reproduce and must be disclosed:

1. **The 2x verdict flips.** §7.1 gives a CI that includes 0; §7.2 gives one that
   excludes it by 0.003. Report this as a *small loss at the edge of
   significance*, not as "no difference" or as a clear loss.
2. **LLMLingua 4x EM** falls from 2 hits to 1 hit. One sample is within noise, but
   the report should quote F1 as the primary metric.

Also note that 12 of 150 uncompressed answers differ word for word between runs,
so greedy decoding is not bit-exact across GPUs.

> 同機器重跑讓延遲可以互相比較：截斷把總延遲降低 44%（2x）與 66%（4x），
> 而 LLMLingua 因為壓縮本身要花 6.7–7.5 秒，2x 反而比不壓縮慢 44%。重跑也
> 確認五個設定的 F1 與 §7.1 差異都在 0.0075 以內，但**頭尾 2x 的顯著性判定
> 會翻轉**，報告必須寫成「小幅下降、處於顯著邊緣」。另外 LLMLingua 4x 的 EM
> 少了一次命中，且 12 題不壓縮答案的文字有變動，說明貪婪解碼跨 GPU 並非
> 完全可重現。

## 8. Issues to resolve before or while writing

| # | Severity | Issue | Suggested action |
| --- | --- | --- | --- |
| 1 | 🔴 High | LLMLingua's drop is far larger than published results (−38.9% / −48.6% relative F1). 296 of 300 rows were **chunked** (mean 6.3 chunks, max 13) because the phi-2 compressor has a short context, so this is not the original whole-prompt LLMLingua. | ✅ Documented in the Member 3 README, qualitative analysis, and report draft; retain it as a limitation |
| 2 | 🟢 Resolved | Latencies come from three different machines (RTX 3060, Colab T4, Apple M5 Pro MPS), but RQ3 asks about end-to-end latency | ✅ Fixed by [run_all.py](./run_all.py); cite §7.2 for every latency number |
| 3 | 🟢 Resolved | `make_table.py` cannot read `results_member3.json` (summary nested under `2x` / `4x`) | ✅ Script rewritten; it reads all five settings and filters Part 3 rows by `target_compression_ratio` |
| 4 | 🟢 Resolved | 6 unfilled placeholders in [part2_truncation/README.md](./part2_truncation/README.md) (`[X]`, `[150]`, `[0.0733]`, `[版本]`) | ✅ Filled from the per-part summaries |
| 5 | 🟠 Medium | The two runs disagree on whether the Uncompressed → Head-tail 2x drop is significant | Quote both intervals and describe the 2x loss as marginal |
| 6 | 🟡 Low | Systematic answer-position analysis missing (planned Part 2 contribution); one qualitative example is available | Implement the systematic analysis or limit the report to the observed case |
| 7 | 🟡 Low | `docs` field empty in all outputs, deviating from the `plan.md` interface | Record as a known deviation, or backfill with `--save-context` |
| 8 | 🟡 Low | The committed [results_same_machine/results_table.md](./results_same_machine/results_table.md) was generated without `--rerun-dir`, so it still shows cross-machine numbers | Regenerate with `make_table.py --rerun-dir results_same_machine`, or keep the warning note at the top of the file |
| 9 | 🟡 Low | `plan.md` still says Colab T4; actual runs are local GPU / Colab / M5 Pro | Leave `plan.md` as the original plan; describe the actual setup in the report |
| 10 | 🟡 Low | [part2_truncation/run_truncation_result.ipynb](./part2_truncation/run_truncation_result.ipynb) (190 KB) is a Colab artifact with embedded outputs | Keep if used as evidence, otherwise drop from the zip |

## 9. What can be written now

- **Introduction**: motivation, literature, and the three research questions — [acl_latex.tex](./acl_latex.tex) §Papers Reviewed / §Existing Methodologies can be condensed directly.
- **Detailed Description — Method**: the shared harness, the three methods, and the comparability contract are fully documented in [README.md](./README.md), [part1](./part1_uncompressed/README.md), [part2](./part2_truncation/README.md), [part3](./part3_llmlingua/README.md).
- **Detailed Description — Results**: the metrics in §7, the combined five-row table, the accuracy–compression figure, and the reproducible qualitative cases are ready; only the systematic position analysis is missing. Note the figure and the case file still embed the per-part F1 values (0.2626 / 0.2207), not the rerun values.
- **Conclusion — difficulties**: the gated model, Windows console encoding crash at sample 87, the compressor context limit forcing chunking, and the Colab T4 OOM forcing chunked prefill are all real, documented difficulties.

> 現在即可動筆：Introduction、方法、結果、五列總表、圖表、質性案例，以及困難
> 與經驗都已有證據。技術上只剩系統化位置分析未做。注意圖表與案例檔內嵌的仍是
> 各 part 原始跑的 F1 值（0.2626 / 0.2207）。

## 10. Suggested order of work

| Order | Task | Owner | Effort |
| ---: | --- | --- | --- |
| 1 | ✅ Five-row combined table from all settings | M2 | Done |
| 2 | ✅ Fill the 6 placeholders in `part2_truncation/README.md` | M2 | Done |
| 3 | ✅ Accuracy–compression figure from the 5 rows | M3 | Done |
| 4 | ✅ Reproducible qualitative success / failure examples | M3 | Done |
| 5 | Answer-position analysis for Part 2, or remove the claim | M2 | ~3 h |
| 6 | ✅ RQ3 latency from the single-GPU rerun | All | Done |
| 7 | Write the ACL final report | All | ~3 days |
| 8 | Slides, 5-minute video, source zip, in-class PPT | All | ~2 days |

> 建議順序：表格、圖表、案例與 RQ3 延遲口徑均已完成，現在只剩 Part 2 的位置
> 分析與文件同步，之後即可動筆寫報告。

## 11. RQ coverage

| RQ | Question | Evidence status |
| --- | --- | --- |
| RQ1 | How does the compression ratio affect QA accuracy? | ✅ Answerable — monotone F1 decline at 2x and 4x for both methods |
| RQ2 | Does LLMLingua beat simple truncation at the same token budget? | ✅ Answerable — no; truncation is significantly better at both ratios (ΔF1 ≈ −0.14, CI excludes 0) |
| RQ3 | Does compression reduce end-to-end latency after compression overhead? | ✅ Answerable from §7.2 — truncation cuts total latency 44% / 66%; LLMLingua 2x is 44% slower than uncompressed |

> RQ1、RQ2、RQ3 現在均可完整回答；RQ3 引用同機器重跑的結果，不再受跨機器延遲
> 不可比的限制。
