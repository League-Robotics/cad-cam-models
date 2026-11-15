#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "scipy", "networkx", "shapely"]
# ///
"""The standard four-view picture of a part: front, left side, top, and an iso view.

Every directory in design/ keeps one, `<part>/views.png` (ignored by git, like
all images), so Eric can see what the part is (Eric, 2026-11-06).

    uv run design/tools/four_view.py OUT.png "TITLE" FILE.scad [-D 'k=v' ...] [--note TEXT]

Layout (first-angle, so the views line up): front top-left, the left side to
its right (seen from the left, sharing its heights), the top below the front
(sharing its widths), the iso view in the fourth cell. The three flat views
are OpenSCAD preview renders (so `color()` shows) at one common scale, with
the overall sizes dimensioned. A part's own script can add dimensions:

    from four_view import four_view
    four_view(out, title, scad, defines, extra=lambda ax: ...)

`extra` gets a dict of matplotlib axes, "front" (x right, z up), "left"
(y, with the machine's front on the right, z up) and "top" (x right, y up),
all in model millimetres, plus "info", the bounding box.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drawing import dim  # noqa: E402

# OpenSCAD gimbal rotations of its own Front, Left and Top views, and what each
# image's right and up are in model axes.
VIEWS = {
    "front": ((90, 0, 0), (0, +1), (2, +1)),   # right = +x, up = +z
    "left": ((90, 0, -90), (1, -1), (2, +1)),   # right = -y (the front), up = +z
    "top": ((0, 0, 0), (0, +1), (1, +1)),      # right = +x, up = +y
}


def openscad(args):
    r = subprocess.run(["openscad", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)


def render_view(scad, defines, png, rot, size=1200):
    openscad(["-o", str(png), *defines, f"--camera=0,0,0,{rot[0]},{rot[1]},{rot[2]},500",
              "--viewall", "--autocenter", "--projection=o", f"--imgsize={size},{size}",
              "--colorscheme=Tomorrow", str(scad)])
    return plt.imread(png)


def pixel_box(img):
    """Columns and rows covered by the part: anything that isn't the corner's background colour."""
    rgb = img[..., :3]
    mask = np.abs(rgb - rgb[0, 0]).sum(axis=2) > 0.04
    rows, cols = np.nonzero(mask)
    return cols.min(), cols.max() + 1, rows.min(), rows.max() + 1


def place(ax, img, lo, hi, right, up):
    """imshow the render in model mm: map its part's pixel box onto the model's box."""
    c0, c1, r0, r1 = pixel_box(img)
    (ia, sa), (ib, sb) = right, up
    h, w = img.shape[:2]
    # model coordinate along the image's right at pixel column c, and along its up at row r
    a0, a1 = (lo[ia], hi[ia]) if sa > 0 else (hi[ia], lo[ia])
    b0, b1 = (hi[ib], lo[ib]) if sb > 0 else (lo[ib], hi[ib])   # row 0 is the top
    ka, kb = (a1 - a0) / (c1 - c0), (b1 - b0) / (r1 - r0)
    ax.imshow(img, extent=(a0 - c0 * ka, a0 + (w - c0) * ka, b0 + (h - r0) * kb, b0 - r0 * kb),
              interpolation="lanczos")


def four_view(out, title, scad, defines=(), extra=None, note=None, iso_eye=(-1, -1.3, 0.9),
              iso_defines=None, iso_title="Iso, from the front left, above"):
    """iso_defines replaces `defines` for the iso cell only, e.g. to explode it."""
    scad = Path(scad).resolve()
    iso_d = [x for d in (defines if iso_defines is None else iso_defines) for x in ("-D", d)]
    defines = [x for d in defines for x in ("-D", d)]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        openscad(["--backend=manifold", "--export-format=binstl", "-o", str(tmp / "p.stl"), *defines, str(scad)])
        m = trimesh.load(tmp / "p.stl")
        lo, hi = m.bounds
        imgs = {k: render_view(scad, defines, tmp / f"{k}.png", v[0]) for k, v in VIEWS.items()}
        c = (lo + hi) / 2
        e = np.array(iso_eye) / np.linalg.norm(iso_eye) * 4 * np.linalg.norm(hi - lo) + c
        openscad(["-o", str(tmp / "iso.png"), *iso_d, f"--camera={e[0]},{e[1]},{e[2]},{c[0]},{c[1]},{c[2]}",
                  "--viewall", "--autocenter", "--projection=o", "--imgsize=1400,1400",
                  "--colorscheme=Tomorrow", str(scad)])
        iso = plt.imread(tmp / "iso.png")

    size = hi - lo
    span = size.max() * 1.45          # one scale for the three flat views, with room for the dimensions
    fig, axs = plt.subplots(2, 2, figsize=(16, 16))
    ax = {"front": axs[0, 0], "left": axs[0, 1], "top": axs[1, 0]}
    titles = {"front": "Front (from where you stand)", "left": "Left side (seen from the left; the front is on the right)",
              "top": "Top (from above; the front is at the bottom)"}
    for k, (rot, right, up) in VIEWS.items():
        a = ax[k]
        place(a, imgs[k], lo, hi, right, up)
        a.set_facecolor(imgs[k][0, 0, :3])   # the render's background, so its edge doesn't show
        (ia, sa), (ib, _) = right, up
        xs = (c[ia] - span / 2, c[ia] + span / 2)
        a.set_xlim(xs if sa > 0 else xs[::-1])
        a.set_ylim(c[ib] - span / 2, c[ib] + span / 2)
        a.set_aspect("equal")
        a.set_title(titles[k], fontsize=13)
        a.tick_params(labelsize=8)
        a.grid(True, lw=0.3, alpha=0.4)
        # overall sizes: below and to the left of the part
        g = span * 0.07
        names = "xyz"
        left_edge = hi[ia] if sa < 0 else lo[ia]
        dim(a, (lo[ia], lo[ib] - g), (hi[ia], lo[ib] - g), f"{size[ia]:.1f} ({names[ia]})")
        dim(a, (left_edge - g * np.sign(sa), lo[ib]), (left_edge - g * np.sign(sa), hi[ib]),
            f"{size[ib]:.1f}\n({names[ib]})")
    ax["iso"] = axs[1, 1]
    ax["iso"].imshow(iso)
    ax["iso"].set_axis_off()
    ax["iso"].set_title(iso_title, fontsize=13)
    ax["info"] = {"lo": lo, "hi": hi}
    if extra:
        extra(ax)
    fig.suptitle(title, fontsize=16)
    if note:
        fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=11, wrap=True)
    fig.tight_layout(rect=(0, 0.04 if note else 0, 1, 0.97))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("out")
    p.add_argument("title")
    p.add_argument("scad")
    p.add_argument("-D", action="append", default=[], dest="defines")
    p.add_argument("--note")
    p.add_argument("--iso-eye", default="-1,-1.3,0.9", help="direction to the iso camera, e.g. -1,-1.3,-0.6 for from below")
    p.add_argument("--iso-title", default="Iso, from the front left, above")
    a = p.parse_args()
    four_view(a.out, a.title, a.scad, a.defines, note=a.note,
              iso_eye=tuple(float(v) for v in a.iso_eye.split(",")), iso_title=a.iso_title)
