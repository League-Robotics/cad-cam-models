#!/usr/bin/env python3
"""Carvera G-code for the cuts in the 11 x 19 robot plates.

    python3 tools/plate_gcode.py                      # the three one-plate jobs into cam/:
                                                      # plate_hole.nc, plate_pockets.nc, plate_hole_and_pockets.nc
    python3 tools/plate_gcode.py --hole 3x4 --nx 2 --ny 2 --layers 2 -o out.nc

Same style of job as CAM/RobotPlate/robot_plate.nc (the plate we already
cut): a 2D contour inside each cut with a corn cutter, climb, a small step
down per pass, to 0.2 past the plate's bottom, with 2 mm tabs (3.5 mm ramps
per mm of tab) in the last two millimetres so the cut-out piece stays put (the
first plate's 1 mm tabs let every slug but the 3x4's pop out, 2026-10-30). Only
the cuts are made; the plate is a bought one.

Cuts (--hole): "3x3" / "3x4" the sensor hole (columns 5-7, rows 6-8 / 5-8;
one rectangle, a tab on each side), "3x3_9" the one the user cuts since
2026-10-30: 3x3 at rows 9-11 (he walked it back from 5-8 over four plates), "cans" the four pockets for the sensor's
cans when it stands on top of the plate (scad/robot_plate.scad: 7.8 x 12.2,
centred 15.55 from the front edge at 14, 38, 50 and 74 across, on the
solder-pad columns of the sensor's scan; the middle two run together into one
pocket since the 4.2 web between them did not survive the first plate, and
the front edge 1.5 further forward since the cans did not clear it, and the
back edge 0.5 further back; each a slug held by a tab on each long side), "3x3_9_cans" both that hole and the can pockets in one plate
(they don't meet: the pockets are in rows 2-3, the hole in rows 9-11), so one
plate takes the sensor either way. The defaults are the original job's 2 mm corn cutter (now T1 on the Carvera,
12000 rpm, feed 500, plunge 300, 0.3 per pass); --tool 1 --feed 300 --plunge
150 --step 0.2 would suit a 1 mm cutter, if it has 7.8 mm of flute.

Coordinates as that job: the plate's long side along X with its front edge
(row 1) on X = 0, the short side along Y, Z = 0 on the top face, origin at
the front-left corner of the first plate. Rows count along X (8 mm each),
columns along Y. The sensor hole is cut exactly on the cell edges (front_ext
0; the existing job ran 1.65 past the front cell edge, nicking the row
above).

Lay-up: nx plates along X, ny along Y, butted together (gap 0) or with a
gap; each plate's cuts are made in turn. layers > 1 stacks that many plates
and cuts through all of them (the tabs then hold only the bottom piece, and
the cutter needs the reach).
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
U = 8.0
COLS, ROWS = 11, 19
PLATE_L = 151.2          # the plate as measured for the existing job (19 * 8 = 152 nominal)
PLATE_W = COLS * U       # 88
PLATE_T = 7.7            # measured 2026-10-30 (the first job used 7.6)
HOLES = {"3x3": ((5, 7), (6, 8)), "3x4": ((5, 7), (5, 8)), "3x3_9": ((5, 7), (9, 11))}   # (columns), (rows), 1-based, inclusive
# the can pockets (scad/robot_plate.scad): robot x of the cans, their y from
# the bracket row (row 5), the body and the clearance per side
CAN_X = [-30, -6, 6, 30]
CAN_MERGE = ((-6, 6),)           # pairs cut as one pocket (the middle two)
CAN_Y = (5 - 0.5) * U - 20.45    # 15.55 from the front edge
CAN_BODY = (5.8, 10.2)
CAN_CLEAR = 1.0
CAN_FRONT_EXT = 1.5              # the pockets' front edge further toward the plate's front: the cans did not clear it (2026-10-30)
CAN_BACK_EXT = 0.5               # and the back edge further back (2026-10-30)
CUTS = list(HOLES) + ["cans"] + [h + "_cans" for h in HOLES]
# where to touch off Z (work origin, not the path origin): the corner where rows
# 5/6 meet columns 3/4, solid, 3.3 mm from the nearest hole's edge, 8 below the
# hole's side (and 24 ahead of it, rows 9-11) and clear of the pockets, so it is still there after the cuts
PROBE = (40, 24)
# the jobs the user cuts (2026-10-30), by their plain names
NAMES = {"3x3_9": "hole", "cans": "pockets", "3x3_9_cans": "hole_and_pockets"}


def hole_rect(hole, front_ext):
    (c0, c1), (r0, r1) = HOLES[hole]
    x0, x1 = (r0 - 1) * U - front_ext, r1 * U            # along the plate
    y0, y1 = (c0 - 1) * U, c1 * U                          # across
    return x0, x1, y0, y1


def cuts(hole, front_ext):
    """The rectangles to cut in one plate, job coordinates: (x0, x1, y0, y1,
    tabbed sides) with sides as in contour(): 0 +y, 1 -x, 2 -y, 3 +x."""
    if hole in HOLES:
        return [(*hole_rect(hole, front_ext), (0, 1, 2, 3))]
    if hole.endswith("_cans"):
        return cuts("cans", front_ext) + cuts(hole[:-5], front_ext)
    w, h = CAN_BODY[0] + 2 * CAN_CLEAR, CAN_BODY[1] + 2 * CAN_CLEAR
    merged = {x for pair in CAN_MERGE for x in pair}
    spans = [(x, x) for x in CAN_X if x not in merged] + [(min(pr), max(pr)) for pr in CAN_MERGE]
    # robot x across -> Y = 44 - x (robot_plate.scad on_cam); the pockets' long side is along X
    return [(CAN_Y - h / 2 - CAN_FRONT_EXT, CAN_Y + h / 2 + CAN_BACK_EXT, 44 - xb - w / 2, 44 - xa + w / 2, (1, 3)) for xa, xb in sorted(spans, reverse=True)]


def contour(f, x0, x1, y0, y1, depth, step, tab_h, tab_ramp, feed, plunge, start_z, tab_sides=(0, 1, 2, 3)):
    """Climb-cut rectangle inside the lines, passes down to -depth, a tab in
    the middle of each side in tab_sides in the last tab_h. Starts and ends
    at (x1, y0) with the cutter up."""
    passes = []
    z = 0.0
    while z < depth - 1e-9:
        z = min(z + step, depth)
        passes.append(round(z, 3))
    f.append(f"G0 X{x1:.3f} Y{y0:.3f}")
    f.append(f"G0 Z{start_z}")
    corners = [(x1, y0), (x1, y1), (x0, y1), (x0, y0), (x1, y0)]
    for z in passes:
        f.append(f"G1 Z{-z:.3f} F{plunge}")
        tab_top = depth - tab_h
        for side, ((ax, ay), (bx, by)) in enumerate(zip(corners, corners[1:])):
            if z <= tab_top + 1e-9 or side not in tab_sides:
                f.append(f"G1 X{bx:.3f} Y{by:.3f} F{feed}")
                continue
            # a tab in the middle of this side: ramp up to -tab_top and back down
            rise = z - tab_top
            L = abs(bx - ax) + abs(by - ay)
            ramp = min(tab_ramp * rise, L / 2 - 0.5)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            ux, uy = (bx - ax) / L, (by - ay) / L
            p1 = (mx - ux * ramp, my - uy * ramp)
            p2 = (mx + ux * ramp, my + uy * ramp)
            f.append(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f} F{feed}")
            f.append(f"G1 X{mx:.3f} Y{my:.3f} Z{-tab_top:.3f} F{feed}")
            f.append(f"G1 X{p2[0]:.3f} Y{p2[1]:.3f} Z{-z:.3f} F{plunge}")
            f.append(f"G1 X{bx:.3f} Y{by:.3f} F{feed}")


def gcode(hole, nx, ny, layers, gap, front_ext, tool_d, tool_n, step, tab_h, tab_ramp, feed, plunge, rpm, safe_z, start_z, through):
    depth = layers * PLATE_T + through
    rects = cuts(hole, front_ext)
    r = tool_d / 2
    def describe(h, rs):
        if h in HOLES:
            return f"; hole: columns {HOLES[h][0][0]}-{HOLES[h][0][1]}, rows {HOLES[h][1][0]}-{HOLES[h][1][1]}; per plate X {rs[0][0]:.2f}..{rs[0][1]:.2f}, Y {rs[0][2]:.2f}..{rs[0][3]:.2f}"
        return "; can pockets (the middle two run together): " + ", ".join(f"X {x0:.2f}..{x1:.2f} Y {y0:.2f}..{y1:.2f}" for x0, x1, y0, y1, _ in rs) + " (slugs held by a tab on each long side)"
    what = describe(hole, rects) if not hole.endswith("_cans") else describe("cans", rects[:-1]) + "\n" + describe(hole[:-5], rects[-1:]) + "\n; (the pockets first, then the hole)"
    f = ["%", "; 3-Axis", "; Material: Plastic (bought 11 x 19 Technic plates)",
         f"; Stock Size: {nx * PLATE_L + (nx - 1) * gap:.1f}(X) * {ny * PLATE_W + (ny - 1) * gap:.1f}(Y) * {layers * PLATE_T:.1f}(Z) mm",
         f"; {hole} in each of {nx} x {ny} plates" + (f", {layers} plates stacked" if layers > 1 else ""),
         what,
         "; origin: front-left corner of the first plate (front edge on X = 0), Z0 on the top face",
         f"; Z probe at X{PROBE[0]:g} Y{PROBE[1]:g} from the work origin (the corner of rows 5/6 and columns 3/4: solid, 3.3 mm to the nearest hole, 8 outside the hole and clear of the pockets)",
         f"; {tool_d:g} mm corn cutter (T{tool_n}; needs {depth:.1f} mm of flute), S{rpm}, F{feed} / plunge {plunge}, {step:g} per pass to Z{-depth:.1f}, {tab_h:g} mm tabs",
         f"; tools/plate_gcode.py --hole {hole} --nx {nx} --ny {ny} --layers {layers} --gap {gap} --tool {tool_d:g} --tool-number {tool_n} --step {step:g} --feed {feed} --plunge {plunge}",
         "", "; Tool List", f"; T{tool_n}-{tool_d:g}mm Corn", "", "; Path List", f"; [T{tool_n}]2D Contour", "",
         "G90 G21", "", f"; T{tool_n}-{tool_d:g}mm Corn", "", f"T{tool_n} M6"]
    first = True
    for j in range(ny):
        for i in range(nx):
            ox, oy = i * (PLATE_L + gap), j * (PLATE_W + gap)
            f.append(f"; plate {i + 1},{j + 1} at X{ox:.1f} Y{oy:.1f}")
            for x0, x1, y0, y1, tabs in rects:
                if first:
                    f.append(f"G0 X{ox + x1 - r:.3f} Y{oy + y0 + r:.3f}")
                    f.append(f"S{rpm} M3")
                    first = False
                f.append(f"G0 Z{safe_z}")
                contour(f, ox + x0 + r, ox + x1 - r, oy + y0 + r, oy + y1 - r, depth, step, tab_h, tab_ramp, feed, plunge, start_z, tabs)
                f.append(f"G0 Z{safe_z}")
    f += ["M05", "G28", "M02", ""]
    return "\n".join(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hole", choices=CUTS, help="which cut (default: write the whole set)")
    ap.add_argument("--nx", type=int, default=1, help="plates along X (default 1)")
    ap.add_argument("--ny", type=int, default=1, help="plates along Y (default 1)")
    ap.add_argument("--layers", type=int, default=1, help="plates stacked (default 1)")
    ap.add_argument("--gap", type=float, default=0, help="gap between plates, mm (default 0: butted)")
    ap.add_argument("--front-ext", type=float, default=0, help="hole past the front cell edge (default 0: on the cell edges)")
    ap.add_argument("--tool", type=float, default=2.0, help="cutter diameter (default 2, as the first job)")
    ap.add_argument("--tool-number", type=int, default=1, help="the Carvera tool number (default 1: the 2 mm corn cutter since 2026-10-30; the first job had it as T3)")
    ap.add_argument("--step", type=float, default=0.3, help="depth per pass (default 0.3; 0.2 for a 1 mm cutter)")
    ap.add_argument("--tab-h", type=float, default=2.0, help="tab height (default 2; the first plate's 1 mm tabs did not hold the slugs)")
    ap.add_argument("--tab-ramp", type=float, default=3.5, help="ramp length per mm of tab height")
    ap.add_argument("--feed", type=int, default=500, help="mm/min (default 500; 300 for a 1 mm cutter)")
    ap.add_argument("--plunge", type=int, default=300, help="mm/min (default 300; 150 for a 1 mm cutter)")
    ap.add_argument("--rpm", type=int, default=12000)
    ap.add_argument("--safe-z", type=float, default=15)
    ap.add_argument("--start-z", type=float, default=3)
    ap.add_argument("--through", type=float, default=0.2, help="cut past the bottom (default 0.2)")
    ap.add_argument("-o", "--out", help="output file (default cam/plate_<name>.nc for the one-plate set, else cam/robot_plate_<hole>_<nx>x<ny>[_x<layers>]_<tool>mm.nc)")
    a = ap.parse_args()
    jobs = [a.hole] if a.hole else list(NAMES)
    for hole in jobs:
        g = gcode(hole, a.nx, a.ny, a.layers, a.gap, a.front_ext, a.tool, a.tool_number, a.step, a.tab_h, a.tab_ramp, a.feed, a.plunge, a.rpm, a.safe_z, a.start_z, a.through)
        plain = hole in NAMES and (a.nx, a.ny, a.layers, a.tool) == (1, 1, 1, 2.0)
        out = Path(a.out) if a.out else ROOT / "cam" / (f"plate_{NAMES[hole]}.nc" if plain else f"robot_plate_{hole}_{a.nx}x{a.ny}" + (f"_x{a.layers}" if a.layers > 1 else "") + f"_{a.tool:g}mm.nc")
        out.parent.mkdir(exist_ok=True)
        out.write_text(g)
        print("wrote", out, f"({g.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
