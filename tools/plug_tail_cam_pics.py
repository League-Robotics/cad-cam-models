#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "shapely"]
# ///
"""Drawings of the plug-tail Carvera program (pcb/plug-tail/cam), read back from the NC itself.

    uv run tools/plug_tail_cam_pics.py   ->  view/plug_tail_cam.html

Strip layout on the stock, then each board's toolpaths: T4 V-bit (dark), T3 1 mm flat (green), T5 outline (orange,
tabs red), over the copper the program leaves. Also the assembly sheet from check_and_draw.py and the job numbers.
"""
import base64
import io
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PT = ROOT / 'pcb' / 'plug-tail'
OUT = ROOT / 'view' / 'plug_tail_cam.html'
JOB = json.loads((PT / 'cam' / 'job.json').read_text())
GEO = json.loads((PT / 'checks' / 'geometry.json').read_text())
VAL = json.loads((PT / 'cam' / 'validation.json').read_text())
NC = PT / 'cam' / JOB['program']
TV, TF, TO = (JOB['tools'][k]['slot'] for k in ('v', 'flat', 'outline'))
C = {'fr4': '#e8dcc0', 'cu': '#d4823a', 'v': '#2b2118', 'flat': '#2e9a4a', 'out': '#ff8c1a', 'tab': '#d0102a'}


def runs():
    """{(board, tool): [[(x, y, z), ...] per cutting run]} in machine coordinates."""
    out, board, tool, pos, cur = {}, None, None, [0.0, 0.0, 5.0], None
    for line in NC.read_text().splitlines():
        if m := re.match(r'\(BOARD (\d+)', line): board = int(m[1])
        if m := re.search(r'M6 T(\d)', line): tool = int(m[1])
        if not line.startswith(('G0', 'G1')): continue
        w = dict(re.findall(r'([XYZ])(-?[\d.]+)', line))
        new = [float(w.get(k, pos[i])) for i, k in enumerate('XYZ')]
        if line.startswith('G0') or new[2] >= 0:
            cur = None
        elif board:
            if cur is None:
                cur = [tuple(pos)]; out.setdefault((board, tool), []).append(cur)
            cur.append(tuple(new))
        pos = new
    return out


R = runs()


def outline(b):
    W, L = GEO[b['name']]['board_mm'][:2]
    return Polygon([(b['x'] + W / 2 + x, b['y'] + L - y) for x, y in GEO[b['name']]['outline']])


def swept(bid, tool, r):
    return unary_union([LineString([p[:2] for p in run]).buffer(r, quad_segs=12) for run in R.get((bid, tool), []) if len(run) > 1])


def fill(ax, g, **kw):
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty: continue
        ax.fill(*p.exterior.xy, **kw)
        for i in p.interiors: ax.fill(*i.xy, color=C['fr4'], lw=0)


def draw_board(ax, b, paths=True):
    o = outline(b)
    v = swept(b['id'], TV, JOB['tools']['v']['effective_diameter_mm'] / 2)
    f = swept(b['id'], TF, JOB['tools']['flat']['diameter_mm'] / 2)
    fill(ax, o, color=C['fr4'], lw=0)
    fill(ax, o.difference(v).difference(f), color=C['cu'], lw=0)
    if not paths:
        ax.plot(*o.exterior.xy, color='#29383a', lw=.6); return
    for run in R.get((b['id'], TF), []):
        ax.plot([p[0] for p in run], [p[1] for p in run], color=C['flat'], lw=.9)
    for run in R.get((b['id'], TV), []):
        ax.plot([p[0] for p in run], [p[1] for p in run], color=C['v'], lw=.35)
    for run in R.get((b['id'], TO), []):
        deep = min(p[2] for p in run)
        if deep > JOB['through_z_mm'] + 1e-6: continue
        ax.plot([p[0] for p in run], [p[1] for p in run], color=C['out'], lw=1.6, alpha=.8)
        for a, c in zip(run, run[1:]):
            if abs(a[2] - JOB['tabs']['z_mm']) < 1e-6 and abs(c[2] - JOB['tabs']['z_mm']) < 1e-6:
                ax.plot([a[0], c[0]], [a[1], c[1]], color=C['tab'], lw=3.2, solid_capstyle='butt')
    ax.plot(*o.exterior.xy, color='#29383a', lw=.6, ls=':')


def svg(fig):
    buf = io.StringIO(); fig.savefig(buf, format='svg', bbox_inches='tight'); plt.close(fig)
    return img(buf.getvalue())


def img(svg_text):
    """Each drawing as its own <img>: inline matplotlib SVGs share glyph ids and garble each other's text."""
    return '<img alt="" style="max-width:100%" src="data:image/svg+xml;base64,' + base64.b64encode(svg_text.encode()).decode() + '">'


