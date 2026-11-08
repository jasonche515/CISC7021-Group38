# Requirement Checklist — CISC7021 Group 38

> **Note**：每一節英文段落下方均附中文對照說明，兩者如有出入以英文為準。

Verification baseline: experiment outputs verified through commit `4c0310b` for
Parts 1–3, plus the Part 4 Colab run (`results_member4.json`, 2026-11-08), checked
against [project.md](./project.md) and [plan.md](./plan.md) on 2026-11-07 and
re-checked after Part 4 on 2026-11-08. All numbers in this file were recomputed
from the result JSON files, not copied from the READMEs.

Two result sets now exist: the **per-part runs** on four different machines
(§7.1) and the **same-environment rerun** produced by `run_all.py`, which covers
Parts 1–3 only (§7.2). Part 4 has no common-hardware counterpart at all, so its
latency must be quoted on its own and never compared with §7.2. Quality is
reported from the per-part runs because that is what each member's README
documents; every latency claim must come from §7.2.

> 核對基準：Part 1–3 的實驗輸出已核對至 commit `4c0310b`，Part 4 則以
> 2026-11-08 的 Colab 執行結果（`results_member4.json`）為準，並於 2026-11-07
> 及 Part 4 完成後的 2026-11-08 兩次對照 [project.md](./project.md) 與
> [plan.md](./plan.md)。本檔所有數字均由結果 JSON 重新計算，非抄自 README。
> 目前存在兩組結果：§7.1 的各 part 原始跑（四台不同機器），以及 §7.2 由
> `run_all.py` 產生、僅涵蓋 Part 1–3 的同環境重跑。Part 4 完全沒有同硬體對照，
> 其延遲必須單獨陳述，不可與 §7.2 相比。品質指標採各 part 原始跑（各成員 README
> 記錄的即是此組）；延遲一律引用 §7.2。

## 1. Status at a glance

| Requirement | Weight | Due | State |
| --- | ---: | --- | --- |
| Task 1 — Review report | 15% | 10 Oct (passed) | ✅ Done |
| Task 2 — Final report (ACL two-column) | 30% | 17 Nov 23:55 | ⚠️ Member 3 and Member 4 contributions drafted; group report not assembled |
| Task 3 — Pre-recorded presentation | 30% (with Task 4) | 17 Nov | ⚠️ 1 of 4 items ready |
| Task 4 — In-class presentation | — (shared with Task 3) | 17 / 24 Nov | ⬜ Not started |
| System implementation (the four parts) | 20% | 17 Nov | ✅ Done |

### 1.1 Experiment and programming audit (2026-11-08)

| Technical item | Evidence | State |
| --- | --- | --- |
| Shared samples, prompt template, and EM/F1 metrics | [shared/](./shared) | ✅ Complete |
| Uncompressed pipeline | [part1_uncompressed/](./part1_uncompressed) — 150 results | ✅ Complete |
| Head-tail 2x and 4x pipelines | [part2_truncation/](./part2_truncation) — 150 results per ratio | ✅ Complete |
| LLMLingua 2x and 4x pipeline | [part3_llmlingua/](./part3_llmlingua) — 300 results | ✅ Complete |
| LLMLingua-enhanced 2x and 4x pipeline | [part4_llmlingua_enhanced/](./part4_llmlingua_enhanced) — 300 results, 0 chunked | ✅ Complete |
| Accuracy–compression plotting code and figure | [plot script](./part4_llmlingua_enhanced/plot_accuracy_compression.py) · [figure](./figures/accuracy_compression_tradeoff.pdf) | ✅ Complete for Parts 1–4 — reads all five result files and overlays seven settings |
| Reproducible qualitative-case analysis | [script](./part3_llmlingua/build_qualitative_cases.py) · [cases](./part3_llmlingua/qualitative_cases.md) | ✅ Complete |
| One generated table covering all seven settings | [make_table.py](./part4_llmlingua_enhanced/make_table.py) · [table](./part4_llmlingua_enhanced/results_table.md) | ✅ 7 rows and 10 paired contrasts from Parts 1–4; `--rerun-dir results_same_machine` switches to the rerun |
| Systematic answer-position analysis | Part 2 plan | ⚠️ Partial — one qualitative example exists, but no systematic implementation |
| Cross-method latency comparison | [run_all.py](./run_all.py) · [results_same_machine/](./results_same_machine) | ✅ Complete for Parts 1–3 — all five of those settings rerun on one GPU; Part 4 has no counterpart |
| Part 2 result documentation | [part2 README](./part2_truncation/README.md) | ✅ Placeholders filled from the per-part summaries |

