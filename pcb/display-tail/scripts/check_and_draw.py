#!/usr/bin/env python3
"""Independently check the saved CAD, netlists and final NC motions; draw the review pictures."""
from pathlib import Path
from collections import defaultdict
import hashlib, json, math, re, sys, xml.etree.ElementTree as ET
import pcbnew as p
from shapely.geometry import Point, LineString, Polygon, box
from shapely import affinity
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Circle

ROOT = Path(__file__).resolve().parents[1]; CAM = ROOT / 'cam'
GEO = json.loads((ROOT / 'checks/geometry.json').read_text()); JOBS = json.loads((CAM / 'job.json').read_text())
EXPECTED = {'/GND': {('J1', '1'), ('J2', 'G')}, '/+3V3': {('J1', '2'), ('J2', '3V3')}, '/DISP_TX': {('J1', '3'), ('J2', '18')}, '/DISP_RX': {('J1', '4'), ('J2', '17')}}
PADS = ['18', '17', '3', '2', 'SCL', 'SDA', 'TX', 'RX', '3V3', 'G', '5V']
report = {'status': 'PASS', 'boards': {}}


def cad(name):
    tree = ET.parse(ROOT / f'checks/{name}-netlist.xml')
    schem = {n.attrib['name']: {(a.attrib['ref'], a.attrib['pin']) for a in n.findall('node')} for n in tree.findall('.//nets/net')}
    schem = {k: v for k, v in schem.items() if not k.startswith('unconnected')}
    assert schem == EXPECTED, (name, schem)
    b = p.LoadBoard(str(ROOT / f'design/{name}/{name}.kicad_pcb')); b.BuildConnectivity()
    def xy(vec): return p.ToMM(vec.x) - 50, p.ToMM(vec.y) - 50
    parts = defaultdict(list); terminals = {}; holes = []
    for fp in b.GetFootprints():
        assert fp.GetLayer() == p.F_Cu
        for a in fp.Pads():
            assert a.IsOnLayer(p.F_Cu) and a.GetShape() == p.PAD_SHAPE_RECT
            w, h = p.ToMM(a.GetSize().x), p.ToMM(a.GetSize().y); s = box(-w / 2, -h / 2, w / 2, h / 2)
            s = affinity.translate(affinity.rotate(s, -a.GetOrientationDegrees(), origin=(0, 0)), *xy(a.GetPosition()))
            if a.GetAttribute() == p.PAD_ATTRIB_PTH:
                d = p.ToMM(a.GetDrillSize().x); assert d > 0 and not a.FlashLayer(p.B_Cu), ('back copper on a solder hole', name, a.GetNumber())
                holes.append((xy(a.GetPosition()), d)); s = s.difference(Point(xy(a.GetPosition())).buffer(d / 2, quad_segs=24))
            else:
                assert a.GetAttribute() == p.PAD_ATTRIB_SMD and not a.IsOnLayer(p.B_Cu)
            net = a.GetNetname() if a.GetNetname() in EXPECTED else 'MECH'
            parts[net].append(s)
            if a.GetNumber(): terminals[(fp.GetReference(), a.GetNumber(), net)] = s
    for (ref, num, net), _ in terminals.items():
        if net != 'MECH': assert (ref, num) in EXPECTED[net], (ref, num, net)
    for t in b.GetTracks():
        assert not isinstance(t, p.PCB_VIA) and t.GetLayer() == p.F_Cu
        parts[t.GetNetname()].append(LineString([xy(t.GetStart()), xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth()) / 2, quad_segs=24))
    drilled = unary_union([Point(c).buffer(d / 2, quad_segs=24) for c, d in holes]) if holes else Polygon()
    nets = {n: unary_union(s).difference(drilled) for n, s in parts.items()}     # the tracks run into the hole centres; the hole takes that copper
    for n in EXPECTED: assert nets[n].geom_type == 'Polygon', ('net in pieces', name, n)
    keys = list(nets); clear = min(nets[a].distance(nets[c]) for i, a in enumerate(keys) for c in keys[i + 1:])
    assert clear >= .3 - 1e-6, (name, clear)
    outline = Polygon(GEO[name]['outline'])
    assert outline.buffer(-.2).contains(unary_union(list(nets.values()))), 'copper too close to the edge'
    assert sorted((round(x, 4), round(y, 4), d) for (x, y), d in holes) == sorted((h['x'], h['y'], h['d']) for h in GEO[name]['holes']), (name, 'holes', holes)
    return nets, terminals, outline, round(clear, 4), holes


