#!/usr/bin/env python3
"""Carvera NC for a strip of plug-tail boards: pcb2gcode isolation, then tabbed outlines generated
here so no tab lands on the tongue. Copper faces up and nothing is mirrored."""
from pathlib import Path
import json, math, re, subprocess
from shapely.geometry import Polygon, Point

ROOT = Path(__file__).resolve().parents[1]; CAM = ROOT / 'cam'
GEO = json.loads((ROOT / 'checks/geometry.json').read_text())
ISO_Z, THROUGH_Z, STEP, TAB_Z, TAB_W, R = -.12, -1.55, .25, -.9, 1.5, .4
VBIT = .2 + 2 * -ISO_Z * math.tan(math.radians(15))
TABS = {'servo-tail': [(-1, 0, 15.8), (1, 0, 15.8), (0, 1, None)],      # (normal x, normal y, along) on the body sides and tail end
        'qwiic-tail': [(-1, 0, 17.8), (1, 0, 17.8), (0, 1, None)]}
STRIP = [('servo-tail', 3.0), ('servo-tail', 14.0), ('qwiic-tail', 25.0), ('qwiic-tail', 37.0)]
MARGIN_Y = 3.0
AREA = (49.0, 30.0)


def millproject(name):
    d = CAM / 'raw' / name; d.mkdir(parents=True, exist_ok=True)
    (d / 'millproject').write_text(f'''metric=true
metricoutput=true
front=../../../exports/{name}/milling/{name}-F_Cu.gtl
output-dir=.
zero-start=false
x-offset=0
y-offset=0
zsafe=5
zchange=10
mill-diameters={VBIT:.6f}
isolation-width=0.5
milling-overlap=50%
zwork={ISO_Z}
mill-feed=300
mill-vertfeed=100
mill-speed=12000
nog64=true
nog91-1=true
nom6=true
spinup-time=3
spindown-time=3
tolerance=0.002
optimise=0.001
''')
    with (d / 'generation.log').open('w') as log:
        subprocess.run(['/home/ros/.local/bin/pcb2gcode'], cwd=d, stdout=log, stderr=log, check=True)
    return d / 'front.ngc'


def isolation(path, dx, dy):
    started = False; out = []
    for raw in path.read_text().splitlines():
        s = re.sub(r'\([^)]*\)', '', raw).strip()
        if not s: continue
        if not started:
            if re.match(r'G0?0\s+X', s): started = True
            else: continue
        if s.startswith('M5'): break
        assert re.match(r'^G0?[014]\b', s), s
        s = re.sub(r'^G0([014])\b', r'G\1', s)
        assert not re.search(r'[IJKR]', s), s
        for axis, d in [('X', dx), ('Y', dy)]: s = re.sub(axis + r'(-?[0-9.]+)', lambda m: axis + f'{float(m[1]) + d:.5f}', s)
        if s.startswith('G0 Z-'): out.extend(['G1' + s[2:] + ' F100', 'G1 F300'])
        else: out.append(s)
    assert started
    return out


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
    out = ['G0 Z5', 'G0 X%.5f Y%.5f' % m(*pts[0]), 'G1 Z0 F100', 'G1 F300']
    depths = [-min(-THROUGH_Z, STEP * k) for k in range(1, math.ceil(-THROUGH_Z / STEP) + 1)]
    z = 0.0
    for depth in depths:
        for i, (x, y) in enumerate(pts):
            want = max(depth, TAB_Z) if in_tab(name, x, y) else depth
            X, Y = m(x, y)
            if i == 0:
                out.append(f'G1 Z{want:.5f} F100'); out.append('G1 F300'); z = want; continue
            if want < z:
                out.append(f'G1 X{X:.5f} Y{Y:.5f}'); out.append(f'G1 Z{want:.5f} F100'); out.append('G1 F300')
            elif want > z:
                out.append(f'G1 Z{want:.5f}'); out.append(f'G1 X{X:.5f} Y{Y:.5f}')
            else:
                out.append(f'G1 X{X:.5f} Y{Y:.5f}')
            z = want
    out.append('G0 Z5')
    return out


def tool(n): return ['M5', 'G4 P3', f'M6 T{n}', 'G0 Z5', 'M3 S12000', 'G4 P3']


if __name__ == '__main__':
    raw = {n: millproject(n) for n in GEO}
    placements = [{'id': i + 1, 'name': n, 'x': x, 'y': MARGIN_Y} for i, (n, x) in enumerate(STRIP)]
    out = ['(NEZHA PLUG TAILS REV B - 2 SERVO + 2 QWIIC - ORIGINAL CARVERA)',
           '(1.4 MM SINGLE-SIDED PCB - COPPER FACING UP - NOTHING MIRRORED)',
           f'(G54 XY0 = LOWER LEFT OF A FREE AREA AT LEAST X{AREA[0]:.0f} Y{AREA[1]:.0f} - Z0 COPPER SURFACE)',
           '(TONGUES POINT +Y)',
           '(T2 30 DEG V BIT 0.2 TIP - T3 0.8 MM CORN BIT)',
           f'(ISOLATION Z{ISO_Z} - THROUGH Z{THROUGH_Z} - TABS RETAIN 0.50 MM, NONE ON THE TONGUES)',
           '(AUTO Z AND AUTO LEVELING REQUIRED BEFORE RUN)',
           'G21', 'G90', 'G17', 'G54', '(OPERATION 1 TRACE ISOLATION)'] + tool(2)
    for b in placements:
        L = GEO[b['name']]['board_mm'][1]
        out.append(f"(BOARD {b['id']} {b['name'].upper()})"); out += isolation(raw[b['name']], b['x'], b['y'] + L)
    out += ['(OPERATION 2 TABBED OUTLINES)'] + tool(3)
    for b in placements:
        out.append(f"(BOARD {b['id']} {b['name'].upper()})"); out += outline(b['name'], b['x'], b['y'])
    out += ['G0 Z10', 'M5', 'G4 P3', 'M9', 'M30']
    name = 'plug-tails-B-4up-iso120-cut155.nc'
    (CAM / name).write_text('\n'.join(out) + '\n')
    job = {'name': 'nezha-plug-tails', 'revision': 'B', 'program': name, 'area_mm': AREA, 'placements': placements,
           'stock_thickness_mm': 1.4, 'isolation': {'depth_mm': -ISO_Z, 'effective_diameter_mm': VBIT, 'tip_mm': .2, 'angle_deg': 30},
           'through_z_mm': THROUGH_Z, 'stepdown_mm': STEP, 'cutter_mm': 2 * R,
           'tabs': {'width_mm': TAB_W, 'z_mm': TAB_Z, 'remaining_mm': round(1.4 + TAB_Z, 2), 'where': TABS},
           'transform': 'machineX = placementX + W/2 + x; machineY = placementY + L - y (local y runs from the tongue tip)'}
    (CAM / 'job.json').write_text(json.dumps(job, indent=1) + '\n')
    print(name, len(out), 'lines')