> 四個部分的程式與完整結果均已完成（Part 4 共 300 筆、完全沒有切塊），Member 3
> 的圖表與可重現案例分析已完成，七列總表與同機器延遲比較亦已就緒。剩下的編程
> 工作有三項：Part 2 的系統化答案位置分析、把 Part 4 加進 accuracy–compression
> 圖，以及為 Part 4 補一組同硬體延遲量測（目前沒有）。

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
| LLMLingua-enhanced 2x and 4x, 150/150 each (300 rows, 0 chunked) | [results_member4.json](./part4_llmlingua_enhanced/results_member4.json) | ✅ |
| Shared sample index, prompt template, metrics | [shared/](./shared) | ✅ |
| Combined table, all seven settings | [Part 4 table](./part4_llmlingua_enhanced/results_table.md) · [same-environment numbers](./results_same_machine/README.md) | ✅ Part 1–4 with paired contrasts; the `results_same_machine` export remains stale for Part 1–3 |
| Accuracy–compression figure | [PNG](./figures/accuracy_compression_tradeoff.png) · [PDF](./figures/accuracy_compression_tradeoff.pdf) | ✅ All seven settings from Parts 1–4 |
| Reproducible qualitative examples | [Markdown](./part3_llmlingua/qualitative_cases.md) · [CSV](./part3_llmlingua/qualitative_cases.csv) | ✅ |
| Member 3 report contribution | [part3 README](./part3_llmlingua/README.md) · [qualitative cases](./part3_llmlingua/qualitative_cases.md) | ⚠️ Narrative lives inside the Part 3 README and the case write-up; no standalone `final_report_contribution.md` was ever created |
| Member 4 report contribution | [part4 README](./part4_llmlingua_enhanced/README.md) | ✅ Methods, results, cost and limitations sections are written; still needs merging into the group report |

> 小組總報告尚未組裝，但 Member 3 與 Member 4 的方法與結果文字已有草稿，分別
> 見於 Part 3 的 README、質性案例檔與 Part 4 的 README（先前指向的
> `final_report_contribution.md` 並不存在）。實驗證據、七個設定的合併表格與
> 質性案例均已齊備；accuracy–compression 圖仍只含 Part 1–3。

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
| Final results | ✅ Five per-part result files (Parts 1–4) plus the same-environment rerun and a 7-row combined table |
| Presentation video uploaded to a public site + shared form | ⬜ Missing |

> 投影片、影片與共用表單均未做；原始碼已在 repo 內，只需打包成 zip；四個部分的
> 結果檔已齊（Part 1 一份、Part 2 兩份、Part 3 一份、Part 4 一份），另有同環境
> 重跑結果與七列合併表格。

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
| Single shared prompt template | M1 | ✅ `render_input_ids` used by all four runners |
| Temperature zero, fixed max new tokens | M1 | ✅ `do_sample=False`, `max_new_tokens=64` |
| EM and token-level F1 | M1 | ✅ `shared/metrics.py` |
| Head-and-tail at 2x and 4x | M2 | ✅ Both ratios, 150/150 |
| Achieved compression ratio recorded | M2 | ✅ Document 2.000 / 4.000, prompt 1.969 / 3.820 |
| **Failure analysis when the answer sits in the middle** | M2 | ⚠️ **Partial** — one reproducible qualitative case is at 65.1%, but `run_truncation.py` has no systematic answer-position logic |
| LLMLingua at 2x and 4x | M3 | ✅ Both ratios, 150/150 |
| Two-stage compress / evaluate to avoid OOM | M3 | ✅ Separate processes |
| Accuracy–compression curve | M3 / M4 | ✅ [PNG](./figures/accuracy_compression_tradeoff.png) · [PDF](./figures/accuracy_compression_tradeoff.pdf) — all three methods, generated by [Part 4 plot script](./part4_llmlingua_enhanced/plot_accuracy_compression.py) |
| Successful / failed compression cases | M3 | ✅ Reproducible [script](./part3_llmlingua/build_qualitative_cases.py), [CSV](./part3_llmlingua/qualitative_cases.csv), and [write-up](./part3_llmlingua/qualitative_cases.md) |
| LLMLingua-enhanced at 2x and 4x, no chunking | M4 | ✅ Both ratios, 150/150, 0 chunked |
| Question-aware single-pass compression verified | M4 | ✅ `condition_on_question=true`, `rank_method=longllmlingua`, `max_num_compression_chunks=1` in `results_member4_compressed.json` |
| Combined table answering RQ1–RQ3 | All | ✅ [Part 4 make_table.py](./part4_llmlingua_enhanced/make_table.py) covers all seven settings; latency from [run_all.py](./run_all.py) for Parts 1–3 |