def legend(ax):
    from matplotlib.lines import Line2D
    h = [Rectangle((0, 0), 1, 1, color=C['cu']), Rectangle((0, 0), 1, 1, color=C['fr4']),
         Line2D([], [], color=C['v'], lw=1), Line2D([], [], color=C['flat'], lw=1.5),
         Line2D([], [], color=C['out'], lw=2), Line2D([], [], color=C['tab'], lw=3.5)]
    ax.legend(h, ['copper left (pads and tracks)', 'bare FR-4, copper cleared', f'T{TV} V-bit path (Z{JOB["tools"]["v"]["z_mm"]})',
                  f'T{TF} 1 mm flat path (Z{JOB["tools"]["flat"]["z_mm"]})', f'T{TO} 0.8 corn outline (Z{JOB["through_z_mm"]})',
                  f'tab, {JOB["tabs"]["remaining_mm"]} mm left'], loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)


# 1. the strip on the stock
A = JOB['area_mm']
fig, ax = plt.subplots(figsize=(9.5, 5.6))
ax.add_patch(Rectangle((0, 0), *A, fill=False, edgecolor='#192a2e', lw=1.4, ls='--'))
for b in JOB['placements']:
    draw_board(ax, b, paths=False)
    W = GEO[b['name']]['board_mm'][0]
    ax.text(b['x'] + W / 2, b['y'] - 1.4, f"{b['id']}  {b['name'].replace('-', ' ')}", ha='center', va='top', fontsize=8)
ax.plot(0, 0, 'ko', ms=5); ax.annotate('G54 X0 Y0\n(lower-left of the free area)', (0, 0), (1.2, -5.5), fontsize=8)
ax.annotate('', (A[0] + 1.2, A[1] - 2), (A[0] + 1.2, A[1] - 9), arrowprops=dict(arrowstyle='->'))
ax.text(A[0] + 1.8, A[1] - 5.5, 'tongues\npoint +Y', fontsize=8, va='center')
ax.set_aspect('equal'); ax.set_xlim(-2, A[0] + 9); ax.set_ylim(-7, A[1] + 2); ax.grid(alpha=.18)
ax.set_xticks(range(0, int(A[0]) + 1, 5)); ax.set_yticks(range(0, int(A[1]) + 1, 5))
ax.set_title(f'Strip: {A[0]:.0f} x {A[1]:.0f} mm of 1.4 mm stock, copper up, nothing mirrored (mm)', fontsize=10)
strip = svg(fig)

# 2. each board's toolpaths
boards = {}
for bid in (1, 3):
    b = next(p for p in JOB['placements'] if p['id'] == bid); W, L = GEO[b['name']]['board_mm'][:2]
    fig, ax = plt.subplots(figsize=(7.2, 8.2))
    draw_board(ax, b); legend(ax)
    ax.set_aspect('equal'); ax.set_xlim(b['x'] - 1.5, b['x'] + W + 1.5); ax.set_ylim(b['y'] - 1.5, b['y'] + L + 1.5)
    ax.set_xticks([x for x in range(int(b['x'] - 1), int(b['x'] + W + 2))]); ax.set_yticks(range(int(b['y'] - 1), int(b['y'] + L + 2)))
    ax.tick_params(labelsize=6); ax.grid(alpha=.25, lw=.4)
    ax.set_title(f"Board {bid}: {b['name'].replace('-', ' ')} {W:g} x {L:g} mm, tongue at the top (machine mm, 1 mm grid)", fontsize=9)
    boards[b['name']] = svg(fig)

asm = img((PT / 'exports' / 'assembly-preview.svg').read_text())
pm = JOB['path_mm']; ck = JOB['clearing_checks']
rows = ''.join(f"<tr><td>{n.replace('-', ' ')}</td><td>{pm[n]['v_iso']:.0f} + {pm[n]['v_rest']:.0f}</td><td>{pm[n]['flat']:.0f}</td>"
               f"<td>{ck[n]['floating_copper_bits']}</td><td>{ck[n]['inside_corner_fillets']} (each &le; {ck[n]['largest_fillet_mm2']} mm&sup2;)</td></tr>" for n in pm)
