# Checks each bracket against the motor: pins line up with open holes, and the parts don't overlap.
import json, sys, numpy as np, trimesh
side = [(4,20),(36,4),(36,20),(52,4),(52,20)]
bottom = [(36,-4),(52,-4),(44,-12),(44,4),(44,-4)]
holes = []  # (point on motor face, outward direction)
for x,z in side: holes += [((x,-16,z),(0,-1,0)), ((x,8,z),(0,1,0))]
for x,y in bottom: holes += [((x,y,0),(0,0,-1)), ((x,y,32),(0,0,1))]
motor = trimesh.load('motor.stl')
for d in json.load(open('designs.json')):
    b = trimesh.load(f"stl/{d['name']}.stl"); b.apply_translation(d['origin'])
    used = []
    for p,n in holes:
        p = np.array(p,float); n = np.array(n,float)
        # does the bracket sit against this face here? probe 4 mm out, 3.6 mm off-axis (solid ring around a hole)
        perp = np.array([1,0,0]) if n[0]==0 else np.array([0,1,0])
        if not b.contains([p+4*n+3.6*perp])[0]: continue
        # center ray from inside the motor outward through the bracket: must pass with no hits in 0.5..7.5 mm
        locs,_,_ = b.ray.intersects_location([p-2*n],[n])
        depth = sorted(float(np.dot(l-p,n)) for l in locs)
        blocked = [t for t in depth if 0.5 < t < 7.5]
        used.append((tuple(p.astype(int)), 'OPEN' if not blocked else f'BLOCKED {blocked}'))
    # overlap: bracket vertices strictly inside the motor envelope boxes
    v=b.vertices; inside=0
    for lo,hi in (([-16,-16,0],[56,8,24]),([32,-16,24],[56,8,32])):
        inside += ((v>np.array(lo)+0.05)&(v<np.array(hi)-0.05)).all(1).sum()
    print(f"{d['name']:18} watertight={b.is_watertight} overlap_pts={inside} pins:{len(used)}")
    for u in used: print('    ', u)
