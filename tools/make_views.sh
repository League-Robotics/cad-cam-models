#!/bin/bash
# Build the browser 3D viewers in view/: self-contained HTML pages (three.js,
# STLs embedded) with a checkbox and colour per component.
#   view/servo9g_cube_low.html   9 g servo gripper with the cube_low racket paddles
#   view/nezha_cube_low.html     Nezha gripper with the same paddles
#   view/gripper_plate.html      gripper plate on the reflectance sensor
#   view/front_plate.html        front plate: 9 g gripper built into the sensor plate, two casters
#   view/robot_plates.html       the 11 x 19 plates with the 3x3 and 3x4 holes, sensor under each
#   view/block_gripper_level.html  the pinned gripper (frame, block, caster post) on the front of the two-plate robot,
#                                sensor on top of the bottom plate; the frame's 2nd and 3rd wall rows on the block
#   view/block_gripper_low.html  the same 8 lower: the top two wall rows on the block
#   view/block_gripper_front.html  16 lower: the top row on the block's lower row, paddles 0.4 off the ground
#   view/cutebot_gripper.html    the same frame and a post on the Cutebot Pro's nose (a stand-in slab with the two bosses) with the tab
#   view/brick_frame.html        the cage round the Nezha brick (two sides, two end bars, pins); brick_frame_stand.html stood up
#   view/tilt_pan9g.html         the 9 g tilt table (flat, the frame on its LEGO wall) with the pan head on it; the Pan slider turns it
#   view/battery_frame.html      the 6 x 6 x 11 LEGO frame round the USB battery: two halves (one print twice), 2L pins
#   view/tilt_table.html         the friction tilt table: two 5 x 5 plates hinged on snap-together triangles; the Tilt slider tilts it
#   view/pi_frame.html           the open frame round a Raspberry Pi 4: base with the weld posts, two windows, top bars
#   view/laser_cam_mount.html    two Arducams and a line laser under the Carvera camera bracket's cap
#   view/plug_tail.html          the 4P4C plug-tail PCBs, a checkbox per layer (tools/plug_tail_view.py)
#   view/l_bracket.html          the 5 x 5 LEGO L bracket, 2L pins in a few holes
#   view/cutebot_cage.html       LEGO cage round the Cutebot Pro (v3): a closed ring of bulkheads, skirts and front wall, decks over the wheels and the front; robot stand-in from the scan
# Usage: bash tools/make_views.sh [view ...]   (default: all; add --open to open them)
#
# How it works: each assembly .scad has a `show` parameter ("all" or one
# component) so every component exports on its own, still in its assembled
# position; tools/mockup_html.py then puts the STLs on one page. A name
# starting with "+" follows the page's Lift slider.
set -e
cd "$(dirname "$0")/.."
T=$(mktemp -d)
S="openscad --backend=manifold --export-format=binstl"
one() { $S -o "$T/$1.stl" "${@:2}" 2>&1 | grep -iE '^error|warning:' || true; }
open_=0; views=()
for a in "$@"; do [ "$a" = --open ] && open_=1 || views+=("$a"); done
[ ${#views[@]} -eq 0 ] && views=(servo9g nezha plate front plates robot_level robot_low robot_front cutebot tiltpan brickframe tilttable batteryframe piframe lasercam plugtail lbracket cutebotcage)

for v in "${views[@]}"; do case $v in
servo9g)
  for c in spline_arm idler_arm left_ext right_ext frame servo axle; do
    one 9g_$c -D 'servo="9g"' -D 'jaw="nub"' -D 'ext="cube_low"' -D "show=\"$c\"" scad/servo_gripper.scad &
  done; wait
  python3 tools/mockup_html.py view/servo9g_cube_low.html "9 g servo gripper, cube_low racket paddles" \
    "+Left paddle=$T/9g_left_ext.stl:#3cb371" "+Right paddle=$T/9g_right_ext.stl:#2e8b57" \
    "Spline arm=$T/9g_spline_arm.stl:#f29a00" "Idler arm=$T/9g_idler_arm.stl:#4169e1" \
    "Frame=$T/9g_frame.stl:#c8c8c8" "Axle=$T/9g_axle.stl:#222222" "9 g servo=$T/9g_servo.stl:#555555:0.6"
  [ $open_ = 1 ] && open -a "Google Chrome" view/servo9g_cube_low.html ;;
nezha)
  for c in motor_nub idler_nub left_ext right_ext frame motor; do
    one nz_$c -D 'ext="cube_low"' -D "show=\"$c\"" scad/nezha_gripper.scad &
  done; wait
  python3 tools/mockup_html.py view/nezha_cube_low.html "Nezha gripper, cube_low racket paddles" \
    "+Left paddle=$T/nz_left_ext.stl:#3cb371" "+Right paddle=$T/nz_right_ext.stl:#2e8b57" \
    "Motor nub=$T/nz_motor_nub.stl:#f29a00" "Idler nub=$T/nz_idler_nub.stl:#4169e1" \
    "Frame=$T/nz_frame.stl:#c8c8c8" "Nezha motor=$T/nz_motor.stl:#ff69b4:0.6"
  [ $open_ = 1 ] && open -a "Google Chrome" view/nezha_cube_low.html ;;
