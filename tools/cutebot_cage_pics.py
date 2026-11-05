#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree", "pillow"]
# ///
"""Labelled drawing of the Cutebot Pro cage (scad/cutebot_cage.scad, v2).

    uv run tools/cutebot_cage_pics.py

    view/cutebot_cage.png  front and rear 3D views; the plan with the robot's keep-outs; a cross-section through
                           the axle (the cell grid's levels k); a side section through the lobe, front bulkhead,
                           deck and rear bulkhead
"""
import json
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Circle, Rectangle

import brick_frame_pics as bf

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "cutebot_cage.scad"
OUT = ROOT / "view"
OUTLINE = Path("/Volumes/Proj/proj/robot-projects/carvera/docs/cutebot-pro-outline.json")
COL = {"nose": "#e67e22", "lobe": "#3cb371", "rail": "#4169e1", "wall": "#5dade2", "front": "#c0392b",
       "skirt": "#d35400", "deck": "#8e44ad", "rear": "#c0392b", "fwall": "#a93226", "fside": "#d35400", "fdeck": "#7d3c98", "caster": "#444444", "screws": "#7f8c8d",
       "pins": "#222222"}
PIECES = ["nose", "lobe_l", "lobe_r", "rail_l", "rail_r", "wall_l", "wall_r", "front_l", "front_r",
          "skirt_l", "skirt_r", "deck_l", "deck_r", "rear", "fwall", "fside_l", "fside_r", "fdeck", "caster", "screws", "pins"]
VIEWS = {"iso_front": "0,20,30,58,0,215,600", "iso_rear": "0,20,30,58,0,35,600"}


def col(p):
    return COL[p.split("_")[0]]


