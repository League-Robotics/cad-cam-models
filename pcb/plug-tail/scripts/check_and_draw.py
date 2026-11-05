#!/usr/bin/env python3
"""Independently check the saved CAD, netlists and final NC motions; draw the review sheets."""
from pathlib import Path
from collections import defaultdict
import hashlib, json, math, re, xml.etree.ElementTree as ET
import pcbnew as p
from shapely.geometry import Point, LineString, Polygon, box
from shapely import affinity
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]; CAM = ROOT / 'cam'
GEO = json.loads((ROOT / 'checks/geometry.json').read_text()); JOB = json.loads((CAM / 'job.json').read_text())
EXPECTED = {
    'header-tail': {'/GND': {('J1', '1'), ('J2', '1')}, '/VCC': {('J1', '2'), ('J2', '2')}, '/S1': {('J1', '3'), ('J2', '3')},
                    '/S2': {('J1', '4'), ('J2', '4')}},
    'qwiic-tail': {'/GND': {('J1', '1'), ('J2', '1')}, '/+3V3': {('J1', '2'), ('J2', '2')}, '/SCL': {('J1', '3'), ('R1', '1')},
                   '/SDA': {('J1', '4'), ('J2', '3')}, '/SCL_QWIIC': {('R1', '2'), ('J2', '4')}}}
report = {'status': 'PASS', 'boards': {}}


def cad(name):
    g = GEO[name]; W = g['board_mm'][0]; X0 = 50 + W / 2
    tree = ET.parse(ROOT / f'checks/{name}-netlist.xml')
    schem = {n.attrib['name']: {(a.attrib['ref'], a.attrib['pin']) for a in n.findall('node')} for n in tree.findall('.//nets/net')}
    schem = {k: v for k, v in schem.items() if not k.startswith('unconnected')}
    assert schem == EXPECTED[name], (name, schem)
    b = p.LoadBoard(str(ROOT / f'design/{name}/{name}.kicad_pcb')); b.BuildConnectivity()

    def xy(vec): return p.ToMM(vec.x) - X0, p.ToMM(vec.y) - 50
    parts = defaultdict(list); terminals = {}
    for fp in b.GetFootprints():
        assert fp.GetLayer() == p.F_Cu
        for a in fp.Pads():
            assert a.GetAttribute() == p.PAD_ATTRIB_SMD and a.IsOnLayer(p.F_Cu) and not a.IsOnLayer(p.B_Cu)
            w, h = p.ToMM(a.GetSize().x), p.ToMM(a.GetSize().y)
            if a.GetShape() == p.PAD_SHAPE_ROUNDRECT:
                r = p.ToMM(a.GetRoundRectCornerRadius()); s = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=24)
            else:
                assert a.GetShape() == p.PAD_SHAPE_RECT; s = box(-w / 2, -h / 2, w / 2, h / 2)
            s = affinity.translate(affinity.rotate(s, -a.GetOrientationDegrees(), origin=(0, 0)), *xy(a.GetPosition()))
            net = a.GetNetname() if a.GetNetname() in EXPECTED[name] else 'MECH'
            parts[net].append(s)
            if a.GetNumber(): terminals[(fp.GetReference(), a.GetNumber(), net)] = s
    for (ref, num, net), _ in terminals.items():
        if net != 'MECH': assert (ref, num) in EXPECTED[name][net], (ref, num, net)
    for t in b.GetTracks():
        assert not isinstance(t, p.PCB_VIA) and t.GetLayer() == p.F_Cu
        parts[t.GetNetname()].append(LineString([xy(t.GetStart()), xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth()) / 2, quad_segs=24))
    nets = {n: unary_union(s) for n, s in parts.items()}
    for n in EXPECTED[name]: assert nets[n].geom_type == 'Polygon', ('net in pieces', name, n)
    keys = list(nets); clear = min(nets[a].distance(nets[c]) for i, a in enumerate(keys) for c in keys[i + 1:])
    assert clear >= .3 - 1e-6, (name, clear)
    outline = Polygon(g['outline'])
    assert outline.buffer(-.2).contains(unary_union(list(nets.values()))), 'copper too close to the edge'
    return nets, terminals, outline, round(clear, 4)


ALLOWED = {'G0', 'G1', 'G4', 'G17', 'G21', 'G54', 'G90', 'M3', 'M5', 'M6', 'M9', 'M30'}


