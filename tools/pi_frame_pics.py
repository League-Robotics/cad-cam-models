#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawings of the frame round a Raspberry Pi (scad/pi_frame.scad).

    uv run tools/pi_frame_pics.py

Exports the pieces with OpenSCAD and draws them with matplotlib (the helpers are brick_frame_pics.py's):
    view/pi_frame_views.png   from above (the base cut at its holes, the Pi's outline over it), from the
                              side (cut down the middle) and from the USB end, dimensioned
    view/pi_frame_plate.png   the five prints on the bed (an OpenSCAD render)
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import trimesh

from brick_frame_pics import dim, draw_geom, label, section_geom, silhouette

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "pi_frame.scad"
OUT = ROOT / "view"
PIECES = {"base": "#3cb371", "window_a": "#f29a00", "window_b": "#4169e1", "top_bars": "#2e8b57", "pins": "#333333",
          "pi": "#1f7a3a"}


def export(tmp):
    procs = [(p, Path(tmp) / f"{p}.stl") for p in PIECES]
    runs = [subprocess.Popen(["openscad", "--backend=manifold", "-o", str(o), "-D", f'part="{p}"', str(SCAD)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for p, o in procs]
    for r in runs:
        r.wait()
    return {p: trimesh.load(o) for p, o in procs}


def views(m):
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(21, 7.5), gridspec_kw=dict(width_ratios=[1.1, 1.1, 1]))
    # from above: the frame cut at the bottom ring's holes (z = 4), the Pi's outline and the weld posts over it
    for p in ("base", "window_a", "window_b"):
        draw_geom(a, section_geom(m[p], (0, 0, 4), (0, 0, 1), (0, 1)), PIECES[p])
    draw_geom(a, section_geom(m["base"], (0, 0, 12), (0, 0, 1), (0, 1)), "#c0392b", alpha=0.6)
    draw_geom(a, silhouette(m["pi"], (0, 1)), PIECES["pi"], alpha=0.12, lw=0.8)
    a.set_title("From above, cut at the bottom's holes (z = 4); the Pi's outline over it")
    dim(a, (-44, 50), (44, 50), "88 = 11 units")
    dim(a, (52, -44), (52, 44), "88")
    dim(a, (-38.86, 31.5), (18.86, 31.5), "57.7", color="#c0392b")
    dim(a, (26, -24.24), (26, 24.24), "48.5", color="#c0392b")
    label(a, (18.86, 24.24), "weld posts (Yahboom's):\n6 across, 6 tall, 2.4 pin 3 tall", (16, 62), "#c0392b")
    label(a, (0, 24), "deck bars at y = +-24:\nthe mounting spot", (-22, 62))
    label(a, (40, 0), "end bars (the base)", (60, 10))
    label(a, (0, 40), "windows: holes out, up, out ...", (-10, -60))
    a.text(44.5, 35, "USB +\nEthernet", fontsize=9, color="#1f7a3a")
    a.text(-30, -34.5, "power, HDMI, audio", fontsize=9, color="#1f7a3a")
    a.set_xlim(-60, 72), a.set_ylim(-70, 72)
    # side: cut through the USB 2 pair (y = -19), from -y, the USB end right
    for p in ("base", "top_bars", "pi"):
        draw_geom(b, section_geom(m[p], (0, -19, 0), (0, 1, 0), (0, 2)), PIECES[p], alpha=0.3 if p == "pi" else 0.45)
    b.set_title("From the side, cut through the Pi's USB 2 pair (y = -19), USB end right")
    dim(b, (-50, 0), (-50, 40), "40 = 5 units")
    dim(b, (0, 7.8), (0, 13.8), "6", off=(2.5, 0), color="#c0392b")
    dim(b, (36, 31.2), (36, 32.2), "1.0", off=(-4, 2.5), color="#c0392b")
    label(b, (30, 24), "USB out through\nthe end window", (16, 50))
    label(b, (-20, 14.5), "board 13.8 up", (-20, -8))
    label(b, (40, 36), "top bar", (55, 50))
    b.set_xlim(-60, 66), b.set_ylim(-14, 58)
    # end: from +x, the frame cut 0.8 inside the end face, the Pi behind it
    draw_geom(c, silhouette(m["pi"], (1, 2)), PIECES["pi"], alpha=0.3)
    for p in ("base", "top_bars", "window_a", "window_b"):
        draw_geom(c, section_geom(m[p], (43.0, 0, 0), (1, 0, 0), (1, 2)), PIECES[p])
    c.set_title("From the USB end (x = 43, just inside the end face)")
    dim(c, (-44, 46), (44, 46), "88")
    label(c, (0, 4), "end bar: joint, x, z, x, z ... joint", (0, -8))
    label(c, (40, 20), "window post:\nout, across, out,\nacross, out", (54, 24))
    label(c, (-14, 24), "USB / Ethernet", (-30, 52), "#1f7a3a")
    c.set_xlim(-58, 72), c.set_ylim(-14, 58)
    for ax in (a, b, c):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "pi_frame_views.png", dpi=95)


def plate():
    subprocess.run(["openscad", "--backend=manifold", "-o", str(OUT / "pi_frame_plate.png"), "--imgsize=1400,1000",
                    "--camera=10,45,0,55,0,25,380", "--projection=p", "--colorscheme=Tomorrow", "-D", 'part="print"',
                    str(SCAD)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        views(export(tmp))
    plate()
    for n in ("pi_frame_views", "pi_frame_plate"):
        print(f"wrote view/{n}.png")


if __name__ == "__main__":
    main()
