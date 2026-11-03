#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the Carvera dust-bin-bay plate (scad/carvera_pi_bin.scad).

    uv run tools/carvera_pi_bin_pics.py   ->  view/carvera_pi_bin.png

From above, from the side (cut through the rail), the rail's front end close
up, and cut across the plate at the front and in the middle.
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh

from brick_frame_pics import dim, draw_geom, label, section_geom, silhouette

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "carvera_pi_bin.scad"
OUT = ROOT / "view" / "carvera_pi_bin.png"
BLUE, RED = "#3b7dd8", "#c0392b"
BODY_W, LEN, RAIL_X = 76.5, 168, 76.5 / 2 + 1   # RAIL_X: a cut through the rail


def main():
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / "p.stl"
        subprocess.run(["openscad", "--backend=manifold", "-o", str(stl), "-D", 'part="plate"', str(SCAD)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        m = trimesh.load(stl)
    fig = plt.figure(figsize=(19, 14))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.5, 1], height_ratios=[1.6, 0.6, 0.8])
    top, side = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :])
    close, ends = fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])

    # from above, front (handle end) left
    draw_geom(top, silhouette(m, (1, 0)), BLUE, alpha=0.35)
    top.set_title("From above, the end that faces you (the bin's handle end) left")
    dim(top, (0, -52), (LEN, -52), "168 (measured)")
    dim(top, (LEN + 8, -80.5 / 2), (LEN + 8, 80.5 / 2), "80.5 across\nthe rails\n(measured)", off=(13, 0))
    dim(top, (-8, -BODY_W / 2), (-8, BODY_W / 2), "76.5\nplate", off=(-9, 0))
    label(top, (80, BODY_W / 2 + 1), "rail, 2 out (measured)", (80, 50))
    label(top, (LEN - 4, BODY_W / 2 + 1.2), "back 10 narrows to 0.6\nto lead in (guessed)", (LEN - 25, 50))
    top.text(LEN / 2, 0, "3 thick, flat both sides:\ndrill it to suit the Pi case", ha="center", va="center", fontsize=12)
    top.set_xlim(-30, 200), top.set_ylim(-60, 60)

    # from the side, cut through the rail (red) with the plate behind it
    draw_geom(side, section_geom(m, (0, 0, 0), (1, 0, 0), (1, 2)), BLUE, alpha=0.3)
    draw_geom(side, section_geom(m, (RAIL_X, 0, 0), (1, 0, 0), (1, 2)), RED, alpha=0.6)
    side.set_title("From the side, cut through the rail (red); the plate behind it (blue). Front left.")
    side.set_xlim(-10, 178), side.set_ylim(-8, 3)

    # the rail's front end close up
    draw_geom(close, section_geom(m, (0, 0, 0), (1, 0, 0), (1, 2)), BLUE, alpha=0.3)
    draw_geom(close, section_geom(m, (RAIL_X, 0, 0), (1, 0, 0), (1, 2)), RED, alpha=0.6)
    close.set_title("Rail, front end: 5.2 thick, an S-curve up to 1.25")
    dim(close, (-1.5, 0), (-1.5, -5.2), "5.2\n(measured)", off=(-4, 0))
    dim(close, (36, 0), (36, -1.25), "1.25 (measured)", off=(6.5, -0.4))
    dim(close, (0, -6.6), (15, -6.6), "15 (guessed)")
    dim(close, (15, -6.6), (22, -6.6), "7 S-curve", off=(0, -0.9))
    label(close, (28, -2.4), "plate, 3 thick", (30, -5))
    close.text(14, 0.5, "tops flush (assumed)", fontsize=9, color="#555")
    close.set_xlim(-10, 45), close.set_ylim(-8.5, 2)

    # cut across the plate, looking from the front: at the front (y = 5) and in the middle (y = 84)
    draw_geom(ends, section_geom(m, (0, 84, 0), (0, 1, 0), (0, 2)), BLUE, alpha=0.35)
    draw_geom(ends, section_geom(m, (0, 5, 0), (0, 1, 0), (0, 2)), RED, alpha=0.35)
    ends.set_title("Cut across, right half: at the front (red)\nand in the middle (blue)")
    dim(ends, (BODY_W / 2, 1.2), (BODY_W / 2 + 2, 1.2), "2", off=(0, 0.6))
    ends.set_xlim(24, 44), ends.set_ylim(-7, 3.5)

    for ax in (top, side, close, ends):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT, dpi=100)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
