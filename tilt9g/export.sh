#!/bin/bash
# Export the tilt-pan prints (frame.stl LEGO face on the bed, table.stl outer
# face on the bed, pan_frame.stl camera face on the bed, spline_plate.stl
# servo face on the bed) and the meshes index.html animates (view/*.stl,
# servo coordinates at theta = 0).
# Usage: bash tilt9g/export.sh
set -e
cd "$(dirname "$0")"
S="openscad --backend=manifold --export-format binstl"
echo frame.stl
$S -o frame.stl -D 'part="frame"' tilt9g.scad 2>&1 | grep -iE '^error|warning:' || true
echo table.stl
$S -o table.stl -D 'part="table"' -D '$fn=64' tilt9g.scad 2>&1 | grep -iE '^error|warning:' || true
echo pan_frame.stl
$S -o pan_frame.stl -D 'part="frame"' -D '$fn=64' pan9g.scad 2>&1 | grep -iE '^error|warning:' || true
echo spline_plate.stl
$S -o spline_plate.stl -D 'part="spline_plate"' -D '$fn=64' pan9g.scad 2>&1 | grep -iE '^error|warning:' || true
mkdir -p view
for p in frame servo spline bottom table pan_plate pan_frame pan_servo; do
  echo view/$p.stl
  $S -o view/$p.stl -D "part=\"${p}_view\"" tilt9g.scad 2>&1 | grep -iE '^error|warning:' || true &
done; wait
