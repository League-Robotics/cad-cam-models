#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["manifold3d", "numpy", "trimesh"]
# ///
"""A clean, low-poly CAD model of the ELECFREAKS Nezha Breakout Board V2 with a micro:bit in it.

    uv run tools/nezha_breakout.py [out.glb] [out.stl]

Defaults to scad/models/nezha_breakout_v2.glb (coloured parts, metres, for viewers) and
scad/models/nezha_breakout_v2.stl (one solid, mm, for the sources to import).

Redrawn from boxes and cylinders (manifold3d booleans) rather than repaired from the
3D-scanner mesh, which was too broken to finish (the scan and the photos are in
nolan/minecraft run/captures/nezha_scan, not kept here). It is meant for laying out robots, so the
outer envelope and the LEGO holes are what must be right; buttons, LEDs and the micro:bit's
details are cosmetic.

Envelope: 80 x 60 x 43.7 mm (front to back, side to side, height; caliper-measured), with the
micro:bit shelf at 31.5 and the button's surface at 40 (scad/models/nezha_breakout_v2_dims.svg).
Holes and sockets were measured on the scan by
imaging each face; the scan sits about 1 degree rotated, which shows up as equal and opposite
+-0.5 mm offsets on opposite faces, so features here are placed square and symmetric.
Standard parts are at their published sizes: LEGO Technic holes (4.8 mm, 6.2 mm counterbore,
8 mm pitch), micro:bit V2 (51.6 x 42 x 1.6 mm).

Coordinates are mm, centred on the footprint, Y up (glTF's convention), and the GLB is written
in metres so viewers show it at real size:
  x  along the long side; +X is the motor end (M1-M4), -X the micro:bit end
  z  across; +Z is the IIC side, -Z the J1-J4 side
Each part is its own coloured mesh with flat shading; nothing is textured.
"""
import sys
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh

# ---- envelope and features (mm) --------------------------------------------------------
# The envelope is caliper-measured (2026-11-01): 80 front to back, 60 side to side, the
# micro:bit shelf 31.5 up, the button's surface 40 up, the ridge over the micro:bit 43.7 up.
# Everything else was measured on the scan relative to the body's centre, and snapped where it
# clearly sits on the LEGO grid (hole pitch measured 8.0).
X0, X1 = -40.0, 40.0          # front to back (micro:bit end to motor end)
Z0, Z1 = -30.0, 30.0          # side to side (J side to IIC side)
ZC = 0.0
Y_BOT = -20.1                 # heights below are measured up from here
Y_BASE = -7.4                 # top of the grey base
Y_BODY = Y_BOT + 31.5         # the shelf the micro:bit lies over
Y_HOLE = Y_BOT + 4.0          # side/end Technic holes: measured 4.0-4.1 above the bottom
X_HUMP = -3.35                # front face of the raised block the micro:bit slides under
HUMP_TOP = Y_BOT + 40.0       # the raised block's top, where the button is
RIDGE_TOP = Y_BOT + 43.7      # the ridge over the micro:bit: the highest point
RIDGE_END, SLOPE_END = 6.8, 13.3
CORNER_R = 2.0
SOCKET_PITCH = 12.8           # measured 12.7-12.95 on all three sides
SOCKETS = [(-1.5 + i) * SOCKET_PITCH for i in range(4)]     # centred rows of four
SOCKET_W, SOCKET_Y0, SOCKET_Y1, SOCKET_CHAMFER_Y = 7.9, -7.4, 7.1, 5.6
SIDE_HOLE_X = 28.0            # two arched holes per long side (+-27.6 measured)
# Each side hole: an arch open to the bottom edge, 1.86 deep (the user's measurement,
# 2026-11-01), then a normal Technic hole; all four alike (2026-11-02). The arch is exactly a
# LEGO beam's rounded end (the user: a beam fits it perfectly), so its width is Technic.scad's
# beam width, 7.36.
ARCH_R, ARCH_D = 7.36 / 2, 1.86
SIDE_SLOTS_X = (-15.0, 0.0, 15.0)
BOTTOM_ROWS_X = (-32.0, -24.0, -16.0, 32.0)                 # from the photo of the bottom
# The on/off button (caliper-measured): 7.8 across, centre 18.7 from the motor end; it slides
# toward the J side, its far edge 16.8 from the J-side top edge when off and 13.7 when on.
BUTTON_D = 7.8
BUTTON_X = X1 - 18.7
BUTTON_Z_OFF = Z0 + 16.8 - BUTTON_D / 2
BUTTON_Z_ON = Z0 + 13.7 - BUTTON_D / 2
BUTTON_ON = False             # which position to model

