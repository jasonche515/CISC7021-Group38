#!/usr/bin/env python3
"""Select reproducible qualitative cases and build Markdown/CSV artifacts.

The script reads only committed experiment outputs.  It applies four explicit
selection rules to the same 150 paired sample ids used in the main evaluation,
then writes a human-readable report and a machine-readable table.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
PART3_DIR = REPO_ROOT / "part3_llmlingua"

def load_results(relative_path: str) -> list[dict]:
    with (REPO_ROOT / relative_path).open(encoding="utf-8") as file:
        return json.load(file)["results"]

def index_by_id(rows: list[dict]) -> dict[str, dict]:
    indexed = {row["id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("Duplicate sample ids found in a result file")
    return indexed

def shortened(text: str, limit: int = 280) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

def load_data() -> dict[str, dict[str, dict]]:
    baseline = index_by_id(load_results("part1_uncompressed/results_member1.json"))
    truncation_2x = index_by_id(
        load_results("part2_truncation/results_member2_2x.json")
    )
    truncation_4x = index_by_id(
        load_results("part2_truncation/results_member2_4x.json")
    )
    llmlingua_rows = load_results("part3_llmlingua/results_member3.json")
    llmlingua_2x = index_by_id(
        [row for row in llmlingua_rows if row["target_compression_ratio"] == 2]
    )
    llmlingua_4x = index_by_id(
        [row for row in llmlingua_rows if row["target_compression_ratio"] == 4]
    )

    data = {
        "Uncompressed": baseline,
        "Head-tail 2x": truncation_2x,
        "Head-tail 4x": truncation_4x,
        "LLMLingua 2x": llmlingua_2x,
        "LLMLingua 4x": llmlingua_4x,
    }
    id_sets = {frozenset(rows) for rows in data.values()}
    if len(id_sets) != 1 or len(next(iter(id_sets))) != 150:
        raise ValueError("The five settings do not contain the same 150 sample ids")
    return data

def select_cases(data: dict[str, dict[str, dict]]) -> list[dict]:
    baseline = data["Uncompressed"]
    truncation_2x = data["Head-tail 2x"]
    truncation_4x = data["Head-tail 4x"]
    llmlingua_2x = data["LLMLingua 2x"]
    llmlingua_4x = data["LLMLingua 4x"]
    sample_ids = sorted(baseline)

    selected: set[str] = set()

    def choose(candidates: list[str], score: Callable[[str], float]) -> str:
        available = [sample_id for sample_id in candidates if sample_id not in selected]
        if not available:
            raise ValueError("No candidate satisfies a qualitative selection rule")
        sample_id = max(available, key=lambda item: (score(item), item))
        selected.add(sample_id)
        return sample_id

    exact_candidates = [
        sample_id
        for sample_id in sample_ids
        if llmlingua_2x[sample_id]["em"] == 1
        and llmlingua_4x[sample_id]["em"] == 1
    ]
    exact_id = choose(
        exact_candidates,
        lambda sample_id: llmlingua_4x[sample_id]["compression_ratio"],
    )

    semantic_id = choose(
        sample_ids,
        lambda sample_id: max(
            llmlingua_2x[sample_id]["f1"], llmlingua_4x[sample_id]["f1"]
        )
        - max(truncation_2x[sample_id]["f1"], truncation_4x[sample_id]["f1"]),
    )

    degradation_id = choose(
        sample_ids,
        lambda sample_id: llmlingua_2x[sample_id]["f1"]
        - llmlingua_4x[sample_id]["f1"],
    )

    failure_id = choose(
        sample_ids,
        lambda sample_id: min(
            baseline[sample_id]["f1"],
            truncation_2x[sample_id]["f1"],
            truncation_4x[sample_id]["f1"],
        )
        - max(llmlingua_2x[sample_id]["f1"], llmlingua_4x[sample_id]["f1"]),
    )

    cases = [
        {
            "category": "exact_preservation",
            "title": "Exact fact preserved after compression",
            "sample_id": exact_id,
            "rule": "LLMLingua EM = 1 at both settings; highest achieved 4x ratio",
            "evidence_phrase": "1964",
            "analysis": (
                "The publication year occurs near the beginning of the source and is "
                "repeated. LLMLingua preserves the exact answer at both settings, "
                "showing that compression can be lossless for a short, salient and "
                "redundant fact. The achieved ratio should be reported because the 4x "
                "target is not reached exactly for this sample."
            ),
        },
        {
            "category": "semantic_advantage",
            "title": "LLMLingua preserves evidence removed by positional truncation",
            "sample_id": semantic_id,
            "rule": "Largest best-LLMLingua F1 minus best-truncation F1",
            "evidence_phrase": "2-5 times smaller",
            "analysis": (
                "The key evidence lies away from the document boundaries. It is outside "
                "the regions retained by head-and-tail truncation, while LLMLingua "
                "keeps the numerical relation. This demonstrates the intended value of "
                "content-aware compression. A higher F1 at the stronger setting in one "
                "case is not evidence that stronger compression generally helps."
            ),
        },
        {
            "category": "compression_degradation",
            "title": "A precise date is lost as compression increases",
            "sample_id": degradation_id,
            "rule": "Largest LLMLingua F1 decrease from 2x to 4x",
            "evidence_phrase": "7 March 2023",
            "analysis": (
                "The date appears near the beginning of the original input, so both "
                "positional baselines preserve it. LLMLingua 2x drops the year and the "
                "stronger setting fails to recover the date. Precise details such as "
                "dates are vulnerable to token-level deletion."
            ),
        },
        {
            "category": "comparative_failure",
            "title": "A related distractor replaces the correct entity",
            "sample_id": failure_id,
            "rule": "Largest minimum-baseline F1 minus best-LLMLingua F1",
            "evidence_phrase": "Wallace electorate",
            "analysis": (
                "The source states that English was elected in Wallace and that the "
                "seat was later renamed Clutha-Southland. LLMLingua returns the related "
                "but temporally incorrect electorate. This suggests that compression "
                "retained a salient distractor while weakening the relation required "
                "by the question."
            ),
        },
    ]

    # These assertions make the documented case identities auditable. If result
    # files change, the script fails rather than silently attaching an old human
    # interpretation to a different sample.
    expected_ids = {
        "exact_preservation": "25ebcea4435f88495b4175446d1d7d6dacb1034a8f861ca5",
        "semantic_advantage": "3074f07df75f95b421d8871cb9f6448e130ad7d948b137b8",
        "compression_degradation": "46b15f1200c46251053ec3dfa806dbdf515eb34053a5e0d1",
        "comparative_failure": "462011b6f9beb976aaf7b38082bcf7d70a91c3c74d2c6e95",
    }
    for case in cases:
        if case["sample_id"] != expected_ids[case["category"]]:
            raise ValueError(
                f"Selection changed for {case['category']}: {case['sample_id']}"
            )
    return cases

def method_rows(data: dict[str, dict[str, dict]], sample_id: str) -> list[dict]:
    records = []
    for method, rows in data.items():
        row = rows[sample_id]
        if method == "Uncompressed":
            target_ratio = 1
            achieved_ratio = 1.0
        elif method.startswith("Head-tail"):
            target_ratio = 2 if method.endswith("2x") else 4
            achieved_ratio = row["prompt_compression_ratio"]
        else:
            target_ratio = row["target_compression_ratio"]
            achieved_ratio = row["compression_ratio"]
        records.append(
            {
                "method": method,
                "target_ratio": target_ratio,
                "achieved_ratio": achieved_ratio,
                "prompt_tokens": row["prompt_tokens"],
                "em": row["em"],
                "f1": row["f1"],
                "prediction": row["answer"],
                "num_compression_chunks": row.get("num_compression_chunks", ""),
            }
        )
    return records

def evidence_position(sample_id: str, phrase: str, samples: dict[str, dict]) -> float:
    document = samples[sample_id]["docs"]
    position = document.lower().find(phrase.lower())
    if position < 0:
        raise ValueError(f"Evidence phrase not found for sample {sample_id}: {phrase}")
    return position / len(document)

def write_csv(
    path: Path,
    cases: list[dict],
    data: dict[str, dict[str, dict]],
) -> None:
    fieldnames = [
        "case_category",
        "case_title",
        "selection_rule",
        "sample_id",
        "question",
        "gold_answer",
        "method",
        "target_ratio",
        "achieved_ratio",
        "prompt_tokens",
        "em",
        "f1",
        "prediction",
        "num_compression_chunks",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            sample_id = case["sample_id"]
            baseline = data["Uncompressed"][sample_id]
            for row in method_rows(data, sample_id):
                writer.writerow(
                    {
                        "case_category": case["category"],
                        "case_title": case["title"],
                        "selection_rule": case["rule"],
                        "sample_id": sample_id,
                        "question": baseline["question"],
                        "gold_answer": baseline["answers"][0],
                        **row,
                    }
                )

def write_markdown(
    path: Path,
    cases: list[dict],
    data: dict[str, dict[str, dict]],
    samples: dict[str, dict],
) -> None:
    lines = [
        "# Qualitative Success and Failure Cases",
        "",
        "This file is generated by `build_qualitative_cases.py` from the committed",
        "150-sample result JSON files. Run the following command from the repository",
        "root to reproduce both this report and its CSV source table:",
        "",
        "```bash",
        "python3 part3_llmlingua/build_qualitative_cases.py",
        "```",
        "",
        "The cases illustrate predefined patterns and do not replace the aggregate",
        "evaluation. Long predictions are shortened only in this Markdown preview;",
        "`qualitative_cases.csv` contains their complete text.",
        "",
        "## Selection rules",
        "",
    ]
    for number, case in enumerate(cases, start=1):
        lines.append(f"{number}. **{case['title']}:** {case['rule']}.")

    for number, case in enumerate(cases, start=1):
        sample_id = case["sample_id"]
        baseline = data["Uncompressed"][sample_id]
        position = evidence_position(
            sample_id, case["evidence_phrase"], samples
        )
        lines.extend(
            [
                "",
                f"## Case {number}: {case['title']}",
                "",
                f"**Sample id:** `{sample_id}`",
                "",
                f"**Question:** {baseline['question']}",
                "",
                f"**Gold answer:** {baseline['answers'][0]}",
                "",
                f"**First evidence position:** {position:.1%} of the original document",
                "",
                "| Method | Achieved ratio | Prompt tokens | Prediction | EM | F1 |",
                "| --- | ---: | ---: | --- | ---: | ---: |",
            ]
        )
        for row in method_rows(data, sample_id):
            lines.append(
                f"| {row['method']} | {row['achieved_ratio']:.2f}x | "
                f"{row['prompt_tokens']:,} | {shortened(row['prediction'])} | "
                f"{row['em']:.0f} | {row['f1']:.3f} |"
            )
        lines.extend(["", case["analysis"]])

    lines.extend(
        [
            "",
            "## Overall interpretation",
            "",
            "The examples show that LLMLingua is not uniformly worse. It can retain",
            "relevant evidence that positional truncation removes, but it can also",
            "delete precise details or preserve a plausible distractor. These cases",
            "help explain the aggregate F1 decrease from 0.2626 at the 2x setting to",
            "0.2207 at 4x. They do not establish a general algorithm ranking because",
            "296 of 300 LLMLingua rows required chunked compression in this",
            "resource-constrained reproduction.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    data = load_data()
    cases = select_cases(data)
    with (REPO_ROOT / "shared/samples.json").open(encoding="utf-8") as file:
        sample_rows = json.load(file)["samples"]
    samples = index_by_id(sample_rows)

    markdown_path = PART3_DIR / "qualitative_cases.md"
    csv_path = PART3_DIR / "qualitative_cases.csv"
    write_markdown(markdown_path, cases, data, samples)
    write_csv(csv_path, cases, data)

    for case in cases:
        print(f"{case['category']}: {case['sample_id']}")
    print(f"Created {markdown_path.relative_to(REPO_ROOT)}")
    print(f"Created {csv_path.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
