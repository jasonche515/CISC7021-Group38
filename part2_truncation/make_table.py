"""Print / save a Markdown comparison table from the result files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "Uncompressed": "part1_uncompressed/results_member1.json",
    "Head-tail 2x": "part2_truncation/results_member2_2x.json",
    "Head-tail 4x": "part2_truncation/results_member2_4x.json",
}
KEYS = [
    "num_samples", "mean_em", "mean_f1", "mean_prompt_tokens",
    "mean_compression_ratio", "mean_compression_latency",
    "mean_generation_latency", "mean_total_latency",
]


def fmt(value):
    return "-" if value is None else f"{value:.4g}"


lines = [
    "| method | " + " | ".join(KEYS) + " |",
    "|" + "---|" * (len(KEYS) + 1),
]
for name, rel in FILES.items():
    path = ROOT / rel
    if not path.exists():
        lines.append(f"| {name} | (file not found: {rel}) |")
        continue
    with open(path, encoding="utf-8") as f:
        summary = json.load(f)["summary"]
    lines.append(f"| {name} | " + " | ".join(fmt(summary.get(k)) for k in KEYS) + " |")

table = "\n".join(lines)
print(table)
(ROOT / "part2_truncation" / "results_table.md").write_text(table + "\n", encoding="utf-8")