plate)
  one plate -D 'part="plate"' scad/gripper_plate.scad
  for c in pcb brackets back_parts sensors; do one rs_$c -D "part=\"$c\"" scad/reflectance_sensor.scad; done
  python3 tools/mockup_html.py view/gripper_plate.html "Gripper plate on line sensor" \
    "+Gripper plate=$T/plate.stl:#7c5cff" "PCB=$T/rs_pcb.stl:#4aa3df" "Brackets=$T/rs_brackets.stl:#eeeeee" \
    "RJ11 plug + button=$T/rs_back_parts.stl:#2f5fd0" "Sensors=$T/rs_sensors.stl:#222222"
  [ $open_ = 1 ] && open -a "Google Chrome" view/gripper_plate.html ;;
front)
  one fp_part -D 'part="part"' scad/front_plate.scad &
  one fp_casters -D 'part="casters"' scad/front_plate.scad &
  one fp_floor -D 'part="floor"' scad/front_plate.scad &
  for c in pcb brackets back_parts sensors; do one rs_$c -D "part=\"$c\"" scad/reflectance_sensor.scad & done
  for c in spline_arm idler_arm left_ext right_ext servo axle; do
    one g_$c -D 'servo="9g"' -D 'jaw="nub"' -D 'ext="cube"' -D "show=\"$c\"" scad/servo_gripper.scad &
  done; wait
  for c in spline_arm idler_arm left_ext right_ext servo axle; do
    one fp_$c -D 'part="gripper_import"' -D "gripper_stl=\"$T/g_$c.stl\"" scad/front_plate.scad &
  done; wait
  python3 tools/mockup_html.py view/front_plate.html "Front plate: 9 g gripper built in, two casters" \
    "Front plate + frame=$T/fp_part.stl:#3cb371" "Casters=$T/fp_casters.stl:#555a60" \
    "9 g servo=$T/fp_servo.stl:#333333:0.85" \
    "Spline arm=$T/fp_spline_arm.stl:#f29a00" "Idler arm=$T/fp_idler_arm.stl:#4169e1" \
    "Left cube arm=$T/fp_left_ext.stl:#9b59b6" "Right cube arm=$T/fp_right_ext.stl:#8e44ad" \
    "Axle=$T/fp_axle.stl:#222222" \
    "PCB=$T/rs_pcb.stl:#4aa3df" "Brackets=$T/rs_brackets.stl:#eeeeee" \
    "RJ11 plug + button=$T/rs_back_parts.stl:#2f5fd0" "Sensors=$T/rs_sensors.stl:#222222" \
    "Sensor scan (real back)=scad/models/reflectance_sensor_scan.stl:#e0453a:0.55" \
    "Board top scan (clips, button)=scad/models/reflectance_sensor_top_scan.stl:#f5c518:0.8" \
    "Floor=$T/fp_floor.stl:#bbbbbb:0.35"
  [ $open_ = 1 ] && open -a "Google Chrome" view/front_plate.html ;;
