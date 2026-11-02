#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawings of the Nezha brick's side holes and the cage round it (scad/brick_frame.scad).

    uv run tools/brick_frame_pics.py

Exports the pieces with OpenSCAD and draws sections of the meshes with matplotlib:
    view/brick_side_holes.png   the J side's two holes: face-on (a slice 0.5 in) and from above (z = 4)
    view/brick_frame_cage.png   the cage from the side and from the motor end, cut just inside its faces, dimensioned
    view/brick_frame_plan.png   the cage and brick cut at the bottom ring's holes (z = 4), dimensioned
    view/brick_frame_stand.png  the cage stood on its motor end, from the side and from the front
"""
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "brick_frame.scad"
OUT = ROOT / "view"
PIECES = {"brick": "#9a9a9a", "side_j": "#f29a00", "side_iic": "#4169e1", "bar_bottom": "#3cb371", "bar_top": "#2e8b57",
          "pins": "#333333"}


def export(tmp, stand=False):
    procs, meshes = [], {}
    for p in PIECES:
        out = Path(tmp) / f"{p}_{stand}.stl"
        procs.append((p, out, subprocess.Popen(["openscad", "--backend=manifold", "-o", str(out), "-D", f'part="{p}"',
                                                 "-D", f"stand={'true' if stand else 'false'}", str(SCAD)],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for p, out, pr in procs:
        pr.wait()
        meshes[p] = trimesh.load(out)
    return meshes


def section(ax, mesh, origin, normal, axes, color, fill=True, lw=1.0):
    """Cut mesh with a plane and draw each loop of the cut, using model axes `axes` (e.g. (0, 1)) as screen x, y."""
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    if s is None:
        return
    for poly in s.discrete:
        xy = poly[:, list(axes)]
        if fill:
            ax.fill(xy[:, 0], xy[:, 1], color=color, alpha=0.35, lw=0)
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=lw)


def section_geom(mesh, origin, normal, axes):
    """A planar cut as shapely geometry with its holes (loops combined even-odd)."""
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    g = Polygon()
    for poly in (s.discrete if s is not None else []):
        g = g.symmetric_difference(Polygon(poly[:, list(axes)]).buffer(0))
    return g


def silhouette(mesh, axes):
    """The mesh's outline seen along the axis not in `axes`: the union of its projected triangles."""
    tri = mesh.vertices[mesh.faces][:, :, list(axes)]
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    keep = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) > 1e-9
    return unary_union([Polygon(t) for t in tri[keep]])


def draw_geom(ax, g, color, alpha=0.45, lw=1.0):
    """Fill shapely polygons, holes left open."""
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or not hasattr(p, "exterior"):
            continue
        rings = [np.asarray(p.exterior.coords)] + [np.asarray(r.coords) for r in p.interiors]
        verts = np.concatenate(rings)
        codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r) - 2) + [MPath.CLOSEPOLY] for r in rings])
        ax.add_patch(PathPatch(MPath(verts, codes), fc=color, alpha=alpha, ec="none"))
        for r in rings:
            ax.plot(r[:, 0], r[:, 1], color=color, lw=lw)


def dim(ax, p0, p1, text, off=(0, 0), color="#222"):
    ax.annotate("", p0, p1, arrowprops=dict(arrowstyle="<->", color=color, lw=1, shrinkA=0, shrinkB=0))
    m = ((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1])
    ax.text(*m, text, ha="center", va="center", fontsize=10, color=color,
            bbox=dict(fc="white", ec="none", pad=1.0))


def label(ax, xy, text, at, color="#222"):
    ax.annotate(text, xy, at, fontsize=10, color=color, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8), bbox=dict(fc="white", ec=color, lw=0.5, pad=2))


