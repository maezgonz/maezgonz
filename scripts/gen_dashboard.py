"""Generate profile dashboard image for GitHub profile README.

Runs in CI (no display needed). Reads benchmark data from this repo's
metrics file and renders the dashboard PNG. The workflow in
.github/workflows/dashboard.yml commits the result back to main.
"""

from __future__ import annotations

import json
import os
import sys

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


def load_metrics() -> dict:
    """Load benchmark metrics from metrics.json (or defaults)."""
    metrics_path = os.path.join(HERE, "..", "metrics.json")
    defaults = {
        "strong_scaling_speedup": "25.2×",
        "strong_scaling_note": "64 cores, FT3",
        "gbm_throughput": "2.66M/s",
        "gbm_note": "C + OpenMP, 10⁹ paths",
        "infiniband_rtt": "2.8 µs",
        "infiniband_rtt_note": "MPI ping-pong, 2 nodes",
        "infiniband_bw": "12.2 GB/s",
        "infiniband_bw_note": "8 MiB messages",
        "gpu_cpu": "310s / 867s / 135s",
        "gpu_cpu_note": "CPU / GPU naive / GPU cuDNN",
        "repos": [
            "hpc-parallel-algorithms     C / MPI / OpenMP / Slurm",
            "quant-trading-models       Python / Monte Carlo / B-S",
            "quant-research-lab         Python / ML / GPU benchmarks",
            "telco-network-automation   Python / fleet probing",
            "telco-engineering-handbook 7 docs / live website",
            "radiolink-clearance        ITU-R P.530 / Fresnel zones",
        ],
        "career_stages": [
            (0.05, "Electrical\n2009-11", A2),
            (0.18, "RAN Eng.\n2012-15", A1),
            (0.31, "Core Net\n2015-17", A4),
            (0.44, "RAN Systems\n2017-21", A3),
            (0.57, "5G / O-RAN\n2021-26", A1),
            (0.73, "MSc HPC\n2026-27", A2),
        ],
    }
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    return defaults


def render(metrics: dict) -> None:
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
    fig.text(0.755, 0.49, "Portfolio — 8 public repos, all CI green", ha="center", va="center",
             fontsize=11, color=FG, fontweight="bold", transform=fig.transFigure, zorder=2)

    for j, line in enumerate(metrics["repos"]):
        fig.text(0.56, 0.45 - j * 0.023, line, ha="left", va="center", fontsize=9, color=MUTED,
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

    out = os.path.abspath(OUT)
    fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    print(f"saved {out}")


if __name__ == "__main__":
    render(load_metrics())
    sys.exit(0)