plates)
  for h in 3x4 3x3 cans; do
    one pl_$h -D 'part="plate"' -D "hole=\"$h\"" scad/robot_plate.scad &
    for c in pcb brackets back_parts sensors; do
      one pl_${h}_$c -D "part=\"sensor_$c\"" -D "hole=\"$h\"" scad/robot_plate.scad &
    done
  done; wait
  python3 tools/mockup_html.py view/robot_plates.html "11 x 19 plates: 3x4 hole (sensor under), can pockets (sensor on top), 3x3 (as cut)" \
    "3x4 plate=$T/pl_3x4.stl:#e3b505" "Sensor under 3x4 (row 4): PCB=$T/pl_3x4_pcb.stl:#4aa3df" "  brackets=$T/pl_3x4_brackets.stl:#eeeeee" \
    "  jack + button=$T/pl_3x4_back_parts.stl:#2f5fd0" "  sensors=$T/pl_3x4_sensors.stl:#222222" \
    "+Cans plate (sensor on top)=$T/pl_cans.stl:#5ec15e:0.9" "+Sensor on top (row 5): PCB=$T/pl_cans_pcb.stl:#1f7a3f" "+  brackets=$T/pl_cans_brackets.stl:#d8f0d8" \
    "+  jack + button=$T/pl_cans_back_parts.stl:#0f4f2a" "+  sensors=$T/pl_cans_sensors.stl:#113311" \
    "3x3 plate (as cut today)=$T/pl_3x3.stl:#9aa0a6:0.6" \
    "Sensor under 3x3 (row 5): PCB=$T/pl_3x3_pcb.stl:#d9534f:0.7" "  brackets=$T/pl_3x3_brackets.stl:#f0c0c0:0.7" \
    "  jack + button=$T/pl_3x3_back_parts.stl:#b03030:0.7" "  sensors=$T/pl_3x3_sensors.stl:#553333:0.7"
  [ $open_ = 1 ] && open -a "Google Chrome" view/robot_plates.html ;;
robot_level|robot_low|robot_front)
  st=${v#robot_}; name=block_gripper_$st
  case $st in
    level) title="Block gripper, level: frame, block and caster post pinned together on the two-plate robot (sensor on top); the frame's 2nd and 3rd wall rows on the block, its top row into the top plate's edge holes" ;;
    low) title="Block gripper, low: 8 lower, the frame's top two wall rows on the block, its bottom row into the bottom plate's edge holes" ;;
    front) title="Block gripper, front: 16 lower, the frame's top row on the block's lower row, paddles 0.4 off the ground" ;;
  esac
  for c in frame block post pins servo spline_arm idler_arm left_ext right_ext axle caster bottom_plate top_plate motors pcb brackets back_parts sensors floor; do
    one bg_$c -D 'ext="cube"' -D "stance=\"$st\"" -D "show=\"$c\"" scad/block_gripper.scad &
  done
  for c in left_ext right_ext; do   # the can arms (theta 0, the Jaws slider turns them), hidden until ticked
    one bgc_$c -D 'ext="can"' -D 'theta=0' -D "stance=\"$st\"" -D "show=\"$c\"" scad/block_gripper.scad &
  done; wait
  L="pivot=12,-21.9,1"; R="pivot=-12,-21.9,-1"   # the spline and idler axles (robot x, y) and each arm's sense
  python3 tools/mockup_html.py view/$name.html "$title" \
    "+Frame=$T/bg_frame.stl:#3cb371" "+Block (between the plates)=$T/bg_block.stl:#deb887" "+Caster post=$T/bg_post.stl:#8fbc8f" "+Pins=$T/bg_pins.stl:#444444" \
    "+9 g servo=$T/bg_servo.stl:#333333:0.85" \
    "+Spline arm=$T/bg_spline_arm.stl:#f29a00:$L" "+Idler arm=$T/bg_idler_arm.stl:#4169e1:$R" \
    "+Left cube arm=$T/bg_left_ext.stl:#9b59b6:$L" "+Right cube arm=$T/bg_right_ext.stl:#8e44ad:$R" "+Axle=$T/bg_axle.stl:#222222" \
    "-+Left can arm=$T/bgc_left_ext.stl:#e07b39:$L" "-+Right can arm=$T/bgc_right_ext.stl:#c9682a:$R" \
    "+Ball caster=$T/bg_caster.stl:#555a60" \
    "Bottom plate=$T/bg_bottom_plate.stl:#e3b505" "Top plate=$T/bg_top_plate.stl:#c9a227:0.9" \
    "Nezha motors=$T/bg_motors.stl:#ff69b4:0.6" \
    "PCB=$T/bg_pcb.stl:#4aa3df" "Brackets=$T/bg_brackets.stl:#eeeeee" "Jack + button=$T/bg_back_parts.stl:#2f5fd0" "Sensors=$T/bg_sensors.stl:#222222" \
    "Floor=$T/bg_floor.stl:#bbbbbb:0.35"
  [ $open_ = 1 ] && open -a "Google Chrome" view/$name.html ;;
