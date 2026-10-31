"""Generate profile dashboard image for GitHub profile README.

Runs in CI (no display needed). Reads benchmark data from this repo's
metrics file and renders the dashboard PNG. The workflow in
.github/workflows/dashboard.yml commits the result back to main.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import re
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
BORDER = "#30363d"
A1 = "#4C9AFF"
A2 = "#FF7A59"
A3 = "#9ECB45"
A4 = "#D2A8FF"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "profile_dashboard.png")
METRICS_PATH = os.path.join(HERE, "..", "metrics.json")

REQUIRED_STRING_KEYS = [
    "strong_scaling_speedup",
    "strong_scaling_note",
    "gbm_throughput",
    "gbm_note",
    "infiniband_rtt",
    "infiniband_rtt_note",
    "infiniband_bw",
    "infiniband_bw_note",
    "gpu_cpu",
    "gpu_cpu_note",
]


def validate_metrics(metrics: dict, metrics_path: str) -> None:
    """Validate metrics.json structure and required value formats."""
    if not isinstance(metrics, dict):
        raise ValueError(f"{metrics_path} must contain a JSON object at the top level.")

    missing = [key for key in REQUIRED_STRING_KEYS if key not in metrics]
    if missing:
        raise ValueError(f"Missing required keys in {metrics_path}: {', '.join(missing)}")

    for key in REQUIRED_STRING_KEYS:
        if not isinstance(metrics[key], str) or not metrics[key].strip():
            raise ValueError(f"Key '{key}' in {metrics_path} must be a non-empty string.")

    gpu_parts = metrics["gpu_cpu"].split(" / ")
    if len(gpu_parts) != 3 or any(not re.fullmatch(r"\d+s", part) for part in gpu_parts):
        raise ValueError(
            "Key 'gpu_cpu' must have format '310s / 867s / 135s' (three integer-second values)."
        )

    repos = metrics.get("repos")
    if not isinstance(repos, list) or not repos:
        raise ValueError(f"Key 'repos' in {metrics_path} must be a non-empty list of strings.")
    if any(not isinstance(repo, str) or not repo.strip() for repo in repos):
        raise ValueError(f"Every entry in 'repos' in {metrics_path} must be a non-empty string.")

    career_stages = metrics.get("career_stages")
    if not isinstance(career_stages, list) or not career_stages:
        raise ValueError(f"Key 'career_stages' in {metrics_path} must be a non-empty list.")

    for i, stage in enumerate(career_stages):
        if not isinstance(stage, list) or len(stage) != 3:
            raise ValueError(
                f"career_stages[{i}] must be a list with three elements: [position, label, color]."
            )
        position, label, color = stage
        if not isinstance(position, (int, float)) or not (0 <= float(position) <= 1):
            raise ValueError(f"career_stages[{i}][0] must be a number between 0 and 1.")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"career_stages[{i}][1] must be a non-empty string.")
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError(f"career_stages[{i}][2] must be a hex color like '#4C9AFF'.")


def load_metrics() -> dict:
    """Load benchmark metrics from metrics.json and validate them."""
    if not os.path.exists(METRICS_PATH):
        raise FileNotFoundError(f"Required metrics file not found: {METRICS_PATH}")

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    validate_metrics(metrics, METRICS_PATH)
    return metrics


def render(metrics: dict, output_path: str = OUT) -> None:
    """Render the dashboard PNG."""
    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=BG)

    fig.text(0.5, 0.96, "MATIAS GONZALEZ", ha="center", va="center",
             fontsize=24, color=FG, fontweight="bold")
    fig.text(0.5, 0.91, "Systems Engineer → HPC & Quantitative Analysis  ·  17 yrs infra  ·  MSc HPC @ USC",
             ha="center", va="center", fontsize=13, color=MUTED)

    cards = [
        (metrics["strong_scaling_speedup"], metrics["strong_scaling_note"], A1),
        (metrics["gbm_throughput"], metrics["gbm_note"], A2),
        (metrics["infiniband_rtt"], metrics["infiniband_rtt_note"], A3),
        (metrics["infiniband_bw"], metrics["infiniband_bw_note"], A4),
    ]
    for i, (big, label, color) in enumerate(cards):
        x = 0.02 + i * 0.245
        rect = plt.Rectangle((x, 0.62), 0.22, 0.22, facecolor="#161b22",
                              edgecolor=BORDER, linewidth=1, transform=fig.transFigure, zorder=1)
        fig.add_artist(rect)
        fig.text(x + 0.11, 0.76, big, ha="center", va="center", fontsize=32, color=color,
                 fontweight="bold", transform=fig.transFigure, zorder=2)
        fig.text(x + 0.11, 0.66, label, ha="center", va="center", fontsize=10, color=MUTED,
                 transform=fig.transFigure, zorder=2)

    rect2 = plt.Rectangle((0.02, 0.28), 0.47, 0.26, facecolor="#161b22",
                          edgecolor=BORDER, linewidth=1, transform=fig.transFigure, zorder=1)
    fig.add_artist(rect2)
    fig.text(0.255, 0.49, "GPU vs CPU — LSTM on A100 (FinisTerrae-3)", ha="center", va="center",
             fontsize=11, color=FG, fontweight="bold", transform=fig.transFigure, zorder=2)

    gpu_parts = metrics["gpu_cpu"].split(" / ")
    gpu_labels = ["CPU\n32 cores", "GPU A100\n(naive)", "GPU A100\n(cuDNN)"]
    gpu_colors = [A1, A2, A3]
    for i, (label, color) in enumerate(zip(gpu_labels, gpu_colors)):
        bx = 0.08 + i * 0.14
        val = int(gpu_parts[i].rstrip("s")) if i < len(gpu_parts) else 0
        h = (val / 900) * 0.14
        bar = plt.Rectangle((bx, 0.32), 0.06, h, facecolor=color, edgecolor="none",
                            alpha=0.85, transform=fig.transFigure, zorder=2)
        fig.add_artist(bar)
        fig.text(bx + 0.03, 0.32 + h + 0.01, f"{val}s", ha="center", va="bottom", fontsize=11,
                 color=FG, fontweight="bold", transform=fig.transFigure, zorder=2)
        fig.text(bx + 0.03, 0.30, label, ha="center", va="top", fontsize=8, color=MUTED,
                 transform=fig.transFigure, zorder=2)

    rect3 = plt.Rectangle((0.53, 0.28), 0.45, 0.26, facecolor="#161b22",
                          edgecolor=BORDER, linewidth=1, transform=fig.transFigure, zorder=1)
    fig.add_artist(rect3)
    fig.text(0.755, 0.49, f"Portfolio — {len(metrics['repos'])} selected repos", ha="center", va="center",
             fontsize=11, color=FG, fontweight="bold", transform=fig.transFigure, zorder=2)

    for j, line in enumerate(metrics["repos"]):
        fig.text(0.56, 0.45 - j * 0.022, line, ha="left", va="center", fontsize=8.5, color=MUTED,
                 family="monospace", transform=fig.transFigure, zorder=2)

    fig.text(0.5, 0.22, "CAREER TIMELINE", ha="center", va="center", fontsize=10, color=FG,
             fontweight="bold", transform=fig.transFigure)

    for x, label, color in metrics["career_stages"]:
        w = 0.11
        rect = plt.Rectangle((x, 0.06), w, 0.07, facecolor=color, edgecolor="none",
                              alpha=0.3, transform=fig.transFigure, zorder=1)
        fig.add_artist(rect)
        fig.text(x + w / 2, 0.095, label, ha="center", va="center", fontsize=8, color=FG,
                 transform=fig.transFigure, zorder=2)

    fig.text(0.87, 0.095, "→ HPC & Quant", ha="left", va="center", fontsize=11, color=A2,
             fontweight="bold", transform=fig.transFigure)

    out = os.path.abspath(output_path)
    fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    print(f"saved {out}")


def check_dashboard_is_up_to_date(metrics: dict) -> None:
    """Render to a temp file and fail if committed dashboard is stale."""
    committed = os.path.abspath(OUT)
    if not os.path.exists(committed):
        raise FileNotFoundError(f"Committed dashboard file not found: {committed}")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        render(metrics, output_path=tmp_path)
        if not filecmp.cmp(committed, tmp_path, shallow=False):
            raise ValueError(
                "profile_dashboard.png is outdated. Run 'python scripts/gen_dashboard.py' and commit changes."
            )
        print("dashboard is up to date")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or verify profile dashboard image.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate metrics and verify committed profile_dashboard.png is up to date.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    loaded_metrics = load_metrics()
    if args.check:
        check_dashboard_is_up_to_date(loaded_metrics)
    else:
        render(loaded_metrics)
    sys.exit(0)
