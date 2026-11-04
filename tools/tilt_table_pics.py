#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawings of the friction tilt table (scad/tilt_table.scad).

    uv run tools/tilt_table_pics.py

    view/tilt_table.png   cut through the hinge axis (flat), the bump in its divot close up,
                          and from the side at 0 and at the 63 deg limit; below, the click
                          teeth: the tongue face-on, and cut across the teeth at a click and between
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh

from brick_frame_pics import dim, draw_geom, label, section_geom

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "tilt_table.scad"
OUT = ROOT / "view"
GREEN, YELLOW = "#3cb371", "#d4a017"
AXIS_Z, HALF = 19.8, 19.8
TILT_MAX = 63.2796        # tilt_table.scad echoes it
CLICK_CUT = AXIS_Z + 5   # a level cut across the teeth above the axis


def export(tmp, part, theta=0):
    out = Path(tmp) / f"{part}_{theta}.stl"
    subprocess.run(["openscad", "--backend=manifold", "-o", str(out), "-D", f'part="{part}"', "-D", f"theta={theta}",
                    str(SCAD)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return trimesh.load(out)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        bot, top0, top_half = export(tmp, "bottom"), export(tmp, "top"), export(tmp, "top", 7.5)
        rolls = {t: export(tmp, "top", t) for t in (-TILT_MAX, -40, -20, 20, 40, TILT_MAX)}
    fig, ((a, b, c), (d, e, f)) = plt.subplots(2, 3, figsize=(19, 15), gridspec_kw=dict(width_ratios=[1.25, 0.8, 1.25]))

    # a: cut through the hinge axis (y = 0), looking along +y: each fork with a tongue in it
    cut = ((0, 0, 0), (0, 1, 0), (0, 2))
    draw_geom(a, section_geom(bot, *cut), GREEN)
    draw_geom(a, section_geom(top0, *cut), YELLOW)
    a.axhline(AXIS_Z, color="#c0392b", lw=0.8, ls="--")
    a.text(22, AXIS_Z + 0.6, "hinge axis", color="#c0392b", fontsize=9)
    a.set_title("Cut through the hinge axis, flat: the same print twice,\nthe top one turned over")
    label(a, (18.5, 12), "bottom's fork\n(a hole through\neach tine)", (31, 5))
    label(a, (15.5, 28), "top's tongue in it\n(a button on each face)", (31, 33))
    label(a, (-15.5, 12), "bottom's tongue", (-31, 5))
    label(a, (-18.5, 28), "top's fork", (-31, 33))
    label(a, (-8, 3.8), "through pin holes, taper on\nthe bed (outer) face", (-12, -6))
    label(a, (16, 2), "blind 8 under\nthe triangles", (17, -6))
    dim(a, (-HALF, 42.5), (HALF, 42.5), "39.6 (5 units)")
    dim(a, (-23.5, 0), (-23.5, 39.6), "39.6\nflat", off=(-3.5, 6))
    dim(a, (-11, 7.6), (-11, 32), "gap 24.4", off=(0, 3))
    a.set_xlim(-40, 40), a.set_ylim(-10, 46)

    # b: close up of the right pair at the axis
    draw_geom(b, section_geom(bot, *cut), GREEN)
    draw_geom(b, section_geom(top0, *cut), YELLOW)
    b.set_title("Close up: the right fork clamping the top's tongue")
    label(b, (18.0, AXIS_Z), "buttons: r 2.6,\n1.2 high,\nsides 50 deg", (21.3, 23.0))
    label(b, (19.5, AXIS_Z - 2.4), "holes through\nthe tines, r 2.75", (21.2, 12.8))
    label(b, (13.8, 16.0), "tongue 3.5 in a 3.5 slot\n(no squeeze: the teeth\nhold the angle)", (12.6, 12.8))
    dim(b, (11.3, 26.8), (13.8, 26.8), "2.5", off=(0, 0.6))
    dim(b, (13.8, 26.8), (17.3, 26.8), "slot 3.5", off=(0, 0.6))
    dim(b, (17.3, 26.8), (19.8, 26.8), "2.5", off=(0, 0.6))
    b.set_xlim(10, 23), b.set_ylim(11, 31)

    # c: from the side (+x): the bottom plate cut through its fork's outer tine (x = 19.5, outside the holes),
    # the top plate's body (x = 4, between hole columns) as it tilts, rolling round the triangle's arc
    side = lambda x: ((x, 0, 0), (1, 0, 0), (1, 2))
    draw_geom(c, section_geom(bot, *side(19.5)), GREEN)
    draw_geom(c, section_geom(top0, *side(4)), YELLOW, alpha=0.3)
    for t, m in rolls.items():
        lim = abs(t) == TILT_MAX
        draw_geom(c, section_geom(m, *side(4)), "#c0392b" if lim else YELLOW, alpha=0.2 if lim else 0.06, lw=1.0 if lim else 0.6)
    c.plot([0], [AXIS_Z], "o", color="#c0392b")
    c.set_title("From the side: the top plate tilting (flat, 20, 40, and the 63 deg\nlimits in red) rolls round the triangle's top, 0.4 clear")
    label(c, (0, 31.6), "arc r 11.8 round the axis", (0, 52))
    label(c, (15.0, 16.4), "at the limit the plate lies\nalong the side, 0.4 off", (30, 2))
    label(c, (-19.5, 7.8), "plates meet at +-63 deg", (-28, -8))
    c.set_xlim(-45, 45), c.set_ylim(-14, 58)

    # d: the bottom plate's tongue face-on (from -x), cut through its teeth
    draw_geom(d, section_geom(bot, (-17.5, 0, 0), (1, 0, 0), (1, 2)), GREEN)
    d.plot([0], [AXIS_Z], "o", color="#c0392b")
    d.axhline(CLICK_CUT, color="#555", lw=0.8, ls=":")
    d.text(9, CLICK_CUT + 0.4, "cut for the right-hand views", fontsize=9, color="#555")
    d.set_title("The tongue face-on, cut through its teeth: 24 ridges, 15 deg apart,\nflanks 19.3 deg: 0.2 high at r 4.5 to 0.4 at r 9 (grooves in the tines, 0.1 deeper)")
    label(d, (0, AXIS_Z + 5.5), "teeth from r 4.5 to r 9,\nends ramped", (-12, 33))
    label(d, (0, AXIS_Z), "button (pivot)", (-12, 8))
    d.set_xlim(-14, 14), d.set_ylim(6, 36)

    # e, f: a level cut across the teeth (z = axis + 5), the right fork and the top plate's tongue, from above
    for ax, top, title in ((e, top0, "At a click (every 15 deg, flat is one):\nevery ridge in its groove"),
                           (f, top_half, "Halfway between (7.5 deg): the ridges ride out of the grooves and spread\neach tine up to 0.37 (the click); the 1.2 buttons stay 0.83 in their holes")):
        draw_geom(ax, section_geom(bot, (0, 0, CLICK_CUT), (0, 0, 1), (0, 1)), GREEN)
        draw_geom(ax, section_geom(top, (0, 0, CLICK_CUT), (0, 0, 1), (0, 1)), YELLOW)
        ax.set_title(title)
        ax.set_xlim(10.5, 20.5), ax.set_ylim(-6, 6)
    label(e, (12.6, 4.5), "inner tine", (12.6, -5))
    label(e, (15.5, 4.5), "tongue", (15.5, -5))
    label(e, (18.6, 4.5), "outer tine", (18.6, -5))

    for ax in (a, b, c, d, e, f):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "tilt_table.png", dpi=110)
    print("wrote", OUT / "tilt_table.png")


if __name__ == "__main__":
    main()
