#!/bin/bash
# Regenerate every printable part under grippers/, in print orientation.
#   grippers/arms            the LEGO-axle gear arms: left (Nezha motor) and
#                            right (the idler arm of every set)
#   grippers/nezha           Nezha motor gripper: frame
#   grippers/servo_standard  standard servo gripper: spline arm, frame
#   grippers/servo_9g        9 g micro servo gripper: spline arm, frame (the original) and
#                            frame_centred (2026-10-28: grid centred on the jaws, full-unit back
#                            wall with 4 rows of holes, a row of holes out of the floor's front face)
#   grippers/extensions      swappable arms (fit every set): can, cube, cube_low, cube_short, ball
#   grippers/plates          everything on one plate with first-layer sprues
#   grippers/block_gripper   the pinned grippers (2026-10-29): frame (the centred 9 g frame turned
#                            over, on its back wall: one print for every robot), the mounts (block:
#                            5 x 3 x 2 between the two-plate robot's plates, flat; cutebot_tab: on
#                            the Cutebot Pro's nose, flat) and a caster post per height (post_level,
#                            post_low, post_front for the two-plate robot, post_cutebot; on their
#                            back faces), all pinned together with 2L pins and glued
# Usage: bash tools/make_parts.sh [set ...]   (default: all sets)
set -e
cd "$(dirname "$0")/.."
S="openscad --backend=manifold"
out() { mkdir -p "grippers/$1"; echo "grippers/$1/$2.stl"; $S -o "grippers/$1/$2.stl" "${@:3}" 2>&1 | grep -iE '^error|warning:' || true; }

sets=${*:-"arms nezha servo_standard servo_9g extensions plates block_gripper"}
for s in $sets; do case $s in
arms)   # one copy for every set, at the servo sets' smoothness
  out arms left_arm -D 'part="nub_print"' -D side=-1 -D '$fn=72' scad/swap_gripper.scad
  out arms right_arm -D 'part="nub_print"' -D side=1 -D '$fn=72' scad/swap_gripper.scad ;;
nezha)
  out nezha frame -D 'part="frame"' scad/nezha_gripper.scad ;;
servo_standard|servo_9g)
  v=standard; [ $s = servo_9g ] && v=9g
  out $s spline_arm -D 'part="spline_arm"' -D "servo=\"$v\"" scad/servo_gripper.scad
  out $s frame -D 'part="frame"' -D "servo=\"$v\"" scad/servo_gripper.scad
  [ $s = servo_9g ] && out $s frame_centred -D 'part="frame"' -D 'servo="9g"' -D centred=true scad/servo_gripper.scad ;;
extensions)
  for a in can cube cube_low cube_short ball; do for side in left right; do
    n=-1; [ $side = right ] && n=1
    out extensions ${a}_arm_$side -D 'part="print"' -D "arm=\"$a\"" -D side=$n scad/swap_gripper.scad
  done; done ;;
plates)
  python3 tools/plate_sprues.py 2>/dev/null
  out plates all_parts -D 'part="plate"' scad/swap_plate.scad ;;
block_gripper)
  out block_gripper frame -D 'part="print_frame"' -D '$fn=64' scad/block_gripper.scad
  out block_gripper block -D 'part="print_block"' -D '$fn=64' scad/block_gripper.scad
  out block_gripper cutebot_tab -D 'part="print_tab"' -D '$fn=64' scad/cutebot_gripper.scad
  for st in level low front; do
    out block_gripper post_$st -D 'part="print_post"' -D "stance=\"$st\"" -D '$fn=64' scad/block_gripper.scad
  done
  out block_gripper post_cutebot -D 'part="print_post"' -D '$fn=64' scad/cutebot_gripper.scad ;;
esac; done