def side_holes(m):
    fig, (a, b) = plt.subplots(1, 2, figsize=(15, 6.5), gridspec_kw=dict(width_ratios=[1.5, 1]))
    # face-on: the J face (y = +30) seen from outside, x to the right, z up; slice 0.5 in
    section(a, m["brick"], (0, 29.5, 0), (0, 1, 0), (0, 2), PIECES["brick"], fill=False, lw=1.5)
    a.set_xlim(-40, 40), a.set_ylim(-2, 14)
    a.set_title("J side, face-on (slice 0.5 in from the face)\nmicro:bit end left, motor end right")
    label(a, (-28, 7.6), "arch, the same at all four holes", (-23, 11.5))
    label(a, (28, 0), "arch open to the bottom, 1.86 deep: a LEGO beam's end\n(r 3.68), then a normal pin hole", (19, 11.5), "#c0392b")
    for x in (-15, 0, 15):
        a.plot([x], [-1], marker="^", color="#888")
    a.text(0, -1.6, "cable slots", ha="center", fontsize=8, color="#888")
    # from above: section z = 4 through the arched hole
    section(b, m["brick"], (0, 0, 4), (0, 0, 1), (0, 1), PIECES["brick"])
    section(b, m["side_j"], (0, 0, 4), (0, 0, 1), (0, 1), PIECES["side_j"])
    section(b, m["pins"], (0, 0, 4), (0, 0, 1), (0, 1), PIECES["pins"], fill=True)
    b.set_xlim(20, 36), b.set_ylim(18, 44)
    b.set_title("From above, cut at the hole (z = 4), motor end right")
    dim(b, (36 - 0.5, 28.14), (36 - 0.5, 30), "1.86", off=(-1.7, 0), color="#c0392b")
    label(b, (28, 24), "normal LEGO hole\n(pin's collar on the arch's floor)", (24.5, 21))
    label(b, (31.5, 37.5), "J side's bottom rail", (33, 41))
    label(b, (25, 29.2), "beam end on the rail\nin the arch", (22.5, 33), "#c0392b")
    for ax in (a, b):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "brick_side_holes.png", dpi=110)


def cage(m):
    fig, (a, b) = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw=dict(width_ratios=[1.35, 1]))
    # side: from the IIC side (-y), motor end right; the side cut through its outer column (y = -40), the brick 0.5 inside its face
    draw_geom(a, section_geom(m["side_iic"], (0, -40.0, 0), (0, 1, 0), (0, 2)), PIECES["side_iic"])
    draw_geom(a, section_geom(m["brick"], (0, -29.5, 0), (0, 1, 0), (0, 2)), PIECES["brick"], alpha=0.12, lw=0.8)
    a.set_title("IIC side, cut through its outer column, motor end right.\nCircles: holes out (y); slots up and down: holes up (z); slots across: holes along x")
    dim(a, (-40, 54), (48, 54), "88 = 11 units")
    dim(a, (54, 0), (54, 48), "48 =\n6 units")
    dim(a, (12, 43.7), (12, 47.8), "4.1", off=(3.5, 0), color="#c0392b")
    label(a, (-4, 44), "top ring: out, up, out, up ... from out at each corner", (-16, 64))
    label(a, (-4, 4), "bottom ring, the same, pinned to the brick", (-8, -10))
    label(a, (-36, 28), "post: across, out,\nacross, out", (-57, 22))
    label(a, (-36, 40), "out twice at the\npost's top", (-57, 44), "#c0392b")
    label(a, (44, 12), "post", (62, 8))
    label(a, (0, 20), "window: the IIC sockets\n(J on the other side)", (24, 32), "#555")
    label(a, (12, 45.5), "clear of the ridge (43.7)", (44, 64), "#c0392b")
    a.set_xlim(-66, 72), a.set_ylim(-18, 72)
    # end: from the motor end (+x), the J side on the right; cut 0.8 inside the end faces
    for p in ("side_j", "side_iic", "bar_bottom", "bar_top"):
        draw_geom(b, section_geom(m[p], (47.0, 0, 0), (1, 0, 0), (1, 2)), PIECES[p])
    draw_geom(b, section_geom(m["brick"], (39.5, 0, 0), (1, 0, 0), (1, 2)), PIECES["brick"], alpha=0.12, lw=0.8)
    b.set_title("From the motor end")
    dim(b, (-44, 54), (44, 54), "88 = 11 units")
    label(b, (0, 4), "end bar: along, up, along ... (pins into 3 of the brick's 5 end holes)", (0, -10))
    label(b, (0, 44), "end bar (the same print)", (0, 64))
    label(b, (10, 20), "M1-M4 sockets", (10, 32), "#555")
    label(b, (40, 24), "posts", (50, 64))
    b.set_xlim(-60, 60), b.set_ylim(-18, 72)
    for ax in (a, b):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "brick_frame_cage.png", dpi=100)