> 四個部分、Member 3 圖表、質性案例、七列總表與同機器延遲比較均已交付。尚未
> 完成的功能性整合只剩三項：Member 2 的系統化答案位置分析（目前僅有個別案例）、
> 把 Part 4 加進 accuracy–compression 圖，以及 Part 4 的同硬體延遲量測。

## 7. Comparability audit (verified 2026-11-08)

### 7.1 Per-part runs (four machines)

Checks recomputed directly from the JSON files:

| Check | Result |
| --- | --- |
| Sample ids identical across all five result files and `samples.json` | ✅ 150 / 150 match in every file |
| Target model identical | ✅ `unsloth/Llama-3.2-3B-Instruct` in all files |
| Row count per result file | ✅ 150, 150, 150, 300 and 300 rows, no duplicate ids |
| Empty answers | ✅ 0 |
| Gold `answers` field present | ✅ 0 missing |
| `docs` field populated | ⚠️ Empty in **all** files, so `plan.md`'s declared interface `{… docs …}` is not met, although every part is equally empty and therefore comparable |
| Chunking (Part 3 vs Part 4) | ✅ Part 3: 296 / 300 rows chunked (mean 6.3 chunks). Part 4: 0 / 300 chunked, `max_num_compression_chunks = 1` |

Recomputed metrics:

| Method | n | EM hits | EM | F1 | F1 sd | Mean prompt tokens | Token reduction vs Part 1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uncompressed | 150 | 14 | 0.0933 | 0.4296 | 0.2910 | 6 966.8 | — |
| Head-tail 2x | 150 | 11 | 0.0733 | 0.4065 | 0.2931 | 3 523.1 | 49.4% |
| Head-tail 4x | 150 | 10 | 0.0667 | 0.3620 | 0.2978 | 1 801.2 | 74.1% |
| LLMLingua 2x | 150 | 1 | 0.0067 | 0.2626 | 0.2675 | 3 308.1 | 52.5% |
| LLMLingua 4x | 150 | 2 | 0.0133 | 0.2207 | 0.2396 | 1 961.6 | 71.8% |
| LLMLingua-Enhanced 2x | 150 | 0 | 0.0000 | 0.3070 | 0.2571 | 3 254.1 | 53.3% |
| LLMLingua-Enhanced 4x | 150 | 1 | 0.0067 | 0.2794 | 0.2559 | 1 663.0 | 76.1% |

Paired F1 differences on the same 150 samples (95% CI, paired by id). This is
the statistical form the report should use; it is much tighter than comparing
independent means:

| Contrast | Mean ΔF1 | 95% CI | Verdict |
| --- | ---: | --- | --- |
| Uncompressed → Head-tail 2x | −0.0231 | [−0.057, +0.011] | **Not significant** — but this flips in §7.2 |
| Uncompressed → Head-tail 4x | −0.0676 | [−0.107, −0.028] | Significant |
| Uncompressed → LLMLingua 2x | −0.1670 | [−0.208, −0.127] | Significant |
| Uncompressed → LLMLingua 4x | −0.2090 | [−0.250, −0.168] | Significant |
| Uncompressed → LLMLingua-Enhanced 2x | −0.1226 | [−0.162, −0.083] | Significant |
| Uncompressed → LLMLingua-Enhanced 4x | −0.1503 | [−0.192, −0.108] | Significant |
| Head-tail 2x → LLMLingua 2x | −0.1440 | [−0.186, −0.102] | Significant |
| Head-tail 4x → LLMLingua 4x | −0.1414 | [−0.183, −0.100] | Significant |
| **LLMLingua 2x → LLMLingua-Enhanced 2x** | **+0.0444** | [+0.013, +0.076] | **Significant gain** |
| **LLMLingua 4x → LLMLingua-Enhanced 4x** | **+0.0587** | [+0.025, +0.093] | **Significant gain** |
| Head-tail 2x → LLMLingua-Enhanced 2x | −0.0995 | [−0.142, −0.057] | Significant loss |
| Head-tail 4x → LLMLingua-Enhanced 4x | −0.0827 | [−0.128, −0.037] | Significant loss |

