#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the Carvera camera bracket (scad/carvera_angle.scad, part="bracket").

    uv run tools/carvera_bracket_pics.py   ->  view/carvera_bracket.png

As mounted, from where the user stands: a 3D view, from the front (the
one-hole leg), from the left (the two-hole leg), from above (an L) and from
below (the square cap with the camera hole).
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
OUT = ROOT / "view" / "carvera_bracket.png"
BLUE, RED, GREY = "#3b7dd8", "#c0392b", "#777"

# as in the scad
LEG, T, R = 25.4, 3.28, 3.5 / 2
ANGLE_L, CAP_T, CAM_D = 56, 6, 6.8
H = ANGLE_L + CAP_T
A_CENTRES = [(15.75, 15.75), (46.95, 16.03)]   # along from the top, across from the corner
B_CENTRES = [(29.75, 12.35)]


def centre_mark(ax, x, y, s=5):
    ax.plot([x - s, x + s], [y, y], color=GREY, lw=0.6, ls="-.")
    ax.plot([x, x], [y - s, y + s], color=GREY, lw=0.6, ls="-.")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / "b.stl"
        subprocess.run(["openscad", "--backend=manifold", "-o", str(stl), "-D", 'part="bracket"', str(SCAD)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        m = trimesh.load(stl)
        imgs = []
        for name, eye in (("front", "-70,-120,115"), ("back", "120,110,120")):
            png = Path(tmp) / f"{name}.png"
            subprocess.run(["openscad", "--backend=manifold", "--render", "-o", str(png), "-D", 'part="bracket"',
                            f"--camera={eye},12.7,12.7,29", "--projection=p", "--imgsize=800,1000",
                            "--colorscheme=Tomorrow", str(SCAD)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            imgs.append(plt.imread(png))
    fig = plt.figure(figsize=(19, 13))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.6, 1])
    i3, i3b, front, left = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[0, 3])
    top, bottom = fig.add_subplot(gs[1, 1]), fig.add_subplot(gs[1, 2])
    for ax, img, title in ((i3, imgs[0], "As mounted, from in front\nand to the left"),
                           (i3b, imgs[1], "From behind and to the right:\ninsert pockets, cap with the camera hole")):
        ax.imshow(img), ax.set_axis_off(), ax.set_title(title, fontsize=12)

    # from the front: the one-hole leg face-on, x right, z up
    draw_geom(front, silhouette(m, (0, 2)), BLUE, alpha=0.3)
    front.set_title("From the front: the one-hole leg", fontsize=12)
    for along, across in B_CENTRES:
        centre_mark(front, across, H - along)
        dim(front, (across, H), (across, H - along), f"{along:.2f}", off=(3.5, 0))
        dim(front, (0, H - along - 7), (across, H - along - 7), f"{across:.2f}", off=(0, -1.6))
    dim(front, (-6, 0), (-6, H), f"{H:g}", off=(-3, 0))
    dim(front, (LEG + 4, CAP_T), (LEG + 4, H), f"{ANGLE_L:g}\nthe angle", off=(4, 0))
    dim(front, (LEG + 4, 0), (LEG + 4, CAP_T), f"{CAP_T:g} cap", off=(5, 0))
    dim(front, (0, -4), (LEG, -4), "25.4", off=(0, -1.6))
    label(front, (2, H - 3), "outside\ncorner", (-8, H + 6))
    front.set_xlim(-14, 40), front.set_ylim(-9, H + 10)

    # from the left: the two-hole leg face-on, front (y = 0) on the right
    draw_geom(left, silhouette(m, (1, 2)), BLUE, alpha=0.3)
    left.invert_xaxis()
    left.set_title("From the left: the two-hole leg\n(front on the right)", fontsize=12)
    for along, across in A_CENTRES:
        centre_mark(left, across, H - along)
        left.text(across - 5, H - along, f"{along:.2f} down\n{across:.2f} from\nthe front", fontsize=9, color=RED,
                  va="center", ha="left")
    left.set_xlim(40, -9), left.set_ylim(-9, H + 10)

    # from above: the L, with the cap seen below it
    draw_geom(top, silhouette(m, (0, 1)), GREY, alpha=0.15)
    draw_geom(top, section_geom(m, (0, 0, 30), (0, 0, 1), (0, 1)), BLUE, alpha=0.45)
    top.set_title("From above: the L, cap below it", fontsize=12)
    label(top, (12.35, 2.5), "insert pocket", (12.35, -6.5))
    label(top, (LEG / 2 + 2, LEG / 2 + 2), f"camera hole\nØ{CAM_D:g}", (LEG + 7, LEG + 5))
    top.text(32, -5, "you (front)", ha="center", fontsize=10, color=GREY)
    dim(top, (LEG / 2, LEG / 2 - 6), (LEG, LEG / 2 - 6), "12.7")

    # from below: the cap
    draw_geom(bottom, silhouette(m, (0, 1)), BLUE, alpha=0.3)
    bottom.invert_yaxis()
    bottom.set_title("From below: the 1 x 1 in cap (front at the top)", fontsize=12)
    centre_mark(bottom, LEG / 2, LEG / 2, 8)
    dim(bottom, (0, LEG + 3), (LEG, LEG + 3), "25.4", off=(0, 1.6))
    dim(bottom, (LEG / 2, -3), (LEG, -3), "12.7", off=(0, -1.6))
    label(bottom, (LEG / 2 + 2.4, LEG / 2 + 2.4), f"Ø{CAM_D:g} through, for a 1/4-20\ncamera screw", (LEG + 4, LEG + 7))
    for ax in (top, bottom):
        ax.set_xlim(-8, 42), ax.set_ylim(-9, 36) if ax is top else ax.set_ylim(36, -9)

    for ax in (front, left, top, bottom):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.suptitle(f"Carvera camera bracket: the angle cut to {ANGLE_L} (same holes and pockets) with a "
                 f"{CAP_T} cap on its lower end", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=100)
    print(OUT)


if __name__ == "__main__":
    main()
