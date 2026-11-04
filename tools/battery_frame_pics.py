#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawings of the LEGO frame round the USB battery (scad/battery_frame.scad).

    uv run tools/battery_frame_pics.py

    view/battery_frame_size.png  why 6 units, not 5: end-on, a 5 x 5 frame drawn by hand, then the 6 x 6 one
                                 cut through an up cell and an out cell
    view/battery_frame.png       from the side (cut through the corner column) and from above (cut through the
                                 corner row): the holes turning cell to cell, the battery out of both ends
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from shapely.geometry import Polygon

import brick_frame_pics as bf

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "battery_frame.scad"
OUT = ROOT / "view"
PIECES = {"battery": "#9a9a9a", "half_a": "#f29a00", "half_b": "#4169e1", "pins": "#333333"}
BATT = (103, 27.25, 25.25)
RED = "#c0392b"


def export(tmp):
    procs, meshes = [], {}
    for p in PIECES:
        out = Path(tmp) / f"{p}.stl"
        procs.append((p, out, subprocess.Popen(["openscad", "--backend=manifold", "-o", str(out), "-D", f'part="{p}"',
                                                 str(SCAD)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for p, out, pr in procs:
        pr.wait()
        meshes[p] = trimesh.load(out)
    return meshes


def cut(ax, m, x, pieces=("half_a", "half_b", "pins", "battery")):
    """End-on cut at x: y to the right, z up."""
    for p in pieces:
        g = bf.section_geom(m[p], (x, 0, 0), (1, 0, 0), (1, 2))
        bf.draw_geom(ax, g, PIECES[p], alpha=0.25 if p == "battery" else 0.5)


def size(m):
    fig, axs = plt.subplots(1, 3, figsize=(19, 7.5))
    # 5 x 5, by hand: the cells on -20 ... 20, the battery centred
    a = axs[0]
    a.add_patch(Rectangle((-19.8, -19.8), 39.6, 39.6, fc="#bbb", alpha=0.4, ec="#777"))
    bw, bh = BATT[1] / 2 + 0.3, BATT[2] / 2 + 0.3
    a.add_patch(FancyBboxPatch((-bw + 2.3, -bh + 2.3), 2 * bw - 4.6, 2 * bh - 4.6, boxstyle="round,pad=2.3",
                               fc="white", ec="#777"))
    a.add_patch(FancyBboxPatch((-BATT[1] / 2 + 2, -BATT[2] / 2 + 2), BATT[1] - 4, BATT[2] - 4, boxstyle="round,pad=2",
                               fc=PIECES["battery"], alpha=0.25, ec=PIECES["battery"]))
    for c in (-16, -8, 0, 8, 16):
        for x, y in ((c, 16), (c, -16), (16, c), (-16, c)):
            hit = abs(x) - 2.475 < bw if abs(y) == 16 and abs(x) == 16 else False
            a.add_patch(Circle((x, y), 2.475, fc="none", ec=RED if hit else "#555", lw=1.2))
        # a pin pushed in from the side face, 7.8 deep
        a.add_patch(Rectangle((19.8 - 7.8, c - 2.4), 7.8, 4.8, fc=RED if 19.8 - 7.8 < bw else "#555", alpha=0.6))
    a.set_title("5 x 5 (40): 6.4 of wall beside the battery\npins in from a face reach 1.7 into it; corner holes break through")
    bf.label(a, (13, 0), "a pin from the side:\n7.8 deep, into the battery", (10, 27), RED)
    bf.label(a, (16, 16), "corner hole cuts\nthe battery's space", (-10, 27), RED)
    bf.dim(a, (-20, -24), (20, -24), "40 = 5 units")
    a.set_xlim(-26, 30), a.set_ylim(-30, 34)
    # 6 x 6, cut 1.5 off the centre of an up cell (x = -24) and of the joint cell (x = -32)
    cut(axs[1], m, -22.5)
    axs[1].set_title("6 x 6 (48), an up cell (the ends, every other one):\nfull grid; the corners up, blind, half a pin deep")
    bf.label(axs[1], (20, 44), "corner up,\n8 deep", (36, 54))
    bf.label(axs[1], (-12, 6), "into the battery's\nspace, 10.9 deep", (-36, 4))
    bf.label(axs[1], (20, 28), "side holes, every cell", (34, 36))
    bf.dim(axs[1], (-24, -4), (24, -4), "48 = 6 units")
    bf.dim(axs[1], (13.9, 18), (23.8, 18), "9.9", off=(0, 2))
    cut(axs[2], m, -30.5)
    axs[2].set_title("a joint cell (2nd from each end; the other out cells\nthe same without the pins): the corners out, blind")
    bf.label(axs[2], (0, 44), "2L pin across the split:\nthe y = +-4 holes give way", (0, 56), RED)
    bf.label(axs[2], (20, 4), "corner out,\n8 deep", (36, -6))
    bf.label(axs[2], (13.6, 16), "rib: grips 0.15", (36, 22), RED)
    axs[2].text(12, -8, "half A (+y)", color=PIECES["half_a"], ha="center", fontsize=11)
    axs[2].text(-12, -8, "half B (-y)", color=PIECES["half_b"], ha="center", fontsize=11)
    for ax in axs[1:]:
        ax.axvline(0, color="#888", lw=0.8, ls="--")
        ax.set_xlim(-46, 46), ax.set_ylim(-12, 62)
    for ax in axs:
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.suptitle("USB battery frame, end-on: why 6 x 6 (battery 27.25 wide, 25.25 high, 0.3 clearance)")
    fig.tight_layout()
    fig.savefig(OUT / "battery_frame_size.png", dpi=100)


def views(m):
    fig, (a, b) = plt.subplots(2, 1, figsize=(14, 13))
    # side, from -y: half B cut through its corner column (y = -20), the battery seen from outside
    bf.draw_geom(a, bf.silhouette(m["battery"], (0, 2)), PIECES["battery"], alpha=0.2, lw=0.8)
    bf.draw_geom(a, bf.section_geom(m["half_b"], (0, -21.5, 0), (0, 1, 0), (0, 2)), PIECES["half_b"])
    a.set_title("From the side, cut through the corner column 1.5 in from its centre (y = -21.5).\n"
                "Circles: holes through the side, every cell; slots at top and bottom: the corner holes up (every other cell)")
    bf.dim(a, (-44, 56), (44, 56), "88 = 11 units")
    bf.dim(a, (-51.5, 30), (-44, 30), "7.7", off=(0, 3))
    bf.dim(a, (44, 30), (51.5, 30), "7.7", off=(0, 3))
    bf.dim(a, (58, 0), (58, 48), "48 =\n6 units", off=(3, 0))
    bf.label(a, (-40, 44), "up cell: corner up,\n8 deep", (-62, 62))
    bf.label(a, (-32, 44), "out cell: corner out", (-20, 68))
    bf.label(a, (48, 24), "battery out of\nboth ends (ports)", (66, 34), "#555")
    a.set_xlim(-76, 80), a.set_ylim(-8, 76)
    # top, cut through the corner row (z = 44)
    for p in ("half_a", "half_b", "pins"):
        bf.draw_geom(b, bf.section_geom(m[p], (0, 0, 45.5), (0, 0, 1), (0, 1)), PIECES[p])
    bf.draw_geom(b, bf.silhouette(m["battery"], (0, 1)), PIECES["battery"], alpha=0.12, lw=0.6)
    b.axhline(0, color="#888", lw=0.8, ls="--")
    b.set_title("From above, cut through the top's corner row 1.5 up from its centre (z = 45.5).\n"
                "Circles: holes up, every cell; slots across: the corner holes out (every other cell), 2L pins (dark) at the split")
    bf.dim(b, (-44, 30), (44, 30), "88 = 11 units")
    bf.dim(b, (52, -24), (52, 24), "48", off=(3, 0))
    bf.label(b, (-32, 0), "2L pins join the halves, top and\nbottom, 2nd cell from each end:\nthe y = +-4 holes give way", (-58, 34), RED)
    bf.label(b, (40, 12), "half A", (64, 18), PIECES["half_a"])
    bf.label(b, (40, -12), "half B: the same\nprint turned round", (66, -18), PIECES["half_b"])
    b.set_xlim(-76, 80), b.set_ylim(-34, 42)
    for ax in (a, b):
        for x in np.arange(-44, 45, 8):
            ax.axvline(x, color="#ddd", lw=0.4, zorder=0)
        ax.set_aspect("equal"), ax.grid(alpha=0.0)
    fig.tight_layout()
    fig.savefig(OUT / "battery_frame.png", dpi=100)


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        m = export(tmp)
        size(m)
        views(m)
    for n in ("battery_frame_size", "battery_frame"):
        print(f"wrote view/{n}.png")


if __name__ == "__main__":
    main()
