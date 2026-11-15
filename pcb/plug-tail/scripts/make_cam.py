#!/usr/bin/env python3
"""Carvera NC for a strip of plug-tail boards with ALL spare copper cleared.

2026-11-11, the user: milled boards get no solder mask, so every bit of copper that is not a pad or a track comes
off; every cutting job switches the vacuum itself (M851 S100 after each M3, M852 after each M5).

Copper comes from exports/layers.json (F.Cu as KiCad draws it, pads and tracks; scripts/dump_layers.py on Buzzkill).
Copper faces up and nothing is mirrored. Tools are the Carvera's standard buildout
(robot-projects/carvera/projects/tool-racks):

  OP1  T4  30 deg V-bit, 0.2 tip   two isolation passes round every pad and track, then the gaps too narrow for T3
  OP2  T3  1.0 mm flat end mill    clears the open copper, its edge never nearer than CLEAR_F to a pad or track
  OP3  T5  0.8 mm corn cutter      tabbed outlines through the 1.4 stock, no tab on the tongue

Only needs shapely:  uv run --with shapely python scripts/make_cam.py   (or python3 on Buzzkill)
"""
from pathlib import Path
import json, math
from shapely.geometry import LineString, Polygon, MultiPolygon, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]; CAM = ROOT / 'cam'
GEO = json.loads((ROOT / 'checks/geometry.json').read_text())
DATA = json.loads((ROOT / 'exports/layers.json').read_text())

STOCK = 1.4                                       # the user's 1.4 mm stock fits the plug (2026-11-11)
SAFE = 5.0                                        # every rapid at or above this
T_V, T_F, T_O = 4, 3, 5                           # buildout slots: V-bit, 1 mm flat, 0.8 corn
ISO_Z = -.12                                      # V-bit depth
R_V = (.2 + 2 * -ISO_Z * math.tan(math.radians(15))) / 2   # half the V-bit's width at ISO_Z (0.132)
ISO_PASSES, ISO_STEP = 2, .15                     # rings at R_V and R_V + 0.15: the V-bit clears 0..0.414 round copper
REST_STEP = .18                                   # V-bit stepover in the narrow gaps
FLAT_Z, R_F, STEP_F = -.10, .5, .45               # 1 mm flat: depth, radius, stepover
CLEAR_F = .30                                     # the flat's edge stays this far from copper (V band reaches 0.414)
EDGE_OVER = .15                                   # the flat clears this far past the outline
THROUGH_Z, STEP, TAB_Z, TAB_W, R = -1.55, .25, -.9, 1.5, .4   # outline: 0.8 corn cutter
FEED, PLUNGE, RPM = 300, 100, 12000
TABS = {'header-tail': [(-1, 0, 15.8), (1, 0, 15.8), (0, 1, None)],      # (normal x, normal y, along) on the body sides and tail end
        'qwiic-tail': [(-1, 0, 17.8), (1, 0, 17.8), (0, 1, None)]}
STRIP = [('header-tail', 3.0), ('header-tail', 16.0), ('qwiic-tail', 29.0), ('qwiic-tail', 41.0)]
MARGIN_Y = 3.0
AREA = (53.0, 30.0)
PROGRAM = 'plug-tails-C-clear-4up-cut155.nc'


def polys(g):
    return [] if g.is_empty else list(g.geoms) if hasattr(g, 'geoms') else [g]


def copper(name):
    out = [Polygon(r[0], [h for h in r[1:] if len(h) >= 3]).buffer(0) for r in DATA[name]['layers']['F.Cu'] if len(r[0]) >= 3]
    return unary_union(out)


def rings(g):
    """Closed centre-line paths: every boundary of every polygon in g."""
    for p in polys(g):
        if p.geom_type != 'Polygon' or p.area < 1e-5:
            continue
        yield [tuple(c) for c in p.exterior.coords]
        for i in p.interiors:
            yield [tuple(c) for c in i.coords]


def pocket(region, step):
    """Concentric rings filling region (centre-line area), outermost first."""
    out, k = [], 0
    while True:
        g = region.buffer(-k * step, quad_segs=16) if k else region
        rs = list(rings(g))
        if not rs:
            return out
        out += rs; k += 1


