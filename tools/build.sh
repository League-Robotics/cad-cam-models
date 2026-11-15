#!/bin/bash
# Build everything generated from case/robot_display_case.scad into out/:
# the STLs (as mounted, and *_print.stl on the bed), the fit check, the
# four-view pictures (case/views.png and out/views/*.png), the labelled
# drawings (case/case_pics.py) and the 3D viewer (out/robot_display_case.html).
#   bash tools/build.sh [stl|check|views|pics|viewer ...]   (default: all)
set -e
cd "$(dirname "$0")/.."
export PATH=/opt/homebrew/bin:$PATH
mkdir -p out out/views
SCAD=case/robot_display_case.scad
S="openscad --backend=manifold --export-format=binstl"
one() { $S -o "$1" "${@:2}" 2>&1 | grep -iE '^error|warning:' || true; }
steps=("$@"); [ ${#steps[@]} -eq 0 ] && steps=(stl check views pics viewer)
for st in "${steps[@]}"; do case $st in
stl)
  for p in shell lid lid_flat board board_env shell_print lid_print lid_flat_print; do one out/$p.stl -D "part=\"$p\"" $SCAD; done
  one out/clash.stl case/clash.scad ;;
check)
  uv run --with trimesh --with numpy --with scipy python - <<'PY'
import trimesh
for n in ["shell","lid","lid_flat","board","board_env","clash"]:
    m=trimesh.load(f"out/{n}.stl"); b=m.bounds
    print(f"{n:9s} vol={m.volume:9.1f} mm3  x[{b[0][0]:7.2f},{b[1][0]:7.2f}] y[{b[0][1]:7.2f},{b[1][1]:7.2f}] z[{b[0][2]:7.2f},{b[1][2]:7.2f}] watertight={m.is_watertight}")
c=trimesh.load("out/clash.stl")
if c.volume: print("overlap bounds", c.bounds.round(2).tolist())
assert abs(c.volume) < 1.0, f"case overlaps the board model by {c.volume:.1f} mm3"
print("fit check: case and board model do not overlap")
PY
  ;;
views)
  uv run tools/four_view.py case/views.png "Robot display case: shell, LEGO lid and board (STEP model) assembled" $SCAD -D 'part="assembly"'
  uv run tools/four_view.py out/views/shell.png "Shell, as mounted (front face up)" $SCAD -D 'part="shell"'
  uv run tools/four_view.py out/views/lid.png "LEGO lid, as mounted" $SCAD -D 'part="lid"' --iso-eye=-1,-1.3,-0.9 --iso-title="Iso, from below (the pin-hole face)"
  cp case/views.png out/views/assembly.png ;;
pics)
  uv run case/case_pics.py
  uv run case/joint_pic.py ;;
viewer)
  python3 tools/mockup_html.py out/robot_display_case.html "Robot display case: Waveshare ESP32-S3-Touch-LCD-1.69 in its shell with the LEGO lid" \
    "Shell=out/shell.stl:#3b7dd8:0.55" "+LEGO lid=out/lid.stl:#f0a030" "-Flat lid=out/lid_flat.stl:#c080f0" "Board=out/board.stl:#50b050" --lift-axis=z
  echo "viewer: out/robot_display_case.html" ;;
esac; done