> 四人的樣本 id 完全一致、模型一致、無重複、無空答案。唯一介面偏差是 `docs`
> 欄位全部為空，但四組一致，故比較仍然公平。Part 3 有 296/300 筆被切塊，Part 4
> 則完全沒有切塊。配對檢定顯示：頭尾 2x 與不壓縮**沒有顯著差異**；4x 顯著下降；
> LLMLingua 兩個比例都大幅顯著下降，且顯著劣於同預算的頭尾截斷。Part 4 相比
> Part 3 顯著回升（2x +0.0444、4x +0.0587），但仍顯著低於頭尾截斷
> （2x −0.0995、4x −0.0827），因此「切塊是唯一原因」的假設只被部分支持。

### 7.2 Same-environment rerun (single RTX 3060)

`run_all.py` replays all five Part 1–3 settings back to back on one GPU with a
single `transformers` install, so the absolute second counts become comparable.
Part 4 is deliberately excluded: its compressor needs a different model family
that could not be loaded on this host, so no Part 4 latency number belongs in
this table. Source:
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
| 1 | 🟠 Medium | LLMLingua's drop is far larger than published results (−38.9% / −48.6% relative F1). 296 of 300 rows were **chunked** (mean 6.3 chunks, max 13) because the phi-2 compressor has a short context, so Part 3 is not the original whole-prompt LLMLingua. Part 4 tests this directly: with 0% chunked it still loses to truncation (−0.0995 / −0.0827), so chunking explains only 31% (2x) and 42% (4x) of the Part 2 → Part 3 gap | ✅ Documented in the Member 3 and Member 4 READMEs; the report must present the chunking explanation as *partially confirmed*, not as the sole cause |
| 2 | 🟢 Resolved | Latencies come from four different machines (RTX 3060, Colab T4, Apple M5 Pro MPS, Colab CUDA GPU), but RQ3 asks about end-to-end latency | ✅ Fixed by [run_all.py](./run_all.py) for Parts 1–3; cite §7.2 for every latency number and state explicitly that Part 4 has no common-hardware counterpart |
| 3 | 🟢 Resolved | `make_table.py` cannot read `results_member3.json` (summary nested under `2x` / `4x`) | ✅ [part4 make_table.py](./part4_llmlingua_enhanced/make_table.py) rewritten as a standalone reader for all seven settings and 10 paired contrasts |
| 4 | 🟢 Resolved | 6 unfilled placeholders in [part2_truncation/README.md](./part2_truncation/README.md) (`[X]`, `[150]`, `[0.0733]`, `[版本]`) | ✅ Filled from the per-part summaries |
| 5 | 🟠 Medium | The two runs disagree on whether the Uncompressed → Head-tail 2x drop is significant | Quote both intervals and describe the 2x loss as marginal |
| 6 | 🟡 Low | Systematic answer-position analysis missing (planned Part 2 contribution); one qualitative example is available | Implement the systematic analysis or limit the report to the observed case |
| 7 | 🟡 Low | `docs` field empty in all outputs, deviating from the `plan.md` interface | Record as a known deviation, or backfill with `--save-context` |
| 8 | 🟡 Low | The committed [results_same_machine/results_table.md](./results_same_machine/results_table.md) was generated without `--rerun-dir`, so it still shows cross-machine numbers | Regenerate with `make_table.py --rerun-dir results_same_machine`, or keep the warning note at the top of the file |
| 9 | 🟡 Low | `plan.md` still says Colab T4; actual runs are local GPU / Colab / M5 Pro / Colab CUDA | Leave `plan.md` as the original plan; describe the actual setup in the report |
| 10 | 🟡 Low | [part2_truncation/run_truncation_result.ipynb](./part2_truncation/run_truncation_result.ipynb) (190 KB) is a Colab artifact with embedded outputs | Keep if used as evidence, otherwise drop from the zip |
| 11 | 🟠 Medium | The Part 3 → Part 4 gain is **confounded**: compressor size (2.7B → 1.5B), question awareness, sentence-level filter, long context and 4-bit weights all change together | Report the gain as an upper bound on the chunking effect, and say so explicitly; do not attribute it to de-chunking alone |
| 12 | 🟠 Medium | Part 4's target numbers were not met (target 0.415 / 0.380, measured 0.3070 / 0.2794 at 2x / 4x) | Present this as a negative result for *this* implementation of the paper's claim, not as evidence against LLMLingua |
| 13 | 🟢 Resolved | The [accuracy–compression figure](./figures/accuracy_compression_tradeoff.png) previously read only `results_member1/2/3.json`, so Part 4 was absent | ✅ [Part 4 plot script](./part4_llmlingua_enhanced/plot_accuracy_compression.py) reads all five result files and both `figures/` files were regenerated |

