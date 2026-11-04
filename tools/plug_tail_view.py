#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["manifold3d", "numpy", "shapely", "trimesh"]
# ///
"""3D viewer of the 4P4C plug-tail boards (pcb/plug-tail), one checkbox per board layer.

    uv run tools/plug_tail_view.py [--open]   ->  view/plug_tail.html

Layers come from pcb/plug-tail/exports/layers.json (scripts/dump_layers.py on Buzzkill, from the saved KiCad
boards); the milling from the Carvera program itself (boards 1 and 3 of cam/plug-tails-*.nc, mapped back through
cam/job.json's placements). Servo tail on the left, Qwiic tail on the right, tongues pointing +y into the plug.

Thin layers are drawn thicker than they are so they show: copper 0.035 -> 0.05, mask/paste/silk 0.02-0.05.
Pins, the Qwiic socket, R1 and the 4P4C plug are stand-ins. The plug is NOT measured beyond the 5.5 x 3.15 cavity:
its channels are put at the cavity's mid-height, so the board pokes below the cavity floor if it is too thick
(see tools/plug_tail_pics.py).
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PT = ROOT / 'pcb' / 'plug-tail'
OUT = ROOT / 'view' / 'plug_tail.html'
DATA = json.loads((PT / 'exports' / 'layers.json').read_text())
GEO = json.loads((PT / 'checks' / 'geometry.json').read_text())
JOB = json.loads((PT / 'cam' / 'job.json').read_text())
NC = max((PT / 'cam').glob('plug-tails-*.nc'))   # the current revision's program

OFFSET = {'servo-tail': -7.5, 'qwiic-tail': 7.5}   # board centrelines along x
NC_BOARD = {'servo-tail': 1, 'qwiic-tail': 3}      # which placement in the program to draw
CU = 0.05                                          # copper, drawn (0.035 real)
PIN = 0.64
PIN_LEN = 15.0                                     # double-length header pin
CAV_W, CAV_H = 5.5, 3.15                           # measured cavity
PLUG = (7.6, 6.6, 18.0)                            # stand-in body: width, height, length (not measured)
CAV_DEPTH = GEO['servo-tail']['tongue_mm'][1]      # back face to channel wall = the tongue length (not measured)


def world(g, name):
    """Board-local (x across, y from the tongue tip) to viewer (x, y), tongue toward +y."""
    return affinity.translate(affinity.scale(g, 1, -1, origin=(0, 0)), OFFSET[name], 0)


def shape(polys):
    out = []
    for rings in polys:
        if len(rings[0]) >= 3:
            out.append(Polygon(rings[0], [r for r in rings[1:] if len(r) >= 3]).buffer(0))
    return unary_union(out) if out else Polygon()


def slab(g, z0, z1):
    """Extrude a shapely area from z0 to z1 as a manifold."""
    gs = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    parts = []
    for p in gs:
        if p.is_empty or p.area < 1e-6:
            continue
        rings = [np.array(p.exterior.coords[:-1])] + [np.array(r.coords[:-1]) for r in p.interiors]
        parts.append(m3.Manifold.extrude(m3.CrossSection(rings, m3.FillRule.EvenOdd), z1 - z0).translate([0, 0, z0]))
    return m3.Manifold.batch_boolean(parts, m3.OpType.Add) if parts else m3.Manifold()


def bar(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def nc_moves():
    """{(board number, tool): [(z, [(x, y), ...]) per cutting run]} in machine coordinates."""
    runs, board, tool, z, xy, cur = {}, None, None, 5.0, (0.0, 0.0), None
    for line in NC.read_text().splitlines():
        if m := re.match(r'\(BOARD (\d+)', line):
            board = int(m.group(1))
        if m := re.search(r'M6 T(\d)', line):
            tool = int(m.group(1))
        if not line.startswith(('G0', 'G1')):
            continue
        rapid = line.startswith('G0 ') or line.startswith('G00')
        w = dict(re.findall(r'([XYZ])(-?[\d.]+)', line))
        nz = float(w.get('Z', z)); nxy = (float(w.get('X', xy[0])), float(w.get('Y', xy[1])))
        if rapid or nz >= 0 or nz != z:
            cur = None
        if not rapid and nz < 0 and board:
            if cur is None:
                cur = (nz, [nxy if nz != z else xy])
                runs.setdefault((board, tool), []).append(cur)
            if nxy != cur[1][-1]:
                cur[1].append(nxy)
        z, xy = nz, nxy
    return runs


def build(t):
    runs = nc_moves()
    meshes = {k: [] for k in ('board', 'cu', 'iso', 'outline', 'mask', 'paste', 'silk', 'fab', 'crtyd', 'edge',
                              'pins', 'parts', 'plug', 'servo_plug')}
    for name, d in DATA.items():
        T = d['thickness']
        lay = {k: world(shape(v), name) for k, v in d['layers'].items()}
        outline = world(Polygon(GEO[name]['outline']), name)
        W, Lb = GEO[name]['board_mm'][:2]
        top = T + CU
        meshes['board'].append(slab(outline, 0, T))
        meshes['cu'].append(slab(lay['F.Cu'], T, top))
        meshes['mask'].append(slab(outline.difference(lay['F.Mask']), top, top + .03))
        meshes['paste'].append(slab(lay['F.Paste'], top, top + .06))
        meshes['silk'].append(slab(lay['F.SilkS'], top + .03, top + .05))
        meshes['fab'].append(slab(lay['F.Fab'], top + .08, top + .1))
        meshes['crtyd'].append(slab(lay['F.CrtYd'], top + .1, top + .12))
        meshes['edge'].append(slab(lay['Edge.Cuts'], -.02, top + .02))

        # milling, from the program: machine -> local -> viewer
        pl = next(p for p in JOB['placements'] if p['id'] == NC_BOARD[name])
        def loc(pts): return [(x - pl['x'] - W / 2, pl['y'] + Lb - y) for x, y in pts]
        iso = unary_union([LineString(loc(p)).buffer(JOB['isolation']['effective_diameter_mm'] / 2)
                           for z, p in runs[(NC_BOARD[name], 2)] if len(p) > 1])
        meshes['iso'].append(slab(world(iso, name), T + min(z for z, _ in runs[(NC_BOARD[name], 2)]), top + .02))
        by_z = {}
        for z, p in runs[(NC_BOARD[name], 3)]:
            if len(p) > 1:
                by_z.setdefault(z, []).append(LineString(loc(p)).buffer(JOB['cutter_mm'] / 2))
        meshes['outline'] += [slab(world(unary_union(g), name), T + z, top + .02) for z, g in by_z.items()]

        # pins: the four plug pins lie on the J1 pads and run on into the plug's channels
        pz = top
        parts = {q['ref']: q for q in d['parts']}
        for pad in parts['J1']['pads']:
            x = pad['at'][0] + OFFSET[name]; yend = pad['at'][1] + pad['size'][1] / 2
            meshes['pins'].append(bar(x - PIN / 2, x + PIN / 2, -yend, -yend + PIN_LEN, pz, pz + PIN))
        if name == 'servo-tail':
            for pad in parts['J2']['pads']:
                x = pad['at'][0] + OFFSET[name]; y0 = pad['at'][1] - pad['size'][1] / 2 + .4
                meshes['pins'].append(bar(x - PIN / 2, x + PIN / 2, -(Lb + 6), -y0, pz, pz + PIN))
            # a 3-way 2.54 servo housing (7.6 x 2.5 x 14) pushed onto the overhang, 0.5 off the board end
            cx, cz, y1 = OFFSET[name], pz + PIN / 2, -(Lb + .5)
            meshes['servo_plug'].append(bar(cx - 3.8, cx + 3.8, y1 - 14, y1, cz - 1.25, cz + 1.25))
        if 'R1' in parts:
            r = parts['R1']
            body = affinity.rotate(box(-1.6, -.8, 1.6, .8), -r['rot']); body = affinity.translate(body, *r['at'])
            meshes['parts'].append(slab(world(body, name), top, top + .55))
        if name == 'qwiic-tail':
            # the courtyard is a drawn line: fill its outside ring, then step in to the body
            c = unary_union([Polygon(r[0]) for r in parts['J2']['courtyard']]).buffer(-.3, join_style=2)
            meshes['parts'].append(slab(world(c, name), top, top + 2.9))

        # 4P4C plug stand-in: cavity centred on the pins, channels forward to the contacts
        cx = OFFSET[name]; pc = pz + PIN / 2
        floor = pc - CAV_H / 2
        body = bar(cx - PLUG[0] / 2, cx + PLUG[0] / 2, -CAV_DEPTH, -CAV_DEPTH + PLUG[2], floor - 1.4, floor - 1.4 + PLUG[1])
        body = body - bar(cx - CAV_W / 2, cx + CAV_W / 2, -CAV_DEPTH - 1, 0, floor, floor + CAV_H)
        for pad in parts['J1']['pads']:
            x = pad['at'][0] + cx
            body = body - bar(x - .45, x + .45, -.5, PLUG[2] - CAV_DEPTH - 1, pc - .45, pc + .45)
        meshes['plug'].append(body)

    files = {}
    for k, ms in meshes.items():
        ms = [m for m in ms if not m.is_empty()]
        if not ms:
            continue
        mesh = m3.Manifold.batch_boolean(ms, m3.OpType.Add).to_mesh()
        f = t / f'{k}.stl'
        trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts)).export(f)
        files[k] = f
    return files


def main():
    with tempfile.TemporaryDirectory() as tmp:
        f = build(Path(tmp))
        specs = [
            f"Board, FR-4 1.4={f['board']}:#d9c7a0",
            f"F.Cu copper={f['cu']}:#c87533",
            f"Isolation cuts, V-bit (from the NC)={f['iso']}:#3a2a1a",
            f"Outline cuts, 0.8 bit with tabs (from the NC)={f['outline']}:#ff8c1a:0.35",
            f"Edge.Cuts={f['edge']}:#e0002a",
            f"-F.Mask (not on milled boards)={f['mask']}:#1f8a3a:0.45",
            f"-F.Paste={f['paste']}:#b8bcc0",
            f"F.Silkscreen={f['silk']}:#ffffff",
            f"-F.Fab={f['fab']}:#7a5cc0",
            f"-F.Courtyard={f['crtyd']}:#e040e0",
            f"Pins, 0.64 square={f['pins']}:#d4d8dc",
            f"Qwiic socket + R1 (stand-ins)={f['parts']}:#efe6cf",
            f"4P4C plug (stand-in, cavity measured)={f['plug']}:#a8c8e8:0.3",
            f"-Servo plug (stand-in)={f['servo_plug']}:#222222:0.6",
        ]
        OUT.parent.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'mockup_html.py'), str(OUT),
                        f"Nezha 4P4C plug tails rev {JOB['revision']}: servo (left), Qwiic (right)", *specs], check=True)
    print(OUT)
    if '--open' in sys.argv:
        subprocess.run(['open', '-a', 'Google Chrome', str(OUT)])


if __name__ == '__main__':
    main()
