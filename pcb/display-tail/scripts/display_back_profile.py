#!/usr/bin/env python3
"""Where the display's back is free along its pad edge, from Waveshare's STEP model meshed to an STL
(robot-projects/watch-display/ref/waveshare/board.stl). STEP frame: x along the short axis (buttons at +x),
y along the long axis (pad edge at -y, y = -18.841), z out of the screen; the PCB back face is z = -2.5.

    uv run --with "trimesh[easy]" --with numpy --with scipy --with rtree python scripts/display_back_profile.py BOARD.stl

Prints, per 1 mm bin of x, how far in from the pad edge the first part on the back begins and how deep it is,
plus what sticks out past the edge (the LCD flex). The STEP has no pads; the pad row is assumed centred.
"""
m = trimesh.load(sys.argv[1], force='mesh')
v = m.vertices; YE = -18.841
# triangles on the back side below the PCB back face
tri = m.triangles; zmax = tri[:, :, 2].max(axis=1)
back = tri[zmax < -2.52]
print('back triangles', len(back))
print(' x bin  | nearest-to-edge (mm inboard) z-at-it | nearest 4.4-deep part')
for x0 in np.arange(-15, 15.5, 1.0):
    sel = back[(back[:, :, 0].min(axis=1) < x0 + 1) & (back[:, :, 0].max(axis=1) > x0)]
    if not len(sel): print('%5.1f..%5.1f  nothing' % (x0, x0 + 1)); continue
    ymin = sel[:, :, 1].min(); zmin = sel[:, :, 2].min()
    i = sel[:, :, 1].min(axis=1).argmin()
    deep = sel[sel[:, :, 2].min(axis=1) < -5.5]
    dy = deep[:, :, 1].min() - YE if len(deep) else None
    print('%5.1f..%5.1f  %.2f  (z %.2f)   deep(>3mm): %s' % (x0, x0 + 1, ymin - YE, sel[i][:, 2].min(), ('%.2f' % dy) if dy is not None else '-'))
# the flex beyond the edge
sel = v[(v[:, 1] < YE - 0.05)]
print('beyond edge: z %.2f..%.2f' % (sel[:,2].min(), sel[:,2].max()))
for z0, z1 in [(-2.5, -1.5), (-1.5, 0), (0, 1.5), (1.5, 2.1)]:
    s = sel[(sel[:,2] >= z0) & (sel[:,2] < z1)]
    if len(s): print('  z %s..%s: x %.2f..%.2f, y to %.2f' % (z0, z1, s[:,0].min(), s[:,0].max(), s[:,1].min()))
