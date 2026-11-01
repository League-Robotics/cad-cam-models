#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scikit-image"]
# ///
"""The front plate's connecting body, as one smooth blended mesh.

scad/front_plate.scad keeps every mating surface exact (the horns, the gripper
frame). Everything that joins them is built here as distance fields:

1. a lid: one hull-like shape over the whole connecting region, its top flat
   with the frame's top over the frame's back wall, then an S-curve down to
   the horns, every edge rounded (LID_R), and blended into the frame (FRAME)
   with fillets;
2. posts hung from the lid's underside, melted into it with fillets (BLEND):
   the columns and feet on the sensor's brackets and PCB, and the caster
   blocks; the faces that mate (bottoms, the casters' seats) stay flat;
3. the controlled spaces taken back out with rolled edges (ROLL): a U round
   the cable jack, 1 mm off it, the arms' slot, and the casters' domes and
   beams.

Seen from above the lid narrows from the casters' width to the floor's in an
S-curve, which keeps it out of the gripper arms' swing.

The scad file then cuts the exact clearances and holes, as before.

    uv run tools/front_plate_body.py      # writes scad/models/front_plate_body.stl

The numbers mirror front_plate.scad (sensor coordinates, mm; z up from the
PCB back, +y toward the robot).
"""
import struct
from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes

OUT = Path(__file__).resolve().parent.parent / "scad" / "models" / "front_plate_body.stl"
STEP = 0.35             # grid spacing
LID_R = 4.0             # the lid's top edges rounded
LID_BOTTOM_R = 1.5      # its bottom edges, small so the posts' fillets run clean into them
BLEND = 5.0             # fillets where the posts and the frame meet the lid
POST_BLEND = 8.0        # the side column and caster seat melt into one post
ROLL = 2.5              # roll-over on the cut-outs' edges
FLOOR_Z = 0.3           # the frame floor's underside, 0.3 over the PCB: the lowest plane, the print bed

# The lid, seen from above, is two rounded boxes joined: wide over the sensor
# and casters, narrowing to the floor's width toward the gripper; a round
# fillet (SIDE_FILLET) in the corner between them gives its sides an S-curve,
# with the narrow part's sides flat, flush with the frame's (PLAN bounds
# everything, so no blend bulges past them). Its bottom is z0. Its top
# is flat at the frame's top (the servo's tab seat) as far back as the
# frame's back wall, then eases down in an S-curve to the horns' top.
LID = dict(wide=(37.5, -6.0, 21.5, 6.0), narrow=(25.9, -16.0, 21.5, 4.0),
           z0=9.6, top=((-9.7, 24.4), (21.5, 17.8)))
SIDE_FILLET = 6.0

# The frame (exact in the scad file; here only so the lid blends into it):
# its back wall and its head over the arms, outer boxes x0, x1, y0, y1, z0, z1.
# The frame reaches 25.9 out on one side and 17.9 on the other; both are drawn
# to 25.9 so the head comes out symmetric (the extra is above the arms' slot).
FRAME = [(-25.9, 25.9, -15.8, -9.75, 0.3, 24.4), (-25.9, 25.9, -35.6, -9.75, 16.3, 24.4)]
FRAME_R = 2.0           # as the frame's rounded outside (frame_r in the scad file)

# Posts: (x0, x1, y0, y1, z0, z1, corner radius, flat), mirrored pairs listed
# once (x > 0). `flat` names a face kept flat and exact because something
# mates with it: "z0" the bottom (on a bracket or the PCB), "x1" the outer
# side (a caster's seat); the box is drawn past that face and cut there.
POSTS = [
    (12.2, 36.4, -3.8, 3.8, 2.2, 12.0, 2.5, "z0"),        # side column, on the side bracket (round the outer pin; inside the lid's side)
    (13.0, 21.0, 4.45, 27.95, -3.0, 12.0, 2.5, "x1"),     # caster seat, its outer face the caster's beam face (pins go in across); down to the bed
    (4.2, 11.8, 12.2, 19.8, 5.15, 12.0, 2.0, "z0"),       # middle bracket's column
    (4.2, 11.8, -11.8, -4.2, 0.3, 12.0, 2.0, "z0"),       # foot, level with the frame floor (0.3 over the PCB) so both print on the bed
]
# The cable jack (x -5..5.4, y 5.2..17.6) with its plug out the back: a
# rounded U, 1 mm off it, open toward the robot.
JACK = (-5.0 - 1.6, 5.4 + 1.6, 5.2 - 1.0, 80.0, 4.0)   # x0, x1, y0, y1, corner radius (sides clear of the jack's exact keep-out)
# The arms' slot ahead of the frame's upper wall (y < -15.8): from the floor's
# top (less clearance) to the top of the frame's slope over the spline arm.
ARM_SLOT = (-60.0, 60.0, -80.0, -15.8, 7.9, 18.5)

# The casters, turned so their pins point in across x: (side, seat face x,
# centre y, top z). Beam 23.5 long (along y) x 7.8 thick (out from the seat)
# x 7.5 high, with a slab as thick under it the caster's whole height; the
# dome 12.27 round a centre 3.9 out from the seat and 19.775
# below the top. Each slides on from outside by IN (the pins' 7.8, and some),
# so its space runs out through the side of the lid; with clearance CLEAR.
CASTERS = [(-1, 21.0, 16.2, 7.1), (1, 21.0, 16.2, 7.1)]   # top 5 below the robot's floor line (caster_drop)
CLEAR = 0.5
IN = 9.0
BOUNDS = ((-42, 42), (-20, 31), (-1, 32))


