"""Standalone Part 1-4 comparison table for Part 4.

    python part4_llmlingua_enhanced/make_table.py
    python part4_llmlingua_enhanced/make_table.py --rerun-dir results_same_machine

This script reads only the JSON result artifacts written by each part; it does
not import any Part 1-3 module and shares no state with them, so it keeps
working when those folders are edited or deleted. Parts whose file is absent are
skipped with a warning, which means the script already runs before Part 4 has
produced `results_member4.json`.
"""
import argparse
import csv
import json
import math
import statistics as st
from pathlib import Path

PART_DIR = Path(__file__).resolve().parent
ROOT = PART_DIR.parent

# (label, path when results live in their own part folder, path in a flat
# rerun folder, LLMLingua-style target ratio or None for a single-file result)
SOURCES = [
    ("Uncompressed", "part1_uncompressed/results_member1.json", "results_member1.json", None),
    ("Head-tail 2x", "part2_truncation/results_member2_2x.json", "results_member2_2x.json", None),
    ("Head-tail 4x", "part2_truncation/results_member2_4x.json", "results_member2_4x.json", None),
    ("LLMLingua 2x", "part3_llmlingua/results_member3.json", "results_member3.json", 2),
    ("LLMLingua 4x", "part3_llmlingua/results_member3.json", "results_member3.json", 4),
    ("LLMLingua-Enhanced 2x", "part4_llmlingua_enhanced/results_member4.json", "results_member4.json", 2),
    ("LLMLingua-Enhanced 4x", "part4_llmlingua_enhanced/results_member4.json", "results_member4.json", 4),
]
CONTRASTS = [
    ("Uncompressed", "Head-tail 2x"),
    ("Uncompressed", "Head-tail 4x"),
    ("Head-tail 2x", "LLMLingua 2x"),
    ("Head-tail 4x", "LLMLingua 4x"),
    ("LLMLingua 2x", "LLMLingua-Enhanced 2x"),
    ("LLMLingua 4x", "LLMLingua-Enhanced 4x"),
    ("Head-tail 2x", "LLMLingua-Enhanced 2x"),
    ("Head-tail 4x", "LLMLingua-Enhanced 4x"),
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


def chunked_count(rows):
    """Rows split into more than one compression chunk, or None if unknown."""
    chunks = [
        int(r["num_compression_chunks"])
        for r in rows
        if r.get("num_compression_chunks") is not None
    ]
    if not chunks:
        return None
    return sum(1 for c in chunks if c > 1)


def summarize(rows):
    f1 = [float(r["f1"]) for r in rows]
    return {
        "n": len(rows),
        "em_hits": int(round(sum(float(r["em"]) for r in rows))),
        "em": mean_of(rows, "em"),
        "f1": sum(f1) / len(f1),
        "f1_sd": st.stdev(f1) if len(f1) > 1 else 0.0,  # sample sd (n-1)
        "tokens": mean_of(rows, "prompt_tokens"),
        "chunked": chunked_count(rows),
        "comp_lat": mean_of(rows, "compression_latency"),
        "gen_lat": mean_of(rows, "generation_latency"),
        "total_lat": mean_of(rows, "total_latency"),
    }


def paired(rows_a, rows_b):
    fa = {str(r["id"]): float(r["f1"]) for r in rows_a}
    fb = {str(r["id"]): float(r["f1"]) for r in rows_b}
    ids = sorted(fa.keys() & fb.keys())
    if not ids:
        return 0, None, None, None, "no overlap"
    diffs = [fb[i] - fa[i] for i in ids]
    n = len(diffs)
    mean = sum(diffs) / n
    if n < 2:
        return n, mean, None, None, "n<2"
    se = st.stdev(diffs) / math.sqrt(n)
    lo, hi = mean - 1.96 * se, mean + 1.96 * se
    verdict = "Significant" if (lo > 0 or hi < 0) else "Not significant"
    return n, mean, lo, hi, verdict


def f(x, nd=4):
    return "-" if x is None else f"{x:.{nd}f}"


def build_table(data):
    stats = {k: summarize(v) for k, v in data.items()}
    base_tokens = stats["Uncompressed"]["tokens"] if "Uncompressed" in stats else None

    head = ("| Method | n | EM hits | EM | F1 | F1 sd | Mean prompt tokens "
            "| Token reduction vs Part 1 | Chunked count | Compress lat (s) "
            "| Generate lat (s) | Total lat (s) |")
    lines = [head, "|" + "---|" * 12]
    csv_rows = []
    for name, s in stats.items():
        red = None if base_tokens is None else 1 - s["tokens"] / base_tokens
        red_txt = "-" if (red is None or name == "Uncompressed") else f"{red * 100:.1f}%"
        chunk_txt = "-" if s["chunked"] is None else f"{s['chunked']}/{s['n']}"
        lines.append(
            f"| {name} | {s['n']} | {s['em_hits']} | {f(s['em'])} | {f(s['f1'])} "
            f"| {f(s['f1_sd'])} | {s['tokens']:.1f} | {red_txt} | {chunk_txt} "
            f"| {f(s['comp_lat'], 3)} | {f(s['gen_lat'], 2)} | {f(s['total_lat'], 2)} |")
        csv_rows.append({"method": name, **s, "token_reduction": red})

    lines += ["",
              "Paired F1 differences (second minus first, paired by id, "
              "95% CI = mean +/- 1.96 SE):", "",
              "| Contrast | n paired | Mean dF1 | 95% CI | Verdict |",
              "|---|---:|---:|---|---|"]
    for a, b in CONTRASTS:
        if a in data and b in data:
            n, m, lo, hi, v = paired(data[a], data[b])
            mean_txt = "-" if m is None else f"{m:+.4f}"
            ci = "-" if lo is None else f"[{lo:+.3f}, {hi:+.3f}]"
            lines.append(f"| {a} -> {b} | {n} | {mean_txt} | {ci} | {v} |")

    lines += ["",
              "Note: latencies come from the machine(s) that produced each file; "
              "compare them only within one part unless all files come from the "
              "same GPU."]
    return "\n".join(lines), csv_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rerun-dir", type=Path, default=None,
                    help="flat folder produced by run_all.py")
    ap.add_argument("--out", type=Path, default=PART_DIR / "results_table.md")
    args = ap.parse_args()

    data = {}
    for name, rel, flat, ratio in SOURCES:
        path = (args.rerun_dir / flat) if args.rerun_dir else (ROOT / rel)
        if not path.exists():
            print(f"[warn] missing: {path}")
            continue
        data[name] = load_rows(path, ratio)

    if not data:
        print("[error] no result files found")
        return 1

    table, csv_rows = build_table(data)
    print(table)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(table + "\n", encoding="utf-8")
    csv_path = args.out.with_suffix(".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\n[saved] {args.out} and {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