cutebot)
  for c in frame tab post pins servo spline_arm idler_arm left_ext right_ext axle caster cutebot floor; do
    one cb_$c -D 'ext="cube"' -D "show=\"$c\"" scad/cutebot_gripper.scad &
  done
  for c in left_ext right_ext; do   # the can arms (theta 0, the Jaws slider turns them), hidden until ticked
    one cbc_$c -D 'ext="can"' -D 'theta=0' -D "show=\"$c\"" scad/cutebot_gripper.scad &
  done; wait
  L="pivot=12,-22.3,1"; R="pivot=-12,-22.3,-1"   # the spline and idler axles (robot x, y) and each arm's sense
  python3 tools/mockup_html.py view/cutebot_gripper.html "Cutebot gripper: three prints pinned together (frame, tab, caster post) on the Cutebot Pro's nose" \
    "+Frame=$T/cb_frame.stl:#3cb371" "+Tab (on the nose's bosses)=$T/cb_tab.stl:#deb887" "+Caster post=$T/cb_post.stl:#8fbc8f" "+Pins=$T/cb_pins.stl:#444444" \
    "+9 g servo=$T/cb_servo.stl:#333333:0.85" \
    "+Spline arm=$T/cb_spline_arm.stl:#f29a00:$L" "+Idler arm=$T/cb_idler_arm.stl:#4169e1:$R" \
    "+Left cube arm=$T/cb_left_ext.stl:#9b59b6:$L" "+Right cube arm=$T/cb_right_ext.stl:#8e44ad:$R" "+Axle=$T/cb_axle.stl:#222222" \
    "-+Left can arm=$T/cbc_left_ext.stl:#e07b39:$L" "-+Right can arm=$T/cbc_right_ext.stl:#c9682a:$R" \
    "+Ball caster=$T/cb_caster.stl:#555a60" \
    "Cutebot nose (stand-in)=$T/cb_cutebot.stl:#f0f0f0:0.9" "Floor=$T/cb_floor.stl:#bbbbbb:0.35"
  [ $open_ = 1 ] && open -a "Google Chrome" view/cutebot_gripper.html ;;
