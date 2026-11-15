"""Pack viewer STLs into the Robot Garage 3D viewer page (template.html).

Usage: uv run --with numpy python tools/viewer3d/pack.py CONFIG.json OUT.html

CONFIG.json: {"title", "sub", "stl_dir", "size_of": [mesh names for the outside size],
"size_note", "axes": [["x", text], ["y", text], ["z", text]], "ends": [-x view name, +x view name], "groups": [{"name", "items": [{"id", "label", "note", "mode"?, "move"?,
"meshes": [[mesh name, colour], ...]}]}]}. A mesh name is an STL's file name in
stl_dir without ".stl". move: 1 lifts with the Explode slider, -1 drops.

The method is usb-power-switch/design/viewer/pack.py's: each STL deduplicated,
snapped to a 0.004 mm grid as int16 and embedded as base64, one self-contained file.
"""
import base64, json, os, struct, sys
import numpy as np

cfg_path, out_html = sys.argv[1:3]
cfg = json.load(open(cfg_path))
here = os.path.dirname(os.path.abspath(__file__))
Q = 0.004
meshes, lo_all, hi_all = {}, {}, {}
names = [m for g in cfg['groups'] for it in g['items'] for m, _ in it['meshes']]
for name in names:
    b = open(os.path.join(cfg['stl_dir'], name + '.stl'), 'rb').read()
    n = struct.unpack('<I', b[80:84])[0]
    rec = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    v = np.frombuffer(b[84:84 + n * 50], dtype=rec)['v'].reshape(-1, 3).astype(np.float64)
    q = np.round(v / Q).astype(np.int32)
    if np.abs(q).max() >= 32767:
        sys.exit(f'{name}: coordinates too large for int16 at {Q} mm')
    uniq, inv = np.unique(q, axis=0, return_inverse=True)
    idx = inv.reshape(-1).astype(np.uint16 if len(uniq) < 65536 else np.uint32)
    meshes[name] = {'p': base64.b64encode(uniq.astype('<i2').tobytes()).decode(),
                    'i': base64.b64encode(idx.tobytes()).decode(),
                    'w': 2 if idx.dtype == np.uint16 else 4}
    lo_all[name], hi_all[name] = v.min(0), v.max(0)

lo = np.min([lo_all[m] for m in cfg['size_of']], axis=0)
hi = np.max([hi_all[m] for m in cfg['size_of']], axis=0)
size = ' × '.join(f'{d:.2f}'.rstrip('0').rstrip('.') for d in hi - lo)
blo = np.min(list(lo_all.values()), axis=0); bhi = np.max(list(hi_all.values()), axis=0)
view = {'target': ((blo + bhi) / 2).round(2).tolist(), 'lo': blo.round(2).tolist(), 'hi': bhi.round(2).tolist(),
        'dist': round(2.0 * float(np.linalg.norm(bhi - blo)), 1),
        'axes': cfg['axes'], 'ends': cfg.get('ends', ['Left', 'Right']),
        'variant': cfg.get('variant', ''), 'title': cfg['title'], 'sub': cfg['sub'],
        'dims': f"{size} mm {cfg.get('size_note', 'outside (X × Y × Z)')}", 'groups': cfg['groups']}
data = 'const MESH_Q=%g;const VIEW=%s;const MESHES=%s;' % (
    Q, json.dumps(view, ensure_ascii=False), json.dumps(meshes, separators=(',', ':')))
page = open(os.path.join(here, 'template.html')).read().replace('/*TITLE*/', cfg['title']).replace('/*DATA*/', data)
open(out_html, 'w').write(page)
print(f'{out_html}: {len(meshes)} meshes, {os.path.getsize(out_html) // 1024} KB, {size} mm')
