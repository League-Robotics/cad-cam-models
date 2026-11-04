#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "shapely", "networkx", "scipy", "rtree"]
# ///
"""Labelled drawing of the two-camera line-laser mount (scad/laser_cam_mount.scad).

    uv run tools/laser_cam_mount_pics.py   ->  view/laser_cam_mount.png

As mounted under the camera bracket's cap: two 3D views, a cut down the
middle from the left (front on the right), the underside (camera pockets,
standoffs, laser bore) and the top (cap recess, cable slots).
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
PITCH, POCKET, POD, POD_H, GAP = 28, 39, 43, 17.1, 30
CAM_Y = GAP / 2 + POD / 2
INS_D, INS_LEN, LASER_TOP, BOSS_BOTTOM, BORE_D = 6.35, 13.5, -19, -35, 9.3
SOCKET_IN, SOCKET_H = 25.8, 3
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
        for p in ("mount", "cameras", "laser"):
            openscad(t / f"{p}.stl", 'part="assembly"', f'show="{p}"')
            m[p] = trimesh.load(t / f"{p}.stl")
        imgs = []
        for name, defs, cam in (("iso", ('part="assembly"',), "-140,-170,110,0,0,-5"),
                                ("under", ('part="mount"',), "110,-150,-120,0,0,-12")):
            png = t / f"{name}.png"
            openscad(png, *defs, extra=(f"--camera={cam}", "--projection=p", "--imgsize=1000,800",
                                        "--colorscheme=Tomorrow"))
            imgs.append(plt.imread(png))

    fig = plt.figure(figsize=(20, 15))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.1])
    i3, i3b, cut = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[0, 2])
    under, top = fig.add_subplot(gs[1, 0:2]), fig.add_subplot(gs[1, 2])
    for ax, img, title in ((i3, imgs[0], "As mounted under the bracket's cap,\nfrom in front and to the left"),
                           (i3b, imgs[1], "From below and to the right:\ncamera pockets, standoffs, laser bore")):
        ax.imshow(img), ax.set_axis_off(), ax.set_title(title, fontsize=12)

    # cut down the middle (x = 0), seen from the left: y to the left, front (-y) on the right
    draw_geom(cut, section_geom(m["mount"], (0, 0, 0), (1, 0, 0), (1, 2)), BLUE)
    draw_geom(cut, silhouette(m["cameras"], (1, 2)), GREEN, alpha=0.35)
    draw_geom(cut, silhouette(m["laser"], (1, 2)), GOLD, alpha=0.6)
    cut.invert_xaxis()
    cut.set_title("Cut down the middle, from the left (front on the right)", fontsize=12)
    label(cut, (0, -7), f"heat-set insert hole\nØ{INS_D} x {INS_LEN} (screw from the cap)", (-30, 14))
    label(cut, (3, -26), f"laser Ø9 in a Ø{BORE_D} bore,\n16 deep; turn it, then lock", (38, -44))
    label(cut, (-4, -17.5), "wire channel\nout the -x side", (-38, -44))
    label(cut, (CAM_Y, -18), "camera board,\nback up", (CAM_Y + 6, 14))
    dim(cut, (CAM_Y, -54), (-CAM_Y, -54), f"{2 * CAM_Y:g} between the cameras", off=(0, -2.6))
    dim(cut, (65, SOCKET_H), (65, SOCKET_H - POD_H), f"{POD_H}", off=(4, 0))
    dim(cut, (12, 0), (12, BOSS_BOTTOM), f"{-BOSS_BOTTOM:g}", off=(-4, 0))
    cut.text(66, 3.5, "back", color=GREY, fontsize=10), cut.text(-56, 3.5, "front", color=GREY, fontsize=10)
    cut.set_xlim(70, -70), cut.set_ylim(-62, 22)

    # from below: y to the right (front, -y, on the left), x down the page (-x at the top)
    draw_geom(under, section_geom(m["mount"], (0, 0, -10), (0, 0, 1), (1, 0)), BLUE)
    draw_geom(under, section_geom(m["mount"], (0, 0, -25), (0, 0, 1), (1, 0)), BLUE, alpha=0.6)
    under.set_title("From below, cut 10 under the cap (the cameras' standoffs), front on the left, -x at the top", fontsize=12)
    under.invert_yaxis()
    for s in (-1, 1):
        dim(under, (s * CAM_Y - PITCH / 2, -24), (s * CAM_Y + PITCH / 2, -24), f"{PITCH} (as your mount)", off=(0, -2))
        dim(under, (s * CAM_Y - POCKET / 2, 25), (s * CAM_Y + POCKET / 2, 25), f"{POCKET} pocket (38 board)", off=(0, 2))
    label(under, (CAM_Y + PITCH / 2, -PITCH / 2), "standoff Ø5, Ø2.2 hole\n11.5 long (connector room)",
          (CAM_Y + 10, 3))
    label(under, (0, -10), "set screw: M3 insert\nfrom -x", (-18, 3))
    dim(under, (-POD - GAP / 2, 30), (POD + GAP / 2, 30), f"{2 * POD + GAP:g}", off=(0, 2.4))
    under.set_xlim(-65, 65), under.set_ylim(36, -32)

    # from above: the cap recess and cable slots, front at the bottom
    draw_geom(top, silhouette(m["mount"], (0, 1)), BLUE, alpha=0.3)
    draw_geom(top, section_geom(m["mount"], (0, 0, 1.5), (0, 0, 1), (0, 1)), RED, alpha=0.5)
    top.set_title("From above: the cap's recess, cable slots (front at the bottom)", fontsize=12)
    label(top, (SOCKET_IN / 2 + 1, -6), f"recess {SOCKET_IN} square, {SOCKET_H} deep\ninto the flat top: the 25.4 cap\nsits in it, so one screw\ncan't turn it; the top\nprints flat on the bed",
          (38, -38))
    label(top, (10, CAM_Y + SLOT_OFF), "cable slot 24 x 4.6\n(as in your mount)", (40, CAM_Y + 4))
    label(top, (0, 0), "screw", (-38, 20))
    top.text(0, -70, "front", ha="center", color=GREY)
    top.set_xlim(-55, 70), top.set_ylim(-74, 70)

    for ax in (cut, under, top):
        ax.set_aspect("equal"), ax.grid(alpha=0.2)
    fig.suptitle("Two Arducams and a line laser under the Carvera camera bracket (first draft): camera, laser, camera, "
                 "front to back, all facing down", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=90)
    print(OUT)


if __name__ == "__main__":
    main()
