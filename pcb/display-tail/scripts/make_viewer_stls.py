#!/usr/bin/env python3
"""Export the display tail as viewer pieces: one binary STL per material, in the CASE frame.

Case frame (the watch-display case session's frame for the tail): the display's pad edge is y = 0 with +y
AWAY from the display, x = 0 is the display PCB's centre line with +x toward the buttons side, z = 0 is the
tail's copper face with +z toward the lid (the jack side). The board frame used by build.py / layers.json is
x from the tail's left edge, y DOWN from the jack edge, seen from the copper side; the two are related by a
half turn about z: X = XC - x, Y = DISPLAY_EDGE_Y - y, Z = z (determinant +1, so no handedness flip).

Pieces (exports/viewer/):
  tail_fr4      the 1.4 mm board, z -1.4..0
  tail_copper   the tracks (F.Cu minus the pads), 35 um
  tail_pads     the pads (J1 signal lands, J1 hold-down lands, the four display-side pads), 35 um
  tail_pins     the four flat 0.64 mm pins with their solder on the tail pads and on the display pads
  jack_body     the Amphenol 73306-111LF housing, from manufacturer drawing 73306 rev M (pcb/references)
  jack_metal    its four contacts/tails and the two hold-down tabs (schematic, 0.2 thick phosphor bronze)
Dimensions marked GUESS are not on the drawing; everything else is read from it or from the KiCad board.
Run with: uv run --with "trimesh[easy]" --with numpy --with shapely --with matplotlib scripts/make_viewer_stls.py
"""
import json, sys
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent.parent
NAME = 'display-tail-butt'
OUT = HERE / 'exports' / 'viewer'
OUT.mkdir(parents=True, exist_ok=True)
L = json.load(open(HERE / 'exports' / 'layers.json'))[NAME]
G = json.load(open(HERE / 'checks' / 'geometry.json'))[NAME]

W, LEN, T = G['board_mm']                      # 23.4 x 22.3 x 1.4
DISPLAY_EDGE_Y = G['display_edge_y']           # 23.5: the display's pad edge, in the board frame
DISPLAY_PCB_W, PAD18_FROM_EDGE, X18 = 29.85, 4.16, 1.5   # Waveshare drawing: pad 18 is 4.16 from the buttons-side edge
XC = DISPLAY_PCB_W / 2 - PAD18_FROM_EDGE + X18  # 12.265: board x that maps to case X = 0
CU = 0.035                                      # 1 oz copper
PIN = 0.64                                      # square header pin
PIN_LEN = 7.0                                   # from the tail pad's far end over the 1.2 gap onto the display pad
DISPLAY_PAD = (1.0, 1.9)                        # GUESS: the display's oval back pads (width across, length along y)

# --- Amphenol 73306-111LF, drawing 73306 rev M sheet 1 (mm) ---
JW, JD, JH = 11.18, 12.7, 14.0                  # housing width at the mouth, depth mouth face to rear (top), height above the PCB
J_REAR_W = 11.68                                # the rear view is drawn 11.68 wide (the drawing's left view)
J_BASE_D = 11.68                                # housing depth at the base: the rear is undercut 1.02 at the bottom
J_STANDOFF = 0.35                               # housing underside above the hold-down bearing plane (0.35 +-0.05, 2x)
J_UNDERCUT_H = 2.0                              # GUESS: height of the rear undercut
J_FLARE_D = 2.0                                 # GUESS: how far forward the 11.68-wide rear portion runs
TAIL_TIP = J_BASE_D + 4.31                      # 15.99 from the mouth face: the solder tails' tips
TAIL_FOOT = 1.8                                 # "1.8 REF": the flat foot of each tail
MOUTH_W, MOUTH_H = 7.9, 7.1                     # plug opening, measured off the drawing's mouth view (+-0.2)
MOUTH_FLOOR = 3.3                               # opening floor above the PCB plane, measured off the mouth view (+-0.2)
STEP_W, STEP_H = 5.75, 1.9                      # first narrowing above the opening (latch lever space), off the mouth view
LATCH_W, LATCH_H = 2.6, 0.9                     # latch keyway above that (view V's 2.6 +-0.3), under a 0.8 roof
CAVITY_D = 10.0                                 # GUESS: depth of the plug cavity from the mouth face
CONTACT_W, METAL_T = 0.4, 0.2                   # drawing: 0.4 (4x) contact width; 0.2 tail thickness
HOLD_W, HOLD_L = 2.35, 5.5                      # hold-down lands (= tab footprints)
HOLD_LEG_H = 4.5                                # GUESS: height of the hold-down tabs' legs up the housing sides