# ---- standard parts -------------------------------------------------------------------
LEGO_PITCH, LEGO_R, LEGO_CB_R, LEGO_CB_D = 8.0, 2.4, 3.1, 0.8
MB_W, MB_D, MB_T = 51.6, 42.0, 1.6
MB_Y1 = 18.5                  # top of the micro:bit board (scan)
MB_Y0 = MB_Y1 - MB_T

SEG = 24                      # segments on a full circle: low-poly but round enough

COLORS = {
    "white": (236, 235, 230), "grey": (78, 81, 85), "jack": (185, 188, 192), "jack_dark": (60, 62, 66),
    "gold": (201, 161, 59), "iic": (47, 111, 214), "j": (224, 122, 31), "m": (214, 58, 47),
    "button": (226, 48, 42), "pcb": (24, 24, 26), "led": (222, 214, 196), "switch": (45, 45, 48),
    "usb": (184, 188, 194), "dot": (40, 40, 42),
}


# ---- helpers (Y-up model coordinates) --------------------------------------------------------
# manifold builds in a Z-up frame; everything here is written Y up by mapping
# (x, y, z) -> (x, -z, y) for manifold and back on export.

def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, z1 - z0, y1 - y0]).translate([x0, -z1, y0])


def rbox(x0, x1, y0, y1, z0, z1, r=CORNER_R):
    """A box with its four vertical edges rounded."""
    pts = [(x0 + r, -z1 + r), (x1 - r, -z1 + r), (x0 + r, -z0 - r), (x1 - r, -z0 - r)]
    cs = m3.CrossSection.batch_hull([m3.CrossSection.circle(r, SEG // 2).translate(p) for p in pts])
    return cs.extrude(y1 - y0).translate([0, 0, y0])


def cyl_y(x, z, r, y0, y1, seg=SEG):
    return m3.Manifold.cylinder(y1 - y0, r, circular_segments=seg).translate([x, -z, y0])


def cyl_x(y, z, r, x0, x1, seg=SEG):
    return m3.Manifold.cylinder(x1 - x0, r, circular_segments=seg).rotate([0, 90, 0]).translate([x0, -z, y])


def cyl_z(x, y, r, z0, z1, seg=SEG):
    return m3.Manifold.cylinder(z1 - z0, r, circular_segments=seg).rotate([90, 0, 0]).translate([x, -z0, y])


def prism_xy(points, z0, z1):
    """A 2D outline in the scan's XY plane, extruded across z. Either winding works."""
    cs = m3.CrossSection([points])
    if cs.area() == 0:
        cs = m3.CrossSection([points[::-1]])      # clockwise outlines read as holes
    return cs.extrude(z1 - z0).rotate([90, 0, 0]).translate([0, -z0, 0])


def union(parts):
    return m3.Manifold.batch_boolean(list(parts), m3.OpType.Add)


def face_box(face, u0, u1, y0, y1, d0, d1):
    """A box on one side of the case: u along the face, d depth in from the face."""
    if face == "+z":
        return box(u0, u1, y0, y1, Z1 - d1, Z1 - d0)
    if face == "-z":
        return box(u0, u1, y0, y1, Z0 + d0, Z0 + d1)
    if face == "+x":
        return box(X1 - d1, X1 - d0, y0, y1, u0, u1)
    if face == "-x":
        return box(X0 + d0, X0 + d1, y0, y1, u0, u1)
    raise ValueError(face)


def face_hole(face, u, y, r, d0, d1, seg=SEG):
    if face == "+z":
        return cyl_z(u, y, r, Z1 - d1, Z1 - d0, seg)
    if face == "-z":
        return cyl_z(u, y, r, Z0 + d0, Z0 + d1, seg)
    if face == "+x":
        return cyl_x(y, u, r, X1 - d1, X1 - d0, seg)
    if face == "-x":
        return cyl_x(y, u, r, X0 + d0, X0 + d1, seg)
    raise ValueError(face)


def lego_hole(face, u, y, depth=7.0, d0=0.0):
    """A Technic hole: 4.8 mm bore with the shallow 6.2 mm counterbore at the mouth, d0 in from the face."""
    return union([face_hole(face, u, y, LEGO_R, -1, d0 + depth), face_hole(face, u, y, LEGO_CB_R, -1, d0 + LEGO_CB_D)])


# ---- the case ---------------------------------------------------------------------------

def base():
    b = rbox(X0, X1, Y_BOT, Y_BASE, Z0, Z1)
    cuts = []
    # Bottom: rows of five, three at the micro:bit end and one at the motor end.
    for x in BOTTOM_ROWS_X:
        for k in range(-2, 3):
            z = ZC + k * LEGO_PITCH
            cuts += [cyl_y(x, z, LEGO_R, Y_BOT - 1, Y_BOT + 7), cyl_y(x, z, LEGO_CB_R, Y_BOT - 1, Y_BOT + LEGO_CB_D)]
    # Both ends: a row of five.
    for face in ("+x", "-x"):
        cuts += [lego_hole(face, ZC + k * LEGO_PITCH, Y_HOLE) for k in range(-2, 3)]
    # Long sides: at each end a normal hole behind an arch open to the bottom edge.
    for face in ("+z", "-z"):
        for arch_x in (SIDE_HOLE_X, -SIDE_HOLE_X):
            cuts += [face_hole(face, arch_x, Y_HOLE, ARCH_R, -1, ARCH_D),
                     face_box(face, arch_x - ARCH_R, arch_x + ARCH_R, Y_BOT - 1, Y_HOLE, -1, ARCH_D),
                     lego_hole(face, arch_x, Y_HOLE, d0=ARCH_D)]
        for x in SIDE_SLOTS_X:
            cuts.append(face_box(face, x - 1.15, x + 1.15, Y_BOT - 1, Y_BASE + 0.01, -1, 1.5))
    return b - union(cuts)


def socket_sites():
    for face in ("+z", "-z", "+x"):
        for u in SOCKETS:
            yield face, u


def socket_window(face, u, d0, d1):
    """The opening a socket sits in: straight sides, top corners chamfered."""
    hw = SOCKET_W / 2
    return m3.Manifold.batch_hull([face_box(face, u - hw, u + hw, SOCKET_Y0, SOCKET_CHAMFER_Y, d0, d1),
                                   face_box(face, u - hw + 1.5, u + hw - 1.5, SOCKET_Y1 - 0.01, SOCKET_Y1, d0, d1)])


def body():
    hump = prism_xy([(X_HUMP, Y_BODY - 0.01), (X_HUMP, RIDGE_TOP), (RIDGE_END, RIDGE_TOP), (SLOPE_END, HUMP_TOP),
                     (X1 + 1, HUMP_TOP), (X1 + 1, Y_BODY - 0.01)], Z0 - 1, Z1 + 1)
    hump = hump ^ rbox(X0, X1, Y_BASE, RIDGE_TOP + 1, Z0, Z1)          # round its corners like the body
    b = rbox(X0, X1, Y_BASE, Y_BODY, Z0, Z1) + hump
    cuts = [socket_window(f, u, -1, 9.0) for f, u in socket_sites()]
    # The micro:bit's slot under the ridge, the bay beneath the board, and the notch at the
    # end that leaves its USB socket reachable.
    cuts.append(box(X_HUMP - 1, X_HUMP + 6.2, MB_Y0 - 0.3, MB_Y1 + 0.5, ZC - MB_W / 2 - 0.3, ZC + MB_W / 2 + 0.3))
    cuts.append(box(X0 + 2.6, X_HUMP + 0.01, -3.5, Y_BODY + 1, ZC - 20, ZC + 20))
    cuts.append(box(X0 - 1, X0 + 2.7, 5.0, Y_BODY + 1, ZC - 16, ZC + 16))
    # Four status LEDs.
    cuts += [cyl_y(15.8, z, 0.55, HUMP_TOP - 0.4, HUMP_TOP + 1, 8) for z in (13.0, 15.5, 18.0, 20.5)]
    cuts.append(button_track())
    b = b - union(cuts)
    # Rails the micro:bit rests on.
    rails = [box(X0 + 1.0, X_HUMP + 0.5, Y_BODY - 0.01, MB_Y0, ZC + s * 21.0, ZC + s * 25.4) if s > 0 else
             box(X0 + 1.0, X_HUMP + 0.5, Y_BODY - 0.01, MB_Y0, ZC - 25.4, ZC - 21.0) for s in (1, -1)]
    # Braille-like raised dots on the top.
    dots = [cyl_y(27.3 + i * 1.6, 9.0 + j * 1.5, 0.42, HUMP_TOP - 0.1, HUMP_TOP + 0.3, 8)
            for i in range(2) for j in range(10) if (i * 7 + j * 3) % 4 != 1]
    return b + union(rails + dots)


def sockets():
    """4P4C jacks filling the windows: plug opening on top, label strip with a coloured mark below."""
    housing, dark, gold = [], [], []
    marks = {"iic": [], "j": [], "m": []}
    yc = -0.2                                  # middle of the plug opening
    for face, u in socket_sites():
        h = socket_window(face, u, 1.2, 9.0)   # jack face sits 1.2 mm back in its window, as scanned
        jack = face_box(face, u - 3.5, u + 3.5, yc - 3.3, yc + 3.3, 1.1, 7.5)
        latch = face_box(face, u - 1.6, u + 1.6, yc - 4.4, yc - 3.2, 1.1, 4.0)
        housing.append(h - jack - latch)
        dark.append(face_box(face, u - 3.5, u + 3.5, yc - 3.3, yc + 3.3, 7.4, 7.5))
        gold += [face_box(face, u - 1.9 + i * 1.27 - 0.25, u - 1.9 + i * 1.27 + 0.25, yc + 0.8, yc + 3.3, 2.0, 7.4)
                 for i in range(4)]
        kind = {"+z": "iic", "-z": "j", "+x": "m"}[face]
        marks[kind].append(face_box(face, u - 2.0, u + 2.0, SOCKET_Y0 + 0.5, SOCKET_Y0 + 1.3, 1.05, 1.25))
    return {"jack": union(housing), "jack_dark": union(dark), "gold": union(gold),
            **{k: union(v) for k, v in marks.items()}}


def button():
    x, z = BUTTON_X, (BUTTON_Z_ON if BUTTON_ON else BUTTON_Z_OFF)
    r = BUTTON_D / 2
    return {"white": cyl_y(x, z, r, HUMP_TOP - 0.6, HUMP_TOP + 1.5),
            "button": cyl_y(x, z, 1.7, HUMP_TOP + 1.4, HUMP_TOP + 1.9, 16)}


def button_track():
    """The shallow slot the button slides in, cut into the top."""
    r = BUTTON_D / 2 + 0.3
    a, b = cyl_y(BUTTON_X, BUTTON_Z_ON, r, HUMP_TOP - 0.6, HUMP_TOP + 1), cyl_y(BUTTON_X, BUTTON_Z_OFF, r, HUMP_TOP - 0.6, HUMP_TOP + 1)
    return m3.Manifold.batch_hull([a, b])


# ---- the micro:bit ----------------------------------------------------------------------

def microbit():
    x0 = X0 + 0.3
    board = box(x0, x0 + MB_D, MB_Y0, MB_Y1, ZC - MB_W / 2, ZC + MB_W / 2)
    cx = (x0 + X_HUMP) / 2               # middle of the part you can see
    leds = [box(cx + (i - 2) * 4.1 - 0.5, cx + (i - 2) * 4.1 + 0.5, MB_Y1 - 0.01, MB_Y1 + 0.45,
                ZC + (j - 2) * 4.1 - 0.9, ZC + (j - 2) * 4.1 + 0.9) for i in range(5) for j in range(5)]
    switch, caps = [], []
    for s in (-1, 1):
        z = ZC + s * 18.6
        switch.append(box(cx - 3, cx + 3, MB_Y1 - 0.01, MB_Y1 + 1.0, z - 3, z + 3))
        caps.append(cyl_y(cx, z, 1.75, MB_Y1 + 0.9, MB_Y1 + 1.6, 16))
    pads = [cyl_y(X_HUMP - 2.2, ZC + k * 9.8, 1.6, MB_Y1 - 0.01, MB_Y1 + 0.06, 16) for k in range(-2, 3)]
    usb = box(x0, x0 + 5.6, MB_Y0 - 2.6, MB_Y0 + 0.01, ZC - 3.8, ZC + 3.8)
    batt = box(x0 + 0.5, x0 + 5.5, MB_Y0 - 4.0, MB_Y0 + 0.01, ZC + 7, ZC + 13)
    return {"pcb": board, "led": union(leds), "switch": union(switch), "dot": union(caps),
            "gold": union(pads), "usb": usb, "white": batt}


# ---- assembly and export ----------------------------------------------------------------

def assemble():
    parts = {"grey": [base()], "white": [body()]}
    for group in (sockets(), button(), microbit()):
        for k, v in group.items():
            parts.setdefault(k, []).append(v)
    return {k: union(v) for k, v in parts.items()}


def to_trimesh(man):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    v = np.column_stack([v[:, 0], v[:, 2], -v[:, 1]])     # back to scan coords, Y up
    t = trimesh.Trimesh(v, np.asarray(mesh.tri_verts), process=True)
    return t


def main():
    models = Path(__file__).resolve().parent.parent / "scad" / "models"
    out_glb = sys.argv[1] if len(sys.argv) > 1 else str(models / "nezha_breakout_v2.glb")
    out_stl = sys.argv[2] if len(sys.argv) > 2 else str(models / "nezha_breakout_v2.stl")
    parts = assemble()
    scene = trimesh.Scene()
    total = 0
    for name, man in parts.items():
        t = to_trimesh(man)
        t.unmerge_vertices()                                # flat shading
        t.apply_scale(0.001)                                # glTF is in metres
        rgb = COLORS[name]                                 # sRGB; glTF wants linear, hence ** 2.2
        t.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=name, baseColorFactor=[*((c / 255) ** 2.2 for c in rgb), 1.0], metallicFactor=0.6 if name in ("gold", "usb") else 0.0,
            roughnessFactor=0.35 if name in ("gold", "usb") else 0.6))
        scene.add_geometry(t, node_name=name, geom_name=name)
        total += len(t.faces)
    scene.export(out_glb)
    print(f"wrote {out_glb}: {len(parts)} coloured parts, {total} triangles")
    solid = to_trimesh(union(parts.values()))
    solid.export(out_stl)
    b = solid.bounds
    print(f"wrote {out_stl}: one solid, {len(solid.faces)} triangles, watertight {solid.is_watertight}, "
          f"envelope {b[1][0] - b[0][0]:.2f} x {b[1][2] - b[0][2]:.2f} x {b[1][1] - b[0][1]:.2f} mm")


if __name__ == "__main__":
    main()
