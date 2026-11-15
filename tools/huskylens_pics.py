#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "numpy", "matplotlib", "scipy", "networkx", "shapely"]
# ///
"""Drawings of the HuskyLens LEGO tray (scad/huskylens_case.scad).

    uv run tools/huskylens_pics.py

    grippers/huskylens_case/views.png  the tray alone: front, side, top, iso, dimensioned
    view/huskylens_case.png            the tray with the HuskyLens in it, what each opening is for
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drawing import label  # noqa: E402
from four_view import four_view  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "huskylens_case.scad"
RED = "#c0392b"


def labels(axes):
    ax = axes["top"]   # x right, y up: looking at the screen
    for xy, text, at in [
        ((-17.9, 18.4), "function dial", (-30, 30)),
        ((19.5, 20.2), "learn button", (30, 30)),
        ((0, 4), "screen side up;\ncamera looks out of the back,\nthrough the floor's notch", (0, 36)),
        ((-32, 4), "column: 5 pin holes,\nfront to back", (-56, 10)),
        ((32, 4), "column: 5 pin holes\n(covers the SD slot)", (56, 10)),
        ((-20.2, -15.5), "micro USB\ncable out here", (-46, -24)),
        ((18.6, -15.5), "UART (4-pin)\ncable out here", (46, -24)),
        ((7.4, -18.65), "2 x M3 through the tab", (40, -34)),
        ((0, -28), "bar under the tab: middle hole\nfront to back, 4 holes up from underneath", (0, -50)),
    ]:
        label(ax, xy, text, at, color=RED)


four_view(ROOT / "grippers" / "huskylens_case" / "views.png", "HuskyLens LEGO tray (first draft): the print, back face on the bed",
          SCAD, ['part="case"'])
four_view(ROOT / "view" / "huskylens_case.png", "HuskyLens LEGO tray (first draft) with the HuskyLens in it. Top view = looking at the screen",
          SCAD, ['part="assembly"'], extra=labels,
          note="Board numbers are from the GrabCAD model, not yet checked on the real HuskyLens.")
