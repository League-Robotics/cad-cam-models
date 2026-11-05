#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the two-camera line-laser mount and its bracket (scad/laser_cam_mount.scad).

    uv run tools/laser_cam_mount_pics.py   ->  view/laser_cam_mount.png

As mounted: two 3D views, the side from the left (bracket's triangles over a
cut down the mount's middle, front on the right), the mount's underside
(camera pockets, standoffs, the rib with the laser bore) and the top (the bracket's
glue pad on it, its one hole over the laser, cable slots).
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
SCAD = ROOT / "scad" / "laser_cam_mount.scad"
OUT = ROOT / "view" / "laser_cam_mount.png"
BLUE, GREEN, GOLD, GREY, RED = "#3b7dd8", "#1f7a3a", "#c9a227", "#777", "#c0392b"

# as in the scad
PITCH, POCKET, POD, POD_H, BASELINE = 28, 39, 43, 17.1, 52
CAM_Y = BASELINE / 2
BORE_D, LASER_LEN = 9.3, 22
BRACKET_Y, BRACKET_H, END_Y = 20, 62, 47.5   # bracket_off (cap centre), bracket_l + cap_t, the mount's ends
LEG_Y = BRACKET_Y - 12.7                       # the bracket's front leg, where the triangles start
CABLE_Z, CABLE_D = 12.35, 12.7                 # the laser cable's hole through the front triangle
SLOT_OFF = 14.65


def openscad(out, *defs, extra=()):
    args = ["openscad", "--backend=manifold", "-o", str(out)]
    for d in defs:
        args += ["-D", d]
    subprocess.run(args + list(extra) + [str(SCAD)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        m = {}
        for p in ("mount", "bracket", "cameras", "laser"):
            openscad(t / f"{p}.stl", 'part="assembly"', f'show="{p}"')
            m[p] = trimesh.load(t / f"{p}.stl")
        imgs = []
        for name, defs, cam in (("iso", ('part="assembly"',), "-170,-180,120,0,0,15"),
                                ("under", ('part="mount"',), "100,-140,-120,0,0,-6")):
            png = t / f"{name}.png"
            openscad(png, *defs, extra=(f"--camera={cam}", "--projection=p", "--imgsize=1000,800",
                                        "--colorscheme=Tomorrow"))
            imgs.append(plt.imread(png))

    fig = plt.figure(figsize=(20, 15))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.1])
    i3, i3b, cut = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2])
    under, top = fig.add_subplot(gs[1, 0:2]), fig.add_subplot(gs[1, 2])
    for ax, img, title in ((i3, imgs[0], "As mounted, from in front and to the left:\nthe bracket (grey) glued on, the 1/2 in cable hole"),
                           (i3b, imgs[1], "The mount from below and to the right: two camera pockets,\nthe laser in the rib between them")):
        ax.imshow(img), ax.set_axis_off(), ax.set_title(title, fontsize=12)

    # from the left: the bracket's outline over a cut down the mount's middle (x = 0); front (-y) on the right
    draw_geom(cut, silhouette(m["bracket"], (1, 2)), GREY, alpha=0.35)
    draw_geom(cut, section_geom(m["mount"], (0, 0, 0), (1, 0, 0), (1, 2)), BLUE)
    draw_geom(cut, silhouette(m["cameras"], (1, 2)), GREEN, alpha=0.35)
    draw_geom(cut, silhouette(m["laser"], (1, 2)), GOLD, alpha=0.6)
    cut.invert_xaxis()
    cut.set_title("From the left: the bracket over a cut down the mount (front on the right)", fontsize=12)
    label(cut, (BRACKET_Y, 50), "the old bracket\n(angle + cap, same holes)", (20, 88))
    label(cut, (-30, 20), "triangle to the\nfront end", (-42, 72))
    label(cut, (-20.1 + 3, 33 - 4), "3 zip-tie slots", (-30, 88))
    label(cut, (44, 12), "triangle to\nthe back end", (58, 72))
    label(cut, (-3, CABLE_Z + 4), f"NEW: Ø{CABLE_D} (1/2 in) hole\nfor the laser's cable", (-45, 38))
    cut.plot([0, 0], [-POD_H - 8, 4], color=RED, lw=1.2, ls="--")
    label(cut, (-40, 2), "glue pad 25.4 wide, 4 thick,\nthe mount's whole length", (-36, -50))
    label(cut, (-3, -LASER_LEN + 1), f"laser sticks out {LASER_LEN - POD_H:.1f}\n(laser 22, a guess)", (25, -48))
    dim(cut, (CAM_Y, -30), (-CAM_Y, -30), f"{BASELINE:g} between cameras,\nlaser halfway", off=(0, -6))
    dim(cut, (60, 0), (60, BRACKET_H), f"{BRACKET_H}", off=(4, 0))
    cut.text(66, -12, "back", color=GREY, fontsize=10), cut.text(-55, -12, "front", color=GREY, fontsize=10)
    cut.set_xlim(72, -65), cut.set_ylim(-62, 95)

    # from below: y to the right (front, -y, on the left), x down the page (-x at the top)
    draw_geom(under, section_geom(m["mount"], (0, 0, -10), (0, 0, 1), (1, 0)), BLUE)
    draw_geom(under, section_geom(m["mount"], (0, 0, -1), (0, 0, 1), (1, 0)), BLUE, alpha=0.6)
    under.set_title("The mount from below, cut 10 under its top, front on the left, -x at the top. Both cameras "
                    "turned 90°:\nthe 1280 px side runs front to back, cable slots on the +x side", fontsize=12)
    under.invert_yaxis()
    for s in (-1, 1):
        dim(under, (s * CAM_Y - PITCH / 2, -24), (s * CAM_Y + PITCH / 2, -24), f"{PITCH} (as your mount)", off=(0, -2))
        dim(under, (s * CAM_Y - POCKET / 2, 27), (s * CAM_Y + POCKET / 2, 27), f"{POCKET} pocket", off=(0, 2))
    label(under, (CAM_Y + PITCH / 2, -PITCH / 2), "standoff Ø5, Ø2.2 hole\n11.5 long", (CAM_Y + 36, -12))
    label(under, (CAM_Y + 8, SLOT_OFF), "cable slot 24 x 4.6", (CAM_Y + 36, 14))
    label(under, (0, -14), "set screw: M3 insert from -x,\nthrough the 13 rib", (-56, -16))
    label(under, (2, 3), "laser Ø9.3 bore,\n1.85 wall each side", (-50, 12))
    dim(under, (-END_Y, 36), (END_Y, 36), f"{2 * END_Y:g} overall", off=(0, 2.4))
    dim(under, (-CAM_Y, -30), (CAM_Y, -30), f"{BASELINE:g} between the cameras", off=(0, -2.4))
    under.set_xlim(-72, 72), under.set_ylim(42, -38)

    # from above: the mount's flat top, the bracket's footprint on it, front at the bottom
    draw_geom(top, silhouette(m["mount"], (0, 1)), BLUE, alpha=0.3)
    draw_geom(top, section_geom(m["mount"], (0, 0, -1), (0, 0, 1), (0, 1)), BLUE, alpha=0.5)
    draw_geom(top, section_geom(m["bracket"], (0, 0, 1), (0, 0, 1), (0, 1)), GREY, alpha=0.6)
    top.set_title("From above: the bracket's glue pad (grey) on the flat top,\nnotched clear of the cable slots (front at the bottom)", fontsize=12)
    label(top, (6, BRACKET_Y), "the old cap", (36, 40))
    label(top, (-11, -30), "front triangle\n(the cable hole)", (-45, -40))
    label(top, (0, 0), "laser hole", (-42, 8))
    label(top, (14.6, CAM_Y), "cable slot,\npad notched", (42, CAM_Y - 6))
    top.text(0, -60, "front", ha="center", color=GREY), top.text(0, 56, "back", ha="center", color=GREY)
    top.set_xlim(-62, 62), top.set_ylim(-64, 62)

    for ax in (cut, under, top):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.suptitle("Two Arducams and a line laser on the Carvera (2026-11-04, v3): cameras 52 apart with the laser between, "
                 "turned 90°; 1/2 in cable hole in the front triangle", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=90)
    print(OUT)


if __name__ == "__main__":
    main()
