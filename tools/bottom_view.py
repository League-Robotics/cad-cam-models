#!/usr/bin/env python3
"""2D line drawing of a part seen from below: outlines sliced at several
heights, the 8 mm cell grid with labels, and the sensor's outline for reference.

    bottom_view.py PART.stl OUT.svg
"""
import sys
import numpy as np
import trimesh

stl, out = sys.argv[1:3]
m = trimesh.load(stl)
S = 8.0          # px per mm
U = 8            # cell size, mm
# levels: (z, stroke, width, dash, label)
levels = [(14, "#5b3fd0", 1.6, "", "deck (z 10-18)"),
          (7, "#d0402f", 1.6, "", "middle stubs (z 5.2-10)"),
          (3.5, "#1f7a3a", 1.8, "", "wing columns (z 2.2-10)"),
          (1, "#c77700", 2.2, "", "feet (to PCB, z 0)")]
lo, hi = m.bounds[0][:2] - 12, m.bounds[1][:2] + 12
W, H = (hi - lo) * S
# seen from below: x mirrored; robot (+Y) at the top
def px(x, y): return ((hi[0] - x) * S, (hi[1] - y) * S)

def polys(z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None: return []
    res = []
    for e in s.discrete:
        res.append(np.asarray(e)[:, :2])
    return res

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H + 120:.0f}" '
       f'viewBox="0 0 {W:.0f} {H + 120:.0f}" font-family="Helvetica, Arial" font-size="11">',
       f'<rect width="100%" height="100%" fill="white"/>']
# grid + labels
i0, i1 = int(np.floor(lo[0] / U)), int(np.ceil(hi[0] / U))
j0, j1 = int(np.floor(lo[1] / U)), int(np.ceil(hi[1] / U))
for i in range(i0, i1 + 1):
    x, _ = px(i * U - U / 2, 0)
    svg.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{H:.1f}" stroke="#e4e4e4"/>')
for j in range(j0, j1 + 1):
    _, y = px(0, j * U - U / 2)
    svg.append(f'<line x1="0" y1="{y:.1f}" x2="{W:.1f}" y2="{y:.1f}" stroke="#e4e4e4"/>')
for i in range(i0, i1 + 1):
    x, _ = px(i * U, 0)
    svg.append(f'<text x="{x:.1f}" y="12" text-anchor="middle" fill="#888">x{i * U:+d}</text>')
for j in range(j0, j1 + 1):
    _, y = px(0, j * U)
    svg.append(f'<text x="4" y="{y + 4:.1f}" fill="#888">y{j * U:+d}</text>')
# sensor outline (dashed): PCB, brackets, jack
def rect(x0, y0, x1, y1, col, dash):
    a, b = px(x1, y1); c, d = px(x0, y0)
    return f'<rect x="{a:.1f}" y="{b:.1f}" width="{c - a:.1f}" height="{d - b:.1f}" fill="none" stroke="{col}" stroke-dasharray="{dash}"/>'
svg.append(rect(-36, -28.4, 36, -3.1, "#4aa3df", "6 4"))
svg.append(rect(-12, -3.1, 12, 19.4, "#4aa3df", "6 4"))
for s_ in (-1, 1):
    svg.append(rect(s_ * 24 - 12, -9.4, s_ * 24 + 12, 3.4, "#999", "3 3"))
svg.append(rect(-12, 5.6, 12, 19.4, "#999", "3 3"))
svg.append(rect(-5, 5.2, 5.4, 17.6, "#2f5fd0", "2 2"))
# part outlines
for z, col, w, dash, _ in levels:
    for p in polys(z):
        d = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in (px(*q) for q in p)) + " Z"
        svg.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}"/>')
# legend
y = H + 18
svg.append(f'<text x="8" y="{y}" font-weight="bold">Gripper plate, seen from BELOW (x mirrored). Robot side at top. Grid = 8 mm cells, labels are cell centres (mm).</text>')
for k, (z, col, w, dash, lab) in enumerate(levels):
    yy = y + 20 + 16 * k
    svg.append(f'<line x1="10" y1="{yy - 4}" x2="40" y2="{yy - 4}" stroke="{col}" stroke-width="{w}"/><text x="48" y="{yy}">{lab}</text>')
svg.append(f'<line x1="320" y1="{y + 16}" x2="350" y2="{y + 16}" stroke="#4aa3df" stroke-dasharray="6 4"/><text x="358" y="{y + 20}">sensor PCB</text>')
svg.append(f'<line x1="320" y1="{y + 32}" x2="350" y2="{y + 32}" stroke="#999" stroke-dasharray="3 3"/><text x="358" y="{y + 36}">brackets</text>')
svg.append(f'<line x1="320" y1="{y + 48}" x2="350" y2="{y + 48}" stroke="#2f5fd0" stroke-dasharray="2 2"/><text x="358" y="{y + 52}">RJ11 jack/plug</text>')
svg.append('</svg>')
open(out, "w").write("\n".join(svg))
print(out)
