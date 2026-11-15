# /// script
# requires-python = ">=3.11"
# dependencies = ["shapely>=2", "matplotlib", "numpy", "scipy"]
# ///
"""Place two header (pin) plug tails on the PCB blank in the Carvera's jig, from today's scan, and write
the job for the Test and Dev program `mill_plug_tails.py` (carvera repo, src/hosts/kinsey/testdev).

    uv run pcb/plug-tail/scripts/mill_job.py GRID.npz SCAN_NAME

GRID.npz: the jig pocket's height grid (machine X/Y, 0.2 mm cells) from Buzzkill's process_trial.py.
Toolpaths come from make_cam.plan() (the cleared-copper paths of the strip program), in PAIR
coordinates: mm, x across the pair (0 between the boards), y from the tail end (0) to the tongue
tips (L), copper up, seen from above (a board's local y runs the other way: pair y = L - local y). The program probes the blank
and turns these into G-code in work coordinates. Placement follows the usb-power-switch job
(tools/mill/place.py there): MARGIN clear of anything that isn't blank, 3 mm from the walls.

Writes cam/testdev/mill_plug_tails.{json,png} and cam/testdev/blank_<scan>.json.
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage
from shapely import affinity, contains_xy
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import substring, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_cam as mc     # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "cam", "testdev")

NAME = "header-tail"                # the pin version
GAP = 3.0                           # mm between the two boards' outlines
ANCHOR = (-359.208, -235.638)       # machine X, Y of work 0, 0: the pocket's front-left corner
POCKET = (0.0, 150.0, 0.0, 100.0)   # work X, Y of the pocket walls (measured 151.0, 100.8)
WALL_CLEAR = 3.0
MARGIN = 5.0                        # mm from the cutter's edge to anything that is not blank (scan XY is good to ~2)
LEVEL_TOL = 0.6
FLOOR_MZ = -110.40                  # probe machine Z on the pocket floor (2026-11-08; 11-11 touches -110.2 to -110.5)
PROBE_BALL = 4.0
MIN_COVER = 0.7                     # share of the footprint measured (big gaps are obstacles, above)
FLOOR_X_MIN = 40.0                  # work X: floor touches no further left (the camera mount sits to -X)

ISO = {"tool": mc.T_V, "name": "30 deg V-bit, 0.2 tip", "depth": -mc.ISO_Z, "rpm": 12000, "feed": 300, "plunge": 100,
       "width": round(2 * mc.R_V, 4)}
CLR = {"tool": mc.T_F, "name": "1.0 mm flat end mill", "dia": 1.0, "depth": -mc.FLAT_Z, "rpm": 12000, "feed": 300, "plunge": 100}
OUTLINE = {"tool": mc.T_O, "name": "0.8 mm corn cutter", "dia": 0.8, "rpm": 12000, "feed": 250, "plunge": 80,
           "step": 0.25, "below": 0.1, "tab_t": 0.5, "tab_w": mc.TAB_W}
FR4 = 1.4                           # the stock in the jig (Eric, 2026-11-11): tab tops are tab_t above its underside
TRAVEL = 2.0


def pair_maps():
    W, L = mc.GEO[NAME]["board_mm"][:2]
    cxs = (-(W + GAP) / 2, (W + GAP) / 2)
    return [lambda x, y, cx=cx: (cx + x, L - y) for cx in cxs], W, L


def ordered(paths, start):
    out, _ = mc.order(paths, start)
    return [[[round(x, 4), round(y, 4)] for x, y in p] for p in out]


def outline_pieces(ol):
    """One closed climb-cut loop round the board (clockwise from above), split at the tabs."""
    r = OUTLINE["dia"] / 2
    ring = LineString(ol.buffer(r, quad_segs=16).exterior.coords)
    if Polygon(ring).exterior.is_ccw:
        ring = LineString(list(ring.coords)[::-1])
    L = ring.length
    W, Lb = mc.GEO[NAME]["board_mm"][:2]
    cx = (ol.bounds[0] + ol.bounds[2]) / 2
    # tabs: the middle of each long side of the wide part and the tail end, as in the strip program
    along = mc.TABS[NAME][0][2]
    centres = [(cx - W / 2 - r, Lb - along), (cx + W / 2 + r, Lb - along), (cx, -r)]
    h = OUTLINE["tab_w"] / 2 + r
    s0 = ring.project(Point(cx, Lb + r))          # start at the tongue tip, far from every tab
    spans = sorted(((ring.project(Point(p)) - s0) % L - h, (ring.project(Point(p)) - s0) % L + h) for p in centres)
    cuts = [0.0] + [v for a, b in spans for v in (a, b)] + [L]
    pieces = []
    for k in range(len(cuts) - 1):
        a, b = (s0 + cuts[k]) % L, (s0 + cuts[k + 1]) % L
        if a < b or cuts[k + 1] - cuts[k] >= L:
            seg = substring(ring, a, b if b > a else L)
        else:
            seg = LineString(list(substring(ring, a, L).coords) + list(substring(ring, 0, b).coords)[1:])
        pieces.append({"tab": k % 2 == 1, "pts": [[round(x, 4), round(y, 4)] for x, y in seg.coords]})
    return pieces, L


def build_paths():
    maps, W, L = pair_maps()
    pl = mc.plan(NAME)
    iso, clear, loops, outlines, cu = [], [], [], [], []
    for m in maps:
        iso += [[m(*c) for c in p] for p in pl["iso"] + pl["rest"]]
        clear += [[m(*c) for c in p] for p in pl["flat"]]
        ol = Polygon([m(*c) for c in mc.GEO[NAME]["outline"]])
        outlines.append(ol)
        pieces, ring_len = outline_pieces(ol)
        loops.append({"pieces": pieces, "length": round(ring_len, 2)})
        cu.append(affinity.affine_transform(affinity.scale(pl["cu"], 1, -1, origin=(0, 0)), [1, 0, 0, 1, m(0, 0)[0], L]))
    start = (-(W + GAP / 2), L)
    return {"iso": ordered(iso, start), "clear": ordered(clear, start), "loops": loops,
            "outlines": [[[round(x, 4), round(y, 4)] for x, y in o.exterior.coords] for o in outlines],
            "copper": unary_union(cu), "W": W, "L": L, "plan": pl}


# ---------- the blank, from the scan (as tools/mill/place.py in usb-power-switch) ----------

def load_grid(path):
    g = np.load(path)
    z, x0, y0, c = g["merged"], float(g["x0"]), float(g["y0"]), float(g["cell"])
    wx0, wx1, wy0, wy1 = -15.0, 165.0, -15.0, 115.0
    i0, i1 = int((wx0 + ANCHOR[0] - x0) / c), int((wx1 + ANCHOR[0] - x0) / c)
    j0, j1 = int((wy0 + ANCHOR[1] - y0) / c), int((wy1 + ANCHOR[1] - y0) / c)
    sub = np.full((j1 - j0, i1 - i0), np.nan)
    a, b = max(j0, 0), min(j1, z.shape[0])
    p, q = max(i0, 0), min(i1, z.shape[1])
    sub[a - j0:b - j0, p - i0:q - i0] = z[a:b, p:q]
    return sub, x0 + i0 * c - ANCHOR[0], y0 + j0 * c - ANCHOR[1], c


def classify(z, ox, oy, c):
    """Blank level and what isn't blank. A cut-out reads LOW: a cell counts when over 30 % of the cells
    measured within about 2 mm are more than LEVEL_TOL below the blank. High readings count only as a
    solid object at least 2 mm across and 1.5 mm up: with one camera (2026-11-11) laser glints on the
    scratched copper read high in streaks. Anything a kerf encloses (a board left in its tabs) is filled in."""
    ny, nx = z.shape
    X = ox + (np.arange(nx) + 0.5) * c
    Y = oy + (np.arange(ny) + 0.5) * c
    inside = (Y[:, None] > POCKET[2] + 2) & (Y[:, None] < POCKET[3] - 2) & (X[None, :] > POCKET[0] + 2) & (X[None, :] < POCKET[1] - 2)
    v = z[inside & np.isfinite(z)]
    hist, edges = np.histogram(v, bins=np.arange(np.floor(v.min()), np.ceil(v.max()) + 0.1, 0.1))
    level = float(edges[np.argmax(hist)] + 0.05)
    level = float(np.median(v[np.abs(v - level) < LEVEL_TOL]))
    fin = np.isfinite(z)
    low = fin & (z < level - LEVEL_TOL)
    k = int(round(2.2 / c)) | 1
    measured = ndimage.uniform_filter(fin.astype(float), k)
    cut = (measured > 0.05) & (ndimage.uniform_filter(low.astype(float), k) / np.maximum(measured, 1e-6) > 0.3)
    r = int(round(1.0 / c))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    high = ndimage.binary_opening(fin & (z > level + 1.5), structure=(xx ** 2 + yy ** 2) <= r * r)
    cut = ndimage.binary_closing(cut | high, iterations=3)
    cut = ndimage.binary_fill_holes(cut) & inside
    lab, n = ndimage.label(cut)
    sizes = ndimage.sum(cut, lab, range(1, n + 1))
    cutouts = []
    for k, s in enumerate(sizes, 1):
        if s * c * c < 4:
            cut[lab == k] = False
            continue
        jj, ii = np.nonzero(lab == k)
        zz = z[lab == k]
        zz = zz[np.isfinite(zz) & (zz < level - 1.0)]
        floor = float(np.median(zz)) if zz.size > 50 else float("nan")
        cutouts.append({"x0": round(ox + ii.min() * c, 1), "x1": round(ox + (ii.max() + 1) * c, 1),
                        "y0": round(oy + jj.min() * c, 1), "y1": round(oy + (jj.max() + 1) * c, 1),
                        "area_mm2": round(float(s * c * c)), "below_blank": round(level - floor, 2), "label": k})
    return level, cut, lab, cutouts


def footprint(paths, angle):
    """Both boards and the probe grid's box, plus the cutter, turned about the pair origin."""
    W, L = paths["W"], paths["L"]
    b = box(-(W + GAP / 2), 0, W + GAP / 2, L).buffer(OUTLINE["dia"], join_style="round")
    return affinity.rotate(b, angle, origin=(0, 0))


