"""Combined 5-row results table + paired dF1 contrasts.

    python part2_truncation/make_table.py
    python part2_truncation/make_table.py --rerun-dir /content/drive/MyDrive/cisc7021/results_same_env
"""
import argparse
import csv
import json
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (name, relative path, LLMLingua target ratio or None)
DEFAULT_SOURCES = [
    ("Uncompressed", "part1_uncompressed/results_member1.json", None),
    ("Head-tail 2x", "part2_truncation/results_member2_2x.json", None),
    ("Head-tail 4x", "part2_truncation/results_member2_4x.json", None),
    ("LLMLingua 2x", "part3_llmlingua/results_member3.json", 2),
    ("LLMLingua 4x", "part3_llmlingua/results_member3.json", 4),
]
RERUN_FILES = {
    "Uncompressed": "results_member1.json",
    "Head-tail 2x": "results_member2_2x.json",
    "Head-tail 4x": "results_member2_4x.json",
    "LLMLingua 2x": "results_member3.json",
    "LLMLingua 4x": "results_member3.json",
}
CONTRASTS = [
    ("Uncompressed", "Head-tail 2x"),
    ("Uncompressed", "Head-tail 4x"),
    ("Uncompressed", "LLMLingua 2x"),
    ("Uncompressed", "LLMLingua 4x"),
    ("Head-tail 2x", "LLMLingua 2x"),
    ("Head-tail 4x", "LLMLingua 4x"),
]


def load_rows(path, ratio):
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)["results"]
    if ratio is not None:
        rows = [r for r in rows if int(r["target_compression_ratio"]) == ratio]
    return rows


def mean_of(rows, key):
    vals = [float(r[key]) for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def summarize(rows):
    f1 = [float(r["f1"]) for r in rows]
    return {
        "n": len(rows),
        "em_hits": int(round(sum(float(r["em"]) for r in rows))),
        "em": mean_of(rows, "em"),
        "f1": sum(f1) / len(f1),
        "f1_sd": st.stdev(f1) if len(f1) > 1 else 0.0,  # sample sd (n-1)
        "tokens": mean_of(rows, "prompt_tokens"),
        "comp_lat": mean_of(rows, "compression_latency"),
        "gen_lat": mean_of(rows, "generation_latency"),
        "total_lat": mean_of(rows, "total_latency"),
    }


def paired(rows_a, rows_b):
    fa = {str(r["id"]): float(r["f1"]) for r in rows_a}
    fb = {str(r["id"]): float(r["f1"]) for r in rows_b}
    ids = sorted(fa.keys() & fb.keys())
    diffs = [fb[i] - fa[i] for i in ids]
    n = len(diffs)
    mean = sum(diffs) / n
    se = st.stdev(diffs) / math.sqrt(n)
    lo, hi = mean - 1.96 * se, mean + 1.96 * se
    verdict = "Significant" if (lo > 0 or hi < 0) else "Not significant"
    return n, mean, lo, hi, verdict


def f(x, nd=4):
    return "-" if x is None else f"{x:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerun-dir", type=Path, default=None,
                    help="flat folder produced by run_all.py")
    ap.add_argument("--out", type=Path, default=ROOT / "results_same_machine" / "results_table.md")
    args = ap.parse_args()

    data = {}
    for name, rel, ratio in DEFAULT_SOURCES:
        path = (args.rerun_dir / RERUN_FILES[name]) if args.rerun_dir else (ROOT / rel)
        if not path.exists():
            print(f"[warn] missing: {path}")
            continue
        data[name] = load_rows(path, ratio)

    stats = {k: summarize(v) for k, v in data.items()}
    base_tokens = stats["Uncompressed"]["tokens"] if "Uncompressed" in stats else None

    head = ("| Method | n | EM hits | EM | F1 | F1 sd | Mean prompt tokens "
            "| Token reduction vs Part 1 | Compress lat (s) | Generate lat (s) | Total lat (s) |")
    lines = [head, "|" + "---|" * 11]
    csv_rows = []
    for name, s in stats.items():
        red = None if base_tokens is None else 1 - s["tokens"] / base_tokens
        red_txt = "-" if (red is None or name == "Uncompressed") else f"{red * 100:.1f}%"
        lines.append(
            f"| {name} | {s['n']} | {s['em_hits']} | {f(s['em'])} | {f(s['f1'])} | {f(s['f1_sd'])} "
            f"| {s['tokens']:.1f} | {red_txt} | {f(s['comp_lat'], 3)} | {f(s['gen_lat'], 2)} | {f(s['total_lat'], 2)} |")
        csv_rows.append({"method": name, **s, "token_reduction": red})

    lines += ["", "Paired F1 differences (second minus first, paired by id, 95% CI = mean +/- 1.96 SE):", "",
              "| Contrast | n paired | Mean dF1 | 95% CI | Verdict |", "|---|---:|---:|---|---|"]
    for a, b in CONTRASTS:
        if a in data and b in data:
            n, m, lo, hi, v = paired(data[a], data[b])
            lines.append(f"| {a} -> {b} | {n} | {m:+.4f} | [{lo:+.3f}, {hi:+.3f}] | {v} |")

    lines += ["", "Note: latencies come from the machine(s) that produced each file; "
              "compare them only within one part unless all files come from the same GPU."]

    table = "\n".join(lines)
    print(table)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(table + "\n", encoding="utf-8")
    csv_path = args.out.with_suffix(".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    print(f"\n[saved] {args.out} and {csv_path}")


if __name__ == "__main__":
    main()