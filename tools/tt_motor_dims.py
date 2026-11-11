#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "trimesh", "scipy", "networkx", "shapely", "pillow"]
# ///
"""Dimension sheets for the TT motor: view/tt_motor_dims.html.

    uv run tools/tt_motor_dims.py

Three orthographic views and an isometric, with numbered dimensions, of the Red
TT draft (scad/tt_motor_red.scad, rendered fresh each run) and the user's
checked gearbox (scad/models/tt_motor/tt_gearbox.stl). The user reads the
drawings and dictates what is wrong; the values live in the .scad.

Frame: origin on the shaft at the gearbox's mid-thickness, X across the
gearbox, Y along the shaft (nub on -Y), motor towards -Z.
"""
import html
import pathlib
import subprocess
import tempfile
import time

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS = ROOT / "scad/models/tt_motor"
OUT = ROOT / "view/tt_dims"
PAGE = ROOT / "view/tt_motor_dims.html"
PPM = 10   # pixels per mm
STAMP = int(time.time())  # so the browser does not show stale pictures

# Caliper corrections from the user, e.g. {"B19": 22.8}.
CORRECTIONS = {}

ex, ey, ez = np.eye(3)
FONT = ImageFont.load_default(size=15)
TITLE = ImageFont.load_default(size=20)

VIEWS = {
    "front": ("Front, nub side towards you: X right, Z up", (ex, ez, -ey)),
    "side": ("Side, from -X: Y right, Z up", (ey, ez, -ex)),
    "end": ("Motor end, from below: X right, Y up", (ex, ey, -ez)),
    "back": ("Dead on at the connector, from +Y: Z up", (-ex, ez, ey)),
}

# Dimensions: (number, what, mm, note, pane, kind, ...)
#   "h" a b at foot   horizontal, u from a to b at height `at`, extension lines from v = foot
#   "v" a b at foot   vertical, v from a to b at column `at`, extension lines from u = foot
#   "o" u v lu lv     a leader from a point to a label, for diameters
GEARBOX = {
    1: ("Gearbox width (X)", 22.0, "", "front", "h", -11, 11, 33, 8),
    2: ("Gearbox thickness (Y)", 19.0, "", "side", "h", -9.5, 9.5, 28, 8),
    3: ("Shaft centre to end face (Z)", 11.5, "", "front", "v", 0, 11.5, 15, 9),
    4: ("Tab height above the end face (Z)", 5.0, "", "front", "v", 11.5, 16.5, -15, -2),
    5: ("Tab width (X)", 5.0, "", "front", "h", -2.5, 2.5, 21, 16.5),
    6: ("Shaft centre to tab hole (Z)", 14.0, "", "front", "v", 0, 14, -25, -1),
    7: ("Tab hole diameter", 3.0, "", "front", "o", 1.5, 14, 9, 17),
    8: ("Shaft centre to nub (Z)", 10.5, "", "front", "v", -10.5, 0, -15, -2),
    9: ("Nub diameter", 4.0, "", "front", "o", 2, -10.5, 7, -7),
    10: ("Nub height off the face (Y)", 2.0, "", "side", "h", -11.5, -9.5, -17, -12.5),
}
CHECKED_GEARBOX = dict(GEARBOX) | {
    11: ("Shaft centre to screw holes (Z)", 20.0, "", "front", "v", -20, 0, -25, -8.5),
    12: ("Screw hole spacing (X)", 17.0, "", "front", "h", -8.5, 8.5, 27, 8),
    13: ("Screw hole diameter", 3.0, "marked on the model, 0.05 deep, not open", "front", "o", 8.5, -20, 4, -16),
    14: ("Shaft tip to tip (Y)", 37.65, "18.25 on the nub side, 19.4 on the other", "side", "h", -18.25, 19.4, 22, 3),
    15: ("Shaft diameter", 5.3, "", "front", "o", 2.65, 0, 7, 4),
    16: ("Shaft centre to the gearbox's end face (Z)", 25.2, "", "front", "v", -25.2, 0, 15, 11),
    29: ("Shaft tip across the flats (Z)", 4.0, "the last 1.65 mm on the -Y side; 5.0 the other way", "side", "v", -2, 2, -25, -18.25),
}