jack = G['jack']; JCX, JMY = jack['centre_x'], jack['mouth_y']      # 11.7, 1.0 (board frame; mouth faces -y = away)

# ---------- helpers ----------
TO_CASE = np.array([[-1, 0, 0, XC], [0, -1, 0, DISPLAY_EDGE_Y], [0, 0, 1, 0], [0, 0, 0, 1]], float)

def bx(x0, x1, y0, y1, z0, z1):
    """An axis-aligned box in the board frame."""
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m

def bar(p0, p1, w, t):
    """A bar of cross-section w (x) by t, from point p0 to p1 (both (x, y, z)), for sloping contacts."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; n = np.linalg.norm(d)
    m = trimesh.creation.box((w, n, t))
    # rotate the bar's +y onto d (d lies in the y-z plane here)
    ang = np.arctan2(d[2], d[1])
    m.apply_transform(trimesh.transformations.rotation_matrix(ang, (1, 0, 0)))
    m.apply_translation((p0 + p1) / 2)
    return m

def extrude(geom, z0, z1):
    polys = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
    ms = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in polys if not p.is_empty and p.area > 1e-6]
    m = trimesh.util.concatenate(ms); m.apply_translation((0, 0, z0)); return m

def hull(rect_lo, z_lo, rect_hi, z_hi):
    """Solder fillet: convex hull of a rectangle at z_lo and a smaller one at z_hi (rects as (x0, x1, y0, y1))."""
    pts = [(x, y, z_lo) for x in rect_lo[:2] for y in rect_lo[2:]] + [(x, y, z_hi) for x in rect_hi[:2] for y in rect_hi[2:]]
    return trimesh.convex.convex_hull(np.array(pts, float))

def poly(coords):
    return Polygon(coords[0], coords[1:]) if coords and isinstance(coords[0][0], (list, tuple)) and len(coords) and isinstance(coords[0][0][0], (int, float)) else Polygon(coords)

def layer(name):
    out = []
    for p in L['layers'][name]:
        # dump format: a polygon is [outer_ring, hole_ring, ...]
        rings = p if isinstance(p[0][0], (list, tuple)) else [p]
        out.append(Polygon(rings[0], rings[1:]))
    return unary_union(out)

# ---------- the tail ----------
outline = Polygon(G['outline'])                                        # the board edge (layers.json's Edge.Cuts is the 0.05 stroke, a thin ring)
fcu = layer('F.Cu')
pads = []
for part in L['parts']:
    for p in part['pads']:
        (x, y), (sx, sy) = p['at'], p['size']
        pads.append(box(x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2))
pads_u = unary_union(pads)
pieces = {}
pieces['tail_fr4'] = extrude(outline, -T, 0)
pieces['tail_copper'] = extrude(fcu.difference(pads_u), 0, CU)
pieces['tail_pads'] = extrude(fcu.intersection(pads_u), 0, CU)

pins = []
j2 = next(p for p in L['parts'] if p['ref'] == 'J2')
pad_far = min(p['at'][1] - p['size'][1] / 2 for p in j2['pads'])           # 19.1: the tail pads' far end (toward the jack)
for p in j2['pads']:
    x, y = p['at']; sx, sy = p['size']
    y0, y1 = pad_far, pad_far + PIN_LEN                                     # 19.1 .. 26.1: 3.8 past the tail edge, 2.6 onto the display
    pins.append(bx(x - PIN / 2, x + PIN / 2, y0, y1, CU, CU + PIN))
    # solder on the tail pad: from the pad's outline up to a cap on the pin
    pins.append(hull((x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2), CU, (x - PIN / 2 - 0.15, x + PIN / 2 + 0.15, y - sy / 2 + 0.4, y + sy / 2 - 0.2), CU + PIN + 0.1))
    # solder on the display pad (the display's back copper face is level with the tail's: z = 0)
    dy = G['display_pads'][p['num']][1]; dw, dl = DISPLAY_PAD
    pins.append(hull((x - dw / 2, x + dw / 2, dy - dl / 2, dy + dl / 2), 0, (x - PIN / 2 - 0.1, x + PIN / 2 + 0.1, dy - dl / 2 + 0.3, min(dy + dl / 2 - 0.2, y1 - 0.1)), CU + PIN + 0.1))
pieces['tail_pins'] = trimesh.util.concatenate(pins)

# ---------- the jack: housing ----------
hw, hwr = JW / 2, J_REAR_W / 2
y_m, y_r, y_rb = JMY, JMY + JD, JMY + J_BASE_D                    # mouth face 1.0, rear (top) 13.7, rear at the base 12.68
z0, zf = J_STANDOFF, MOUTH_FLOOR                                  # housing underside; opening floor
zt = zf + MOUTH_H                                                 # opening top; latch keyway above it to zt + LATCH_H
y_c = y_m + CAVITY_D                                              # back of the plug cavity
zu = z0 + J_UNDERCUT_H
body = [
    bx(JCX - hw, JCX + hw, y_m, y_rb, z0, zf),                     # floor under the cavity, to the base rear
    bx(JCX - hw, JCX + hw, y_m, y_r, zu, zf) if zu < zf else None, # (floor part above the undercut, when the floor is taller than it)
    bx(JCX - hw, JCX - MOUTH_W / 2, y_m, y_r, zf, JH),             # left wall
    bx(JCX + MOUTH_W / 2, JCX + hw, y_m, y_r, zf, JH),             # right wall
    bx(JCX - MOUTH_W / 2, JCX - STEP_W / 2, y_m, y_r, zt, zt + STEP_H),      # shoulders beside the lever space
    bx(JCX + STEP_W / 2, JCX + MOUTH_W / 2, y_m, y_r, zt, zt + STEP_H),
    bx(JCX - STEP_W / 2, JCX - LATCH_W / 2, y_m, y_r, zt + STEP_H, zt + STEP_H + LATCH_H),   # beside the keyway
    bx(JCX + LATCH_W / 2, JCX + STEP_W / 2, y_m, y_r, zt + STEP_H, zt + STEP_H + LATCH_H),
    bx(JCX - hw, JCX + hw, y_m, y_r, zt + STEP_H + LATCH_H, JH),   # roof (0.8 thick)
    bx(JCX - hw, JCX + hw, y_c, y_rb, z0, zu),                     # rear block, lower part (undercut: ends at the base rear)
    bx(JCX - hw, JCX + hw, y_c, y_r, zu, JH),                      # rear block, upper part
    bx(JCX - hwr, JCX + hwr, y_r - J_FLARE_D, y_r, zu, JH),        # the 11.68-wide rear portion (GUESS how far forward)
]
pieces['jack_body'] = trimesh.util.concatenate([b for b in body if b is not None])

# ---------- the jack: metal (schematic) ----------
metal = []
j1 = next(p for p in L['parts'] if p['ref'] == 'J1')
for p in j1['pads']:
    x, y = p['at']
    if p['num']:                                                   # a contact: tail foot, riser, run along the cavity floor, spring
        tip = JMY + TAIL_TIP                                       # 16.99
        metal.append(bx(x - CONTACT_W / 2, x + CONTACT_W / 2, tip - TAIL_FOOT, tip, 0, METAL_T))              # foot on the land
        metal.append(bar((x, y_rb, zu - 0.6), (x, tip - TAIL_FOOT, METAL_T / 2), CONTACT_W, METAL_T))         # out of the base rear, down to the foot
        metal.append(bx(x - CONTACT_W / 2, x + CONTACT_W / 2, y_rb - 0.6, y_rb, zu - 0.6, zf + 0.3))        # up inside the rear block (hidden)
        metal.append(bx(x - CONTACT_W / 2, x + CONTACT_W / 2, y_m + 1.5, y_rb, zf, zf + METAL_T + 0.1))     # along the cavity floor
        metal.append(bar((x, y_m + 1.5, zf + 0.2), (x, y_m + 6.0, zf + 3.2), CONTACT_W, METAL_T))            # the spring, rising rearward (GUESS)
    else:                                                          # a hold-down tab: plate on the land and a leg up the housing side
        metal.append(bx(x - HOLD_W / 2, x + HOLD_W / 2, y - HOLD_L / 2, y + HOLD_L / 2, 0, METAL_T))
        s = -1 if x < JCX else 1
        xi = JCX + s * hw
        metal.append(bx(min(xi, xi - s * METAL_T), max(xi, xi - s * METAL_T), y - HOLD_L / 2, y + HOLD_L / 2, METAL_T, HOLD_LEG_H))
pieces['jack_metal'] = trimesh.util.concatenate(metal)

# ---------- to the case frame, write, report ----------
report = {'frame': 'case: pad edge y=0 (+y away from the display), x=0 display PCB centre (+x buttons side), z=0 tail copper face (+z toward the lid)',
          'board_to_case': {'X': f'{XC:.3f} - x', 'Y': f'{DISPLAY_EDGE_Y} - y', 'Z': 'z'}, 'units': 'mm', 'pieces': {}}
for name, m in pieces.items():
    m.apply_transform(TO_CASE)
    m.export(OUT / f'{name}.stl')                                   # binary STL
    lo, hi = m.bounds
    report['pieces'][name] = {'bounds_min': [round(v, 3) for v in lo], 'bounds_max': [round(v, 3) for v in hi],
                              'volume_mm3': round(float(m.volume), 3), 'faces': int(len(m.faces))}
report['jack'] = {'part': 'Amphenol 73306-111LF', 'drawing': 'pcb/references/Amphenol-73306-revM.pdf',
                  'housing_mm': {'width_at_mouth': JW, 'width_at_rear': J_REAR_W, 'depth_top': JD, 'depth_base': J_BASE_D, 'height': JH, 'standoff': J_STANDOFF},
                  'mouth_face_case_y': round(DISPLAY_EDGE_Y - JMY, 3), 'centre_case_x': round(XC - JCX, 3),
                  'opening_mm': {'width': MOUTH_W, 'height': MOUTH_H, 'floor_z': MOUTH_FLOOR, 'lever_step_w': STEP_W, 'lever_step_h': STEP_H, 'latch_keyway_w': LATCH_W, 'latch_keyway_h': LATCH_H, 'keyway_top_z': MOUTH_FLOOR + MOUTH_H + STEP_H + LATCH_H},
                  'tails_tip_from_mouth': TAIL_TIP, 'guesses': ['J_UNDERCUT_H', 'J_FLARE_D', 'CAVITY_D', 'HOLD_LEG_H', 'spring shape', 'DISPLAY_PAD']}
json.dump(report, open(OUT / 'manifest.json', 'w'), indent=1)
print(json.dumps(report, indent=1))

# ---------- review picture ----------
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
COL = {'tail_fr4': '#2e7d32', 'tail_copper': '#c8743a', 'tail_pads': '#e0a040', 'tail_pins': '#9e9e9e', 'jack_body': '#303030', 'jack_metal': '#c0c0c8'}
fig = plt.figure(figsize=(16, 8))
for k, (el, az, title) in enumerate([(28, -50, 'from the lid side, mouth toward the viewer'), (0, -90, 'from the jack mouth (the case end wall)'), (0, 0, 'from the buttons side')]):
    ax = fig.add_subplot(1, 3, k + 1, projection='3d')
    for n, m in pieces.items():
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolor=COL[n], edgecolor='none', alpha=0.55 if n == 'jack_body' else 1.0))
    ax.set_xlim(-14, 14); ax.set_ylim(-4, 24); ax.set_zlim(-2, 16); ax.set_box_aspect((28, 28, 18))
    ax.view_init(elev=el, azim=az); ax.set_title(title, fontsize=9)
    ax.set_xlabel('x (+buttons side)'); ax.set_ylabel('y (+away from the display)'); ax.set_zlabel('z (+lid)')
fig.suptitle('Display tail viewer pieces in the case frame: pad edge y=0, x=0 display centre, z=0 copper face.  '
             'green FR4, orange tracks, gold pads, grey pins+solder, black jack housing (Amphenol 73306-111LF), silver contacts/tabs', fontsize=9)
plt.tight_layout(); fig.savefig(OUT / 'display-tail-viewer-pieces.png', dpi=110)
import shutil; shutil.copy(OUT / 'display-tail-viewer-pieces.png', HERE.parent.parent / 'view' / 'display-tail-viewer-pieces.png')
