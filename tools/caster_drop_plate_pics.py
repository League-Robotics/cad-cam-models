#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""Dimensioned front and side views of scad/caster_drop_plate.scad -> view/caster_drop_plate_dims.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

U, MID, E, CB, PIN, CBD = 8.0, 3.5, 0.2, 3.2, 2.475, 0.89
W, H, T = 3 * U, 2 * U + MID, U
ROWS = [U / 2, U + MID + U / 2]
RED, BLUE = "#c0392b", "#1f4fbf"

def dim(ax, p, q, text, off=(0, 0), color=BLUE):
    ax.annotate("", p, q, arrowprops=dict(arrowstyle="<->", color=color, lw=1))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, color=color, ha="center", va="center", fontsize=10,
            bbox=dict(fc="white", ec="none", pad=1))

fig, (a, b) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw=dict(width_ratios=[2, 1]))
# front view
a.set_title("front: three layers, the middle one squeezed to 3.5", loc="left")
for z0, z1, c, name in [(0, U, "#f2d57a", "full unit: 3 pin holes"), (U, U + MID, "#e9a0a0", "middle layer: 3.5, no holes"), (U + MID, H, "#f2d57a", "full unit: 3 pin holes")]:
    a.add_patch(Rectangle((E, max(z0, E)), W - 2 * E, min(z1, H - E) - max(z0, E), fc=c, ec="none"))
    a.text(W + 9.5, (z0 + z1) / 2, name, va="center", fontsize=10, color=RED if c == "#e9a0a0" else "black")
a.add_patch(Rectangle((E, E), W - 2 * E, H - 2 * E, fc="none", ec="black", lw=1.5))
for z in ROWS:
    for i in range(3):
        x = U / 2 + i * U
        a.add_patch(Circle((x, z), CB, fc="white", ec="black", lw=1))
        a.add_patch(Circle((x, z), PIN, fc="white", ec="black", lw=1))
for z in (U, U + MID):
    a.plot([0, W], [z, z], color=RED, lw=0.8, ls="--")
dim(a, (-3, 0), (-3, U), "8", off=(-2, 0))
dim(a, (-3, U), (-3, U + MID), "3.5", off=(-2.6, 0), color=RED)
dim(a, (-3, U + MID), (-3, H), "8", off=(-2, 0))
dim(a, (-9, 0), (-9, H), "19.5", off=(-2.6, 0))
dim(a, (W + 3, ROWS[0]), (W + 3, ROWS[1]), "11.5\nrow to row", off=(3.4, 0))
dim(a, (0, -3), (W, -3), "24 (3 units)", off=(0, -1.6))
dim(a, (U / 2, H + 2.5), (U / 2 + U, H + 2.5), "8", off=(0, 1.4))
a.set_xlim(-14, W + 32); a.set_ylim(-7, H + 6)
# side view
b.set_title("side: one unit thick, holes straight through", loc="left")
b.add_patch(Rectangle((E, E), T - 2 * E, H - 2 * E, fc="#f2d57a", ec="black", lw=1.5))
b.add_patch(Rectangle((E, U), T - 2 * E, MID, fc="#e9a0a0", ec="none"))
for z in ROWS:
    for r, x0, x1 in [(CB, E, E + CBD), (PIN, E + CBD, T - E - CBD), (CB, T - E - CBD, T - E)]:
        b.add_patch(Rectangle((x0, z - r), x1 - x0, 2 * r, fc="white", ec="black", lw=0.8, ls="--"))
    b.plot([-1.5, T + 1.5], [z, z], color="gray", lw=0.6, ls="-.")
dim(b, (0, -3), (T, -3), "8 (7.6 printed)", off=(0, -1.6))
dim(b, (T + 3, ROWS[0]), (T + 3, ROWS[1]), "11.5", off=(2.4, 0))
b.set_xlim(-6, T + 10); b.set_ylim(-7, H + 6)
for ax in (a, b):
    ax.set_aspect("equal"); ax.axis("off")
fig.suptitle("Caster drop plate (draft): a 3 x 3 plate with the middle row 3.5 instead of 8   (mm)", x=0.02, ha="left", fontsize=13)
fig.tight_layout()
fig.savefig("view/caster_drop_plate_dims.png", dpi=130)