def parse(path):
    pos = {'X': None, 'Y': None, 'Z': None}; op = bid = tool = feed = None; spin = False; changes = []; minutes = 0.0
    segs = defaultdict(list); last = None; place = {b['id']: b for b in JOB['placements']}; deepest = defaultdict(float)
    for no, raw in enumerate(path.read_text().splitlines(), 1):
        if raw.startswith('(OPERATION '): op = int(re.search(r'OPERATION (\d+)', raw)[1]); bid = None
        if raw.startswith('(BOARD '): bid = int(re.search(r'BOARD (\d+)', raw)[1])
        s = re.sub(r'\([^)]*\)', '', raw).strip()
        if not s: continue
        words = re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)', s); assert ''.join(k + v for k, v in words) == s.replace(' ', ''), (no, s)
        cmd = words[0][0] + words[0][1]; assert cmd in ALLOWED, (no, s); last = cmd
        data = {k: float(v) for k, v in words[1:]}
        if cmd == 'M6': assert not spin and (tool is None or pos['Z'] >= 5); tool = int(data['T']); changes.append(tool)
        if cmd == 'M3': assert data['S'] == 12000 and tool in (2, 3); spin = True
        if cmd == 'M5': spin = False
        if cmd == 'G4': minutes += data['P'] / 60
        if 'F' in data: feed = data['F']; assert 0 < feed <= 300
        if cmd not in ('G0', 'G1'): continue
        new = {k: data.get(k, pos[k]) for k in pos}
        if None not in new.values():
            assert -1 <= new['X'] <= JOB['area_mm'][0] + 1 and -1 <= new['Y'] <= JOB['area_mm'][1] + 1 and JOB['through_z_mm'] - 1e-5 <= new['Z'] <= 10, (no, new)
        if None not in pos.values() and None not in new.values() and pos != new:
            a, c = tuple(pos.values()), tuple(new.values())
            if cmd == 'G0': assert (a[:2] == c[:2] and c[2] >= 5) or min(a[2], c[2]) >= 5, (no, s)
            if min(a[2], c[2]) < 0 and cmd == 'G0': assert spin  # vertical retract out of the cut
            elif min(a[2], c[2]) < 0:
                assert spin and feed, (no, s)
                if max(a[2], c[2]) > 0: assert a[:2] == c[:2], (no, 'plunge with XY motion')
                if op == 2:
                    assert c[2] >= deepest[bid] - .25 - 1e-5, (no, 'more than one step below anything cut so far')
                    deepest[bid] = min(deepest[bid], c[2])
                b = place[bid]; L = GEO[b['name']]['board_mm'][1]; W = GEO[b['name']]['board_mm'][0]

                def local(P): return (P[0] - b['x'] - W / 2, b['y'] + L - P[1], min(0, P[2]))
                segs[(bid, op)].append((local(a), local(c)))
            minutes += math.dist(a, c) / (feed if cmd == 'G1' else 2000)
        pos = new
    assert changes == [2, 3] and not spin and pos['Z'] == 10 and last == 'M30'
    return segs, round(minutes, 1)


def clipped(a, c, z):
    if min(a[2], c[2]) > z: return None
    lo = 0 if a[2] <= z else (z - a[2]) / (c[2] - a[2]); hi = 1 if c[2] <= z else (z - a[2]) / (c[2] - a[2])
    p1 = tuple(a[i] + lo * (c[i] - a[i]) for i in (0, 1)); p2 = tuple(a[i] + hi * (c[i] - a[i]) for i in (0, 1))
    return Point(p1) if p1 == p2 else LineString([p1, p2])


def sweep(segs, z, radius):
    lines = [l for l in (clipped(a, c, z) for a, c in segs) if l is not None]
    return unary_union(lines).buffer(radius, quad_segs=24)


