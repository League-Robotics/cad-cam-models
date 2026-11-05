#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["manifold3d", "numpy", "shapely", "trimesh", "networkx", "scipy"]
# ///
"""Printed stand-ins for the 4P4C plug-tail PCBs (pcb/plug-tail), to try in a plug before cutting copper.

    uv run tools/plug_tail_fit_print.py [THICK ...]   ->  pcb/plug-tail/print/fit_test_plate.stl

Each board's outline at full size with its copper (F.Cu: traces and pads) standing one 0.2 layer proud, so the
pins can be laid on the pads. One of each board per thickness given (default 1.4, the stock), measured to the
top of the pads where the pins sit (real board: 1.4 FR-4 + 0.035 copper). With several thicknesses, notches in
the +x edge, outside the plug, tell them apart in the order given: none, 1, 2, 3 (rev A/B prints: 1.4, 1.2, 1.0, 0.8).
Columns by thickness, header tails in the back row, Qwiic tails in front; copper up, tongues pointing +y.
"""
import json
import sys
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PT = ROOT / 'pcb' / 'plug-tail'
OUT = PT / 'print' / 'fit_test_plate.stl'
DATA = json.loads((PT / 'exports' / 'layers.json').read_text())
GEO = json.loads((PT / 'checks' / 'geometry.json').read_text())

THICK = [float(a) for a in sys.argv[1:]] or [1.4]   # to the top of the pads
CU = 0.2                         # copper drawn one layer proud
NOTCH = (0.5, 0.8)               # depth into the +x edge, length along it
NOTCH_Y = [12.0, 13.5, 15.0]     # local y (from the tongue tip): on the wide part past the 10 tongue, clear of copper
PITCH_X, ROW_Y = 14.0, {'header-tail': 14.0, 'qwiic-tail': -14.0}


def area(polys):
    return unary_union([Polygon(r[0], [h for h in r[1:] if len(h) >= 3]).buffer(0) for r in polys if len(r[0]) >= 3])


def slab(g, z0, z1):
    gs = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    ms = [m3.Manifold.extrude(m3.CrossSection([np.array(p.exterior.coords[:-1])] +
                                              [np.array(r.coords[:-1]) for r in p.interiors], m3.FillRule.EvenOdd),
                              z1 - z0).translate([0, 0, z0]) for p in gs if p.area > 1e-6]
    return m3.Manifold.batch_boolean(ms, m3.OpType.Add)


def board(name, t, notches):
    outline = Polygon(GEO[name]['outline'])
    W = GEO[name]['board_mm'][0]
    cuts = [box(W / 2 - NOTCH[0], y - NOTCH[1] / 2, W / 2 + 1, y + NOTCH[1] / 2) for y in NOTCH_Y[:notches]]
    body = outline.difference(unary_union(cuts)) if cuts else outline
    cu = area(DATA[name]['layers']['F.Cu']).intersection(body)
    flip = lambda g: affinity.scale(g, 1, -1, origin=(0, 0))      # local y runs down the KiCad page
    return slab(flip(body), 0, t - CU) + slab(flip(cu), t - CU - 0.01, t)


def main():
    parts = []
    for i, t in enumerate(THICK):
        for name, row in ROW_Y.items():
            L = GEO[name]['board_mm'][1]
            parts.append(board(name, t, i).translate([(i - (len(THICK) - 1) / 2) * PITCH_X, row + L / 2, 0]))
    mesh = m3.Manifold.batch_boolean(parts, m3.OpType.Add).to_mesh()
    OUT.parent.mkdir(exist_ok=True)
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
    tm.export(OUT)
    print(OUT, 'bounds', tm.bounds.round(2).tolist(), 'bodies', len(tm.split(only_watertight=False)))


if __name__ == '__main__':
    main()