R_PANES = ("front", "side", "back", "end")
G_PANES = ("front", "side", "end")
TOP = 11.5
Z_END = -25.21
Z_BULGE0 = TOP - 46
Z_BULGE1 = TOP - 68.16
Z_BOT = TOP - 75
MY = 0.5  # motor axis, off the gearbox's centre
Y_FLAT = -9.5 + 1.12  # the cover's -Y flat
Y_END = Y_FLAT + 25.5  # the connector block's +Y face
Z_BLOCK = Z_BOT + 13.25  # the connector block's top
Z_NUB = TOP - 41.6  # the nub's gearbox-side edge
Y_NECK = MY - 8.625  # the neck's -Y flat
YOU, PHOTO, CHECKED = "you", "estimate from your photos", "checked gearbox"
RED = {
    1: ("Overall, top of the gearbox to the bottom (Z)", 75, YOU, "tabs left off", "front", "v", Z_BOT, TOP, 45, 12),
    2: ("Below the gearbox: across the rounds (X)", 22.35, YOU, "", "front", "h", -22.35 / 2, 22.35 / 2, -84, -29),
    3: ("Below the gearbox: across the flats (Y)", 17.25, YOU, "", "side", "h", MY - 8.625, MY + 8.625, -84, -36),
    4: ("Bulge: across the rounds (X)", 25, YOU, "", "front", "h", -12.5, 12.5, -77, -45),
    5: ("Bulge: across the flats (Y)", 20, YOU, "", "side", "h", MY - 10, MY + 10, -77, -45),
    6: ("Encoder cover: across the rounds (X)", 19, YOU, "", "front", "h", -9.5, 9.5, -70, -60),
    7: ("Top to the end of the gearbox (Z)", 36.71, CHECKED, "", "front", "v", Z_END, TOP, 18, 11),
    8: ("Top to the start of the bulge (Z)", 46, YOU, "moved 1 mm after the first case print", "front", "v", Z_BULGE0, TOP, 27, 12.5),
    9: ("Top to the end of the bulge (Z)", 68.16, YOU, "the bulge is 22.16 long", "front", "v", Z_BULGE1, TOP, 36, 12.5),
    10: ("Motor axis, off the gearbox's centre (+Y)", 0.5, PHOTO, "the bulge's -Y flat is flush with the gearbox's -Y face", "side", "h", 0, MY, 26, 12),
    11: ("Cover's flat, in from the gearbox's -Y face (Y)", 1.12, YOU, "", "side", "h", -9.5, Y_FLAT, -70, -62),
    12: ("Cover's flat to the connector block's end (Y)", 25.5, YOU, "the block's end lands 17.12 from the gearbox's centre", "end", "v", Y_FLAT, Y_END, -20, -8),
    13: ("Connector block width (X)", 16.8, YOU, "you also measured 16.7", "end", "h", -8.4, 8.4, 25, Y_END),
    14: ("Connector block length (Z)", 13.25, YOU, "", "back", "v", Z_BOT, Z_BLOCK, 18, 9),
    15: ("White connector height (Z)", 4.75, YOU, "", "back", "v", Z_BLOCK - 6.75, Z_BLOCK - 2, -20, -7),
    16: ("White connector's top, down from the block's top (Z)", 2, YOU, "the photo looks nearer 3.2, with the circuit board at 2", "back", "v", Z_BLOCK - 2, Z_BLOCK, -30, -7),
    17: ("White connector width (X)", 14, PHOTO, "modelled as an opening 6 deep, also a guess", "back", "h", -7, 7, -71, -57),
    18: ("Nub width (X)", 4.84, YOU, "one on each flat", "back", "h", -2.42, 2.42, -27.6, -30),
    19: ("Nub length at its base (Z)", 3.13, YOU, "", "back", "v", Z_NUB - 3.13, Z_NUB, 18, 3),
    20: ("Top to the nub's gearbox-side edge (Z)", 41.6, YOU, "", "back", "v", Z_NUB, TOP, 29, 3),
    21: ("Nub height off the flat (Y)", 2.55, YOU, "", "side", "h", Y_NECK - 2.55, Y_NECK, -37, -33),
    22: ("Nub length at its outer end (Z)", 2.16, YOU, "straight back; the motor side flares from halfway", "side", "v", Z_NUB - 2.16, Z_NUB, -18, Y_NECK - 2.55),
}