prog = CAM / JOB['program']; segs, minutes = parse(prog)
for b in JOB['placements']:
    name = b['name']; nets, terminals, outline, clear = cad(name)
    iso = sweep(segs[(b['id'], 1)], -.001, JOB['isolation']['effective_diameter_mm'] / 2)
    top = iso.union(sweep(segs[(b['id'], 2)], -.001, .4)); bottom = sweep(segs[(b['id'], 2)], JOB['through_z_mm'] + .1, .4)
    copper = unary_union(list(nets.values()))
    assert copper.buffer(-.01).intersection(top).area < 1e-6, ('copper damaged', name, copper.buffer(-.01).intersection(top).area)
    residual = outline.difference(top); islands = list(residual.geoms) if hasattr(residual, 'geoms') else [residual]; seen = {}
    for (ref, num, net), s in terminals.items():
        if net == 'MECH': continue
        anchor = s.buffer(-.05).representative_point(); hit = [i for i, isl in enumerate(islands) if isl.covers(anchor)]
        assert len(hit) == 1, (name, ref, num, 'pad lost')
        assert seen.setdefault(net, hit[0]) == hit[0], (name, net, 'open')
    assert len(set(seen.values())) == len(seen), (name, 'nets shorted')
    for net, i in seen.items(): assert islands[i].area < nets[net].area * 1.25 + .2, (name, net, 'joined to background copper')
    path = outline.buffer(.4, quad_segs=16).exterior
    left = path.difference(bottom.buffer(.002)); pieces = [left] if left.geom_type == 'LineString' else list(left.geoms)
    pieces = [q for q in pieces if q.length > .05]
    tongue = GEO[name]['tongue_mm'][1]
    assert len(pieces) == 3, (name, [round(q.length, 3) for q in pieces])
    for q in pieces:
        assert JOB['tabs']['width_mm'] - .02 < q.length < JOB['tabs']['width_mm'] + .12, (name, q.length)
        assert min(y for _, y in q.coords) > tongue + .5, (name, 'tab on the tongue')
    uncut = outline.buffer(.35).difference(outline.buffer(.05)).difference(bottom).intersection(box(-10, -1, 10, tongue))
    assert uncut.is_empty or uncut.bounds[1] > tongue - .45, ('tongue not cut free', uncut.bounds)  # only the 0.4 mm root fillet the 0.8 mm cutter leaves
    depths = {op: round(min(min(a[2], c[2]) for a, c in segs[(b['id'], op)]), 3) for op in (1, 2)}
    assert depths == {1: -JOB['isolation']['depth_mm'], 2: JOB['through_z_mm']}, depths
    report['boards'][str(b['id'])] = {'name': name, 'cad_min_clearance_mm': clear, 'tab_necks_mm': sorted(round(q.length, 2) for q in pieces), 'min_z': depths}

colors = {'/GND': '#263d47', '/+3V3': '#cb4a38', '/VS': '#cb4a38', '/SDA': '#1d88a8', '/SCL': '#b48a09', '/SCL_QWIIC': '#b48a09', '/SIG': '#d8811f', '/VCC': '#cb4a38', '/S1': '#3a9a3a', '/S2': '#d4b106', 'MECH': '#969e9c'}
LABELS = {'header-tail': (['GND', 'VCC', 'S1', 'S2'], ['G', 'V', 'S1', 'S2']), 'qwiic-tail': (['GND', '3V3', 'SCL', 'SDA'], None)}


def draw(ax, name, dx=0, dy=0, labels=True):
    nets, terminals, outline, _ = cad(name); L = GEO[name]['board_mm'][1]

    def flip(g): return affinity.translate(affinity.scale(g, 1, -1, origin=(0, 0)), dx, dy + L)
    xx, yy = flip(outline).exterior.xy; ax.fill(xx, yy, color='#e9dcc0'); ax.plot(xx, yy, color='#29383a', lw=1)
    for n, g in nets.items():
        for poly in (g.geoms if hasattr(g, 'geoms') else [g]):
            xx, yy = flip(poly).exterior.xy; ax.fill(xx, yy, color=colors[n])
    if not labels: return
    tl = GEO[name]['tongue_mm'][1]; W = GEO[name]['board_mm'][0]
    ax.plot([dx - W / 2 - 3, dx + W / 2 + 3], [dy + L - tl] * 2, ls='--', color='#7a4d9e', lw=1)
    ax.text(dx + W / 2 + 3.2, dy + L - tl, 'plug back face', va='center', fontsize=8, color='#7a4d9e')
    for i, s in enumerate(LABELS[name][0]):
        ax.text(dx + (i - 1.5) * 1.02, dy + L + .5, s, ha='center', va='bottom', fontsize=7, rotation=90)
    # 15 mm double-length pins lying along the whole pad, the rest in the plug's channels
    pad_end = 2 * GEO[name]['pads']['J1.1'][1] - .25
    for i in range(4):
        ax.add_patch(Rectangle((dx + (i - 1.5) * 1.02 - .32, dy + L - pad_end + .1), .64, 15, color='#9aa5a8', alpha=.55))
    ax.text(dx, dy + L + 15 - pad_end + .6, 'into plug\n(pins run on to the contacts)', ha='center', fontsize=7)
    if LABELS[name][1]:
        for i, s in enumerate(LABELS[name][1]):
            px = dx + (i - (len(LABELS[name][1]) - 1) / 2) * 2.54
            ax.add_patch(Rectangle((px - .32, dy - 6), .64, 11, color='#9aa5a8', alpha=.55))
            ax.text(px, dy - 6.6, s, ha='center', va='top', fontsize=9, weight='bold')
        ax.text(dx, dy - 8.4, 'servo plug on G V S1;\na J-port device uses all four', ha='center', va='top', fontsize=7)
    else:
        ax.text(dx, dy - 1, 'Qwiic cable', ha='center', va='top', fontsize=8)