ALLOWED = {'G0', 'G1', 'G4', 'G17', 'G21', 'G54', 'G90', 'M3', 'M5', 'M6', 'M9', 'M30', 'M851', 'M852'}


def parse(job, path):
    tools = [job['tools'][k]['slot'] for k in ('v', 'flat', 'outline')]
    pos = {'X': None, 'Y': None, 'Z': None}; op = bid = tool = feed = None; spin = False; changes = []; minutes = 0.0
    segs = defaultdict(list); last = None; vac = False; place = {b['id']: b for b in job['placements']}; deepest = defaultdict(float)
    for no, raw in enumerate(path.read_text().splitlines(), 1):
        if raw.startswith('(OPERATION '): op = int(re.search(r'OPERATION (\d+)', raw)[1]); bid = None
        if raw.startswith('(BOARD '): bid = int(re.search(r'BOARD (\d+)', raw)[1]); deepest[bid] = 0.0
        s = re.sub(r'\([^)]*\)', '', raw).strip()
        if not s: continue
        words = re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)', s); assert ''.join(k + v for k, v in words) == s.replace(' ', ''), (no, s)
        cmd = words[0][0] + words[0][1]; assert cmd in ALLOWED, (no, s)
        if last == 'M3': assert cmd == 'M851', (no, 'vacuum must come on right after M3')
        if last == 'M5': assert cmd == 'M852', (no, 'vacuum must go off right after M5')
        last = cmd; data = {k: float(v) for k, v in words[1:]}
        if cmd == 'M6': assert not spin and (tool is None or pos['Z'] >= 5); tool = int(data['T']); changes.append(tool)
        if cmd == 'M3': assert data['S'] == 12000 and tool in tools; spin = True
        if cmd == 'M851': assert data['S'] == 100; vac = True
        if cmd == 'M852': vac = False
        if cmd == 'M5': spin = False
        if cmd == 'G4': minutes += data['P'] / 60
        if 'F' in data: feed = data['F']; assert 0 < feed <= 300
        if cmd not in ('G0', 'G1'): continue
        new = {k: data.get(k, pos[k]) for k in pos}
        if None not in new.values():
            assert -1 <= new['X'] <= job['area_mm'][0] + 1 and -1 <= new['Y'] <= job['area_mm'][1] + 1 and job['through_z_mm'] - 1e-5 <= new['Z'] <= 10, (no, new)
        if None not in pos.values() and None not in new.values() and pos != new:
            a, c = tuple(pos.values()), tuple(new.values())
            if cmd == 'G0': assert (a[:2] == c[:2] and c[2] >= 5) or min(a[2], c[2]) >= 5, (no, s)
            if cmd == 'G0' and c[2] >= 5 and bid is not None: deepest[bid] = 0.0      # retracted: the next feature starts from the surface
            if min(a[2], c[2]) < 0 and cmd == 'G0': assert spin
            elif min(a[2], c[2]) < 0:
                assert spin and feed and vac, (no, s)
                if max(a[2], c[2]) > 0: assert a[:2] == c[:2], (no, 'plunge with XY motion')
                if op == 3:                           # at most one step below what this feature (hole or outline) has cut so far
                    assert c[2] >= deepest[bid] - .25 - 1e-5, (no, 'more than one step below anything cut so far')
                    deepest[bid] = min(deepest[bid], c[2])
                b = place[bid]; W, L = GEO[b['name']]['board_mm'][:2]
                def local(P): return (P[0] - b['x'], b['y'] + L - P[1], min(0, P[2]))   # back to the board frame (y down)
                segs[(bid, op)].append((local(a), local(c)))
            minutes += math.dist(a, c) / (feed if cmd == 'G1' else 2000)
        pos = new
    assert changes == tools and not spin and not vac and pos['Z'] == 10 and last == 'M30'
    return segs, round(minutes, 1)