def render(V, F, axes, color, padx=36, pady=26):
    """Orthographic z-buffer render. Returns the image and a data-to-pixel map."""
    U, Vv, W = [np.asarray(a, float) for a in axes]
    A = np.c_[V @ U, V @ Vv, V @ W]
    umin, vmin = A[:, :2].min(0) - [padx, pady]
    umax, vmax = A[:, :2].max(0) + [padx, pady]
    w, h = int((umax - umin) * PPM), int((vmax - vmin) * PPM)
    Z = np.full((h, w), -1e9)
    img = np.full((h, w, 3), 255, np.uint8)
    x, y, z = (A[:, 0] - umin) * PPM, (vmax - A[:, 1]) * PPM, A[:, 2]
    n = np.cross(A[F[:, 1]] - A[F[:, 0]], A[F[:, 2]] - A[F[:, 0]])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    light = np.array([0.3, 0.4, 0.85]) / np.linalg.norm([0.3, 0.4, 0.85])
    shade = 0.3 + 0.7 * np.abs(n @ light)
    col = np.asarray(color, float)
    for i, t in enumerate(F):
        xs, ys, zs = x[t], y[t], z[t]
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, w - 1))
        y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, h - 1))
        if x1 < x0 or y1 < y0:
            continue
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        c = 1 - a - b
        m = (a >= -0.02) & (b >= -0.02) & (c >= -0.02)
        if not m.any():
            continue
        zz = a * zs[0] + b * zs[1] + c * zs[2]
        py, px, zv = gy[m].astype(int), gx[m].astype(int), zz[m]
        up = zv > Z[py, px]
        Z[py[up], px[up]] = zv[up]
        img[py[up], px[up]] = (col * shade[i]).astype(np.uint8)
    # Outline every step in depth, or flat-on features like the shaft and nub vanish.
    edge = np.zeros((h, w), bool)
    edge[:, 1:] |= np.abs(np.diff(Z, axis=1)) > 0.3
    edge[1:, :] |= np.abs(np.diff(Z, axis=0)) > 0.3
    img[edge] = (45, 45, 45)
    return Image.fromarray(img), (lambda u, v: ((u - umin) * PPM, (vmax - v) * PPM + 32))


def arrow(d, a, b, col):
    a, b = np.array(a), np.array(b)
    n = (b - a) / (np.linalg.norm(b - a) + 1e-9)
    p = np.array([-n[1], n[0]])
    for tip, s in ((a, 1), (b, -1)):
        d.polygon([tuple(tip), tuple(tip + s * n * 10 + p * 4), tuple(tip + s * n * 10 - p * 4)], fill=col)


def tag(d, x, y, text, col):
    box = d.textbbox((0, 0), text, font=FONT)
    w, h = box[2] - box[0], box[3] - box[1]
    d.rounded_rectangle([x - w / 2 - 5, y - h / 2 - 5, x + w / 2 + 5, y + h / 2 + 7], radius=4, fill=col)
    d.text((x - w / 2, y - h / 2 - box[1]), text, fill="white", font=FONT)


def label(letter, num, value, diameter=False):
    v = CORRECTIONS.get(f"{letter}{num}", value)
    return f"{letter}{num}  {'dia ' if diameter else ''}{v:g}"


def draw_dim(d, tx, letter, num, dim, col):
    _, value, _, _, kind, *p = dim
    ink = (40, 40, 40)
    ext = (150, 150, 150)
    if kind == "o":
        u, v, lu, lv = p
        d.line([tx(u, v), tx(lu, lv)], fill=ink, width=2)
        tag(d, *tx(lu, lv), label(letter, num, value, True), col)
        return
    a, b, at, foot = p
    text = label(letter, num, value)
    if kind == "h":
        p0, p1 = tx(a, at), tx(b, at)
        for u in (a, b):
            d.line([tx(u, foot), tx(u, at)], fill=ext)
        d.line([p0, p1], fill=ink, width=2)
        arrow(d, p0, p1, ink)
        short = abs(p1[0] - p0[0]) < 90
        tag(d, p0[0] - 62 if short else (p0[0] + p1[0]) / 2, p0[1], text, col)
    else:
        p0, p1 = tx(at, a), tx(at, b)
        for v in (a, b):
            d.line([tx(foot, v), tx(at, v)], fill=ext)
        d.line([p0, p1], fill=ink, width=2)
        arrow(d, p0, p1, ink)
        short = abs(p1[1] - p0[1]) < 70
        tag(d, p0[0], min(p0[1], p1[1]) - 18 if short else (p0[1] + p1[1]) / 2, text, col)