fig, axs = plt.subplots(1, 2, figsize=(11, 7.5))
for ax, name, title in [(axs[0], 'header-tail', 'HEADER TAIL  {:.1f} × {:.1f} mm'), (axs[1], 'qwiic-tail', 'QWIIC TAIL  {:.1f} × {:.1f} mm\nR1 = 0 Ω 1206 crossover')]:
    draw(ax, name); ax.set_title(title.format(*GEO[name]['board_mm'][:2]), fontsize=11); ax.set_aspect('equal'); ax.grid(alpha=.15); ax.set_xlim(-9, 14); ax.set_ylim(-11, 32)
fig.suptitle('Nezha 4P4C plug tails, rev C — copper side up, plug end at the top (1 mm grid)', fontsize=13)
fig.text(.5, .02, 'Pad order is as seen from the plug contacts with the nose away. Header pins follow the plug contacts 1-4 (GND, VCC, S1, S2 by cable colour): check a port before use.', ha='center', fontsize=8.5)
fig.tight_layout(rect=[0, .05, 1, .95])
for ext in ['pdf', 'svg', 'png']: fig.savefig(ROOT / f'exports/assembly-preview.{ext}', dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5.5)); A = JOB['area_mm']
ax.add_patch(Rectangle((0, 0), *A, fill=False, edgecolor='#192a2e', lw=1.5, ls='--'))
for b in JOB['placements']:
    W = GEO[b['name']]['board_mm'][0]; draw(ax, b['name'], b['x'] + W / 2, b['y'], labels=False)
    ax.text(b['x'] + W / 2, b['y'] - 1.6, str(b['id']), ha='center', fontsize=8)
ax.plot(0, 0, 'ko'); ax.annotate('G54 (0,0)', (0, 0), (1, -3), fontsize=9)
ax.set_aspect('equal'); ax.set_xlim(-2, A[0] + 2); ax.set_ylim(-5, A[1] + 2); ax.grid(alpha=.15)
ax.set_title(f'Strip: 2 header + 2 Qwiic tails in {A[0]:.0f} × {A[1]:.0f} mm of free stock, copper up', fontsize=11)
fig.tight_layout()
for ext in ['pdf', 'svg', 'png']: fig.savefig(CAM / f'strip-layout.{ext}', dpi=200)

report.update({'program': JOB['program'], 'program_sha256': hashlib.sha256(prog.read_bytes()).hexdigest(), 'motion_minutes': minutes,
               'checks': ['Schematic netlists match the independent net table', 'Front copper only, SMD only, no vias',
                          'Every net one piece in CAD; clearance at least 0.30 mm; copper 0.2 mm inside the outline',
                          'Replayed V-bit and outline sweeps leave copper undamaged, every net whole and no two nets joined',
                          'Each board has exactly 3 tabs of 1.5 mm, none on the tongue; the tongue is cut free all round',
                          'Bounded feeds and depths, safe rapids, spindle on for every cut, tools T2 then T3'],
               'limits': 'Offline geometry only. The plug cavity, pin pitch and servo-port pinout are not yet measured; not test-cut.'})
(CAM / 'validation.json').write_text(json.dumps(report, indent=1) + '\n'); print(json.dumps(report, indent=1))