def export(tmp):
    procs, meshes, imgs = [], {}, {}
    for p in PIECES:
        out = Path(tmp) / f"{p}.stl"
        procs.append((p, out, subprocess.Popen(["openscad", "--backend=manifold", "-D", f'part="{p}"', "-o", str(out), str(SCAD)],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for v, cam in VIEWS.items():
        out = Path(tmp) / f"{v}.png"
        procs.append((None, out, subprocess.Popen(
            ["openscad", "--preview", "-o", str(out), "--imgsize=1300,1000", f"--camera={cam}", "--viewall",
             "--autocenter", "--projection=o", "--colorscheme=Tomorrow", str(SCAD)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for p, out, pr in procs:
        pr.wait()
        if p:
            meshes[p] = trimesh.load(out)
        else:
            imgs[out.stem] = plt.imread(out)
    return meshes, imgs


def iso(ax, img, title):
    h, w = img.shape[:2]
    ax.imshow(img[int(0.08 * h):int(0.80 * h), int(0.24 * w):int(0.90 * w)])
    ax.set_title(title, fontsize=12)
    ax.axis("off")


def keepouts_plan(ax):
    ol = json.loads(OUTLINE.read_text())
    for k, c in (("footprint", "#bbb"), ("lower_deck", "#2a9d8f")):
        p = np.array(ol[k] + ol[k][:1])
        ax.plot(p[:, 0], p[:, 1], color=c, lw=1)
    ax.add_patch(Rectangle((-7.75, -33.54), 18.25, 70.88, fc="#f6d55c", ec="#c9a227", alpha=0.6))
    for x0, x1 in ((-55.26, -38.81), (36.74, 53.97)):
        ax.add_patch(Rectangle((x0, -25.5), x1 - x0, 51, fc="#333", alpha=0.3, ec="none"))
    ax.add_patch(Rectangle((-26.91, 50.62), 51.6, 1.6, fc="#2e7d32"))
    for x in (-28.5, 26):
        ax.add_patch(Rectangle((x, 48), 2.5, 8, fc="#222"))
    for x in (-32, 32):
        ax.add_patch(Rectangle((x - 3, 71), 6, 4, fc="#ffd400", ec="#b59500"))


def plan(ax, m):
    keepouts_plan(ax)
    # the low pieces cut at their mid-heights; the deck, skirts and bulkheads as outlines
    for p, z in (("lobe_l", 24), ("lobe_r", 24), ("nose", 24), ("rail_l", 39.9), ("rail_r", 39.9)):
        bf.draw_geom(ax, bf.section_geom(m[p], (0, 0, z), (0, 0, 1), (0, 1)), col(p), alpha=0.55)
    for p in ("front_l", "front_r", "skirt_l", "skirt_r", "rear", "fwall", "fside_l", "fside_r"):
        bf.draw_geom(ax, bf.silhouette(m[p], (0, 1)), col(p), alpha=0.35)
    for p in ("deck_l", "deck_r", "fdeck"):
        g = bf.silhouette(m[p], (0, 1))
        for q in getattr(g, "geoms", [g]):
            c = np.asarray(q.exterior.coords)
            ax.plot(c[:, 0], c[:, 1], color=col(p), lw=2, ls="--")
    bf.draw_geom(ax, bf.silhouette(m["caster"], (0, 1)), COL["caster"], alpha=0.3)
    for x, y in ((-32, 64), (-8, 80), (8, 80), (32, 64), (-16, -8), (-16, 8), (16, -8), (16, 8)):
        ax.add_patch(Circle((x, y), 1.7, fc="#c0392b", ec="none"))
    ax.set_xlim(-72, 72)
    ax.set_ylim(-50, 122)
    ax.set_aspect("equal")
    ax.set_xticks(range(-72, 73, 8))
    ax.set_yticks(range(-48, 121, 8))
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.25)
    ax.set_xlabel("x (robot's right)")
    ax.set_ylabel("y (forward)")
    ax.set_title("Plan, front up: lower parts cut at mid-height, deck dashed", fontsize=12)
    lab = bf.label
    lab(ax, (0, 84), "nose 5 x 2, M3 into B2 / B3,\npinned into the front wall", (-40, 112), COL["nose"])
    lab(ax, (0, 108), "ball caster on the front\nwall's bottom row", (44, 114), COL["caster"])
    lab(ax, (32, 96), "front wall 17 x 5: windows\nin front of the headlights", (56, 104), COL["fwall"])
    lab(ax, (-64, 70), "front side", (-66, 98), COL["fside"])
    lab(ax, (0, 56), "front deck: opening over\nthe micro:bit", (-2, 66), COL["fdeck"])
    lab(ax, (-44, 56), "lobe, M3 into B1;\npins into the bulkhead", (-50, 86), COL["lobe"])
    lab(ax, (-48, 40), "front bulkhead", (-64, 64), COL["front"])
    lab(ax, (-64, 10), "skirt", (-66, -20), COL["skirt"])
    lab(ax, (-40, -12), "deck over\nthe wheel", (-44, 22), COL["deck"])
    lab(ax, (-16, 0), "rail (+ wall on its\nouter column)", (-36, -26), COL["rail"])
    lab(ax, (1, 10), "battery:\nopen above", (30, 30), "#a07d00")
    lab(ax, (0, -40), "rear bulkhead, full width", (0, -47), COL["rear"])
    lab(ax, (32, 73), "headlight", (44, 80), "#b59500")


def cross(ax, m):
    """Section through the axle (y = 0): the levels k."""
    for p in ("rail_l", "rail_r", "wall_l", "wall_r", "skirt_l", "skirt_r", "deck_l", "deck_r"):
        bf.draw_geom(ax, bf.section_geom(m[p], (0, 4.01, 0), (0, 1, 0), (0, 2)), col(p), alpha=0.5)
    for x0, x1 in ((-55.26, -38.81), (36.74, 53.97)):
        ax.add_patch(Rectangle((x0, 0), x1 - x0, 51, fc="#333", alpha=0.3, ec="none"))
    ax.add_patch(Rectangle((-7.75, 36.1), 18.25, 22.7, fc="#f6d55c", ec="#c9a227", alpha=0.6))
    ax.add_patch(Rectangle((-25, 34.6), 50, 1.5, fc="#ccc"))
    for k in range(6):
        z = 24 + 8 * k
        ax.axhline(z, color="#999", lw=0.5, ls=":")
        ax.text(73, z, f"k={k}  z {z}", fontsize=8, va="center")
    ax.axhline(0, color="#222", lw=1)
    ax.text(-70, 22, "k=0: plates on the lower\ndeck; caster pins", fontsize=8)
    ax.text(-30, 70, "k=5: decks, 9 over the tyres", fontsize=9, color=COL["deck"])
    ax.text(-6, 40, "battery\nopen", fontsize=9, ha="center")
    ax.set_xlim(-74, 92)
    ax.set_ylim(-3, 76)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    ax.set_title("Cut at y = 4 (between hole rows, by the axle), from behind: one grid, k = 0 ... 5", fontsize=12)


def side(ax, m):
    """Section at x = -44 (between hole columns): lobe, front bulkhead, deck, rear bulkhead, skirt behind."""
    x = -44.01
    bf.draw_geom(ax, bf.silhouette(m["skirt_l"], (1, 2)), COL["skirt"], alpha=0.12)
    bf.draw_geom(ax, bf.silhouette(m["fside_l"], (1, 2)), COL["fside"], alpha=0.12)
    for p in ("lobe_l", "front_l", "deck_l", "rear", "fdeck", "fwall", "nose"):
        bf.draw_geom(ax, bf.section_geom(m[p], (x, 0, 0), (1, 0, 0), (1, 2)), col(p), alpha=0.5)
    ax.add_patch(Circle((0, 25.5), 25.5, fc="#333", alpha=0.25, ec="#333"))
    ax.axhline(20.2, color="#2a9d8f", lw=0.8, ls=":")
    ax.axhline(0, color="#222", lw=1)
    ax.set_xlim(-50, 104)
    ax.set_ylim(-3, 72)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_xlabel("y (forward)")
    ax.set_ylabel("z")
    ax.set_title("Cut at x = -44 (between hole columns), from the left: the ring and the lobe", fontsize=12)
    lab = bf.label
    lab(ax, (52, 24), "lobe (k=0), pinned\ninto the bulkhead", (60, 10), COL["lobe"])
    lab(ax, (40, 40), "front\nbulkhead", (52, 48), COL["front"])
    lab(ax, (96, 40), "front wall", (88, 10), COL["fwall"])
    lab(ax, (80, 64), "front deck", (70, 70), COL["fdeck"])
    lab(ax, (70, 32), "front side\n(behind)", (72, 50), COL["fside"])
    lab(ax, (0, 64), "deck", (14, 69), COL["deck"])
    lab(ax, (-40, 40), "rear", (-44, 64), COL["rear"])
    lab(ax, (-30, 30), "skirt\n(behind)", (-26, 8), COL["skirt"])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        m, imgs = export(tmp)
    fig = plt.figure(figsize=(20, 26))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.95, 1.45, 0.75])
    iso(fig.add_subplot(gs[0, 0]), imgs["iso_front"], "From the front left")
    iso(fig.add_subplot(gs[0, 1]), imgs["iso_rear"], "From the rear right")
    plan(fig.add_subplot(gs[1, :]), m)
    cross(fig.add_subplot(gs[2, 0]), m)
    side(fig.add_subplot(gs[2, 1]), m)
    fig.suptitle("Cutebot Pro cage v3: a closed ring on one 8 mm grid, decks over the wheels and the front; 18 flat prints, "
                 "2L pins", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(OUT / "cutebot_cage.png", dpi=85)
    print(OUT / "cutebot_cage.png")


if __name__ == "__main__":
    main()
