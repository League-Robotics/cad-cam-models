#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""Dimensioned front view of scad/caster_drop_plate.scad -> view/caster_drop_plate_dims.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

U, DROP, E, CB, PIN = 8.0, 3.5, 0.2, 3.2, 2.475
COLS = 5
W, H = COLS * U, U + DROP
MID_Z, END_Z = U / 2, U / 2 + DROP
RED, BLUE = "#c0392b", "#1f4fbf"

def dim(ax, p, q, text, off=(0, 0), color=BLUE):
    ax.annotate("", p, q, arrowprops=dict(arrowstyle="<->", color=color, lw=1))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, color=color, ha="center", va="center", fontsize=10,
            bbox=dict(fc="white", ec="none", pad=1))

fig, a = plt.subplots(figsize=(13, 6))
outline = [(E, DROP + E), (U, DROP + E), (U, E), (W - U, E), (W - U, DROP + E), (W - E, DROP + E), (W - E, H - E), (W - U, H - E),
           (W - U, U - E), (U, U - E), (U, H - E), (E, H - E)]
a.add_patch(Polygon(outline, closed=True, fc="#f2d57a", ec="black", lw=1.5))
for i in range(COLS):
    z = END_Z if i in (0, COLS - 1) else MID_Z
    x = U / 2 + i * U
    a.add_patch(Circle((x, z), CB, fc="white", ec="black", lw=1))
    a.add_patch(Circle((x, z), PIN, fc="white", ec="black", lw=1))
a.plot([-2, W + 9], [END_Z, END_Z], color=RED, lw=0.8, ls="--")
a.plot([U / 2, W + 9], [MID_Z, MID_Z], color=RED, lw=0.8, ls="--")
dim(a, (W + 6, MID_Z), (W + 6, END_Z), "3.5", off=(3, 0), color=RED)
a.text(W + 11.5, (MID_Z + END_Z) / 2, "middle three holes\nbelow the end holes", color=RED, va="center", fontsize=10)
dim(a, (0, -3), (W, -3), "40 (5 units)", off=(0, -1.6))
dim(a, (U, -0.9), (W - U, -0.9), "24 (3 units), dropped", off=(0, -1.3))
dim(a, (-3, DROP), (-3, H), "8", off=(-1.6, 0))
dim(a, (-8, 0), (-8, H), "11.5", off=(-2.4, 0))
dim(a, (U / 2, H + 2), (U / 2 + U, H + 2), "8", off=(0, 1.3))
a.text(U / 2, H + 5.2, "end hole", ha="center", fontsize=10)
a.text(W - U / 2, H + 5.2, "end hole", ha="center", fontsize=10)
a.text(W / 2, U + 1.2, "three holes, 3.5 lower", ha="center", fontsize=10)
a.set_xlim(-13, W + 30); a.set_ylim(-7, H + 8)
a.set_aspect("equal"); a.axis("off")
fig.suptitle("Caster drop plate v2 (draft): 1 x 5, the middle three holes 3.5 below the two end holes; 8 thick, holes straight through   (mm)", x=0.02, ha="left", fontsize=12)
fig.tight_layout()
fig.savefig("view/caster_drop_plate_dims.png", dpi=130)
