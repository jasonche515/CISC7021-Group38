#!/usr/bin/env python3
"""Plot the accuracy--compression trade-off for all three project methods.

The values are loaded directly from the committed result JSON files.  Running
this script creates both a high-resolution PNG and a vector PDF in figures/.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "figures"

# Keep Matplotlib's cache outside the repository on machines where the default
# user cache directory is not writable (for example, a managed lab machine).
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cisc7021-matplotlib")
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load_json(relative_path: str) -> dict:
    path = REPO_ROOT / relative_path
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_points() -> dict[str, list[dict[str, float | str]]]:
    baseline = load_json("part1_uncompressed/results_member1.json")
    truncation_2x = load_json("part2_truncation/results_member2_2x.json")
    truncation_4x = load_json("part2_truncation/results_member2_4x.json")
    llmlingua = load_json("part3_llmlingua/results_member3.json")

    baseline_summary = baseline["summary"]
    truncation_2x_summary = truncation_2x["summary"]
    truncation_4x_summary = truncation_4x["summary"]
    llmlingua_2x_summary = llmlingua["summary"]["2x"]
    llmlingua_4x_summary = llmlingua["summary"]["4x"]

    sample_counts = {
        baseline_summary["num_samples"],
        truncation_2x_summary["num_samples"],
        truncation_4x_summary["num_samples"],
        llmlingua_2x_summary["num_samples"],
        llmlingua_4x_summary["num_samples"],
    }
    if sample_counts != {150}:
        raise ValueError(f"Expected 150 samples for every setting, got {sample_counts}")

    uncompressed = {
        "label": "Uncompressed",
        "ratio": 1.0,
        "f1": baseline_summary["mean_f1"],
        "tokens": baseline_summary["mean_prompt_tokens"],
    }

    return {
        "Head-and-tail truncation": [
            uncompressed,
            {
                "label": "2x target",
                "ratio": truncation_2x_summary["mean_prompt_compression_ratio"],
                "f1": truncation_2x_summary["mean_f1"],
                "tokens": truncation_2x_summary["mean_prompt_tokens"],
            },
            {
                "label": "4x target",
                "ratio": truncation_4x_summary["mean_prompt_compression_ratio"],
                "f1": truncation_4x_summary["mean_f1"],
                "tokens": truncation_4x_summary["mean_prompt_tokens"],
            },
        ],
        "LLMLingua": [
            uncompressed,
            {
                "label": "2x target",
                "ratio": llmlingua_2x_summary["mean_achieved_compression_ratio"],
                "f1": llmlingua_2x_summary["mean_f1"],
                "tokens": llmlingua_2x_summary["mean_prompt_tokens"],
            },
            {
                "label": "4x target",
                "ratio": llmlingua_4x_summary["mean_achieved_compression_ratio"],
                "f1": llmlingua_4x_summary["mean_f1"],
                "tokens": llmlingua_4x_summary["mean_prompt_tokens"],
            },
        ],
    }


def make_figure(points: dict[str, list[dict[str, float | str]]]) -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.titlesize": 14,
            "legend.fontsize": 10,
        }
    )

    figure, axis = plt.subplots(figsize=(8.2, 5.2), constrained_layout=True)
    styles = {
        "Head-and-tail truncation": {"color": "#2878B5", "marker": "o"},
        "LLMLingua": {"color": "#E07A2D", "marker": "s"},
    }

    for method, method_points in points.items():
        ratios = [float(point["ratio"]) for point in method_points]
        scores = [float(point["f1"]) for point in method_points]
        style = styles[method]
        axis.plot(
            ratios,
            scores,
            label=method,
            color=style["color"],
            marker=style["marker"],
            linewidth=2.3,
            markersize=7.5,
            markeredgecolor="white",
            markeredgewidth=0.9,
            zorder=3,
        )

    # Draw and label the common uncompressed reference only once.
    baseline = points["Head-and-tail truncation"][0]
    axis.scatter(
        [float(baseline["ratio"])],
        [float(baseline["f1"])],
        s=92,
        color="#4A4A4A",
        edgecolor="white",
        linewidth=1.0,
        zorder=5,
    )
    axis.annotate(
        f"Uncompressed\nF1 = {float(baseline['f1']):.3f}",
        (float(baseline["ratio"]), float(baseline["f1"])),
        xytext=(11, -3),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9.5,
        fontweight="bold",
        color="#333333",
    )

    annotation_offsets = {
        ("Head-and-tail truncation", 1): (0, 13),
        ("Head-and-tail truncation", 2): (-2, 13),
        ("LLMLingua", 1): (0, -30),
        ("LLMLingua", 2): (0, -30),
    }
    for method, method_points in points.items():
        for index, point in enumerate(method_points[1:], start=1):
            ratio = float(point["ratio"])
            f1 = float(point["f1"])
            tokens = float(point["tokens"])
            axis.annotate(
                f"{ratio:.2f}x, F1 {f1:.3f}\n{tokens:,.0f} tokens",
                (ratio, f1),
                xytext=annotation_offsets[(method, index)],
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.8,
                color=styles[method]["color"],
            )

    axis.set_title("Accuracy–Compression Trade-off on Long-Context QA", pad=13)
    axis.set_xlabel("Achieved whole-prompt compression ratio (x)")
    axis.set_ylabel("Token-level F1 (higher is better)")
    axis.set_xlim(0.8, 4.05)
    axis.set_ylim(0.18, 0.47)
    axis.set_xticks([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
    axis.grid(True, color="#D9DEE5", linewidth=0.8, alpha=0.85)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.legend(loc="lower left", frameon=True, framealpha=0.95)
    axis.text(
        0.995,
        0.015,
        "LongBench multifieldqa_en | Llama-3.2-3B-Instruct | n = 150",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        color="#5A5A5A",
    )

    return figure


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    points = load_points()
    figure = make_figure(points)

    png_path = OUTPUT_DIR / "accuracy_compression_tradeoff.png"
    pdf_path = OUTPUT_DIR / "accuracy_compression_tradeoff.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)

    print(f"Created {png_path.relative_to(REPO_ROOT)}")
    print(f"Created {pdf_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
