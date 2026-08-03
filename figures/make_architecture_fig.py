"""
Regenerates figures/architecture.png — the HybridCloudSim component diagram.

Usage (from repo root):
    python figures/make_architecture_fig.py

Emits both PNG (400 dpi, for drafts) and PDF (vector, preferred for camera-ready).
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ----------------------------------------------------------------------
# Print-oriented styling: serif to match manuscript body text, muted fills
# that stay legible when the figure is reproduced in greyscale.
# ----------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "text.usetex": False,
})

INK = "#1A1A1A"
MUTE = "#5A5A5A"
RULE = "#7A7A7A"
FILL_ROOT = "#DCE7EF"
FILL_PLAIN = "#F2F2F2"
FILL_QPU = "#CFE0EC"
FILL_CPU = "#EFE2CC"
EDGE_ROOT = "#2E6B8F"
EDGE_QPU = "#2E6B8F"
EDGE_CPU = "#8A6224"

FS_TITLE = 8.6
FS_SUB = 6.9
FS_LABEL = 6.4
FS_HEAD = 7.4


def box(ax, cx, cy, w, h, title, sub=None, fill=FILL_PLAIN, edge=RULE, lw=0.8):
    """Rounded box centred on (cx, cy), with a title and optional caption line."""
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0,rounding_size=0.012",
        linewidth=lw, edgecolor=edge, facecolor=fill,
        mutation_aspect=1.0, zorder=2,
    ))
    if sub:
        ax.text(cx, cy + h * 0.16, title, ha="center", va="center",
                fontsize=FS_TITLE, color=INK, zorder=3)
        ax.text(cx, cy - h * 0.22, sub, ha="center", va="center",
                fontsize=FS_SUB, color=MUTE, style="italic", zorder=3)
    else:
        ax.text(cx, cy, title, ha="center", va="center",
                fontsize=FS_TITLE, color=INK, zorder=3)


def _seg(ax, p0, p1, dashed=False, head=True):
    ax.add_patch(FancyArrowPatch(
        p0, p1,
        arrowstyle="-|>" if head else "-", mutation_scale=7,
        linewidth=0.8, color=RULE, zorder=1,
        linestyle=(0, (2.5, 2)) if dashed else "solid",
        shrinkA=0, shrinkB=0,
    ))


def arrow(ax, x, y0, y1, label=None, dashed=False):
    """Vertical arrow from y0 down to y1, with an optional side label."""
    _seg(ax, (x, y0), (x, y1), dashed)
    if label:
        ax.text(x + 0.012, (y0 + y1) / 2, label, ha="left", va="center",
                fontsize=FS_LABEL, color=MUTE, zorder=3)


def harrow(ax, x0, x1, y, label=None, dashed=False):
    """Horizontal arrow, label centred above it."""
    _seg(ax, (x0, y), (x1, y), dashed)
    if label:
        ax.text((x0 + x1) / 2, y + 0.022, label, ha="center", va="bottom",
                fontsize=FS_LABEL, color=MUTE, zorder=3)


def fork(ax, x, y0, y_bus, targets, y1, label=None):
    """One source dropping to a bus line, then branching into several targets."""
    _seg(ax, (x, y0), (x, y_bus), head=False)
    _seg(ax, (min(targets), y_bus), (max(targets), y_bus), head=False)
    for tx in targets:
        _seg(ax, (tx, y_bus), (tx, y1))
    if label:
        ax.text(x + 0.012, (y0 + y_bus) / 2, label, ha="left", va="center",
                fontsize=FS_LABEL, color=MUTE, zorder=3)


def build():
    fig, ax = plt.subplots(figsize=(7.0, 4.15))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.01, 1)
    ax.axis("off")

    left, right = 0.25, 0.76
    bw, bh = 0.36, 0.105
    lx1, rx0 = left + bw / 2, right - bw / 2          # facing edges of the columns

    # rows
    r1, r2, r3, r4 = 0.700, 0.495, 0.280, 0.085

    # --- composition root -------------------------------------------------
    box(ax, 0.5, 0.940, 0.62, 0.108,
        "HybridCloudSimEnv",
        "subclasses simpy.Environment  ·  owns the clock and cost configuration",
        fill=FILL_ROOT, edge=EDGE_ROOT, lw=1.1)

    # branch from root down into the two paths
    _seg(ax, (0.5, 0.886), (0.5, 0.858), head=False)
    _seg(ax, (left, 0.858), (right, 0.858), head=False)
    arrow(ax, left, 0.858, 0.828)
    arrow(ax, right, 0.858, 0.828)

    ax.text(left, 0.800, "EXECUTION PATH", ha="center", va="center",
            fontsize=FS_HEAD, color=INK)
    ax.text(right, 0.800, "OBSERVATION PATH", ha="center", va="center",
            fontsize=FS_HEAD, color=INK)

    # --- execution path ---------------------------------------------------
    box(ax, left, r1, bw, bh, "JobGenerator",
        "replays a batch file, or synthesizes arrivals")
    arrow(ax, left, r1 - bh / 2, r2 + bh / 2, "one process per job")
    box(ax, left, r2, bw, bh, "HybridBroker",
        "places jobs  ·  drives the iteration loop")

    qpu_cx, cpu_cx, pw = left - 0.093, left + 0.093, 0.175
    fork(ax, left, r2 - bh / 2, r3 + bh / 2 + 0.055,
         (qpu_cx, cpu_cx), r3 + bh / 2, "acquires capacity")
    box(ax, qpu_cx, r3, pw, bh, "QPU pool", "qubits + topology",
        fill=FILL_QPU, edge=EDGE_QPU)
    box(ax, cpu_cx, r3, pw, bh, "CPU pool", "cores + memory BW",
        fill=FILL_CPU, edge=EDGE_CPU)

    # --- observation path -------------------------------------------------
    box(ax, right, r2, bw, bh, "JobRecordsManager",
        "per-job timestamps, energy, cost")
    box(ax, right, r3, bw, bh, "EventBus",
        "device start / finish")
    arrow(ax, right, r3 - bh / 2, r4 + bh / 2, "subscribes")
    box(ax, right, r4, bw, bh, "CloudMonitor",
        "integrates utilization  ·  fleet power")

    # telemetry links, dashed: they observe, they never steer scheduling
    harrow(ax, lx1, rx0, r2, "stamps phases", dashed=True)
    harrow(ax, cpu_cx + pw / 2, rx0, r3, "publishes", dashed=True)

    fig.tight_layout(pad=0.25)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    png = os.path.join(out_dir, "architecture.png")
    pdf = os.path.join(out_dir, "architecture.pdf")
    fig.savefig(png, dpi=400, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, pdf


if __name__ == "__main__":
    for p in build():
        print("wrote", p)
