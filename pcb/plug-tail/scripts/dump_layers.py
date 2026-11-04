#!/usr/bin/env python3
"""Dump every front layer of the saved plug-tail boards as polygons, for the 3D viewer (gears/tools/plug_tail_view.py).

    python3 scripts/dump_layers.py   ->  exports/layers.json

Local coordinates as in build.py: x across the board, 0 on the tongue's centreline; y from the tongue tip toward
the tail. Each layer is a list of polygons, each [outline, hole, hole ...] of [x, y] points. Footprint courtyards and
body sizes come along so the viewer can stand parts up.
"""
from pathlib import Path
import json
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
O = 50.
LAYERS = {'F.Cu': p.F_Cu, 'F.Mask': p.F_Mask, 'F.Paste': p.F_Paste, 'F.SilkS': p.F_SilkS, 'F.Fab': p.F_Fab,
          'F.CrtYd': p.F_CrtYd, 'Edge.Cuts': p.Edge_Cuts}
ERR = p.FromMM(.005)


def polys(ps, X0):
    ps.Simplify()
    out = []
    for i in range(ps.OutlineCount()):
        rings = [ps.Outline(i)] + [ps.Hole(i, j) for j in range(ps.HoleCount(i))]
        out.append([[[round(p.ToMM(c.x) - X0, 4), round(p.ToMM(c.y) - O, 4)]
                     for c in (r.CPoint(k) for k in range(r.PointCount()))] for r in rings])
    return out


def items(board):
    for fp in board.GetFootprints():
        yield from fp.Pads()
        yield from fp.GraphicalItems()
        yield from (f for f in fp.GetFields() if f.IsVisible())
    yield from board.GetDrawings()
    yield from board.GetTracks()


def dump(name):
    b = p.LoadBoard(str(ROOT / f'design/{name}/{name}.kicad_pcb'))
    W = json.loads((ROOT / 'checks/geometry.json').read_text())[name]['board_mm'][0]; X0 = O + W / 2
    out = {'thickness': p.ToMM(b.GetDesignSettings().GetBoardThickness()), 'layers': {}, 'parts': []}
    for lname, layer in LAYERS.items():
        ps = p.SHAPE_POLY_SET()
        for it in items(b):
            if it.IsOnLayer(layer):
                it.TransformShapeToPolygon(ps, layer, 0, ERR, p.ERROR_INSIDE)
        out['layers'][lname] = polys(ps, X0)
    for fp in b.GetFootprints():
        ps = p.SHAPE_POLY_SET()
        for g in fp.GraphicalItems():
            if g.IsOnLayer(p.F_CrtYd):
                g.TransformShapeToPolygon(ps, p.F_CrtYd, 0, ERR, p.ERROR_INSIDE)
        pos = fp.GetPosition()
        out['parts'].append({'ref': fp.GetReference(), 'footprint': fp.GetFPIDAsString(),
                             'at': [round(p.ToMM(pos.x) - X0, 4), round(p.ToMM(pos.y) - O, 4)],
                             'rot': fp.GetOrientationDegrees(), 'courtyard': polys(ps, X0),
                             'pads': [{'num': a.GetNumber(), 'net': a.GetNetname(),
                                       'at': [round(p.ToMM(a.GetPosition().x) - X0, 4), round(p.ToMM(a.GetPosition().y) - O, 4)],
                                       'size': [p.ToMM(a.GetSize().x), p.ToMM(a.GetSize().y)],
                                       'rot': a.GetOrientationDegrees()} for a in fp.Pads()]})
    return out


if __name__ == '__main__':
    res = {n: dump(n) for n in ('servo-tail', 'qwiic-tail')}
    (ROOT / 'exports/layers.json').write_text(json.dumps(res))
    for n, d in res.items():
        print(n, {k: len(v) for k, v in d['layers'].items()}, [q['ref'] for q in d['parts']])