def box(p, x0, x1, y0, y1, z0, z1, r, flat=None):
    # drawn past a flat face by r, then cut there
    e = {"z0": (0, 0, 0, 0, -r, 0), "y1": (0, 0, 0, r, 0, 0),
         "x0": (-r, 0, 0, 0, 0, 0), "x1": (0, r, 0, 0, 0, 0)}.get(flat, (0,) * 6)
    x0, x1, y0, y1, z0b, z1 = x0 + e[0], x1 + e[1], y0 + e[2], y1 + e[3], z0 + e[4], z1 + e[5]
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0b + z1) / 2])
    h = np.array([(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0b) / 2]) - r
    q = np.abs(p - c) - h
    d = np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(axis=-1), 0) - r
    if flat == "z0":
        d = np.maximum(d, z0 - p[..., 2])
    elif flat == "y1":
        d = np.maximum(d, p[..., 1] - (y1 - r))
    elif flat == "x0":
        d = np.maximum(d, (x0 + r) - p[..., 0])
    elif flat == "x1":
        d = np.maximum(d, p[..., 0] - (x1 - r))
    return d


def prism(p, x0, x1, y0, y1, r):
    """A rounded rectangle in plan, through all z."""
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    h = np.array([(x1 - x0) / 2, (y1 - y0) / 2]) - r
    q = np.abs(p[..., :2] - c) - h
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(axis=-1), 0) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def round_union(a, b, r):
    # union with a round fillet of radius r in the corner; exact (no bulge) along faces
    u = np.hypot(np.maximum(r - a, 0), np.maximum(r - b, 0))
    return np.maximum(r, np.minimum(a, b)) - u


def plan(p, y1=None):
    """The lid's outline seen from above, through all z; y1 runs it on back."""
    (wx, wy0, wy1, wr), (nx, ny0, ny1, nr) = LID["wide"], LID["narrow"]
    if y1 is not None:
        wy1 = ny1 = y1
        ny0 = -60.0
    return round_union(prism(p, -wx, wx, wy0, wy1, wr), prism(p, -nx, nx, ny0, ny1, nr), SIDE_FILLET)


def lid_top(y):
    """The lid's top height and slope along y: flat, an S-curve, flat."""
    (ya, za), (yb, zb) = LID["top"]
    t = np.clip((y - ya) / (yb - ya), 0, 1)
    z = za + (zb - za) * t * t * (3 - 2 * t)
    dz = (zb - za) * 6 * t * (1 - t) / (yb - ya)
    return z, dz


def lid(p):
    z, dz = lid_top(p[..., 1])
    top = (p[..., 2] - z) / np.hypot(1, dz)
    d = plan(p)
    d = smax(d, LID["z0"] - p[..., 2], LID_BOTTOM_R)  # its bottom edges, lightly rolled
    return smax(d, top, LID_R)                        # its top edges


def caster_space(p, side, seat, y, top):
    q = p * np.array([side, 1, 1])           # work on the +x side
    # the beam and the slab under it down the caster's whole height (the flat face)
    beam = box(q, seat - 0.01, 60.0, y - 11.75 - CLEAR, y + 11.75 + CLEAR, top - 29.5, top + CLEAR, 0.5)
    a = np.array([seat + 3.9, y, top - 24.775 + 5.0])
    b = a + np.array([IN, 0, 0])
    t = np.clip((q[..., 0] - a[0]) / (b[0] - a[0]), 0, 1)[..., None]
    dome = np.linalg.norm(q - (a + t * (b - a)), axis=-1) - (12.27 + CLEAR)   # the dome along its way in
    return np.minimum(beam, dome)


def field(p):
    d = lid(p)
    for f in FRAME:
        d = smin(d, box(p, *f, FRAME_R), BLEND)
    posts = []
    for s in POSTS:
        posts.append(s)
        flat = {"x0": "x1", "x1": "x0"}.get(s[7], s[7])
        posts.append((-s[1], -s[0]) + s[2:7] + (flat,))
    # each side's column and caster seat (the first two posts, and their
    # mirrors) melt into one post first, so it hangs as a single smooth shape
    for i in (0, 1):
        side = smin(box(p, *posts[i]), box(p, *posts[i + 2]), POST_BLEND)
        d = smin(d, side, BLEND)
    for s in posts[4:]:
        d = smin(d, box(p, *s), BLEND)
    d = smax(d, plan(p, 80.0), 0.5)         # nothing out past the lid's sides
    d = smax(d, -prism(p, *JACK), ROLL)
    d = smax(d, -box(p, *ARM_SLOT, 0.01), ROLL)
    for c in CASTERS:
        d = smax(d, -caster_space(p, *c), 0.8)
    d = np.maximum(d, p[..., 2] - (LID["top"][0][1] - 0.02))   # just under the frame's top (the tab seat), not flush
    return np.maximum(d, FLOOR_Z - p[..., 2])   # nothing below the frame floor's plane (it prints on the bed)


def write_stl(path, verts, faces):
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    with open(path, "wb") as f:
        f.write(b"front_plate_body".ljust(80, b" "))
        f.write(struct.pack("<I", len(faces)))
        for k in range(len(faces)):
            f.write(struct.pack("<12fH", *n[k], *tri[k].ravel(), 0))


def main():
    axes = [np.arange(lo, hi + STEP, STEP) for lo, hi in BOUNDS]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)
    d = field(grid)
    # close the mesh where it reaches the bounds
    d[[0, -1], :, :] = 1.0
    d[:, [0, -1], :] = 1.0
    d[:, :, [0, -1]] = 1.0
    verts, faces, _, _ = marching_cubes(d, 0.0, spacing=(STEP,) * 3)
    verts += np.array([lo for lo, _ in BOUNDS])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_stl(OUT, verts, faces)
    print(f"{OUT}: {len(faces)} triangles")


if __name__ == "__main__":
    main()