def plan(m):
    fig, ax = plt.subplots(figsize=(11, 11))
    for p in ("brick", "side_j", "side_iic", "bar_bottom", "pins"):
        section(ax, m[p], (0, 0, 4), (0, 0, 1), (0, 1), PIECES[p])
    # the cage's grid
    for x in np.arange(-40, 49, 8):
        ax.axvline(x, color="#ccc", lw=0.4, zorder=0)
    for y in np.arange(-44, 45, 8):
        ax.axhline(y, color="#ccc", lw=0.4, zorder=0)
    dim(ax, (-40, 50), (48, 50), "88 = 11 units (brick 80 + 8 at the motor end)")
    dim(ax, (54, -44), (54, 44), "88 = 11 units", off=(0, 0))
    dim(ax, (-46, 36), (-46, 44), "8", off=(0, 0))
    dim(ax, (-46, -30), (-46, 30), "brick\n60,\ncentred")
    dim(ax, (0, 30), (0, 36.2), "6.2", off=(3, 0), color="#c0392b")
    label(ax, (4, 33), "cable gap all round: the sides are\nonly their outer unit", (4, 22), "#c0392b")
    label(ax, (-20, 40), "holes alternate: out (through the side), up, out, up ...", (-14, 58))
    label(ax, (44, 40), "corner: out, pins the end bar", (30, 58))
    label(ax, (44, 0), "end bar: along, up, along ...\npins into 3 of the brick's end holes", (64, 12))
    label(ax, (28, 29), "pad across the gap, beam end\nin the arch, hole right through", (24, 14), "#c0392b")
    label(ax, (-28, -29), "pads and beam ends at\nall four of the brick's pins", (-20, -16), "#c0392b")
    ax.text(-36, -4, "micro:bit\nend (posts,\nno bars)", fontsize=10, va="center")
    ax.text(36, -6, "M1-M4\nsockets\n(above\nthe bar)", fontsize=9, va="center", ha="center", color="#666")
    ax.text(0, 37, "J side", ha="center", fontsize=10), ax.text(0, -37, "IIC side", ha="center", fontsize=10)
    ax.set_xlim(-50, 72), ax.set_ylim(-50, 64), ax.set_aspect("equal")
    ax.set_title("Cage round the Nezha brick, from above, cut at the bottom ring's holes (z = 4); the top ring (z = 44) is the same.\n"
                 "orange / blue: the two sides, green: the motor-end bar, dark: 2L pins; grid: 8 mm cells")
    fig.tight_layout()
    fig.savefig(OUT / "brick_frame_plan.png", dpi=100)


def stand(m):
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 7.5))
    # side: from the IIC side (-y), x forward to the right, z up; front: from +x, the J side (+y) on the right
    for p in ("brick", "side_iic", "bar_bottom", "bar_top", "side_j", "pins"):
        for ax, axes in ((a, (0, 2)), (b, (1, 2))):
            draw_geom(ax, silhouette(m[p], axes), PIECES[p], alpha=0.25 if p == "brick" else 0.55, lw=0.8)
    for ax in (a, b):
        ax.axhline(0, color="#555", lw=1.5)
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    a.set_title("Stood up, from the IIC side: robot front to the right")
    b.set_title("Stood up, from the front (the display faces you)")
    label(a, (43.7, 60), "display / switch\nface forward", (66, 60))
    label(a, (25, 4), "M1-M4 sockets face down,\n8 off the plate", (62, 10))
    label(a, (20, 88), "micro:bit USB end up", (40, 98))
    label(a, (4, 30), "bottom ring", (-24, 30))
    label(a, (44, 30), "top ring", (66, 30))
    label(b, (-37, 60), "IIC side", (-48, 96))
    label(b, (37, 60), "J side", (48, 96))
    label(b, (0, 4), "end bars", (0, -10))
    a.set_xlim(-48, 85), a.set_ylim(-18, 104)
    b.set_xlim(-60, 60), b.set_ylim(-18, 104)
    fig.tight_layout()
    fig.savefig(OUT / "brick_frame_stand.png", dpi=100)


def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        flat = export(tmp)
        side_holes(flat)
        cage(flat)
        plan(flat)
        stand(export(tmp, stand=True))
    for n in ("brick_side_holes", "brick_frame_cage", "brick_frame_plan", "brick_frame_stand"):
        print(f"wrote view/{n}.png")


if __name__ == "__main__":
    main()
