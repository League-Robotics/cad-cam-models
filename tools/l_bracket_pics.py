#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the 5 x 5 LEGO L bracket (scad/l_bracket.scad).

    uv run tools/l_bracket_pics.py

    view/l_bracket.png  both outer faces (cut just inside them: every hole), and the bracket cut through
                        corner cell 0 (up through the base) and cell 1 (in through the wall): the holes the
                        whole unit, the 1 mm skin over them
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh

import brick_frame_pics as bf

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "l_bracket.scad"
OUT = ROOT / "view"
PIECES = {"bracket": "#3cb371", "pins": "#333333"}
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


def frame(ax, title, lim=(-4, 46)):
    ax.set_title(title, fontsize=11)
    ax.set_aspect("equal")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.grid(alpha=0.2)


def face(ax, m, origin, normal, axes, title, corner_label):
    bf.draw_geom(ax, bf.section_geom(m["bracket"], origin, normal, axes), PIECES["bracket"])
    frame(ax, title)
    for i in range(6):
        ax.axvline(8 * i, color="#999", lw=0.5, ls=":")
        ax.axhline(8 * i, color="#999", lw=0.5, ls=":")
    ax.text(*corner_label)


def cut(ax, m, y, title):
    for p in PIECES:
        bf.draw_geom(ax, bf.section_geom(m[p], (0, y, 0), (0, 1, 0), (0, 2)), PIECES[p],
                     alpha=0.5 if p == "bracket" else 0.35)
    frame(ax, title, (-10, 50))
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    bf.dim(ax, (-3, 0.2), (-3, 8.3), "8.1\nhole", off=(-3.5, 0))
    bf.label(ax, (30, 8.8), "1 mm skin over the holes\n(holes run 0.3 past the unit)", (30, 17), RED)
    bf.label(ax, (8.8, 30), "1 mm skin", (20, 34), RED)
    bf.label(ax, (25, 0.2), "bed face (prints this side down)", (25, -6))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        m = export(tmp)
    fig, axs = plt.subplots(2, 2, figsize=(14, 14))
    face(axs[0, 0], m, (0, 0, 0.6), (0, 0, 1), (0, 1),
         "Base, outer face (from below): x across, y up", (2, 41, "corner edge on the left: cells 0, 2, 4 open here", ))
    axs[0, 0].set_xlabel("x")
    axs[0, 0].set_ylabel("y")
    face(axs[0, 1], m, (0.6, 0, 0), (1, 0, 0), (1, 2),
         "Wall, outer face: y across, z up", (2, 41, "corner edge at the bottom: cells 1, 3 open here"))
    axs[0, 1].set_xlabel("y")
    axs[0, 1].set_ylabel("z")
    cut(axs[1, 0], m, 4, "Cut through corner cell 0 (y = 4): corner hole up through the base, 2L pins in")
    cut(axs[1, 1], m, 12, "Cut through corner cell 1 (y = 12): corner hole in through the wall")
    fig.suptitle("5 x 5 LEGO L bracket: 5 x 5 holes on each leg, holes the whole unit, 1 mm skin inside", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "l_bracket.png", dpi=110)
    print(OUT / "l_bracket.png")


if __name__ == "__main__":
    main()
