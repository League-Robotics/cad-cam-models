#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the USB hub rack on the Carvera PSU (scad/usb_hub_rack.scad).

    uv run tools/usb_hub_rack_pics.py   ->  view/usb_hub_rack.png

From behind (as you see it from the back panel), from the side cut through the
middle column of hooks, and one hook close up: pushed on, then slid down.
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
SCAD = ROOT / "scad" / "usb_hub_rack.scad"
OUT = ROOT / "view" / "usb_hub_rack.png"
COL = {"plate": "#3b7dd8", "angle": "#f29a00", "hub": "#555555", "hub_up": "#555555", "psu": "#b0b0b0",
       "panel": "#c0392b"}
TOP_ROW, BOT_ROW = -46.7, -126.7


def export(tmp):
    procs = {p: subprocess.Popen(["openscad", "--backend=manifold", "-o", f"{tmp}/{p}.stl", "-D", f'part="{p}"',
                                  str(SCAD)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for p in COL}
    for p in procs.values():
        p.wait()
    return {p: trimesh.load(f"{tmp}/{p}.stl") for p in COL}


def cut(ax, m, parts, x=0.0, alpha=0.45):
    for p in parts:
        draw_geom(ax, section_geom(m[p], (x, 0, 0), (1, 0, 0), (1, 2)), COL[p], alpha=alpha)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        m = export(tmp)
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.15, 1.0, 0.9], height_ratios=[1, 1])
    back, side = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[:, 1])
    push, locked = fig.add_subplot(gs[0, 2]), fig.add_subplot(gs[1, 2])

    # from behind: x mirrored so it reads as seen from the back panel
    draw_geom(back, silhouette(m["plate"], (0, 2)), COL["plate"], alpha=0.35)
    draw_geom(back, silhouette(m["angle"], (0, 2)), COL["angle"], alpha=0.5)
    hub = section_geom(m["hub"], (0, 4, 0), (0, 1, 0), (0, 2))   # cut through the hub's plate: shows the slots
    draw_geom(back, hub, COL["hub"], alpha=0.25)
    back.invert_xaxis()
    back.set_title("From behind (from the back panel), hub on.\nBlue: the plate. Orange: the angle. Grey: the hub's plate (outline guessed from the photo).")
    dim(back, (35, 6), (-35, 6), "70 (hub 63 + a bit)", off=(0, 3))
    dim(back, (44, 0), (44, -132), "132 = the PSU's height", off=(5, 0))
    dim(back, (-41, 0), (-41, -130), "130: hub's\nbottom edge", off=(-6, 20))
    dim(back, (-41, -20), (-41, 0), "20", off=(-3, 0))
    dim(back, (-10, TOP_ROW), (-10, BOT_ROW), "80", off=(0, 0))
    dim(back, (-20, -38), (0, -38), "20", off=(0, 0))
    dim(back, (0, -38), (20, -38), "20", off=(0, 0))
    label(back, (-20, TOP_ROW), "6 hooks, one through\neach slot (10 x 3.6)", (-48, -75))
    label(back, (28, -10), "angle's 20 leg glued\nonto the plate", (55, -30))
    back.text(0, -88, "hub", ha="center", fontsize=14, color="#333")
    back.text(0, -150, "Seen from behind the machine: the hub's top faces you, so it is your photo turned over.",
              ha="center", fontsize=9, color="#666")
    back.set_xlim(70, -70), back.set_ylim(-160, 18)

    # side, cut through the middle hooks (x = 0)
    cut(side, m, ["psu", "panel", "plate", "angle", "hub"])
    side.set_title("From the side, cut through the middle hooks.\nPSU left (grey), back panel right (red, where 8 mm puts it).")
    dim(side, (-40, 7), (0, 7), "40 on top of the PSU", off=(0, 2))
    dim(side, (-44, 0), (-44, 4), "4", off=(-3, 0))
    dim(side, (9, 0), (9, -20), "20", off=(3, 0))
    dim(side, (0, -138), (3, -138), "3", off=(1.5, -3))
    dim(side, (30, -100), (36.5, -100), "5 left\n(was 8)", off=(4, 7))
    label(side, (4.5, TOP_ROW), "hook", (18, -30))
    label(side, (-30, -70), "power supply\n(its back face)", (-30, -70))
    side.text(18, -90, "hub\n(25 deep:\nguess)", ha="center", fontsize=10, color="#333")
    side.set_xlim(-55, 50), side.set_ylim(-150, 15)

    # one hook (top row, middle) close up: pushed on, then slid down
    for ax, hubp, title in ((push, "hub_up", "1. Hold the hub 1 mm high, push it on\nover the heads, flat against the plate"),
                            (locked, "hub", "2. Slide it down 1 mm: the slot's top edge\nsits on the neck, the head's lip holds it on")):
        cut(ax, m, ["plate", hubp])
        ax.set_title(title)
        ax.set_xlim(-2, 11), ax.set_ylim(TOP_ROW - 5, TOP_ROW + 5)
    z = TOP_ROW
    dim(locked, (5.6, z - 0.6), (5.6, z + 2.6), "head\n3.2", off=(1.3, 0))
    dim(locked, (4.4, z - 0.6), (4.4, z + 1.8), "neck\n2.4", off=(-1.6, 0))
    dim(locked, (8.6, z + 1.8), (8.6, z + 2.6), "0.8 lip", off=(1.4, 0))
    dim(locked, (3, z + 3.6), (5, z + 3.6), "hub sheet 2", off=(0, 0.6))
    dim(locked, (5.3, z - 1.6), (7.3, z - 1.6), "head 2", off=(1.8, -0.6))
    dim(push, (8.6, z - 0.8), (8.6, z + 2.8), "slot\n3.6", off=(1.3, 0))
    dim(push, (0, z - 3.6), (3, z - 3.6), "plate 3", off=(0, -0.6))
    label(push, (6, z + 3.5), "hub's sheet", (8, z + 4.3))
    label(push, (1.5, z + 2), "plate", (0.5, z + 4.3))
    for ax in (back, side, push, locked):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT, dpi=90)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
