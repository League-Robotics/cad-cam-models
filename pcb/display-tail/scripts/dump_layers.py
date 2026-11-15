#!/usr/bin/env python3
"""Dump every front layer of the saved boards as polygons (board frame: x from the left edge, y DOWN from the top edge).

    python3 scripts/dump_layers.py   ->  exports/layers.json

Each layer is a list of polygons, each [outline, hole, hole ...] of [x, y] points. Footprint courtyards, pads and
holes come along for the drawings and the CAM.
"""
from pathlib import Path
import json, sys
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
O = 50.
LAYERS = {'F.Cu': p.F_Cu, 'F.Mask': p.F_Mask, 'F.Paste': p.F_Paste, 'F.Fab': p.F_Fab, 'F.CrtYd': p.F_CrtYd, 'Edge.Cuts': p.Edge_Cuts}
ERR = p.FromMM(.005)


def polys(ps):
    ps.Simplify(); out = []
    for i in range(ps.OutlineCount()):
        rings = [ps.Outline(i)] + [ps.Hole(i, j) for j in range(ps.HoleCount(i))]
        out.append([[[round(p.ToMM(c.x) - O, 4), round(p.ToMM(c.y) - O, 4)] for c in (r.CPoint(k) for k in range(r.PointCount()))] for r in rings])
    return out


def items(board):
    for fp in board.GetFootprints():
        yield from fp.Pads(); yield from fp.GraphicalItems(); yield from (f for f in fp.GetFields() if f.IsVisible())
    yield from board.GetDrawings(); yield from board.GetTracks()


def dump(name):
    b = p.LoadBoard(str(ROOT / f'design/{name}/{name}.kicad_pcb'))
    out = {'thickness': p.ToMM(b.GetDesignSettings().GetBoardThickness()), 'layers': {}, 'parts': [], 'holes': []}
    for lname, layer in LAYERS.items():
        ps = p.SHAPE_POLY_SET()
        for it in items(b):
            if it.IsOnLayer(layer): it.TransformShapeToPolygon(ps, layer, 0, ERR, p.ERROR_INSIDE)
        out['layers'][lname] = polys(ps)
    for fp in b.GetFootprints():
        ps = p.SHAPE_POLY_SET()
        for g in fp.GraphicalItems():
            if g.IsOnLayer(p.F_CrtYd): g.TransformShapeToPolygon(ps, p.F_CrtYd, 0, ERR, p.ERROR_INSIDE)
        pos = fp.GetPosition()
        out['parts'].append({'ref': fp.GetReference(), 'footprint': fp.GetFPIDAsString(), 'at': [round(p.ToMM(pos.x) - O, 4), round(p.ToMM(pos.y) - O, 4)],
                             'rot': fp.GetOrientationDegrees(), 'courtyard': polys(ps),
                             'pads': [{'num': a.GetNumber(), 'net': a.GetNetname(), 'at': [round(p.ToMM(a.GetPosition().x) - O, 4), round(p.ToMM(a.GetPosition().y) - O, 4)],
                                       'size': [p.ToMM(a.GetSize().x), p.ToMM(a.GetSize().y)], 'rot': a.GetOrientationDegrees(), 'drill': p.ToMM(a.GetDrillSize().x)} for a in fp.Pads()]})
        for a in fp.Pads():
            if a.GetDrillSize().x: out['holes'].append({'x': round(p.ToMM(a.GetPosition().x) - O, 4), 'y': round(p.ToMM(a.GetPosition().y) - O, 4), 'd': p.ToMM(a.GetDrillSize().x)})
    return out


if __name__ == '__main__':
    names = sys.argv[1:] or list(json.loads((ROOT / 'checks/geometry.json').read_text()))
    res = {n: dump(n) for n in names}
    (ROOT / 'exports').mkdir(exist_ok=True); (ROOT / 'exports/layers.json').write_text(json.dumps(res))
    for n, d in res.items(): print(n, {k: len(v) for k, v in d['layers'].items()}, [q['ref'] for q in d['parts']], len(d['holes']), 'holes')