def place(paths, z, ox, oy, c):
    level, cut, lab, cutouts = classify(z, ox, oy, c)
    r = int(round(MARGIN / c))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    keep = ndimage.binary_dilation(cut, structure=(xx ** 2 + yy ** 2) <= r * r)
    # unmeasured patches 2 mm or more across could hide a kerf: treat them as obstacles too. Small
    # dropouts on the shiny copper (coverage runs 73-92 % over bare blank, 2026-11-11) don't count.
    g = int(round(1.0 / c))
    gy, gx = np.mgrid[-g:g + 1, -g:g + 1]
    keep |= ndimage.binary_opening(~np.isfinite(z), structure=(gx ** 2 + gy ** 2) <= g * g)
    best = None
    for angle in (0, 90, 180, 270):
        fp = footprint(paths, angle)
        fx0, fy0, fx1, fy1 = fp.bounds
        ii = np.arange(int(np.floor(fx0 / c)), int(np.ceil(fx1 / c)) + 1)
        jj = np.arange(int(np.floor(fy0 / c)), int(np.ceil(fy1 / c)) + 1)
        gx, gy = np.meshgrid((ii + 0.5) * c, (jj + 0.5) * c)
        m = contains_xy(fp, gx, gy)
        for px in np.arange(POCKET[0] + WALL_CLEAR - fx0, POCKET[1] - WALL_CLEAR - fx1 + 1e-9, 1.0):
            for py in np.arange(POCKET[2] + WALL_CLEAR - fy0, POCKET[3] - WALL_CLEAR - fy1 + 1e-9, 1.0):
                ci = ((px + (ii + 0.5) * c - ox) / c).astype(int)
                cj = ((py + (jj + 0.5) * c - oy) / c).astype(int)
                if keep[np.ix_(cj, ci)][m].any():
                    continue
                cover = np.isfinite(z[np.ix_(cj, ci)][m]).mean()
                if cover < MIN_COVER:
                    continue
                # pack toward the front-right corner (X high, Y low): keeps the big free area in one piece
                score = (POCKET[1] - (px + fx1)) + (py + fy0 - POCKET[2])
                if best is None or score < best[0]:
                    best = (score, px, py, angle, cover)
    if best is None:
        sys.exit("no room for the two boards on this blank")
    _, px, py, angle, cover = best
    return {"x": float(px), "y": float(py), "angle": angle, "coverage": round(float(cover), 3)}, level, cut, lab, cutouts