vb = {b['name']: b for b in VAL['boards'].values()}
cu = ''.join(f"<tr><td>{n.replace('-', ' ')}</td><td>{vb[n]['cad_copper_mm2']}</td><td>{vb[n]['copper_left_mm2']}</td></tr>" for n in vb if True)
checks = ''.join(f'<li>{c}</li>' for c in VAL['checks'])
html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plug tail CAM</title><style>
body{{font:15px/1.45 -apple-system,system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px;color:#1d2427;background:#f6f4ef}}
h1{{font-size:22px}} h2{{font-size:17px;margin-top:28px;border-bottom:1px solid #ccc}} svg{{max-width:100%;height:auto}}
table{{border-collapse:collapse;margin:8px 0}} td,th{{border:1px solid #ccc;padding:3px 8px;text-align:left}} th{{background:#ebe6da}}
.pair{{display:flex;flex-wrap:wrap;gap:12px}} .pair>div{{flex:1 1 480px}} code{{background:#ebe6da;padding:0 3px}}
.new{{background:#fff4d6;border-left:4px solid #e0a400;padding:8px 12px}}</style></head><body>
<h1>Nezha 4P4C plug tails, rev C: Carvera program with all spare copper cleared</h1>
<p>Program <code>pcb/plug-tail/cam/{JOB['program']}</code>: 2 header tails + 2 Qwiic tails.
3D mock: <a href="plug_tail.html">plug_tail.html</a>. For approval before cutting.</p>
<div class="new"><b>What changed from the last program</b>
<ul><li><b>Vacuum:</b> <code>M851 S100</code> right after every <code>M3</code>, <code>M852</code> right after every <code>M5</code> (each tool change and the end).</li>
<li><b>All copper that isn't a pad or a track comes off.</b> The old program only cut isolation lines and left the rest floating.</li>
<li><b>Tool numbers follow the standard buildout:</b> T{TV} V-bit, T{TF} 1 mm flat, T{TO} 0.8 corn. The old one called the V-bit T2 and the corn T3; T2 is now the O-flute.</li>
<li>Stock 1.4 mm, as you confirmed. Board shapes, pads and tabs unchanged.</li></ul></div>

<h2>Setup</h2>
<table><tr><th>Stock</th><td>1.4 mm single-sided, copper up, flat on the backer with full-area tape. Free area at least {A[0]:.0f} x {A[1]:.0f} mm.</td></tr>
<tr><th>Origin</th><td>G54 X0 Y0 at the lower-left of the free area; Z0 on the copper. Tongues point +Y.</td></tr>
<tr><th>Probe</th><td>Auto Z, then Auto Leveling over about X2..51 Y2..28 (e.g. 6 x 4 points, 2 mm lift).</td></tr>
<tr><th>OP1 T{TV}</th><td>30&deg; V-bit, 0.2 tip, Z{JOB['tools']['v']['z_mm']} (cuts {JOB['tools']['v']['effective_diameter_mm']} wide): two passes round every pad and track, then the gaps too narrow for the flat.</td></tr>
<tr><th>OP2 T{TF}</th><td>1.0 mm flat end mill, Z{JOB['tools']['flat']['z_mm']}, stepover {JOB['tools']['flat']['stepover_mm']}: clears the open copper; its edge stays {JOB['tools']['flat']['edge_to_copper_mm']} mm from any pad or track.</td></tr>
<tr><th>OP3 T{TO}</th><td>0.8 mm corn cutter: outlines to Z{JOB['through_z_mm']} in {JOB['stepdown_mm']} mm steps, three {JOB['tabs']['width_mm']} mm tabs a board leaving {JOB['tabs']['remaining_mm']} mm, none on the tongue.</td></tr>
<tr><th>Feeds</th><td>{JOB['feeds']['rpm']} rpm, {JOB['feeds']['feed_mm_min']} mm/min, plunge {JOB['feeds']['plunge_mm_min']}. Rapids at Z{JOB['safe_z_mm']:g}.</td></tr>
<tr><th>Time</th><td>About {VAL['motion_minutes']:.0f} min of motion, plus probing and two tool changes (the old isolation-only program was about 11).</td></tr></table>

<h2>1. Strip on the stock</h2>{strip}
<h2>2. Header tail toolpaths (board 1; board 2 is the same)</h2>{boards['header-tail']}
<h2>3. Qwiic tail toolpaths (board 3; board 4 is the same)</h2>{boards['qwiic-tail']}

<h2>Copper check (replayed from the program on Buzzkill)</h2>
<table><tr><th>Board</th><th>Copper in KiCad, mm&sup2;</th><th>Copper left after milling, mm&sup2;</th></tr>{cu}</table>
<table><tr><th>Board</th><th>V-bit path, mm (round copper + gaps)</th><th>Flat path, mm</th><th>Loose copper bits</th><th>Inside-corner fillets</th></tr>{rows}</table>
<p>The fillets are the bits the round cutter can't reach where a track meets a pad. They stay attached to that pad, so they aren't loose copper.</p>
<ul>{checks}</ul><p><i>{VAL['limits']}</i></p>

<h2>4. Assembly (unchanged)</h2>{asm}
</body></html>"""
OUT.write_text(html)
print(OUT)