def sweep(paths, r):
    return unary_union([LineString(p).buffer(r, quad_segs=16) if len(p) > 1 else Point(p[0]).buffer(r) for p in paths])


def plan(name):
    """Toolpaths in board-local coordinates (x across, y from the tongue tip), plus the checks' numbers."""
    outline = Polygon(GEO[name]['outline']); cu = copper(name)
    target = outline.difference(cu)                                   # all copper that must go (inside the board)
    iso = [r for k in range(ISO_PASSES) for r in rings(cu.buffer(R_V + k * ISO_STEP, quad_segs=16))]
    flat_area = outline.buffer(-R_F + EDGE_OVER, join_style=2).difference(cu.buffer(CLEAR_F + R_F, quad_segs=16))
    flat_area = flat_area.buffer(-1e-3).buffer(1e-3)
    flat = pocket(flat_area, STEP_F)
    done = sweep(iso, R_V).union(sweep(flat, R_F))
    left = unary_union([p for p in polys(target.difference(done)) if p.area > 1e-4])
    v_ok = outline.buffer(.3).difference(cu.buffer(R_V + .01, quad_segs=16))   # where the V-bit's centre may go
    rest = pocket(left.buffer(R_V - .03, quad_segs=16).intersection(v_ok), REST_STEP) if not left.is_empty else []
    # clean-up: whatever the rings still miss is a sliver; run the V-bit round its edge (clipped to where it may go)
    for _ in range(4):
        left = [p for p in polys(target.difference(done.union(sweep(rest, R_V)))) if p.area > 1e-6]
        if not left:
            break
        for p in left:
            for r in rings(p.buffer(.01)):
                g = LineString(r).intersection(v_ok)
                rest += [list(s.coords) for s in (g.geoms if hasattr(g, 'geoms') else [g]) if not s.is_empty and s.length > 0]
    vcut = sweep(iso + rest, R_V); fcut = sweep(flat, R_F)
    remain = target.difference(vcut.union(fcut))
    bits = [p for p in polys(remain) if p.area > 1e-6]
    return {'outline': outline, 'cu': cu, 'iso': iso, 'rest': rest, 'flat': flat,
            'vcut': vcut, 'fcut': fcut,
            'check': {'copper_hit_by_v_mm2': round(vcut.intersection(cu.buffer(-.005)).area, 6),
                      'copper_hit_by_flat_mm2': round(fcut.intersection(cu.buffer(-.005)).area, 6),
                      'flat_nearest_copper_mm': round(min((LineString(p).distance(cu) for p in flat), default=9) - R_F, 3),
                      'inside_corner_fillets': sum(p.distance(cu) < 1e-3 for p in bits),   # the round cutter can't reach in
                      'largest_fillet_mm2': round(max((p.area for p in bits), default=0), 5),
                      'floating_copper_bits': sum(p.distance(cu) >= 1e-3 for p in bits)}}


def order(paths, start=(0.0, 0.0)):
    """Nearest-neighbour order; each closed ring starts at its vertex nearest the cutter."""
    todo, out, at = [p for p in paths if len(p) > 1], [], start
    while todo:
        best = min(range(len(todo)), key=lambda i: min(math.dist(at, c) for c in todo[i]))
        p = todo.pop(best)
        if p[0] == p[-1]:
            j = min(range(len(p) - 1), key=lambda i: math.dist(at, p[i])); p = p[j:-1] + p[:j + 1]
        out.append(p); at = p[-1]
    return out, at


def cut(paths, z, m):
    out = []
    for p in paths:
        p = list(LineString(p).simplify(.002).coords) if len(p) > 2 else p
        out += ['G0 Z%.1f' % SAFE, 'G0 X%.5f Y%.5f' % m(*p[0]), f'G1 Z{z:.5f} F{PLUNGE}', f'G1 F{FEED}']
        out += ['G1 X%.5f Y%.5f' % m(*c) for c in p[1:]]
    return out + ['G0 Z%.1f' % SAFE]


def tab_boxes(name):
    g = GEO[name]; W, L = g['board_mm'][:2]; boxes = []
    for nx, ny, along in TABS[name]:
        cx, cy = (nx * W / 2, along) if nx else (0.0, L)
        boxes.append((cx, cy, nx, ny))
    return boxes