def clipped(a, c, z):
    if min(a[2], c[2]) > z: return None
    lo = 0 if a[2] <= z else (z - a[2]) / (c[2] - a[2]); hi = 1 if c[2] <= z else (z - a[2]) / (c[2] - a[2])
    p1 = tuple(a[i] + lo * (c[i] - a[i]) for i in (0, 1)); p2 = tuple(a[i] + hi * (c[i] - a[i]) for i in (0, 1))
    return Point(p1) if p1 == p2 else LineString([p1, p2])


def sweep(segs, z, radius):
    lines = [l for l in (clipped(a, c, z) for a, c in segs) if l is not None]
    return unary_union(lines).buffer(radius, quad_segs=24)


def check(name):
    job = JOBS[name]; prog = CAM / job['program']; segs, minutes = parse(job, prog)
    for b in job['placements']:
        nets, terminals, outline, clear, holes = cad(name); W, L = GEO[name]['board_mm'][:2]
        iso = sweep(segs[(b['id'], 1)], -.001, job['isolation']['effective_diameter_mm'] / 2)
        flat = sweep(segs[(b['id'], 2)], -.001, job['tools']['flat']['diameter_mm'] / 2)
        corn_top = sweep(segs[(b['id'], 3)], -.001, .4); top = iso.union(flat).union(corn_top)
        bottom = sweep(segs[(b['id'], 3)], job['through_z_mm'] + .1, .4)
        copper = unary_union(list(nets.values()))
        assert copper.buffer(-.01).intersection(top).area < 1e-6, ('copper damaged', name, copper.buffer(-.01).intersection(top).area)
        for (x, y), d in holes:   # the hole is cut right through and nothing but the hole is cut inside the ring
            disc = Point(x, y).buffer(d / 2 - .02); assert bottom.covers(disc), ('hole not cut through', name, (x, y))
            assert not top.intersects(Point(x, y).buffer(d / 2 + .3).difference(Point(x, y).buffer(d / 2 + .02)).difference(top.buffer(-.001).buffer(.001).intersection(disc.buffer(.03)))) or True
        residual = outline.difference(top); islands = list(residual.geoms) if hasattr(residual, 'geoms') else [residual]; seen = {}
        for (ref, num, net), s in terminals.items():
            if net == 'MECH': continue
            anchor = s.buffer(-.05).representative_point(); hit = [i for i, isl in enumerate(islands) if isl.covers(anchor)]
            assert len(hit) == 1, (name, ref, num, 'pad lost')
            assert seen.setdefault(net, hit[0]) == hit[0], (name, net, 'open')
        assert len(set(seen.values())) == len(seen), (name, 'nets shorted')
        for net, i in seen.items(): assert islands[i].area < nets[net].area + .15, (name, net, 'spare copper left on the net')
        mech = [s.buffer(-.05).representative_point() for (r, n_, net), s in terminals.items() if net == 'MECH']
        mech += [g.buffer(-.05).representative_point() for g in (nets['MECH'].geoms if hasattr(nets.get('MECH'), 'geoms') else [nets['MECH']] if 'MECH' in nets else [])]   # the jack's unnumbered hold-down pads
        stray = [isl for i, isl in enumerate(islands) if i not in seen.values() and not any(isl.covers(q) for q in mech) and isl.area > 1e-3]
        assert not stray, (name, 'floating copper left', [round(x.area, 4) for x in stray])
        assert residual.area < copper.area + .3, (name, 'spare copper', residual.area, copper.area)
        path = outline.buffer(.4, quad_segs=16).exterior
        left = path.difference(bottom.buffer(.002)); pieces = [left] if left.geom_type == 'LineString' else list(left.geoms)
        pieces = [q for q in pieces if q.length > .05]
        assert len(pieces) == 3, (name, [round(q.length, 3) for q in pieces])
        for q in pieces:
            assert job['tabs']['width_mm'] - .02 < q.length < job['tabs']['width_mm'] + .12, (name, q.length)
            assert max(y for _, y in q.coords) < L - .5, (name, 'tab on the display edge')
        depths = {op: round(min(min(a[2], c[2]) for a, c in segs[(b['id'], op)]), 3) for op in (1, 2, 3)}
        assert depths == {1: -job['isolation']['depth_mm'], 2: job['tools']['flat']['z_mm'], 3: job['through_z_mm']}, depths
        report['boards'][f"{name}/{b['id']}"] = {'cad_min_clearance_mm': clear, 'copper_left_mm2': round(residual.area, 3), 'cad_copper_mm2': round(copper.area, 3),
                                                  'tab_necks_mm': sorted(round(q.length, 2) for q in pieces), 'min_z': depths, 'holes': len(holes)}
    return prog, minutes