tiltpan)
  for c in frame servo spline bottom table pan_plate pan_frame pan_servo; do
    one tp_$c -D 'part="world"' -D 'theta=-90' -D "show=\"$c\"" tilt9g/tilt9g.scad &
  done; wait
  P="pivot=19.625,7.98,-1"   # the pan axis at theta -90 (tilt9g.scad echoes pan_axis_world)
  python3 tools/mockup_html.py --slider=Pan,-90,90 view/tilt_pan9g.html "9 g tilt-pan: the tilt table flat, the pan head pinned to it (camera on the top face)" \
    "Tilt frame=$T/tp_frame.stl:#c8c8c8" "Tilt servo=$T/tp_servo.stl:#555555:0.85" \
    "Spline nub=$T/tp_spline.stl:#f29a00" "Bottom nub + axle=$T/tp_bottom.stl:#4169e1" \
    "Table + pins=$T/tp_table.stl:#3cb371:0.9" "+Spline plate + pins + screw=$T/tp_pan_plate.stl:#9370db" \
    "+Pan frame=$T/tp_pan_frame.stl:#e8c22a:$P" "+Pan servo=$T/tp_pan_servo.stl:#333333:0.85:$P"
  [ $open_ = 1 ] && open -a "Google Chrome" view/tilt_pan9g.html ;;
brickframe)
  for st in false true; do
    for c in side_j side_iic bar_bottom bar_top pins brick; do one bf_${st}_$c -D "part=\"$c\"" -D "stand=$st" scad/brick_frame.scad & done
  done; wait
  for st in false true; do
    out=view/brick_frame.html; [ $st = true ] && out=view/brick_frame_stand.html
    python3 tools/mockup_html.py $out "Cage round the Nezha brick (first draft)" \
      "J side=$T/bf_${st}_side_j.stl:#f29a00" "IIC side=$T/bf_${st}_side_iic.stl:#4169e1" \
      "Bottom end bar=$T/bf_${st}_bar_bottom.stl:#3cb371" "Top end bar=$T/bf_${st}_bar_top.stl:#2e8b57" \
      "2L pins=$T/bf_${st}_pins.stl:#333333" \
      "+Nezha brick=$T/bf_${st}_brick.stl:#eeeeee:0.85"
  done
  [ $open_ = 1 ] && open -a "Google Chrome" view/brick_frame.html ;;
tilttable)
  for c in bottom top; do one tt_$c -D "part=\"$c\"" -D 'theta=0' scad/tilt_table.scad & done; wait
  python3 tools/mockup_html.py --slider=Tilt,-63,63 view/tilt_table.html "Friction tilt table: the same 5 x 5 plate twice, the top one turned over, snapped together on the triangles" \
    "Bottom plate=$T/tt_bottom.stl:#3cb371" "+Top plate=$T/tt_top.stl:#e8c22a:xpivot=0,19.8,1"
  [ $open_ = 1 ] && open -a "Google Chrome" view/tilt_table.html ;;
batteryframe)
  for c in half_a half_b pins battery; do one bat_$c -D "part=\"$c\"" scad/battery_frame.scad & done; wait
  python3 tools/mockup_html.py view/battery_frame.html "LEGO frame round the USB battery (first draft)" \
    "Half A=$T/bat_half_a.stl:#f29a00" "Half B=$T/bat_half_b.stl:#4169e1" "2L pins=$T/bat_pins.stl:#333333" \
    "+USB battery=$T/bat_battery.stl:#eeeeee:0.85"
  [ $open_ = 1 ] && open -a "Google Chrome" view/battery_frame.html ;;
piframe)
  for c in base window_a window_b top_bars pins pi; do one pf_$c -D "part=\"$c\"" scad/pi_frame.scad & done; wait
  python3 tools/mockup_html.py view/pi_frame.html "Frame round a Raspberry Pi (first draft)" \
    "Base (weld posts)=$T/pf_base.stl:#3cb371" "+y window=$T/pf_window_a.stl:#f29a00" "-y window=$T/pf_window_b.stl:#4169e1" \
    "Top bars=$T/pf_top_bars.stl:#2e8b57" "2L pins=$T/pf_pins.stl:#333333" "+Raspberry Pi 4=$T/pf_pi.stl:#1f7a3a"
  [ $open_ = 1 ] && open -a "Google Chrome" view/pi_frame.html ;;