def w_pt(p, pl):
    a = math.radians(pl["angle"])
    return (pl["x"] + math.cos(a) * p[0] - math.sin(a) * p[1], pl["y"] + math.sin(a) * p[0] + math.cos(a) * p[1])


def floor_spots(centre, z, ox, oy, c, cut, lab, cutouts):
    d = ndimage.distance_transform_edt(cut) * c
    X = ox + (np.arange(cut.shape[1]) + 0.5) * c
    spots = []
    big = [q for q in cutouts if q["area_mm2"] > 100]
    for co in sorted(big, key=lambda q: np.hypot((q["x0"] + q["x1"]) / 2 - centre[0], (q["y0"] + q["y1"]) / 2 - centre[1]))[:2]:
        dd = np.where((lab == co["label"]) & (X[None, :] >= FLOOR_X_MIN), d, 0)
        j, i = np.unravel_index(np.argmax(dd), dd.shape)
        if dd[j, i] >= PROBE_BALL:
            spots.append([round(float(ox + (i + 0.5) * c), 2), round(float(oy + (j + 0.5) * c), 2)])
    return spots


def picture(z, ox, oy, c, level, job, pl, floors, path, title, zoom=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ny, nx = z.shape
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    ax.imshow(z - level, origin="lower", extent=[ox, ox + nx * c, oy, oy + ny * c], cmap="gray", vmin=-2.5, vmax=0.8)
    ax.add_patch(plt.Rectangle((POCKET[0], POCKET[2]), POCKET[1], POCKET[3], fill=False, ec="#ff4040", lw=1.2))
    for o in job["board"]["outlines"]:
        q = np.array([w_pt(p, pl) for p in o])
        ax.fill(q[:, 0], q[:, 1], color="#20c060", alpha=0.75)
    for loop in job["outline"]["loops"]:
        for pc in loop["pieces"]:
            q = np.array([w_pt(p, pl) for p in pc["pts"]])
            ax.plot(q[:, 0], q[:, 1], color="#ff7f11" if pc["tab"] else "#ffd166", lw=3.5 if pc["tab"] else 1.2)
    for p in job["probe"]:
        x, y = w_pt(p, pl)
        ax.plot(x, y, "x", color="magenta", ms=10 if zoom else 8, mew=2.5)
    for x, y in floors:
        ax.plot(x, y, "+", color="cyan", ms=16, mew=3)
        ax.add_patch(plt.Circle((x, y), PROBE_BALL, fill=False, ec="cyan", lw=1))
    if zoom:
        xs = [w_pt(p, pl)[0] for o in job["board"]["outlines"] for p in o] + [f[0] for f in floors]
        ys = [w_pt(p, pl)[1] for o in job["board"]["outlines"] for p in o] + [f[1] for f in floors]
        ax.set_xlim(min(xs) - 8, max(xs) + 8)
        ax.set_ylim(min(ys) - 8, max(ys) + 8)
    else:
        ax.set_xlim(ox, ox + nx * c)
        ax.set_ylim(oy, oy + ny * c)
    ax.set_xlabel("work X, mm")
    ax.set_ylabel("work Y, mm")
    ax.set_title(title, fontsize=10)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def length(paths):
    return sum(LineString(p).length for p in paths if len(p) > 1)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    grid, scan = sys.argv[1], sys.argv[2]
    paths = build_paths()
    z, ox, oy, c = load_grid(grid)
    W, L = paths["W"], paths["L"]
    probe = [[x, y] for y in (1.0, L / 2, L - 1.0) for x in (-(W + GAP / 2) + 1.0, 0.0, W + GAP / 2 - 1.0)]
    job = {"board": {"name": "two Nezha header (pin) plug tails, rev C", "outlines": paths["outlines"],
                     "pair_box": [-(W + GAP / 2), 0, W + GAP / 2, L]},
           "isolate": dict(ISO, paths=paths["iso"]), "clear": dict(CLR, paths=paths["clear"]),
           "outline": dict(OUTLINE, fr4=FR4, loops=paths["loops"]),
           "probe": probe, "travel": TRAVEL}
    pl, level, cut, lab, cutouts = place(paths, z, ox, oy, c)
    floors = floor_spots(w_pt([0, L / 2], pl), z, ox, oy, c, cut, lab, cutouts)
    deep = [co["below_blank"] for co in cutouts if np.isfinite(co["below_blank"]) and co["area_mm2"] > 100]
    stack = float(np.median(deep)) if deep else 1.7
    passes = math.ceil((FR4 + 0.3 + OUTLINE["below"]) / OUTLINE["step"])
    est = {"isolate_s": round(length(paths["iso"]) / ISO["feed"] * 60 + len(paths["iso"]) * 2),
           "clear_s": round(length(paths["clear"]) / CLR["feed"] * 60 + len(paths["clear"]) * 2),
           "outline_s": round(sum(lp["length"] for lp in paths["loops"]) * passes / OUTLINE["feed"] * 60)}
    job.update({"place": {k: pl[k] for k in ("x", "y", "angle")}, "scan": scan, "floor_spots": floors,
                "stack": round(stack, 2), "expect_floor_mz": FLOOR_MZ, "expect_top_mz": round(FLOOR_MZ + stack, 2),
                "estimate": est, "source": "gears pcb/plug-tail (make_cam.plan, mill_job.py)"})
    # every cut must stay on the footprint the scan cleared
    fp = affinity.translate(footprint(paths, pl["angle"]), pl["x"], pl["y"])
    for key in ("isolate", "clear"):
        for p in job[key]["paths"]:
            for q in p:
                assert fp.covers(Point(w_pt(q, pl))), (key, q)
    os.makedirs(OUT, exist_ok=True)
    rec = {"scan": scan, "blank_level_above_bed": round(level, 2),
           "cutouts_work_mm": [{k: v for k, v in co.items() if k != "label"} for co in cutouts],
           "placed": {"boards": "2 x header-tail", **pl}, "floor_spots": floors}
    with open(os.path.join(OUT, "blank_%s.json" % scan), "w") as f:
        json.dump(rec, f, indent=1)
    with open(os.path.join(OUT, "mill_plug_tails.json"), "w") as f:
        json.dump(job, f)
    title = ("Scan %s. Grey: blank, dark: cut away. Green: the two boards (yellow outline, orange tabs).\n"
             "Magenta x: 9 touches on the PCB top. Cyan +: touches on the jig floor (circle: probe ball room)." % scan)
    picture(z, ox, oy, c, level, job, pl, floors, os.path.join(OUT, "mill_plug_tails.png"), title)
    picture(z, ox, oy, c, level, job, pl, floors, os.path.join(OUT, "mill_plug_tails_zoom.png"), title, zoom=True)
    print("blank level %.2f (scan), stack above floor %.2f, %d cut-outs" % (level, stack, len(cutouts)))
    for co in cutouts:
        print("   cut-out X %(x0).1f-%(x1).1f  Y %(y0).1f-%(y1).1f  %(area_mm2)d mm2  %(below_blank).2f below" % co)
    print("pair at work X %.1f Y %.1f, turned %d, scan coverage %.0f%%" % (pl["x"], pl["y"], pl["angle"], 100 * pl["coverage"]))
    print("floor touches", floors, "expect top %.2f floor %.2f (probe machine Z)" % (job["expect_top_mz"], FLOOR_MZ))
    print("T4 %d paths %.0f mm, T3 %d paths %.0f mm, T5 2 loops; estimate %s, %.0f min"
          % (len(paths["iso"]), length(paths["iso"]), len(paths["clear"]), length(paths["clear"]), est, sum(est.values()) / 60))


if __name__ == "__main__":
    main()