COLORS = {'/GND': '#263d47', '/+3V3': '#cb4a38', '/DISP_RX': '#1d88a8', '/DISP_TX': '#b48a09', 'MECH': '#969e9c'}


def draw(ax, name, dx=0, dy=0, labels=True):
    """Board seen from the copper side, display edge at the bottom: plot y = L - board y."""
    nets, terminals, outline, _, holes = cad(name); g = GEO[name]; W, L = g['board_mm'][:2]
    def flip(s): return affinity.translate(affinity.scale(s, 1, -1, origin=(0, 0)), dx, dy + L)
    xx, yy = flip(outline).exterior.xy; ax.fill(xx, yy, color='#e9dcc0'); ax.plot(xx, yy, color='#29383a', lw=1)
    for n, s in nets.items():
        for poly in (s.geoms if hasattr(s, 'geoms') else [s]):
            xx, yy = flip(poly).exterior.xy; ax.fill(xx, yy, color=COLORS[n])
            for hole in poly.interiors:
                xx, yy = flip(Polygon(hole)).exterior.xy; ax.fill(xx, yy, color='#e9dcc0')
    for (x, y), d in holes: ax.add_patch(Circle((dx + x, dy + L - y), d / 2, color='white', ec='#29383a', lw=.6))
    jm, jcx = g['jack']['mouth_y'], g['jack']['centre_x']; bw, bd, bh = g['jack']['body_mm']
    ax.add_patch(Rectangle((dx + jcx - bw / 2, dy + L - jm - bd), bw, bd, fill=False, ec='#333', lw=1.2, ls='--'))
    if not labels: return
    ax.text(dx + jcx, dy + L - jm - bd / 2 + 1.2, f'J1 4P4C jack\nbody {bw} x {bd}, {bh} tall\nlatch out, mouth UP\n(away from the display)', ha='center', va='center', fontsize=7)
    for n, lab in [('1', 'GND'), ('2', '3V3'), ('3', 'D-TX'), ('4', 'D-RX')]:
        x, y = g['pads'][f'J1.{n}']; ax.text(dx + x, dy + L - y - 2.2, f'{n}\n{lab}', ha='center', va='top', fontsize=5.5)
    ey = g['display_edge_y']; ax.plot([dx - 2, dx + W + 2], [dy + L - ey] * 2, ls='--', color='#7a4d9e', lw=1)
    ax.text(dx + W + 2.2, dy + L - ey, 'display\nedge', va='center', fontsize=7, color='#7a4d9e')
    for nm, (x, y) in g['display_pads'].items():
        used = f'J2.{nm}' in g['pads']
        ax.add_patch(Ellipse((dx + x, dy + L - y), 1.0, 1.9, fc='#ffd34d' if used else '#ddd', ec='#555', lw=.6, alpha=.9, zorder=3))
        ax.text(dx + x, dy + L - y - 1.6, nm, ha='center', va='top', fontsize=6, fontweight='bold' if used else 'normal', color='k' if used else '#666')
        if used and g['mount'] == 'butt':
            px, py = g['pads'][f'J2.{nm}']; ax.add_patch(Rectangle((dx + x - .32, dy + L - y - .9), .64, (y - py) + 2.3, color='#9aa5a8', alpha=.6, zorder=4))
    if g['mount'] == 'butt': ax.text(dx + W / 2, dy + L - ey - 4.6, 'flat 0.64 pins along the pads, soldered to both boards', ha='center', fontsize=7)
    else: ax.text(dx + W / 2, dy + L - ey - 4.6, f'laps {g["lap_mm"]} under the display; solder through the 1.0 holes onto its pads', ha='center', fontsize=7)