lasercam)
  for c in mount bracket cameras laser; do one lc_$c -D 'part="assembly"' -D "show=\"$c\"" scad/laser_cam_mount.scad & done; wait
  python3 tools/mockup_html.py view/laser_cam_mount.html "Two Arducams and a line laser on the Carvera, with their bracket" \
    "+Mount=$T/lc_mount.stl:#3b7dd8" "+Bracket (new)=$T/lc_bracket.stl:#888888" \
    "+Cameras (stand-ins)=$T/lc_cameras.stl:#1f7a3a" "+Laser=$T/lc_laser.stl:#c9a227"
  [ $open_ = 1 ] && open -a "Google Chrome" view/laser_cam_mount.html ;;
plugtail)
  uv run tools/plug_tail_view.py
  [ $open_ = 1 ] && open -a "Google Chrome" view/plug_tail.html ;;
lbracket)
  for c in bracket pins; do one lb_$c -D "part=\"$c\"" scad/l_bracket.scad & done; wait
  python3 tools/mockup_html.py view/l_bracket.html "5 x 5 LEGO L bracket: holes the whole unit, 1 mm skin inside" \
    "Bracket=$T/lb_bracket.stl:#3cb371" "+2L pins=$T/lb_pins.stl:#333333"
  [ $open_ = 1 ] && open -a "Google Chrome" view/l_bracket.html ;;
cutebotcage)
  for c in nose lobe_l lobe_r rail_l rail_r wall_l wall_r front_l front_r skirt_l skirt_r deck_l deck_r rear fwall fside_l fside_r fdeck robot caster pins screws; do one cc_$c -D "part=\"$c\"" scad/cutebot_cage.scad & done; wait
  python3 tools/mockup_html.py view/cutebot_cage.html "Cutebot Pro cage v3 (Lift raises the decks)" \
    "Nose=$T/cc_nose.stl:#e67e22" "Lobe L=$T/cc_lobe_l.stl:#3cb371" "Lobe R=$T/cc_lobe_r.stl:#3cb371" \
    "Rail L=$T/cc_rail_l.stl:#4169e1" "Rail R=$T/cc_rail_r.stl:#4169e1" "Wall L=$T/cc_wall_l.stl:#5dade2" "Wall R=$T/cc_wall_r.stl:#5dade2" \
    "Front bulkhead L=$T/cc_front_l.stl:#c0392b" "Front bulkhead R=$T/cc_front_r.stl:#c0392b" "Rear bulkhead=$T/cc_rear.stl:#a93226" \
    "Skirt L=$T/cc_skirt_l.stl:#d35400" "Skirt R=$T/cc_skirt_r.stl:#d35400" \
    "Front wall=$T/cc_fwall.stl:#a93226" "Front side L=$T/cc_fside_l.stl:#d35400" "Front side R=$T/cc_fside_r.stl:#d35400" \
    "+Deck L=$T/cc_deck_l.stl:#8e44ad" "+Deck R=$T/cc_deck_r.stl:#8e44ad" "+Front deck=$T/cc_fdeck.stl:#7d3c98" \
    "M3 screws=$T/cc_screws.stl:#7f8c8d" "2L pins=$T/cc_pins.stl:#222222" "EV3 ball caster=$T/cc_caster.stl:#444444" \
    "Cutebot Pro (scan stand-in)=$T/cc_robot.stl:#dddddd:0.6"
  [ $open_ = 1 ] && open -a "Google Chrome" view/cutebot_cage.html ;;
*) echo "unknown view $v (servo9g, nezha, plate, front, plates, robot_level, robot_low, robot_front, cutebot, tiltpan, brickframe, tilttable, batteryframe, piframe, lasercam, plugtail, lbracket, cutebotcage)"; exit 1 ;;
esac; done
rm -rf "$T"