def in_tab(name, x, y):
    for cx, cy, nx, ny in tab_boxes(name):
        along = abs((x - cx) * ny - (y - cy) * nx) if nx else abs(x - cx)
        normal = (x - cx) * nx + (y - cy) * ny
        if along <= TAB_W / 2 + R and -.1 <= normal <= R + .3: return True
    return False


def outline(name, ox, oy):
    """Climb-cut the board's outside in 0.25 mm steps; tab windows stay at TAB_Z below it."""
    g = GEO[name]; W, L = g['board_mm'][:2]
    ring = Polygon(g['outline']).buffer(R, quad_segs=16).exterior
    pts = []
    for a, b in zip(ring.coords, ring.coords[1:]):
        n = max(1, math.ceil(math.dist(a, b) / .05))
        pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    pts.append(pts[0])
    if Polygon(pts).exterior.is_ccw: pts.reverse()  # clockwise in local y-down coordinates is counterclockwise (climb) on the machine

    def m(x, y): return ox + W / 2 + x, oy + L - y
    out = ['G0 Z%.1f' % SAFE, 'G0 X%.5f Y%.5f' % m(*pts[0]), f'G1 Z0 F{PLUNGE}', f'G1 F{FEED}']
    depths = [-min(-THROUGH_Z, STEP * k) for k in range(1, math.ceil(-THROUGH_Z / STEP) + 1)]
    z = 0.0
    for depth in depths:
        for i, (x, y) in enumerate(pts):
            want = max(depth, TAB_Z) if in_tab(name, x, y) else depth
            X, Y = m(x, y)
            if i == 0:
                out.append(f'G1 Z{want:.5f} F{PLUNGE}'); out.append(f'G1 F{FEED}'); z = want; continue
            if want < z:
                out.append(f'G1 X{X:.5f} Y{Y:.5f}'); out.append(f'G1 Z{want:.5f} F{PLUNGE}'); out.append(f'G1 F{FEED}')
            elif want > z:
                out.append(f'G1 Z{want:.5f}'); out.append(f'G1 X{X:.5f} Y{Y:.5f}')
            else:
                out.append(f'G1 X{X:.5f} Y{Y:.5f}')
            z = want
    out.append('G0 Z%.1f' % SAFE)
    return out


def tool(n):
    """Spindle and vacuum off for the change, both back on after it."""
    return ['M5', 'M852', 'G4 P3', f'M6 T{n}', 'G0 Z%.1f' % SAFE, f'M3 S{RPM}', 'M851 S100', 'G4 P3']


def length(paths): return sum(LineString(p).length for p in paths if len(p) > 1)