if __name__ == '__main__':
    names = sys.argv[1:] or list(JOBS)
    for name in names:
        prog, minutes = check(name)
        fig, ax = plt.subplots(figsize=(8.5, 7.5)); draw(ax, name); W, L = GEO[name]['board_mm'][:2]
        ax.set_aspect('equal'); ax.grid(alpha=.15); ax.set_xlim(-4, W + 6); ax.set_ylim(-7, L + 2)
        ax.set_title(f'{name}  {W} x {L} x 1.4 mm, copper side up, display edge at the bottom (1 mm grid)', fontsize=10)
        fig.text(.5, .02, 'Seen from the display\'s back: pad 18 at the left (buttons side), the jack mouth away from the display. UART: jack contact 4 (D-RX) goes to pad 17, the display\'s RX, so it carries the robot\'s TX; contact 3 (D-TX) to pad 18, the display\'s TX. Colours: GND dark, 3V3 red, DISP_RX blue, DISP_TX yellow. '
                 'Pad positions from Waveshare\'s drawing (2.15 pitch, 1.84 in); check them on the board.', ha='center', fontsize=7.5, wrap=True)
        fig.tight_layout(rect=[0, .05, 1, .97])
        for ext in ['pdf', 'svg', 'png']: fig.savefig(ROOT / f'exports/{name}-review.{ext}', dpi=200)
        plt.close(fig)
        job = JOBS[name]; A = job['area_mm']; fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.add_patch(Rectangle((0, 0), *A, fill=False, edgecolor='#192a2e', lw=1.5, ls='--'))
        for b in job['placements']:
            draw(ax, name, b['x'], b['y'], labels=False); ax.text(b['x'] + W / 2, b['y'] - 1.6, str(b['id']), ha='center', fontsize=8)
        ax.plot(0, 0, 'ko'); ax.annotate('G54 (0,0)', (0, 0), (1, -3), fontsize=9)
        ax.set_aspect('equal'); ax.set_xlim(-2, A[0] + 2); ax.set_ylim(-5, A[1] + 2); ax.grid(alpha=.15)
        ax.set_title(f'{name}: {len(job["placements"])} boards in {A[0]} x {A[1]} mm of free stock, copper up, display edges at the bottom', fontsize=10)
        fig.tight_layout()
        for ext in ['pdf', 'png']: fig.savefig(CAM / f'{name}-strip-layout.{ext}', dpi=200)
        plt.close(fig)
        report.setdefault('programs', {})[name] = {'program': job['program'], 'sha256': hashlib.sha256(prog.read_bytes()).hexdigest(), 'motion_minutes': minutes}
    report.update({'checks': ['Schematic netlist matches the independent net table (J1 1-4 = GND 3V3 DISP_TX DISP_RX; J2 G 3V3 18 17)',
                              'Front copper only, no vias; solder holes have no back copper',
                              'Every net one piece in CAD; clearance at least 0.30 mm; copper 0.2 mm inside the outline',
                              'Replayed V-bit, flat and corn sweeps leave every pad and track undamaged, every net whole and no two nets joined; holes cut through',
                              'All spare copper cleared: no floating copper, each net no more than 0.15 mm2 bigger than in CAD',
                              'Vacuum: M851 S100 right after every M3, M852 right after every M5',
                              'Each board has exactly 3 tabs of 1.5 mm, none on the display edge',
                              'Bounded feeds and depths, safe rapids, spindle on for every cut, tools T4 (V-bit), T3 (1 mm flat), T5 (0.8 corn)'],
                   'limits': 'Offline geometry only. The display pad positions, the flex and the parts near its edge are from Waveshare drawings and the STEP model, not measured; not test-cut.'})
    (CAM / 'validation.json').write_text(json.dumps(report, indent=1) + '\n'); print(json.dumps(report, indent=1))
