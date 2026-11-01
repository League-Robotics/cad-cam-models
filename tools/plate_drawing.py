#!/usr/bin/env python3
"""Drawing of the 11 x 19 robot plates with their holes, cell by cell.

    python3 tools/plate_drawing.py            -> view/robot_plates_drawing.svg (+ .png via Chrome)

Three panels: the plate with the 3x3 hole (as cut today) and with the 3x4
hole (one row further forward), each with the reflectance sensor drawn
under it where it then sits, and the Carvera lay-up of four plates (two
rows of two, long side along X) with the job origin. Cells are numbered as
the user counts them: the plate held with its 19 side up and down, column 1
on the left, row 1 at the top (the front of the robot). Same numbers as
scad/robot_plate.scad and tools/plate_gcode.py.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "view" / "robot_plates_drawing.svg"

U = 8
COLS, ROWS = 11, 19
PLATE_L = 151.2          # measured length, as the CAM stock
FRONT_EXT = 0
HOLES = {"3x3": ((5, 7), (6, 8)), "3x4": ((5, 7), (5, 8))}
SENSOR_ROW = {"3x3": 5, "3x4": 4, "cans": 5}
# the sensor's cans (reflectance_sensor.scad): x, y from the bracket row, body, clearance per side
CAN_X = [-30, -6, 6, 30]
CAN_Y = -20.45
CAN_BODY = (5.8, 10.2)
CAN_CLEAR = 1.0
K = 3.0                  # px per mm in the plate panels


def h_cell(c, r):
    if r in (1, ROWS):
        return c % 2 == 0
    if c in (1, COLS):
        return r % 2 == 0
    return False


def hole_box(name):
    (c0, c1), (r0, r1) = HOLES[name]
    return ((c0 - 1) * U, c1 * U, (r0 - 1) * U - FRONT_EXT, r1 * U)   # x0, x1 (across), y0, y1 (down from the front)


def plate_panel(name, ox, oy):
    """SVG for one plate at pixel origin (ox, oy): plate x across (0..88) to
    the right, y down from the front edge (0..152)."""
    s = []
    X = lambda x: ox + x * K
    Y = lambda y: oy + y * K
    s.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{COLS*U*K}" height="{ROWS*U*K}" rx="6" fill="#f3d55b" stroke="#6b5a12" stroke-width="2"/>')
    for c in range(1, COLS + 1):
        for r in range(1, ROWS + 1):
            cx, cy = (c - 0.5) * U, (r - 0.5) * U
            if h_cell(c, r):
                # horizontal hole: a bar in from the face it sits on
                if r == 1:
                    s.append(f'<rect x="{X(cx-2.4)}" y="{Y(0)}" width="{4.8*K}" height="{U*K}" fill="#8a7a2a"/>')
                elif r == ROWS:
                    s.append(f'<rect x="{X(cx-2.4)}" y="{Y(ROWS*U-U)}" width="{4.8*K}" height="{U*K}" fill="#8a7a2a"/>')
                elif c == 1:
                    s.append(f'<rect x="{X(0)}" y="{Y(cy-2.4)}" width="{U*K}" height="{4.8*K}" fill="#8a7a2a"/>')
                else:
                    s.append(f'<rect x="{X(COLS*U-U)}" y="{Y(cy-2.4)}" width="{U*K}" height="{4.8*K}" fill="#8a7a2a"/>')
            else:
                s.append(f'<circle cx="{X(cx)}" cy="{Y(cy)}" r="{2.4*K}" fill="#fff" stroke="#6b5a12" stroke-width="1"/>')
    # numbers
    for c in range(1, COLS + 1):
        s.append(f'<text x="{X((c-0.5)*U)}" y="{Y(0)-8}" font-size="12" text-anchor="middle" fill="#333">{c}</text>')
    for r in range(1, ROWS + 1):
        s.append(f'<text x="{X(0)-8}" y="{Y((r-0.5)*U)+4}" font-size="12" text-anchor="end" fill="#333">{r}</text>')
    # the sensor under the plate (dashed) or on top of it (solid)
    sr = SENSOR_ROW[name]
    top = name == "cans"
    sx = lambda x: X(44 + x)
    sy = lambda y: Y((sr - 0.5) * U + y)
    g = 'fill="rgba(74,163,223,0.25)" stroke="#1a5fa0" stroke-width="1.5"' + ('' if top else ' stroke-dasharray="5,3"')
    s.append(f'<rect x="{sx(-36)}" y="{sy(-28.4)}" width="{72*K}" height="{25.3*K}" {g}/>')
    s.append(f'<rect x="{sx(-12)}" y="{sy(-3.1)}" width="{24*K}" height="{22.5*K}" {g}/>')
    for bx in (-24, 24):
        s.append(f'<rect x="{sx(bx-12)}" y="{sy(-9.4)}" width="{24*K}" height="{12.8*K}" fill="none" stroke="#1a5fa0" stroke-width="1.5"/>')
    s.append(f'<rect x="{sx(-12)}" y="{sy(5.6)}" width="{24*K}" height="{13.8*K}" fill="none" stroke="#1a5fa0" stroke-width="1.5"/>')
    s.append(f'<rect x="{sx(-5)}" y="{sy(5.4)}" width="{10.2*K}" height="{12.2*K}" fill="#2f5fd0" stroke="#10306a" stroke-width="1"/>')
    for hx, hy in [(-32, 0), (-16, 0), (16, 0), (32, 0), (-8, 16), (8, 16)]:
        s.append(f'<circle cx="{sx(hx)}" cy="{sy(hy)}" r="{1.5*K}" fill="#1a5fa0"/>')
    for lx in CAN_X:
        s.append(f'<rect x="{sx(lx-2.9)}" y="{sy(CAN_Y-5.1)}" width="{5.8*K}" height="{10.2*K}" fill="#333" opacity="0.5"/>')
    # the hole(s)
    if top:
        w, h = CAN_BODY[0] + 2 * CAN_CLEAR, CAN_BODY[1] + 2 * CAN_CLEAR
        for cx in CAN_X:
            s.append(f'<rect x="{sx(cx-w/2)}" y="{sy(CAN_Y-h/2)}" width="{w*K}" height="{h*K}" fill="rgba(220,40,40,0.45)" stroke="#c01818" stroke-width="2.5"/>')
        cy = (sr - 0.5) * U + CAN_Y
        cap = ["sensor on top of the plate: four can pockets",
               f"{w:.1f} x {h:.1f}, centred y {cy:.1f} ({cy-h/2:.1f}..{cy+h/2:.1f}):",
               f"row 2 and {cy+h/2-16:.1f} into row 3; row 1 stays free",
               "(cans on the scan's solder pads, 1.0 clearance)",
               f"sensor (solid) standing on its brackets, pinned at row {sr}",
               "from below; cans end 5 above the plate's bottom face"]
        cap = [(t, 15 if i < 1 else 12, "bold" if i < 1 else "normal", "#1a5fa0" if i >= 4 else "#111") for i, t in enumerate(cap)]
    else:
        x0, x1, y0, y1 = hole_box(name)
        s.append(f'<rect x="{X(x0)}" y="{Y(y0)}" width="{(x1-x0)*K}" height="{(y1-y0)*K}" fill="rgba(220,40,40,0.35)" stroke="#c01818" stroke-width="2.5"/>')
        (c0, c1), (r0, r1) = HOLES[name]
        cap = [(f"{name} hole: columns {c0}-{c1}, rows {r0}-{r1}", 15, "bold", "#111"),
               (f"(first cut cell {c0},{r0})", 15, "bold", "#111"),
               (f"{x1-x0:.0f} across x {y1-y0:.0f} along, on the cell edges", 12, "normal", "#333"),
               ("(the old job ran 1.65 into the row above; not any more)", 12, "normal", "#333"),
               (f"sensor (dashed) under the plate, pinned at row {sr}: its PCB", 12, "normal", "#1a5fa0"),
               (f"front edge {(sr-0.5)*U-28.4:+.1f} from the plate edge, jack in the hole", 12, "normal", "#1a5fa0")]
    for i, (t, fs, fw, col) in enumerate(cap):
        s.append(f'<text x="{X(COLS*U/2)}" y="{Y(ROWS*U)+22+i*17}" font-size="{fs}" font-weight="{fw}" text-anchor="middle" fill="{col}">{t}</text>')
    s.append(f'<text x="{X(COLS*U/2)}" y="{Y(0)-40}" font-size="12" text-anchor="middle" fill="#333">front edge (row 1)</text>')
    s.append(f'<text x="{X(COLS*U/2)}" y="{Y(0)-26}" font-size="12" text-anchor="middle" fill="#333">horizontal edge holes in the even cells</text>')
    return "\n".join(s)


def cam_panel(name, ox, oy, k=1.5, nx=2, ny=2, gap=0):
    """The Carvera lay-up: plates with the long side along X, origin at the
    first plate's front-left corner (the front edge on X = 0)."""
    s = []
    W = PLATE_L * nx + gap * (nx - 1)
    H = COLS * U * ny + gap * (ny - 1)
    X = lambda x: ox + x * k
    Y = lambda y: oy + (H - y) * k   # CAM y up
    x0, x1, y0, y1 = hole_box(name)   # across, along
    for i in range(nx):
        for j in range(ny):
            px, py = i * (PLATE_L + gap), j * (COLS * U + gap)
            s.append(f'<rect x="{X(px)}" y="{Y(py+COLS*U)}" width="{PLATE_L*k}" height="{COLS*U*k}" rx="4" fill="#f3d55b" stroke="#6b5a12" stroke-width="1.5"/>')
            for c in range(1, COLS + 1):
                for r in range(1, ROWS + 1):
                    if not h_cell(c, r):
                        s.append(f'<circle cx="{X(px+(r-0.5)*U)}" cy="{Y(py+(c-0.5)*U)}" r="{2.4*k}" fill="#fff" stroke="#6b5a12" stroke-width="0.6"/>')
            s.append(f'<rect x="{X(px+y0)}" y="{Y(py+x1)}" width="{(y1-y0)*k}" height="{(x1-x0)*k}" fill="rgba(220,40,40,0.35)" stroke="#c01818" stroke-width="1.5"/>')
    s.append(f'<circle cx="{X(0)}" cy="{Y(0)}" r="5" fill="#111"/>')
    s.append(f'<text x="{X(0)+8}" y="{Y(0)+16}" font-size="12" fill="#111">job origin X0 Y0 (Z0 on top of the stock), as the existing job</text>')
    s.append(f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(40)}" y2="{Y(0)}" stroke="#c01818" stroke-width="2"/><text x="{X(44)}" y="{Y(0)+4}" font-size="12" fill="#c01818">X</text>')
    s.append(f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(0)}" y2="{Y(40)}" stroke="#1a8a1a" stroke-width="2"/><text x="{X(0)-4}" y="{Y(44)}" font-size="12" fill="#1a8a1a" text-anchor="end">Y</text>')
    s.append(f'<text x="{X(W/2)}" y="{Y(H)-44}" font-size="15" font-weight="bold" text-anchor="middle" fill="#111">Carvera lay-up: {nx} x {ny} plates, {W:.1f} x {H:.0f} mm, front edges toward X = 0</text>')
    s.append(f'<text x="{X(W/2)}" y="{Y(H)-26}" font-size="12" text-anchor="middle" fill="#333">{name} hole per plate at X {y0:.2f}..{y1:.2f}, Y {x0:.0f}..{x1:.0f} (+ plate offsets)</text>')
    s.append(f'<text x="{X(W/2)}" y="{Y(H)-10}" font-size="12" text-anchor="middle" fill="#333">2 mm cutter, 0.3 steps, four 1 mm tabs; stacking two plates doubles the depth (cam/*_x2.nc)</text>')
    return "\n".join(s)


def main():
    panels = []
    step = 88 * K + 150
    panels.append(plate_panel("3x4", 60, 90))
    panels.append(plate_panel("cans", 60 + step, 90))
    panels.append(plate_panel("3x3", 60 + 2 * step, 90))
    w = int(60 + 3 * step)
    h = int(90 + 152 * K + 130)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{w}" height="{h}" fill="#fafaf4"/>',
           '<text x="20" y="30" font-size="20" font-weight="bold" fill="#111">11 x 19 robot plates: cuts for the reflectance sensor, counted in cells (column across, row down from the front)</text>']
    svg += panels
    svg.append("</svg>")
    OUT.write_text("\n".join(svg))
    print("wrote", OUT)
    png = OUT.with_suffix(".png")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(chrome).exists():
        subprocess.run([chrome, "--headless=new", "--hide-scrollbars", f"--window-size={w},{h}", f"--screenshot={png}", OUT.as_uri()],
                       capture_output=True)
        print("wrote", png)


if __name__ == "__main__":
    main()
