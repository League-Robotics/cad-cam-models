#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "scipy", "networkx", "shapely"]
# ///
"""How the lid joins the shell: out/case_joint.png.

Left: the x = 0 section with the joint boxed. Middle: that corner zoomed, with
the plug, the clearances and the walls dimensioned (picks in red, STEP numbers
in black). Right: an exploded OpenSCAD render of case/exploded.scad, seen from
the back, where the lid goes in.
"""
import subprocess, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from drawing import section_geom, draw_geom, dim, label  # noqa: E402

OUT = ROOT / "out"
shell = trimesh.load(OUT / "shell.stl"); lid = trimesh.load(OUT / "lid.stl"); board = trimesh.load(OUT / "board_env.stl")
C = {"shell": "#3b7dd8", "lid": "#f0a030", "board": "#50b050"}
BLACK, RED = "#111", "#c0392b"

iso = OUT / "exploded.png"
subprocess.run(["openscad", "-o", str(iso), "--camera=0,0,-9,55,0,215,0", "--viewall", "--autocenter", "--projection=p",
                "--imgsize=1400,1400", "--colorscheme=Tomorrow", str(ROOT / "case/exploded.scad")], check=True, capture_output=True)

fig, axs = plt.subplots(1, 3, figsize=(24, 9), gridspec_kw={"width_ratios": [1.1, 1, 1]})

# 1. full section at x = 0 (y right, z up)
ax = axs[0]
for m, k in ((shell, "shell"), (lid, "lid"), (board, "board")):
    draw_geom(ax, section_geom(m, (0, 0, 0), (1, 0, 0), (1, 2)), C[k])
zy0, zy1, zz0, zz1 = 13.5, 24.5, -11.5, -3.0
ax.add_patch(Rectangle((zy0, zz0), zy1 - zy0, zz1 - zz0, fill=False, ec=RED, lw=1.5, ls="--"))
ax.text(zy1 + 0.5, zz1, "zoomed\nat right", color=RED, fontsize=10, va="top")
label(ax, (0, 1.0), "glass held from the front by the shell's lip", (0, 9), RED)
label(ax, (-8, -14), "lid: 9 mm LEGO plate, outside flush with the shell", (-4, -22.5), RED)
ax.set_title("Section along the long axis (x = 0). Blue shell, orange lid, green board envelope", fontsize=11)
lo, hi = shell.bounds[0], shell.bounds[1]
ax.set_xlim(lo[1] - 6, hi[1] + 9); ax.set_ylim(lid.bounds[0][2] - 6, hi[2] + 12); ax.set_aspect("equal")

# 2. the joint corner, zoomed
ax = axs[1]
for m, k in ((shell, "shell"), (lid, "lid"), (board, "board")):
    draw_geom(ax, section_geom(m, (0, 0, 0), (1, 0, 0), (1, 2)), C[k], alpha=0.5)
shell_bot, floor_z = -9.4, -7.4
wall_in = -1.52 + 38.6 / 2            # cavity edge at +y: module centre + (38.0 module + 2 x 0.3) / 2
plug_out = wall_in - 0.15             # the plug's +y face
outer = hi[1]
dim(ax, (wall_in, shell_bot - 0.8), (outer, shell_bot - 0.8), f"end wall {outer - wall_in:.1f}\n(1.6 side wall + the ledge,\nthe glass is 3 mm longer than the module)", off=(0, -1.3), color=RED)
dim(ax, (plug_out - 1.0, shell_bot), (plug_out - 1.0, floor_z), "plug\n2.0 deep", off=(-1.3, 0), color=RED)
label(ax, ((plug_out + wall_in) / 2, floor_z - 0.3), "0.15 gap a side\n(push fit)", (15.5, -5.6), RED)
dim(ax, (14.5, -6.9), (14.5, floor_z), "0.5", off=(-0.5, 0), color=RED)
label(ax, (16.0, -7.15), "deepest component on the back, z = -6.9 (STEP),\n0.5 above the lid's inner face: the lid stops\nthe board sliding back", (17.5, -4.2), BLACK)
label(ax, (outer - 0.8, -5.0), "shell, open at the back", (22.0, -3.6), RED)
label(ax, (16.5, -8.4), "the lid's plug: a plain 2 mm boss,\nno snaps, no screws, no undercut", (17.5, -10.5), RED)
ax.set_title("The joint, zoomed (same section)", fontsize=11)
ax.set_xlim(zy0, zy1); ax.set_ylim(zz0, zz1); ax.set_aspect("equal"); ax.grid(True, lw=0.3, alpha=0.4)

# 3. exploded render
ax = axs[2]
ax.imshow(plt.imread(iso)); ax.set_axis_off()
ax.set_title("Exploded, seen from the back: the board drops into the shell, the lid's plug follows it in", fontsize=11)

fig.suptitle("Robot display case: how the lid joins the shell (2026-11-14 model, unprinted)", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(OUT / "case_joint.png", dpi=90)
print(OUT / "case_joint.png")
