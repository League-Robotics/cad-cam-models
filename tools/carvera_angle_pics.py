#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Dimensioned drawing of the aluminium angle on the Carvera (scad/carvera_angle.scad).

    uv run tools/carvera_angle_pics.py   ->  view/carvera_angle.png

Each leg face-on with the corner along the bottom, the measured numbers (to
the near side of each hole) and the centres they give; the insert pockets on
the inside faces dashed; and two cuts across the angle, through the holes.
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

from brick_frame_pics import dim, draw_geom, label, section_geom, silhouette

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "carvera_angle.scad"
OUT = ROOT / "view" / "carvera_angle.png"
BLUE, RED, GREY = "#3b7dd8", "#c0392b", "#777"

# as in the scad
LEG, T, LEN, R = 25.4, 3.28, 127, 3.5 / 2
POCKET_D, POCKET_H = 9.0, 1.4
A_HOLES = [(14, 14), (45.2, 14.28)]   # measured to the near side: along, across from the corner
B_HOLES = [(28, 10.6)]


def pockets(ax, g):
    """The pocket circles from a cut through the pockets, dashed (they are on the far, inside face)."""
    for p in getattr(g, "geoms", [g]):
        for ring in p.interiors:
            c = np.asarray(ring.coords)
            if np.ptp(c[:, 0]) < POCKET_D + 0.5:
                ax.plot(c[:, 0], c[:, 1], color=RED, lw=1, ls="--")


def leg_view(ax, m, holes, axes, cut_axis, title):
    draw_geom(ax, silhouette(m, axes), BLUE, alpha=0.3)
    o = [0, 0, 0]
    o[cut_axis] = T - POCKET_H / 2
    n = [0, 0, 0]
    n[cut_axis] = 1
    pockets(ax, section_geom(m, o, n, axes))
    ax.set_title(title, fontsize=12)
    for i, (along, across) in enumerate(holes):
        cx, cy = along + R, across + R
        ax.plot([cx - 5, cx + 5], [cy, cy], color=GREY, lw=0.6, ls="-.")
        ax.plot([cx, cx], [cy - 5, cy + 5], color=GREY, lw=0.6, ls="-.")
        # along, from the end to the hole's near side
        y = LEG + 4 + 5 * i
        ax.plot([0, 0], [LEG, y + 1], color=GREY, lw=0.6)
        ax.plot([along, along], [cy, y + 1], color=GREY, lw=0.6)
        dim(ax, (0, y), (along, y), f"{along:g}")
        # across, from the corner to the hole's near side
        x = along - 6
        ax.plot([x - 1, cx], [across, across], color=GREY, lw=0.6)
        dim(ax, (x, 0), (x, across), f"{across:g}", off=(-2.5, 0))
        ax.text(cx + 5.5, cy - 3.2, f"centre\n{cx:.2f}, {cy:.2f}", fontsize=9, color=RED, va="top")
    ax.text(LEN - 2, 1, "outside corner", ha="right", va="bottom", fontsize=9, color=GREY)
    ax.text(LEN - 2, LEG - 1, "free edge", ha="right", va="top", fontsize=9, color=GREY)
    dim(ax, (LEN + 4, 0), (LEN + 4, LEG), "25.4", off=(3.5, 0))
    ax.set_xlim(-6, LEN + 12), ax.set_ylim(-4, LEG + 16)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / "a.stl"
        subprocess.run(["openscad", "--backend=manifold", "-o", str(stl), str(SCAD)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        m = trimesh.load(stl)
    fig = plt.figure(figsize=(17, 15))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.05])
    a, b = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :])
    ca, cb = fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])

    leg_view(a, m, A_HOLES, (0, 1), 2, "Two-hole leg, face-on, corner along the bottom. Black: your numbers, end or corner "
             "to the near side of the hole.\nRed: hole centres (+1.75). Dashed: insert pockets on the inside face, "
             f"Ø{POCKET_D:g} x {POCKET_H:g} deep.")
    leg_view(b, m, B_HOLES, (0, 2), 1, "One-hole leg, face-on, corner along the bottom (across: 10.6 read as from the "
             "corner, like the other two)")
    for ax in (a, b):
        ax.text(0.5, LEG / 2, "measured\nend", rotation=90, ha="left", va="center", fontsize=9, color=GREY)
        ax.text(LEN / 2 + 15, LEG / 2, f"length {LEN} (5 in): a guess, not measured", ha="center", fontsize=11)

    # cuts across the angle, looking from the measured end
    for ax, (along, _), name in ((ca, A_HOLES[0], "two-hole leg's first hole"), (cb, B_HOLES[0], "one-hole leg's hole")):
        x = along + R
        draw_geom(ax, section_geom(m, (x, 0, 0), (1, 0, 0), (1, 2)), RED, alpha=0.5)
        draw_geom(ax, section_geom(m, (LEN - 1, 0, 0), (1, 0, 0), (1, 2)), BLUE, alpha=0.12)
        ax.set_title(f"Cut through the {name} ({x:.2f} along)", fontsize=12)
        ax.set_aspect("equal"), ax.set_xlim(-8, 34), ax.set_ylim(-8, 32)
    dim(ca, (-3, 0), (-3, LEG), "25.4", off=(-2.5, 0))
    dim(ca, (0, -3), (LEG, -3), "25.4", off=(0, -1.6))
    dim(ca, (28, 0), (28, T), f"{T:g}", off=(2.5, 0))
    label(ca, (15.75, T - 0.5), f"pocket Ø{POCKET_D:g} x {POCKET_H:g}\nfor the Ø7.5 x 1.1 insert boss", (20, 15))
    label(ca, (15.75, 1), "Ø3.5 hole (6-32)", (11, 9))
    label(cb, (T - 0.5, 12.35), f"pocket Ø{POCKET_D:g} x {POCKET_H:g}", (14, 20))
    cb.text(14, 8, "inside of the angle", ha="center", fontsize=10, color=GREY)

    for ax in (a, b):
        ax.set_aspect("equal")
    for ax in (a, b, ca, cb):
        ax.grid(alpha=0.2)
    fig.suptitle("Carvera aluminium angle, 1 x 1 in, 3.28 wall, as measured", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT, dpi=110)
    print(OUT)


if __name__ == "__main__":
    main()