if __name__ == '__main__':
    placements = [{'id': i + 1, 'name': n, 'x': x, 'y': MARGIN_Y} for i, (n, x) in enumerate(STRIP)]
    plans = {n: plan(n) for n in GEO}
    ops = {1: [], 2: [], 3: []}; at = {1: (0, 0), 2: (0, 0)}
    for b in placements:
        W, L = GEO[b['name']]['board_mm'][:2]; pl = plans[b['name']]

        def m(x, y, b=b, W=W, L=L): return b['x'] + W / 2 + x, b['y'] + L - y
        tag = f"(BOARD {b['id']} {b['name'].upper()})"
        # nearest-neighbour order in machine coordinates so each operation sweeps the strip once
        vm, at[1] = order([[m(*c) for c in p] for p in pl['iso'] + pl['rest']], at[1])
        fm, at[2] = order([[m(*c) for c in p] for p in pl['flat']], at[2])
        ops[1] += [tag] + cut(vm, ISO_Z, lambda x, y: (x, y))
        ops[2] += [tag] + cut(fm, FLAT_Z, lambda x, y: (x, y))
        ops[3] += [tag] + outline(b['name'], b['x'], b['y'])
    out = ['(NEZHA PLUG TAILS REV C - ALL SPARE COPPER CLEARED - 2 HEADER + 2 QWIIC - ORIGINAL CARVERA)',
           f'(1.4 MM SINGLE-SIDED PCB - COPPER FACING UP - NOTHING MIRRORED)',
           f'(G54 XY0 = LOWER LEFT OF A FREE AREA AT LEAST X{AREA[0]:.0f} Y{AREA[1]:.0f} - Z0 COPPER SURFACE)',
           '(TONGUES POINT +Y)',
           f'(T{T_V} 30 DEG V BIT 0.2 TIP - T{T_F} 1.0 MM FLAT END MILL - T{T_O} 0.8 MM CORN CUTTER)',
           f'(V BIT Z{ISO_Z} - FLAT Z{FLAT_Z} - THROUGH Z{THROUGH_Z} - TABS RETAIN 0.50 MM, NONE ON THE TONGUES)',
           '(VACUUM M851 S100 ON WITH THE SPINDLE, M852 OFF WITH IT)',
           '(AUTO Z AND AUTO LEVELING REQUIRED BEFORE RUN)',
           'G21', 'G90', 'G17', 'G54',
           '(OPERATION 1 V BIT: ISOLATION ROUND PADS AND TRACKS, THEN NARROW GAPS)'] + tool(T_V) + ops[1] + \
          ['(OPERATION 2 FLAT: CLEAR THE OPEN COPPER)'] + tool(T_F) + ops[2] + \
          ['(OPERATION 3 CORN: TABBED OUTLINES)'] + tool(T_O) + ops[3] + \
          ['G0 Z10', 'M5', 'M852', 'G4 P3', 'M9', 'M30']
    (CAM / PROGRAM).write_text('\n'.join(out) + '\n')
    checks = {n: p['check'] for n, p in plans.items()}
    for n, c in checks.items():
        assert c['copper_hit_by_v_mm2'] < 1e-4 and c['copper_hit_by_flat_mm2'] < 1e-4, (n, c)
        assert c['flat_nearest_copper_mm'] >= CLEAR_F - .01, (n, c)
        assert c['floating_copper_bits'] == 0 and c['largest_fillet_mm2'] < .005, (n, c)
    job = {'name': 'nezha-plug-tails', 'revision': 'C', 'program': PROGRAM, 'area_mm': AREA, 'placements': placements,
           'stock_thickness_mm': STOCK, 'safe_z_mm': SAFE,
           'tools': {'v': {'slot': T_V, 'tool': '30 deg V-bit, 0.2 mm tip', 'z_mm': ISO_Z, 'effective_diameter_mm': round(2 * R_V, 4),
                           'passes_round_copper': ISO_PASSES, 'pass_step_mm': ISO_STEP, 'rest_step_mm': REST_STEP},
                     'flat': {'slot': T_F, 'tool': '1.0 mm flat end mill', 'z_mm': FLAT_Z, 'diameter_mm': 2 * R_F,
                              'stepover_mm': STEP_F, 'edge_to_copper_mm': CLEAR_F},
                     'outline': {'slot': T_O, 'tool': '0.8 mm corn cutter', 'diameter_mm': 2 * R, 'through_z_mm': THROUGH_Z, 'stepdown_mm': STEP}},
           'isolation': {'depth_mm': -ISO_Z, 'effective_diameter_mm': round(2 * R_V, 4), 'tip_mm': .2, 'angle_deg': 30},
           'through_z_mm': THROUGH_Z, 'stepdown_mm': STEP, 'cutter_mm': 2 * R,
           'tabs': {'width_mm': TAB_W, 'z_mm': TAB_Z, 'remaining_mm': round(STOCK + TAB_Z, 2), 'where': TABS},
           'feeds': {'rpm': RPM, 'feed_mm_min': FEED, 'plunge_mm_min': PLUNGE},
           'vacuum': 'M851 S100 after every M3, M852 after every M5',
           'path_mm': {n: {'v_iso': round(length(p['iso']), 1), 'v_rest': round(length(p['rest']), 1), 'flat': round(length(p['flat']), 1)}
                       for n, p in plans.items()},
           'clearing_checks': checks,
           'transform': 'machineX = placementX + W/2 + x; machineY = placementY + L - y (local y runs from the tongue tip)'}
    (CAM / 'job.json').write_text(json.dumps(job, indent=1) + '\n')
    print(PROGRAM, len(out), 'lines'); print(json.dumps({'path_mm': job['path_mm'], 'checks': checks}, indent=1))
