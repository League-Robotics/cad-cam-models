#!/usr/bin/env python3
"""Build a self-contained three.js page that shows several STLs together.

The STLs are embedded (base64), so the page works straight from file://.

    mockup_html.py OUT.html TITLE name=file.stl:#color[:opacity][:pivot=x,y,sign | :xpivot=y,z,sign] ...

Each name becomes a "Show" checkbox. Z is up (OpenSCAD coordinates). A name
starting with "+" also follows the Lift slider (the part being fitted); one
starting with "-" starts hidden (an alternative part, e.g. the can arms). A
part with a pivot (x, y of a vertical axis, sign +-1) turns about it with the
Jaws slider: the STL is the part at theta 0 and it turns sign * theta. xpivot
is the same about an axis along x through (y, z), e.g. a tilt hinge.
An option --slider=LABEL,MIN,MAX renames and re-ranges that slider (e.g.
--slider=Pan,-90,90).
"""
import base64
import json
import sys
from pathlib import Path

args = sys.argv[1:]
slider = ["Jaws", "-6", "90"]
for a in list(args):
    if a.startswith("--slider="):
        slider = a[9:].split(",")
        args.remove(a)
out, title, *specs = args
parts = []
for spec in specs:
    name, rest = spec.split("=", 1)
    path, color, *op = rest.split(":")
    lift = name.lstrip("-").startswith("+")
    pivot = xpivot = None
    for o in list(op):
        if o.startswith("pivot="):
            pivot = [float(v) for v in o[6:].split(",")]
            op.remove(o)
        elif o.startswith("xpivot="):
            xpivot = [float(v) for v in o[7:].split(",")]
            op.remove(o)
    parts.append({
        "name": name.lstrip("+-"), "lift": lift, "hidden": name.startswith("-"), "color": color, "pivot": pivot, "xpivot": xpivot,
        "opacity": float(op[0]) if op else 1.0,
        "data": base64.b64encode(Path(path).read_bytes()).decode(),
    })

page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITLE</title>
<style>
  :root { --bg:#f4f2ee; --panel:#fff; --ink:#1f2328; --muted:#6a6f76; --line:#d9d6cf; }
  @media (prefers-color-scheme: dark) { :root { --bg:#16171a; --panel:#1f2125; --ink:#e8e6e1; --muted:#9a9ea6; --line:#33363c; } }
  html, body { margin:0; height:100%; background:var(--bg); color:var(--ink); font:13px/1.4 -apple-system, sans-serif; }
  #app { display:flex; height:100%; } #view { flex:1; min-width:0; }
  #panel { width:240px; padding:14px 16px; background:var(--panel); border-left:1px solid var(--line); overflow:auto; }
  h1 { font-size:15px; margin:0 0 10px; } label { display:block; margin:6px 0; }
  i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; }
  button { margin:2px 4px 2px 0; } .muted { color:var(--muted); }
</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
</head><body><div id="app"><div id="view"></div><div id="panel">
<h1>TITLE</h1><div id="toggles"></div>
<label>Lift <input type="range" id="lift" min="0" max="40" value="0"></label>
<label>SL_NAME <input type="range" id="jaws" min="SL_MIN" max="SL_MAX" value="0" step="1"> <span id="jawv">0</span>&deg;</label>
<div><button data-v="iso">Iso</button><button data-v="top">Top</button><button data-v="front">Front</button><button data-v="side">Side</button><button data-v="under">Under</button></div>
<p class="muted">Drag to orbit, scroll to zoom, right-drag to pan. mm, Z up.</p>
</div></div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
const PARTS = PARTS_JSON;
const view = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(devicePixelRatio); view.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim());
const camera = new THREE.PerspectiveCamera(35, 1, 1, 3000); camera.up.set(0, 0, 1);
const controls = new OrbitControls(camera, renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x777788, 1.5));
const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(80, -60, 150); scene.add(sun);
const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(-80, 80, -60); scene.add(fill);
const loader = new STLLoader(), box = new THREE.Box3(), meshes = [];
for (const p of PARTS) {
  const bin = Uint8Array.from(atob(p.data), c => c.charCodeAt(0));
  const g = loader.parse(bin.buffer); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: p.color, roughness: .55,
    transparent: p.opacity < 1, opacity: p.opacity, side: THREE.DoubleSide }));
  if (p.pivot) { g.translate(-p.pivot[0], -p.pivot[1], 0); m.position.set(p.pivot[0], p.pivot[1], 0); }
  if (p.xpivot) { g.translate(0, -p.xpivot[0], -p.xpivot[1]); m.position.set(0, p.xpivot[0], p.xpivot[1]); }
  p.z0 = m.position.z;
  m.userData = p; m.visible = !p.hidden; scene.add(m); meshes.push(m); if (!p.hidden) box.expandByObject(m);
  const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox" ${p.hidden ? '' : 'checked'}> <i style="background:${p.color}"></i>${p.name}`;
  l.querySelector('input').onchange = e => { m.visible = e.target.checked; };
  document.getElementById('toggles').appendChild(l);
}
const c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length();
document.getElementById('lift').oninput = e => meshes.forEach(m => { if (m.userData.lift) m.position.z = m.userData.z0 + +e.target.value; });
document.getElementById('jaws').oninput = e => { document.getElementById('jawv').textContent = e.target.value;
  meshes.forEach(m => { if (m.userData.pivot) m.rotation.z = m.userData.pivot[2] * e.target.value * Math.PI / 180;
    if (m.userData.xpivot) m.rotation.x = m.userData.xpivot[2] * e.target.value * Math.PI / 180; }); };
const V = { iso: [1, -1.2, .9], top: [0, -0.001, 1.6], front: [0, -1.6, .2], side: [1.6, 0, .2], under: [.6, -.9, -1.1] };
function setView(v) { const d = V[v]; camera.position.set(c.x + d[0]*r, c.y + d[1]*r, c.z + d[2]*r); controls.target.copy(c); controls.update(); }
document.querySelectorAll('[data-v]').forEach(b => b.onclick = () => setView(b.dataset.v));
setView('iso');
function resize() { renderer.setSize(view.clientWidth, view.clientHeight); camera.aspect = view.clientWidth / view.clientHeight; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
</script></body></html>
"""
page = page.replace("SL_NAME", slider[0]).replace("SL_MIN", slider[1]).replace("SL_MAX", slider[2])
page = page.replace("TITLE", title).replace("PARTS_JSON", json.dumps(parts))
Path(out).write_text(page)
print(out, f"{len(page) / 1e6:.1f} MB")
