#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "scipy", "networkx", "shapely"]
# ///
"""Labelled drawings of the robot display case: out/case_section.png.

Reads the STLs tools/build.sh exported (out/shell.stl, out/lid.stl,
out/board_env.stl) and draws two sections through the assembly, the shell from
the back, and the lid from the back. Numbers from Waveshare's STEP model are in
black; our picks are in red.
"""
import subprocess, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from drawing import section_geom, silhouette, draw_geom, dim, label  # noqa: E402

shell = trimesh.load(ROOT / "out/shell.stl")
lid = trimesh.load(ROOT / "out/lid.stl")
board = trimesh.load(ROOT / "out/board_env.stl")
C = {"shell": "#3b7dd8", "lid": "#f0a030", "board": "#50b050"}
BLACK, RED = "#111", "#c0392b"

fig, axs = plt.subplots(2, 2, figsize=(17, 15))

# 1. Section along the long axis (plane x = 0): y right, z up
ax = axs[0, 0]
for m, k in ((shell, "shell"), (lid, "lid"), (board, "board")):
    draw_geom(ax, section_geom(m, (0, 0, 0), (1, 0, 0), (1, 2)), C[k])
ax.set_title("Section through the middle, along the long axis (x = 0): header edge on the left, +y right, z up", fontsize=11)
lip_top = shell.bounds[1][2]; lid_bot = lid.bounds[0][2]; oy0, oy1 = shell.bounds[0][1], shell.bounds[1][1]
dim(ax, (oy1 + 3, lid_bot), (oy1 + 3, lip_top), f"{lip_top - lid_bot:.1f}\ncase\nheight", color=RED)
dim(ax, (oy0, lid_bot - 3), (oy1, lid_bot - 3), f"{oy1 - oy0:.2f} outside (41.13 glass + 2 x 0.2 + 2 x 1.6 wall)", color=RED)
label(ax, (oy1 - 1.0, lip_top - 0.6), "lip 1.2 thick, 1.5 over the glass edge\n(our pick): the glass face sits 1 mm behind it", (10, 12), RED)
label(ax, (oy1 - 1.5, 2.0), "ledge the glass edge rests on: 0.6 flat at z = 1.9,\nthen a 45 deg chamfer (prints face down)", (18, -4), RED)
label(ax, (0, 3.2), "glass 41.13 x 33.13, 1.75 thick, 2 mm chamfer\n(from Waveshare's STEP)", (0, 9), BLACK)
label(ax, (-5, -2.0), "PCB 37.14 x 29.85 x 1.0 (STEP)", (-6, -12), BLACK)
label(ax, (-14.5, -5.5), "deepest part on the back:\nz = -6.9 (STEP)", (-12, -15.5), BLACK)
label(ax, (12, -8.4), "lid plug, 2 deep, 0.15 clearance a side\n(friction fit; glue if loose)", (14, -14), RED)
label(ax, (-8, -14), "5 x 4 LEGO pin holes, 8 deep, blind\n(Part Designer fits, lego.scad)", (-4, -22.5), RED)
label(ax, (-oy1 + 1.5, -5.0), "header / wire slot\n28 x 4 under the PCB (pick)", (-16, 9), RED)
ax.set_xlim(oy0 - 8, oy1 + 8); ax.set_ylim(lid_bot - 7, lip_top + 13)

# 2. Section across (plane y = usb centre): x right, z up; shows the USB cutout and a button slot
ax = axs[0, 1]
yc = -1.02
for m, k in ((shell, "shell"), (lid, "lid"), (board, "board")):
    draw_geom(ax, section_geom(m, (0, yc, 0), (0, 1, 0), (0, 2)), C[k])
ax.set_title(f"Section across, through the USB-C port (y = {yc}): USB edge on the left, buttons on the right", fontsize=11)
ox0, ox1 = shell.bounds[0][0], shell.bounds[1][0]
dim(ax, (ox0, lid_bot - 3), (ox1, lid_bot - 3), f"{ox1 - ox0:.2f} outside (33.13 glass + 2 x 0.2 + 2 x 1.6)", color=RED)
label(ax, (ox0 + 0.8, -3.8), "USB-C cutout 13 x 7.5\n(receptacle 8.3 x 3.6 at z -3.8, STEP)", (-9, 9), RED)
label(ax, (ox1 - 0.8, -3.2), "button slot 7 x 4\n(button 4.6 x 2.2 at z -3.2, STEP)", (9, 9), RED)
label(ax, (0, -7.0), "0.5 between the deepest part and the lid (pick)", (0, -11.5), RED)
ax.set_xlim(ox0 - 10, ox1 + 10); ax.set_ylim(lid_bot - 7, lip_top + 13)

# 3. The shell from the back: x right, y up (seen from -z)
ax = axs[1, 0]
g = section_geom(shell, (0, 0, -5), (0, 0, 1), (0, 1))
draw_geom(ax, g, C["shell"])
draw_geom(ax, section_geom(shell, (0, 0, 3), (0, 0, 1), (0, 1)), C["shell"], alpha=0.15)
ax.set_title("Shell from the back (cut at z = -5, the lip's window shown faint): buttons +x, USB -x, header -y", fontsize=11)
dim(ax, (-15.35, 21), (15.35, 21), "cavity 30.7 (30.07 module + 2 x 0.3)", color=RED)
dim(ax, (17, -20.57 + -1.19 + 1.19), (17, 18.03), "cavity 38.6\n(38.0 module\n+ 2 x 0.3)", off=(5, 0), color=RED)
for y in (-9.75, -0.85, 8.07):
    label(ax, (ox1 - 0.8, y), f"button y={y}", (ox1 + 9, y), BLACK)
label(ax, (ox0 + 0.8, -1.02), "USB-C\ny=-1.02", (ox0 - 7, -1.02), BLACK)
label(ax, (0, oy0 + 0.8), "header slot (28 wide)", (0, oy0 - 6), RED)
ax.set_xlim(ox0 - 14, ox1 + 14); ax.set_ylim(oy0 - 9, oy1 + 6)

# 4. The lid from the back: the LEGO grid
ax = axs[1, 1]
draw_geom(ax, section_geom(lid, (0, 0, lid_bot + 0.3), (0, 0, 1), (0, 1)), C["lid"])
ax.set_title("LEGO lid from the back (cut 0.3 in from its face): 5 x 4 pin holes on the 8 mm grid", fontsize=11)
dim(ax, (-12, -20), (12, -20), "4 x 8 = 32 (short axis)", color=RED)
dim(ax, (20, -16), (20, 16), "5 x 8 = 40\n(long axis)", off=(5, 0), color=RED)
label(ax, (3.2, 0), "counterbore Ø6.4, bore Ø4.95\n(Part Designer fits)", (0, 24), RED)
ax.set_xlim(ox0 - 14, ox1 + 14); ax.set_ylim(oy0 - 9, oy1 + 6)

for a in axs.flat:
    a.set_aspect("equal"); a.grid(True, lw=0.3, alpha=0.4); a.tick_params(labelsize=8)
fig.suptitle("Robot display case for the Waveshare ESP32-S3-Touch-LCD-1.69: shell (blue), LEGO lid (orange), board envelope (green)\n"
             "black = from Waveshare's STEP model (nothing measured on the real board yet); red = our picks", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = ROOT / "out/case_section.png"
fig.savefig(out, dpi=90)
print(out)