## 9. What can be written now

- **Introduction**: motivation, literature, and the three research questions — [acl_latex.tex](./acl_latex.tex) §Papers Reviewed / §Existing Methodologies can be condensed directly.
- **Detailed Description — Method**: the shared harness, the four parts, and the comparability contract are fully documented in [README.md](./README.md), [part1](./part1_uncompressed/README.md), [part2](./part2_truncation/README.md), [part3](./part3_llmlingua/README.md), [part4](./part4_llmlingua_enhanced/README.md).
- **Detailed Description — Results**: the metrics in §7, the seven-row combined table with 10 paired contrasts, the accuracy–compression figure covering all seven settings, and the reproducible qualitative cases are ready; only the systematic position analysis is missing. Note the figure and the case file still embed the per-part F1 values (0.2626 / 0.2207), not the rerun values; the figure now also carries Part 4 (0.3070 / 0.2794).
- **Conclusion — difficulties**: the gated model, Windows console encoding crash at sample 87, the compressor context limit forcing chunking, the Colab T4 OOM forcing chunked prefill, and the Windows commit-limit failure that blocked Part 4 locally are all real, documented difficulties.

> 現在即可動筆：Introduction、方法、結果、七列總表（含 10 組配對檢定）、圖表、
> 質性案例，以及困難與經驗都已有證據。技術上只剩系統化位置分析未做。撰寫時務必
> 注意兩點：圖表與案例檔內嵌的仍是各 part 原始跑的 F1 值（0.2626 / 0.2207），
> 圖表已加入 Part 4；Part 3 → Part 4 的改善同時混雜了壓縮器大小、問題感知、
> 句級過濾與 4-bit 量化，只能視為切塊效應的上界。

## 10. Suggested order of work

| Order | Task | Owner | Effort |
| ---: | --- | --- | --- |
| 1 | ✅ Seven-row combined table from all settings | M4 | Done |
| 2 | ✅ Fill the 6 placeholders in `part2_truncation/README.md` | M2 | Done |
| 3 | ✅ Accuracy–compression figure from the 5 rows | M3 | Done |
| 4 | ✅ Reproducible qualitative success / failure examples | M3 | Done |
| 5 | Answer-position analysis for Part 2, or remove the claim | M2 | ~3 h |
| 6 | ✅ RQ3 latency from the single-GPU rerun | All | Done |
| 7 | ✅ Add Part 4 to the accuracy–compression figure | M4 | Done |
| 8 | Write the ACL final report | All | ~3 days |
| 9 | Slides, 5-minute video, source zip, in-class PPT | All | ~2 days |

> 建議順序：表格、圖表（含 Part 4）、案例與 RQ3 延遲口徑均已完成，現在只剩
> Part 2 的位置分析與文件同步，之後即可動筆寫報告。

## 11. RQ coverage

| RQ | Question | Evidence status |
| --- | --- | --- |
| RQ1 | How does the compression ratio affect QA accuracy? | ✅ Answerable — monotone F1 decline from 1x to 2x to 4x in all three compressed families (Parts 1 → 2/3/4) |
| RQ2 | Does LLMLingua beat simple truncation at the same token budget? | ✅ Answerable — no in any variant. Part 3 loses by ΔF1 ≈ −0.14; Part 4 recovers +0.0444 / +0.0587 over Part 3 but still trails truncation by −0.0995 / −0.0827, all CIs excluding 0 |
| RQ3 | Does compression reduce end-to-end latency after compression overhead? | ✅ Answerable from §7.2 — truncation cuts total latency 44% / 66%; LLMLingua 2x is 44% slower than uncompressed. Part 4 is slower still (16.9 s compression per sample) but has no common-hardware rerun |

> RQ1、RQ2、RQ3 現在均可完整回答；RQ3 引用同機器重跑的結果，不再受跨機器延遲
> 不可比的限制，但該重跑只涵蓋 Part 1–3。RQ2 的答案比 Part 3 時期更明確：Part 4
> 已消除切塊並顯著改善 LLMLingua 本身（2x +0.0444、4x +0.0587），卻仍顯著低於
> 同預算的頭尾截斷（2x −0.0995、4x −0.0827），因此「LLMLingua 勝過簡單截斷」
> 在本專案的實作下不成立，且不能歸因於單一實作缺陷。