def sheet(path, letter, dims, color, tagcol, panes):
    m = trimesh.load(path, process=False)
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    for pane in panes:
        title, axes = VIEWS[pane]
        im, tx = render(V, F, axes, color)
        canvas = Image.new("RGB", (im.width, im.height + 32), "white")
        canvas.paste(im, (0, 32))
        d = ImageDraw.Draw(canvas)
        d.text((8, 5), title, fill="black", font=TITLE)
        for num, dim in dims.items():
            if dim[3] == pane:
                draw_dim(d, tx, letter, num, dim, tagcol)
        canvas.save(OUT / f"{letter}_{pane}.png")
    n = np.array([0.55, -0.7, 0.45])
    n = n / np.linalg.norm(n)
    u = np.cross(ez, n)
    u /= np.linalg.norm(u)
    im, _ = render(V, F, (u, np.cross(n, u), n), color, padx=6, pady=6)
    canvas = Image.new("RGB", (im.width, im.height + 32), "white")
    canvas.paste(im, (0, 32))
    ImageDraw.Draw(canvas).text((8, 5), "Isometric", fill="black", font=TITLE)
    canvas.save(OUT / f"{letter}_iso.png")


def nub_detail():
    """Close-up of the nub from the side, as it passes through the case's cap."""
    p = 46
    ul, vl = (-19, 2.5), (-36, -23.5)
    W, H = int((ul[1] - ul[0]) * p), int((vl[1] - vl[0]) * p)
    im = Image.new("RGB", (W, H + 32), "white")
    d = ImageDraw.Draw(im)
    d.text((8, 5), "The nub on the neck, from the side: motor down", fill="black", font=TITLE)
    tx = lambda y, z: ((y - ul[0]) * p, (vl[1] - z) * p + 32)
    z0, flat, tip_y = Z_NUB, Y_NECK, Y_NECK - 2.55
    body = [(-9.5, vl[1]), (-9.5, Z_END), (flat, Z_END), (flat, z0), (tip_y, z0), (tip_y, z0 - 2.16),
            (flat - 1.275, z0 - 2.16), (flat, z0 - 3.13), (flat, Z_BULGE0), (-9.5, Z_BULGE0), (-9.5, vl[0]),
            (ul[1], vl[0]), (ul[1], vl[1])]
    d.polygon([tx(*q) for q in body], fill=(222, 120, 110), outline=(70, 20, 20))
    slot_hi, slot_lo = z0 + 0.3, z0 - 3.13 - 0.3
    for z_a, z_b in ((vl[1], slot_hi), (slot_lo, vl[0])):
        d.rectangle([tx(-11.4, z_a), tx(-9.7, z_b)], fill=(235, 150, 70), outline=(120, 70, 20))
    ink, ext, col = (40, 40, 40), (120, 120, 120), (150, 30, 28)
    def v(y, a, b, foot, text):
        p0, p1 = tx(y, a), tx(y, b)
        for z in (a, b):
            d.line([tx(foot, z), tx(y, z)], fill=ext)
        d.line([p0, p1], fill=ink, width=2)
        arrow(d, p0, p1, ink)
        tag(d, p0[0] - 44, (p0[1] + p1[1]) / 2, text, col)
    v(-12.6, z0 - 2.16, z0, tip_y, "R22  2.16")
    v(-14.0 + 0.2, z0 - 3.13, z0, flat, "R19  3.13")
    q0, q1 = tx(tip_y, z0 + 1.6), tx(flat, z0 + 1.6)
    d.line([tx(tip_y, z0), q0], fill=ext)
    d.line([tx(flat, z0), q1], fill=ext)
    d.line([q0, q1], fill=ink, width=2)
    arrow(d, q0, q1, ink)
    tag(d, q0[0] - 44, q0[1], "R21  2.55", col)
    d.text(tx(-8.0, z0 + 0.05), "straight back: 41.6 from the top", fill="black", font=FONT)
    d.text(tx(-8.9, -31.6), "straight to halfway, then flares", fill="black", font=FONT)
    d.text(tx(-11.25, -24.6), "cap", fill=(90, 50, 10), font=FONT)
    d.text(tx(-8.9, -24.6), "gearbox", fill="black", font=FONT)
    d.text(tx(-8.9, -35), "bulge", fill="black", font=FONT)
    im.save(OUT / "nub_detail.png")


