#!/usr/bin/env python3
"""Toolpath picture of a plate job from tools/plate_gcode.py on the 11 x 19 cell grid.

    uv run --with matplotlib tools/plate_job_pic.py cam/robot_plate_3x4_cans_1x1_2mm.nc view/robot_plate_3x4_cans_job.png

Red: the cutter's centreline on the last pass (the gaps are the tabs).
"""
import re
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

U = 8; L = 151.2; W = 88


def main(nc, png):
    x = y = None; z = 0; segs = []
    lines = open(nc).read().splitlines()
    job = next((ln[2:] for ln in lines if "corn cutter" in ln), "")
    for ln in lines:
        m = re.match(r"(G0|G1) (.*)", ln)
        if not m:
            continue
        d = dict((k, float(v)) for k, v in re.findall(r"([XYZ])(-?[\d.]+)", m.group(2)))
        nx, ny, nz = d.get("X", x), d.get("Y", y), d.get("Z", z)
        if m.group(1) == "G1" and x is not None and nz <= -7.2 and z <= -7.2:
            segs.append(((x, y), (nx, ny)))
        x, y, z = nx, ny, nz
    fig, ax = plt.subplots(figsize=(14, 9.6))
    ax.add_patch(Rectangle((0, 0), L, W, fc="#f3eedc", ec="k", lw=1.5))
    for r in range(19):
        for c in range(11):
            ax.add_patch(Rectangle((r * U, c * U), U, U, fc="none", ec="#bbb", lw=0.5))
            ax.add_patch(plt.Circle((r * U + U / 2, c * U + U / 2), 2.4, fc="none", ec="#ccc", lw=0.5))
    for (a, b) in segs:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#c0392b", lw=2.2)
    for r in range(19):
        ax.text(r * U + U / 2, -2.5, str(r + 1), ha="center", va="top", fontsize=8, color="#555")
    for c in range(11):
        ax.text(-2.5, c * U + U / 2, str(c + 1), ha="right", va="center", fontsize=8, color="#555")
    ax.text(L / 2, -7.5, "rows 1..19 along X (job X; the plate's front edge, row 1, on X = 0; origin at the front-left corner, Z0 on top)", ha="center", va="top", fontsize=9)
    ax.text(-7.5, W / 2, "columns 1..11 along Y", rotation=90, ha="right", va="center", fontsize=9)
    ax.annotate("3x3 hole: columns 5-7, rows 9-11 (the 3x4 at rows 5-8 walked back here)\nX 64..88, Y 32..56, exactly on the cell edges\na 2 mm tab in the middle of each side", (88, 44), (106, 44), fontsize=9, arrowprops=dict(arrowstyle="->"), ha="left", va="center")
    ax.annotate("can pockets X 7.95..22.15 (the body + 1.0 clearance, the front 1.5 further forward, the back 0.5 further back), 7.8 wide\nthe middle two run together (Y 34.1..53.9); at Y 14, 38 + 50, 74 (robot x +-30, +-6)\nslugs, a 2 mm tab on each long side; cut first", (21.65, 74), (34, 98), fontsize=9, arrowprops=dict(arrowstyle="->"), ha="left", va="top")
    ax.plot(40, 24, marker="+", color="#1a5fb4", ms=16, mew=2.5)
    ax.annotate("Z probe: X40 Y24 from the work origin, the corner of rows 5/6 and columns 3/4\nsolid, 3.3 mm to the nearest hole, 8 below and 24 ahead of the hole, clear of the pockets", (40, 24), (74, 14), fontsize=9, color="#1a5fb4", arrowprops=dict(arrowstyle="->", color="#1a5fb4"), ha="left", va="top")
    ax.text(-14, W + 24, f"{nc}: {job}\nred = the cutter's centreline on the last pass (1 mm inside the cut lines); the gaps are the 2 mm tabs", ha="left", va="top", fontsize=9)
    ax.set_xlim(-14, L + 4); ax.set_ylim(-12, W + 26); ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(png, dpi=110)
    print(png)


if __name__ == "__main__":
    main(*sys.argv[1:3])
