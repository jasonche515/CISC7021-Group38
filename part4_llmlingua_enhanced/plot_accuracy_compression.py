#!/usr/bin/env python3
"""Plot the accuracy--compression trade-off for all four project parts.

This is the Part 4 replacement for ``part3_llmlingua/plot_accuracy_compression.py``.
It reads the four committed result files (Parts 1--4) and writes the canonical
figure to ``figures/``.  The Part 3 script is kept as Member 3's own record and
still produces the three-part version, so re-run *this* script when the figure
has to include Part 4.

Usage:
    python plot_accuracy_compression.py
    python plot_accuracy_compression.py --out-dir /tmp/figures   # preview
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "figures"

# Keep Matplotlib's cache outside the repository on machines where the default
# user cache directory is not writable (for example, a managed lab machine).
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cisc7021-matplotlib")
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

SOURCES = {
    "baseline": "part1_uncompressed/results_member1.json",
    "head_tail_2x": "part2_truncation/results_member2_2x.json",
    "head_tail_4x": "part2_truncation/results_member2_4x.json",
    "llmlingua": "part3_llmlingua/results_member3.json",
    "enhanced": "part4_llmlingua_enhanced/results_member4.json",
}

EXPECTED_SAMPLES = 150

STYLES = {
    "Head-and-tail truncation": {"color": "#2878B5", "marker": "o"},
    "LLMLingua (Part 3, 98.7% chunked)": {"color": "#E07A2D", "marker": "s"},
    "LLMLingua-Enhanced (Part 4, 0% chunked)": {"color": "#1F7A5A", "marker": "^"},
}
BASELINE_COLOR = "#4A4A4A"


def load_json(relative_path: str) -> dict:
    path = REPO_ROOT / relative_path
    if not path.is_file():
        raise SystemExit(f"Missing result file: {path}")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def summary_of(payload: dict, ratio: str | None = None) -> dict:
    """Return the flat summary for single-ratio files or one nested ratio."""
    if ratio is None:
        return payload["summary"]
    return payload["summary"][ratio]


def load_points() -> dict[str, list[dict[str, float | str]]]:
    baseline = summary_of(load_json(SOURCES["baseline"]))
    head_tail_2x = summary_of(load_json(SOURCES["head_tail_2x"]))
    head_tail_4x = summary_of(load_json(SOURCES["head_tail_4x"]))
    llmlingua_2x = summary_of(load_json(SOURCES["llmlingua"]), "2x")
    llmlingua_4x = summary_of(load_json(SOURCES["llmlingua"]), "4x")
    enhanced_2x = summary_of(load_json(SOURCES["enhanced"]), "2x")
    enhanced_4x = summary_of(load_json(SOURCES["enhanced"]), "4x")

    sample_counts = {
        summary["num_samples"]
        for summary in (
            baseline,
            head_tail_2x,
            head_tail_4x,
            llmlingua_2x,
            llmlingua_4x,
            enhanced_2x,
            enhanced_4x,
        )
    }
    if sample_counts != {EXPECTED_SAMPLES}:
        raise SystemExit(
            f"Expected {EXPECTED_SAMPLES} samples for every setting, got {sample_counts}"
        )

    uncompressed = {
        "label": "Uncompressed",
        "ratio": 1.0,
        "f1": baseline["mean_f1"],
        "tokens": baseline["mean_prompt_tokens"],
    }

    return {
        "baseline": [uncompressed],
        "Head-and-tail truncation": [
            uncompressed,
            {
                "label": "2x target",
                "ratio": head_tail_2x["mean_prompt_compression_ratio"],
                "f1": head_tail_2x["mean_f1"],
                "tokens": head_tail_2x["mean_prompt_tokens"],
            },
            {
                "label": "4x target",
                "ratio": head_tail_4x["mean_prompt_compression_ratio"],
                "f1": head_tail_4x["mean_f1"],
                "tokens": head_tail_4x["mean_prompt_tokens"],
            },
        ],
        "LLMLingua (Part 3, 98.7% chunked)": [
            uncompressed,
            {
                "label": "2x target",
                "ratio": llmlingua_2x["mean_achieved_compression_ratio"],
                "f1": llmlingua_2x["mean_f1"],
                "tokens": llmlingua_2x["mean_prompt_tokens"],
            },
            {
                "label": "4x target",
                "ratio": llmlingua_4x["mean_achieved_compression_ratio"],
                "f1": llmlingua_4x["mean_f1"],
                "tokens": llmlingua_4x["mean_prompt_tokens"],
            },
        ],
        "LLMLingua-Enhanced (Part 4, 0% chunked)": [
            uncompressed,
            {
                "label": "2x target",
                "ratio": enhanced_2x["mean_achieved_compression_ratio"],
                "f1": enhanced_2x["mean_f1"],
                "tokens": enhanced_2x["mean_prompt_tokens"],
            },
            {
                "label": "4x target",
                "ratio": enhanced_4x["mean_achieved_compression_ratio"],
                "f1": enhanced_4x["mean_f1"],
                "tokens": enhanced_4x["mean_prompt_tokens"],
            },
        ],
    }


# Hand-tuned offsets keep the seven labels clear of each other and of the lines.
ANNOTATION_OFFSETS = {
    ("Head-and-tail truncation", 1): (10, 16),
    ("Head-and-tail truncation", 2): (0, 14),
    ("LLMLingua (Part 3, 98.7% chunked)", 1): (0, -13),
    ("LLMLingua (Part 3, 98.7% chunked)", 2): (-9, -12),
    ("LLMLingua-Enhanced (Part 4, 0% chunked)", 1): (13, 9),
    ("LLMLingua-Enhanced (Part 4, 0% chunked)", 2): (-8, 16),
}
ANNOTATION_ALIGNMENTS = {
    ("Head-and-tail truncation", 1): ("left", "bottom"),
    ("Head-and-tail truncation", 2): ("center", "bottom"),
    ("LLMLingua (Part 3, 98.7% chunked)", 1): ("center", "top"),
    ("LLMLingua (Part 3, 98.7% chunked)", 2): ("right", "top"),
    ("LLMLingua-Enhanced (Part 4, 0% chunked)", 1): ("left", "bottom"),
    ("LLMLingua-Enhanced (Part 4, 0% chunked)", 2): ("right", "bottom"),
}


def make_figure(points: dict[str, list[dict[str, float | str]]]) -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.titlesize": 14,
            "legend.fontsize": 9.2,
        }
    )

    figure, axis = plt.subplots(figsize=(8.6, 5.4), constrained_layout=True)

    for method, style in STYLES.items():
        method_points = points[method]
        axis.plot(
            [float(point["ratio"]) for point in method_points],
            [float(point["f1"]) for point in method_points],
            label=method,
            color=style["color"],
            marker=style["marker"],
            linewidth=2.3,
            markersize=7.5,
            markeredgecolor="white",
            markeredgewidth=0.9,
            zorder=3,
        )

    # The uncompressed reference is shared by every series; draw it once.
    baseline = points["baseline"][0]
    baseline_x = float(baseline["ratio"])
    baseline_y = float(baseline["f1"])
    axis.scatter(
        [baseline_x],
        [baseline_y],
        s=92,
        color=BASELINE_COLOR,
        edgecolor="white",
        linewidth=1.0,
        zorder=5,
    )
    axis.annotate(
        f"Uncompressed\nF1 {baseline_y:.3f} · {float(baseline['tokens']):,.0f} tok",
        (baseline_x, baseline_y),
        xytext=(9, 9),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=8.8,
        fontweight="bold",
        color="#333333",
    )

    for method, style in STYLES.items():
        for index, point in enumerate(points[method][1:], start=1):
            ratio = float(point["ratio"])
            f1 = float(point["f1"])
            tokens = float(point["tokens"])
            horizontal, vertical = ANNOTATION_ALIGNMENTS[(method, index)]
            axis.annotate(
                f"{ratio:.2f}x · F1 {f1:.3f}\n{tokens:,.0f} tokens",
                (ratio, f1),
                xytext=ANNOTATION_OFFSETS[(method, index)],
                textcoords="offset points",
                ha=horizontal,
                va=vertical,
                fontsize=8.6,
                color=style["color"],
            )

    axis.set_title("Accuracy–Compression Trade-off on Long-Context QA", pad=28)
    axis.set_xlabel("Achieved whole-prompt compression ratio (x)")
    axis.set_ylabel("Token-level F1 (higher is better)")
    axis.set_xlim(0.85, 4.45)
    axis.set_ylim(0.183, 0.478)
    axis.set_xticks([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
    axis.grid(True, color="#D9DEE5", linewidth=0.8, alpha=0.85)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.text(
        0.5,
        1.012,
        "LongBench multifieldqa_en | Llama-3.2-3B-Instruct | n = 150 | per-part runs",
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.8,
        color="#5A5A5A",
    )
    axis.legend(
        handles=[
            Line2D(
                [0],
                [0],
                linestyle="none",
                marker="o",
                markersize=7.5,
                markerfacecolor=BASELINE_COLOR,
                markeredgecolor="white",
                label="Uncompressed (Part 1)",
            )
        ]
        + [
            Line2D(
                [0],
                [0],
                color=style["color"],
                marker=style["marker"],
                linewidth=2.3,
                markersize=7.5,
                markeredgecolor="white",
                label=method,
            )
            for method, style in STYLES.items()
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.11),
        ncol=2,
        frameon=False,
        columnspacing=2.4,
    )

    return figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the PNG and PDF (default: figures/)",
    )
    parser.add_argument("--dpi", type=int, default=300, help="PNG resolution")
    args = parser.parse_args()

    points = load_points()

    for method in STYLES:
        for point in points[method][1:]:
            print(
                f"{method:<44} {float(point['ratio']):.3f}x  "
                f"F1 {float(point['f1']):.4f}  {float(point['tokens']):>8,.0f} tok"
            )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    figure = make_figure(points)

    png_path = args.out_dir / "accuracy_compression_tradeoff.png"
    pdf_path = args.out_dir / "accuracy_compression_tradeoff.pdf"
    figure.savefig(png_path, dpi=args.dpi, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)

    print(f"\nCreated {png_path}")
    print(f"Created {pdf_path}")


if __name__ == "__main__":
    main()
