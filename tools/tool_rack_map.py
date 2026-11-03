#!/usr/bin/env python3
"""Draw the Carvera bit racks as labelled diagrams, with the standard
buildout's tools (T1-T6) highlighted, from carvera/tool_racks.json.

    python3 tools/tool_rack_map.py   ->  view/tool_racks.html (local) and
                                         carvera/tool_racks_artifact.html (published as the
                                         "Carvera Bit Racks" claude.ai artifact)

Each rack is drawn as photographed: horizontal slots 1-12 down the left
(caps to the right), vertical pairs A B (top) and C D (bottom) on the right.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "carvera" / "tool_racks.json"
OUT = ROOT / "view" / "tool_racks.html"
ART = ROOT / "carvera" / "tool_racks_artifact.html"   # same page without the document skeleton, for the claude.ai artifact

# Rack geometry, SVG units.
W, H = 620, 1010
LX0, LX1 = 18, 402            # left column
SH, SG = 64, 8                # slot height, gap
TOP0 = 18
BOT0 = TOP0 + 6 * SH + 5 * SG + 124
RX = [420, 518]               # right column slot x
RW = 84
CAP = 62                      # cap length


def esc(s):
    return html.escape(str(s), quote=True)


def labels(s):
    """(big line, small line) for a slot."""
    k = s["kind"]
    size = f"Ø{s.get('d')} × {s.get('l')}"
    return {
        "oflute": (size, "O-flute, 1 flute"),
        "ball": (size, "ball nose, 2 flute"),
        "corn": (size, "corn cutter"),
        "drill": (size, "drill"),
        "thread": (s.get("m", ""), f"thread mill Ø{s.get('d')} × {s.get('l')}"),
        "chamfer": (f"{s.get('a')}°", "chamfer"),
        "vbit": (f"{s.get('a')}° · {s.get('tip')} tip", "engraving V, 1 flute"),
        "uv": ("UV mask", "solder-mask removal"),
        "loose": ("loose bit", s.get("note", "")),
    }[k]


def darken(hexc, f=0.72):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def slot_svg(rack, key, s, x, y, w, h, vertical):
    rid = rack["id"]
    recess = f'<rect class="recess" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{darken(rack["plate"])}"/>'
    if s is None:
        cx, cy = x + w / 2, y + h / 2
        rot = f' transform="rotate(-90 {cx} {cy})"' if vertical else ""
        return (f'<g class="slot empty" data-text="empty {key}">{recess}'
                f'<text class="empty-t" x="{cx}" y="{cy + 7}" text-anchor="middle"{rot}>{key} · empty</text></g>')
    build = s.get("build", "")
    spare = s.get("spare", "")
    drawer = s.get("drawer", "")
    big, small = labels(s)
    cls = "slot" + (" build" if build else "") + (" spare" if spare else "") + (" drawer" if drawer else "")
    text = " ".join([big, small, s["kind"], build or spare, drawer, key, rack["name"]]).lower()
    parts = [f'<g class="{cls}" data-build="{build}" data-spare="{spare}" data-text="{esc(text)}" data-rack="{rid}">', recess]
    i = 5  # case inset
    cx, cy, cw, ch = x + i, y + i, w - 2 * i, h - 2 * i
    if s["kind"] == "loose":
        parts.append(f'<rect class="case loose" x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="4"/>')
    else:
        parts.append(f'<rect class="case" x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="4"/>')
        cap = s.get("cap", "#999")
        n = 5
        if vertical:
            for j in range(n):
                parts.append(f'<rect x="{cx}" y="{cy + j * CAP / n}" width="{cw}" height="{CAP / n - 3}" fill="{cap}"/>')
        else:
            for j in range(n):
                parts.append(f'<rect x="{cx + cw - CAP + j * CAP / n}" y="{cy}" width="{CAP / n - 3}" height="{ch}" fill="{cap}"/>')
    parts.append(f'<rect class="outline" x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="4"/>')
    if vertical:
        # Text reads bottom to top, centred on the case below the cap.
        mx, my = cx + cw / 2, cy + CAP + (ch - CAP) / 2
        parts.append(f'<g transform="rotate(-90 {mx} {my})">'
                     f'<text class="key" x="{mx - (ch - CAP) / 2 + 12}" y="{my - 12}">{key}</text>'
                     f'<text class="big" x="{mx - (ch - CAP) / 2 + 52}" y="{my - 2}">{esc(big)}</text>'
                     f'<text class="small" x="{mx - (ch - CAP) / 2 + 52}" y="{my + 24}">{esc(small)}</text></g>')
        bx, by = cx + cw / 2, cy + CAP / 2
    else:
        parts.append(f'<text class="key" x="{cx + 10}" y="{cy + 22}">{key}</text>'
                     f'<text class="big" x="{cx + 50}" y="{cy + 27}">{esc(big)}</text>'
                     f'<text class="small" x="{cx + 50}" y="{cy + 46}">{esc(small)}</text>')
        bx, by = cx + cw - CAP / 2, cy + ch / 2
    if build:
        parts.append(f'<g class="badge"><rect x="{bx - 34}" y="{by - 22}" width="68" height="44" rx="8"/>'
                     f'<text x="{bx}" y="{by + 10}" text-anchor="middle">{build}</text></g>')
    elif spare or drawer:
        t = "spare" if spare else ("T4 alt" if drawer.startswith("T4") else "drawer")
        parts.append(f'<g class="dtag"><rect x="{bx - 38}" y="{by - 15}" width="76" height="30" rx="6"/>'
                     f'<text x="{bx}" y="{by + 6}" text-anchor="middle">{t}</text></g>')
    parts.append("</g>")
    return "".join(parts)


def rack_svg(rack):
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(rack["name"])} rack">',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="{rack["plate"]}"/>']
    sl = rack["slots"]
    for n in range(12):
        y = (TOP0 if n < 6 else BOT0) + (n % 6) * (SH + SG)
        p.append(slot_svg(rack, str(n + 1), sl.get(str(n + 1)), LX0, y, LX1 - LX0, SH, False))
    th = 6 * SH + 5 * SG
    for key, x, y in (("A", RX[0], TOP0), ("B", RX[1], TOP0), ("C", RX[0], BOT0), ("D", RX[1], BOT0)):
        p.append(slot_svg(rack, key, sl.get(key), x, y, RW, th, True))
    # Handle(s) in the middle band.
    my = TOP0 + th + (BOT0 - TOP0 - th) / 2
    dark = darken(rack["plate"], 0.8)
    if rack["handle"] == "round":
        p.append(f'<circle cx="{(LX1 + RX[0]) / 2 + 40}" cy="{my}" r="44" fill="{rack["plate"]}" stroke="{dark}" stroke-width="5"/>'
                 f'<circle cx="{(LX1 + RX[0]) / 2 + 40}" cy="{my}" r="30" fill="none" stroke="{dark}" stroke-width="2"/>')
    else:
        p.append(f'<rect x="{LX0 + 4}" y="{my - 34}" width="{LX1 - LX0 - 8}" height="68" rx="4" fill="{dark}"/>'
                 f'<rect x="{RX[0]}" y="{my - 34}" width="{RX[1] + RW - RX[0]}" height="68" rx="4" fill="{dark}"/>'
                 f'<rect x="{LX0 + 150}" y="{my - 40}" width="110" height="80" rx="4" fill="{rack["plate"]}" stroke="#1d7a25" stroke-width="3"/>'
                 f'<rect x="{RX[0] + 60}" y="{my - 40}" width="80" height="80" rx="4" fill="{rack["plate"]}" stroke="#1d7a25" stroke-width="3"/>')
    p.append("</svg>")
    return "".join(p)


NOTES = {
    "T1": "Orange 7, with a spare in 8. T1 has been in the machine since 2026-10-30; if it is still in there, that is a third. The drawer list wants 2–3 spares.",
    "T2": "Ø3.175 × 12 fits the 12–17 mm flute spec. Longer O-flutes if you need reach: Orange B (×25), Orange C, D (×42), Green square C, D (×25).",
    "T3": "Single-flute, so it counts as the 1 mm flat end mill. Second choice: Orange 5, Ø1.0 × 7 corn.",
    "T4": "No 30° × 0.1 tip in the racks: these are 30° × 0.2. At 0.1 deep it cuts about 0.25 wide, which still clears 1.0 mm pitch pads. The 60° × 0.1 (Purple A–D) cuts narrower when shallow but widens twice as fast with depth.",
    "T5": "Two in the racks; the drawer list wants 5–10.",
    "T6": "TiN drill, Ø1.0 × 10.",
}

MISSING = [
    "30° V-bit with a 0.1 mm tip (T4 as specified)",
    "0.2–0.3 mm flat end mill",
    "Carbide PCB drills 0.8 and 1.2 mm",
    "Rivet drill (1.0–1.2 mm), if you go with hollow rivets",
    "Wasteboard surfacing bit",
    "More 0.8 corn spares (have 2; the drawer list wants 5–10)",
]


def main():
    data = json.loads(DATA.read_text())
    racks = data["racks"]
    where = {}
    for r in racks:
        for k, s in r["slots"].items():
            if s and (s.get("build") or s.get("spare")):
                where.setdefault(s.get("build") or s["spare"], []).append((r, k, bool(s.get("spare"))))

    rows = []
    for b in data["buildout"]:
        locs = where.get(b["t"], [])
        locs.sort(key=lambda x: x[2])  # the main slot first, then spares
        chips = "".join(f'<span class="chip" style="--c:{r["plate"]}">{esc(r["name"])} <b>{k}</b>'
                        + (' <span class="sp">spare</span>' if sp else '') + '</span>' for r, k, sp in locs) \
            or '<span class="none">not in any rack</span>'
        rows.append(f'<tr data-t="{b["t"]}"><td class="t"><span class="tb">{b["t"]}</span></td>'
                    f'<td><b>{esc(b["tool"])}</b><div class="want">{esc(b["want"])}</div></td>'
                    f'<td>{chips}<div class="note">{esc(NOTES.get(b["t"], ""))}</div></td></tr>')

    cards = []
    for r in racks:
        handle = "" if "handle" in r["name"] else ("round handle" if r["handle"] == "round" else "square handles")
        cards.append(f'<figure class="rack" id="{r["id"]}"><figcaption><span class="sw" style="background:{r["plate"]}"></span>'
                     f'{esc(r["name"])}<span class="h">{handle}</span></figcaption>{rack_svg(r)}</figure>')

    page = TEMPLATE.replace("%ROWS%", "".join(rows)).replace("%RACKS%", "".join(cards)) \
        .replace("%MISSING%", "".join(f"<li>{esc(m)}</li>" for m in MISSING))
    ART.write_text(page)
    OUT.write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
                   '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + page + "\n</html>\n")
    print(f"wrote {OUT.relative_to(ROOT)} and {ART.relative_to(ROOT)}")


TEMPLATE = """<title>Carvera Bit Racks</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700;800&family=Barlow:wght@400;500;600&display=swap">
<style>
/* Layout: where-is-it table on top, then the four racks drawn as photographed, buildout slots in shop-label yellow. */
:root {
  --bg:#eef0ec; --surface:#ffffff; --fg:#1b1f1c; --muted:#5d665f; --line:#d3d8d2;
  --rowhi:#fff4b8; --warn:#b3261e; --hi:#ffe14d;
  --display:"Barlow Semi Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"Barlow",system-ui,-apple-system,"Segoe UI",sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg:#151916; --surface:#1f2520; --fg:#e6ebe6; --muted:#9aa59c; --line:#323b34;
  --rowhi:#3b3517; --warn:#ff8a80; color-scheme:dark; } }
:root[data-theme="dark"] {
  --bg:#151916; --surface:#1f2520; --fg:#e6ebe6; --muted:#9aa59c; --line:#323b34;
  --rowhi:#3b3517; --warn:#ff8a80; color-scheme:dark; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 var(--body); }
.wrap { max-width:1500px; margin:0 auto; padding-block:24px 60px;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); }
h1, h2, figcaption { font-family:var(--display); text-wrap:balance; }
h1 { margin:0 0 4px; font-size:2rem; font-weight:700; }
.sub { color:var(--muted); margin:0 0 20px; max-width:80ch; }
.tbox { overflow-x:auto; background:var(--surface); border:1px solid var(--line); border-radius:8px; }
table { border-collapse:collapse; width:100%; min-width:520px; }
td { padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
tr:last-child td { border-bottom:0; }
tr[data-t] { cursor:pointer; }
tr[data-t]:hover, tr.on { background:var(--rowhi); }
td.t { width:64px; }
.tb { display:inline-block; background:#111; color:var(--hi); font-family:var(--display); font-weight:800; font-size:1.2rem; padding:3px 10px; border-radius:6px; }
.want, .note { color:var(--muted); font-size:.88rem; }
.note { margin-top:6px; max-width:70ch; }
.chip { display:inline-block; margin:0 6px 4px 0; padding:2px 10px 2px 8px; border-radius:20px; background:var(--surface); color:var(--fg); border:2px solid var(--c); font-size:.92rem; }
.chip b { font-size:1rem; }
.chip .sp { color:var(--muted); font-size:.8rem; }
.none { color:var(--warn); }
.bar { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin:22px 0 12px; }
.bar input { font:inherit; padding:8px 12px; border:1px solid var(--line); border-radius:8px; background:var(--surface); color:var(--fg); width:min(320px,100%); }
.bar button { font:inherit; padding:8px 12px; border:1px solid var(--line); border-radius:8px; background:var(--surface); color:var(--fg); cursor:pointer; }
.bar input:focus-visible, .bar button:focus-visible { outline:2px solid var(--fg); outline-offset:2px; }
.legend { color:var(--muted); font-size:.88rem; }
.racks { display:grid; grid-template-columns:repeat(auto-fill,minmax(min(330px,100%),1fr)); gap:20px; }
figure.rack { margin:0; background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:12px; min-width:0; }
figcaption { font-weight:700; font-size:1.25rem; margin:0 0 8px; display:flex; align-items:center; gap:8px; }
figcaption .h { font-weight:500; color:var(--muted); font-size:1rem; }
.sw { width:18px; height:18px; border-radius:4px; display:inline-block; }
svg { width:100%; height:auto; display:block; }
svg text { font-family:var(--display); }
.case { fill:#fbfbf8; }
.case.loose { fill:#e9e9e9; stroke:#555; stroke-dasharray:8 6; stroke-width:2; }
.outline { fill:none; stroke:none; }
.big { font-size:30px; font-weight:700; fill:#111; }
.small { font-size:19px; font-weight:500; fill:#444; }
.key { font-size:17px; font-weight:700; fill:#999; }
.empty-t { font-size:20px; font-style:italic; fill:rgba(255,255,255,.85); }
.slot.build .case { fill:var(--hi); }
.slot.spare .case { fill:#fff8d6; }
.slot.build .outline { stroke:#111; stroke-width:6; }
.slot.build .key { fill:#111; }
.badge rect { fill:#111; }
.badge text { fill:var(--hi); font-size:28px; font-weight:800; }
.dtag rect { fill:#fff; stroke:#111; stroke-width:2; stroke-dasharray:5 4; }
.dtag text { fill:#111; font-size:16px; font-weight:700; }
.slot { transition:opacity .15s; }
body.focus .slot:not(.on) { opacity:.22; }
body.search .slot:not(.match) { opacity:.22; }
body.search .slot.match .outline { stroke:#d0021b; stroke-width:6; }
h2 { font-size:1.2rem; margin:32px 0 8px; }
ul.miss { margin:0; padding-left:1.2rem; color:var(--muted); }
@media (prefers-reduced-motion: reduce) { .slot { transition:none; } }
</style>
<div class="wrap">
<h1>Carvera bit racks</h1>
<p class="sub">Where each tool in the standard buildout lives. Racks drawn as photographed: slots 1–12 down the left (caps to the right), pairs A B and C D on the right. Sizes: diameter × cutting length, mm. Click a row to show only that tool.</p>
<div class="tbox"><table><tbody>%ROWS%</tbody></table></div>
<div class="bar">
  <input id="q" type="search" placeholder="Find a bit: 0.8, ball, chamfer, M4 …" autocomplete="off">
  <button id="clear">Show all</button>
  <span class="legend">Yellow with a black badge = the buildout tool · "spare" tag = second copy of a buildout tool · "drawer" tag = drawer spare</span>
</div>
<div class="racks">%RACKS%</div>
<h2>Not in any rack</h2>
<ul class="miss">%MISSING%</ul>
</div>
<script>
const body = document.body, q = document.getElementById('q');
const slots = [...document.querySelectorAll('.slot')];
function clear() {
  body.classList.remove('focus', 'search');
  slots.forEach(s => s.classList.remove('on', 'match'));
  document.querySelectorAll('tr.on').forEach(r => r.classList.remove('on'));
}
document.querySelectorAll('tr[data-t]').forEach(tr => tr.addEventListener('click', () => {
  const was = tr.classList.contains('on');
  clear(); q.value = '';
  if (was) return;
  tr.classList.add('on'); body.classList.add('focus');
  slots.forEach(s => s.classList.toggle('on', s.dataset.build === tr.dataset.t || s.dataset.spare === tr.dataset.t));
}));
q.addEventListener('input', () => {
  const v = q.value.trim().toLowerCase();
  clear();
  if (!v) return;
  body.classList.add('search');
  slots.forEach(s => s.classList.toggle('match', (s.dataset.text || '').includes(v)));
});
document.getElementById('clear').addEventListener('click', () => { clear(); q.value = ''; });
</script>
"""

if __name__ == "__main__":
    main()