def table(letter, dims, sources):
    rows = []
    for num, (what, value, note, *_) in sorted(dims.items()):
        key = f"{letter}{num}"
        fixed = key in CORRECTIONS
        rows.append(
            f"<tr{' class=fixed' if fixed else ''}><td class=id>{key}</td><td>{html.escape(what)}</td>"
            f"<td class=num>{CORRECTIONS.get(key, value):g}</td><td>{'corrected by you' if fixed else html.escape(sources[num])}</td>"
            f"<td>{html.escape(note)}</td></tr>")
    return ("<table><thead><tr><th>#</th><th>Dimension</th><th>mm</th><th>From</th><th>Note</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def section(letter, title, note, dims, sources, panes):
    pics = "".join(f'<img src="tt_dims/{letter}_{p}.png?v={STAMP}" alt="{title}, {p}">' for p in (*panes, "iso"))
    return f"<section><h2>{html.escape(title)}</h2><p>{html.escape(note)}</p><div class=grid>{pics}</div>{table(letter, dims, sources)}</section>"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        stl = pathlib.Path(t) / "red.stl"
        subprocess.run(["openscad", "--backend=manifold", "--export-format=binstl", "-o", str(stl),
                        str(ROOT / "scad/tt_motor_red.scad")], check=True, capture_output=True)
        # the table's source column is its own field in RED: drop it for the drawing
        sheet(stl, "R", {k: (v[0], v[1], v[3], *v[4:]) for k, v in RED.items()}, (222, 92, 84), (150, 30, 28), R_PANES)
    sheet(MODELS / "tt_gearbox.stl", "G", CHECKED_GEARBOX, (135, 155, 200), (40, 62, 128), G_PANES)
    red = {k: (v[0], v[1], v[3], *v[4:]) for k, v in RED.items()}
    red_src = {k: v[2] for k, v in RED.items()}
    g_src = {k: "checked by you" for k in CHECKED_GEARBOX}
    nub_detail()
    css = """
    :root{--ink:#1c1c1c;--line:#ddd;--head:#f3f3f3;--fix:#fff4cf}
    body{background:#fff;color:var(--ink);font:16px/1.45 system-ui,sans-serif;margin:0 auto;max-width:1500px;padding:16px}
    h1{font-size:26px;margin:4px 0}h2{font-size:22px;margin:28px 0 4px}p{margin:6px 0;max-width:80ch}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}
    .grid img{width:100%;height:auto;border:1px solid var(--line);background:#fff}
    table{border-collapse:collapse;width:100%}th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
    th{background:var(--head)}.id{font-weight:700;white-space:nowrap}.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
    tr.fixed td{background:var(--fix)}
    @media (max-width:720px){.grid{grid-template-columns:1fr}}
    """
    page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>TT Motor Dimensions</title><style>{css}</style></head><body>
<h1>Red TT motor, first draft</h1>
<p>Each number on a drawing matches a row in the table. Tell me the ones that are wrong, for example &ldquo;R8 is 44&rdquo;. Values are in mm. &ldquo;Top&rdquo; means the end face of the gearbox, the one with the tab on it. The tab on the gearbox is included, and the overall length leaves it out.</p>
{section("R", "Red TT", "Your checked gearbox with a modelled motor end. The rows marked as estimates are read off your two photos.", red, red_src, R_PANES)}
{section("G", "Gearbox, checked", "The gearbox the Red TT is built on.", CHECKED_GEARBOX, g_src, G_PANES)}
</body></html>
"""
    PAGE.write_text(page)
    print("wrote", PAGE)


if __name__ == "__main__":
    main()
