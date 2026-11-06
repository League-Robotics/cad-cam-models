# Geared grippers

Two-jaw LEGO-compatible grippers driven by a pair of meshing 24T gears. The
gears are molded into short **gear arms** that stay in the frame. The jaws are
swappable **extension arms** that pin onto each gear arm's stub with two 2L
LEGO friction pins, 16 mm (2 studs) apart. The pins point at the other jaw, so
gripping pushes the arm further onto them.

## Printable parts: `grippers/`

| Folder | What | Parts |
|---|---|---|
| `arms/` | The gear arms on LEGO axles, shared by every set | `left_arm` (the Nezha motor's driven arm, cross hub), `right_arm` (the idler arm of every set: one plain 4.95 round hole, it turns on the axle the frame holds in cross holes; `idler_hub_pins` brings the four hub pin holes back) |
| `nezha/` | Gripper on the Nezha motor; uses both `arms/` | `frame` |
| `servo_standard/` | Gripper on a standard-size hobby servo; idler is `arms/right_arm` | `spline_arm`, `frame` |
| `servo_9g/` | Gripper on a 9 g micro servo; the frame top is a 3 × 5 block of pin holes, and the idler runs on a 3L axle; idler is `arms/right_arm`. `frame_centred` is the 2026-10-28 revision (`centred = true`): hole grid centred on the jaws (6 columns, the mesh on the 4th), full-unit back wall with 4 rows × 6 holes, the top plate a row longer with 6 holes out of its front face | `spline_arm`, `frame`, `frame_centred` |
| `extensions/` | Swappable arms; fit every set | `can_arm`, `cube_arm`, `cube_low_arm`, `cube_short_arm`, `ball_arm`, each `_left` and `_right` |
| `plates/` | One sheet of parts with first-layer sprues | `all_parts` |
| `brick_frame/` | The cage round the Nezha brick (`scad/brick_frame.scad`, 2026-11-02): four flat prints, each on its outer face, put together with 11 2L pins | `plate` (all four on one bed, 122 x 114), or one at a time: `side_j`, `side_iic`, `end_bar` (print two) |
| `pi_frame/` | The open frame round a Raspberry Pi (`scad/pi_frame.scad`, 2026-11-03): five flat prints, 8 2L pins; weld the Pi onto the base's posts | `plate` (all five on one bed, 114 x 164), or `base`, `window` (print two), `top_bar` (print two) |

Every STL is already in print orientation. The driven arm differs by motor
only in its hub: a LEGO cross-axle hole (`arms/left_arm`, Nezha) or a press-fit
spline socket (each servo set's `spline_arm`; the 9 g one is a plain 4.65 mm
hole). The idler arm is the same `arms/right_arm` everywhere.

- **Left / right:** the left extension arm goes on the driven gear arm (motor
  or spline), the right one on the idler arm.
- **Ball arms** stand on the cup and need supports under their base.
- **Cube arms** print on their outer face with the texture up.
- **Can arms** print flat.

| Arm | Holds | Closed at 0° |
|---|---|---|
| can | 66 mm can | 65 mm ring |
| cube | 26 mm foam cube | parallel paddles, 26 mm apart |
| cube_low | 26 mm foam cube, near the floor | as cube, but an open "racket" paddle (rim + diagonal ribs) 50 long × 62 tall: 16 mm further down and 8 up; swap left and right to put the 8 mm end down. On the Nezha frame it clears to ~29° open |
| cube_short | 26 mm foam cube, low mounts | as cube, paddle 32 tall (3 mm off each end), for mounts where the full paddle would reach the floor |
| ball | 40 mm ball | cylindrical cups, R 20.5 |

Clear opening, checked against frame and motor/servo for all three arms:

- Servo frames (standard and 9 g): 66°
- Nezha frame: 60°

## Viewing assemblies in the browser

`bash tools/make_views.sh [servo9g|nezha|plate] --open` builds self-contained
3D viewer pages in `view/` (three.js, STLs embedded, works from file://), one
checkbox and colour per component, and opens them in Chrome. Each assembly's
`show` parameter exports one component in place; `tools/mockup_html.py` (a part named with a leading `-` starts unticked, e.g. the can arms; a `pivot=x,y,sign` option makes it turn about that vertical axis with the Jaws slider) puts
them on one page. `bash tools/serve_views.sh` serves `view/` on http://127.0.0.1:8768/ so a page opens in VS Code's Simple Browser (file:// pages open as text there). `tools/bottom_view.py PART.stl OUT.svg` draws a part from
below on the 8 mm cell grid, for marking up changes.

## Sources

Carvera parts are moving to `/Volumes/Proj/proj/robot-projects/carvera/design/`
(read its `AGENTS.md`). The camera bracket (was `carvera_angle.scad`) and the
two-camera laser mount (was `laser_cam_mount.scad`) moved there on 2026-11-06.

`scad/` holds the OpenSCAD sources:

| File | What |
|---|---|
| `gripper.scad` | Gear sector, original ring arm, Nezha 1U frame (library) |
| `swap_gripper.scad` | Gear arms (`nub` in the code) and the can / cube / ball extension arms. The can ring's rear ends (where it completes the circle inboard of the beam) are cut flat `ring_trim` (3.1) up from their lowest point so the closed arms clear the Cutebot gripper's caster beam (2026-10-29; 0 for the full ring), the cut meeting the base's inner face with a `ring_trim_r` (2) fillet. The ring is turned `can_ring_rot` (15) on the arm and then `can_ring_open` (5) about the axle relative to the stub (2026-10-29: the halves concentric with the arms 5 open), so gripper.scad's unchanged tips (10 mm thinned on opposite faces) meet on the centre line at theta 6.8, the halves are concentric at 5 and the tips lap fully at 4.3, the closing limit (past it the thick parts jam; the lap grows 3.9 mm per degree); `view/cutebot_can_ring.png` shows the ring closing |
| `nezha_gripper.scad` | Nezha set: assembly, parts, `clash` check |
| `servo_gripper.scad` | Servo sets (`servo = "standard"` or `"9g"`): assembly, parts, `clash` check; `jaw = "ring"` gives the old one-piece arms. `centred = true` (9 g, 2026-10-28, used by the block and Cutebot grippers): the hole grid centred on the gear mesh (`grid_z`, 6 columns about `mesh_z`; the axles sit 1.5 units off it, so the axle row keeps only the holes 12 from an axle), the wall behind the arm layer a full unit (`wall_t`) with a 4th row of holes (`lego_y`), the top plate's rows 3.9 in from the back face (`top_rows_x`: the axles 1.9 ahead of the first) and its front face one row further out at the gear teeth's reach, with blind holes (`front_hole_depth`, `front_skip`) in it for a caster or a part pinned on ahead. The default keeps the original frames unchanged |
| `lever_gripper.scad` | CONCEPT (2026-10-26): gearless gripper on a horizontal 9 g servo. Servo on edge, shaft forward between the jaw axles; vertical double horn with a ball on each tip; each jaw is a lever on a vertical axle with the swappable-arm stub and a fore-aft fork that straddles its ball (left jaw's fork over the upper ball, right jaw's under the lower one; both jaws are one part turned over). `phi` is the servo angle (-45 closed, +45 open, 53 deg of jaw); `show` = "all", "jaw", "clash", or one component. Pictures: `view/lever_gripper_concepts.png` (four concepts), `view/lever_gripper_mockup.png`, viewer `view/lever_gripper.html` |
| `swap_plate.scad` | The all-parts plate layout |
| `swap_plate_sprues.scad` | The plate's sprue bars (generated) |
| `lego.scad` | Include this for any LEGO Technic feature: pulls in `lib/Technic.scad` ([cfinke/Technic.scad](https://github.com/cfinke/Technic.scad): beams, pins, axles, connectors, gears) and adds `technic_pin_hole()` (exact LEGO hole, for models of real parts) and `pd_pin_hole()` / `pd_axle_hole()` (print-tuned holes from the League's Part Designer, lego3d.jointheleague.org; use these on anything we print) |
| `reflectance_sensor.scad` | The robots' 4-channel reflectance sensor with its LEGO brackets, from a scan (`models/reflectance_sensor_top_scan.stl` is a later scan of the board's top face, registered to the same coordinates on the bracket holes) (`part = "overlay"` shows `models/reflectance_sensor_scan.stl` over it); `pin_holes()` and `rs_holes` for parts that mount to it; the four cans' positions are from the top scan's solder-pad columns (2026-10-29), their TCRT5000 size from a photo |
| `front_plate.scad` | Sensor plate with the 9 g gripper frame built onto its front. Exact geometry only where something mates: the horns (the two beams into the robot), the gripper frame (arm bearing, pivot, idler axle, the servo's tab legs), the pin holes, the casters' seats, and pockets under the frame floor for what stands on the board's top (the sensors' clips, the button, two solder rows), measured on `models/reflectance_sensor_top_scan.stl`. Everything else is `models/front_plate_body.stl`, made by `tools/front_plate_body.py`: a smoothed hull-like lid with filleted posts down to the sensor, and the cable U, arm sweep and caster spaces carved out with rolled edges (re-run it with `uv run tools/front_plate_body.py` after moving anything it wraps). `part = "required"` shows the mating surfaces alone; `part = "control"` is just the control surfaces (the gripper frame, the horns, the servo tab seat, the sensor pads on the side brackets (pinned) and middle bracket (flat: the jack covers its holes), the caster seats, holes cut; print file `grippers/sensor_plate/control_surfaces.3mf` / `.stl`, `part = "control_print"`); `part = "clash_*"` checks it. Two LEGO EV3 ball casters (`models/ev3_ball_caster/`, SquareD's model, thing:622701, CC BY-SA) turned 90 degrees, slide on from the sides onto pins into seats beside the cable, set `caster_drop` (5 mm) below the robot's floor line so they bear on every robot Print files: `grippers/sensor_plate/front_plate_print.3mf` (clean manifold; prefer it) and `.stl`, frame floor down on the bed, support under the deck and horns |
| `robot_plate.scad` | The bought 11 x 19 Technic panel plate (LEGO 39369's shape: pin holes through every cell, a horizontal hole in from the face at every even cell round the edge) with the cut for the reflectance sensor, exactly on the cell edges: `hole = "3x4"` (columns 5-7, rows 5-8; the sensor under the plate, pinned at row 4 with its jack up through the hole and its PCB edge at the plate's front edge), `"3x3_9"` (the default and the one cut since 2026-10-30: 3x3 at rows 9-11, the sensor pinned at row 8; the user walked the hole back from 5-8 over four plates), `"cans"` (the sensor standing on top of the plate on its brackets, pinned at row 5 from below, with a pocket through the plate for its cans, one row behind the front so row 1's holes stay free, the middle two cans sharing one pocket since the 4.2 web between them did not survive the first cut, and the pockets' front edge 1.5 further forward (`can_front_ext`) since the cans did not clear it, the back edge 0.5 further back (`can_back_ext`) (2026-10-30); the cans at x = +-6 and +-30, 20.45 ahead of the bracket row, on the solder-pad columns of the top scan (2026-10-29), the body size still a guess, so `can_clear` is 1.0) or `"3x3"` (rows 6-8, the plate cut so far; its job ran 1.65 past the front cell edge, which is dropped). Cells count from the front-left corner, the plate held with its 19 side up and down. `part = "assembly"` puts the sensor in place; `"cam"` is the plate in the Carvera job's coordinates. Drawing: `view/robot_plates_drawing.png` (`tools/plate_drawing.py`), viewer `view/robot_plates.html` |
| `caster_post.scad` | The caster post (2026-10-28): a separate flat print for the grippers that stand on the EV3 ball caster ahead of the jaws (since 2026-10-29 every stance of the block gripper and the Cutebot gripper has one, its name etched in its top). Its back face is the centred frame's front face (the gear teeth's reach); two blind pin holes mate with the floor's front-face holes at x = +-8, two more in its front take the caster's pins; the post is a box from the floor's bed face or the beam's bottom up to the beam's top or the floor's top, with a pocket in its front for the caster's housing, which widens behind the beam face below the beam (`housing_prof`, from the caster model; the user measured its widest, 8.3), and `post_depth_for(floor_z, caster_top_z, min_depth)` makes it as shallow as the mating holes allow: `pin_wall` (0.8) between their bottoms and the pocket, or 8 + wall + 8 when they share a height band with the caster's pin holes (16.8), and at least `min_depth`: `post_min_depth(arm_z, caster_top_z)` gives `ring_post_depth` (17) when the beam is in the arm layer, which the closed can arms' trimmed ring ends need (so 17.0 on the Cutebot and the low stance, 17.55 on front, where the housing wants more). Also the caster model, `caster_on_post`, a 2L pin model and the mating pins. `caster_post(y_face, floor_z, pin_x, caster_top_z, min_depth, label)` in place, `caster_post_print` on its back face (every hole vertical) |
| `block_gripper.scad` | The 9 g gripper on the front of the two-plate robot (plates 3 units apart on the Nezha motors), since 2026-10-29 built from the Cutebot gripper's pieces: three flat prints pinned with 2L pins and glued. The frame is the centred 9 g frame turned over (the same print as the Cutebot's, unlabelled: floor of pin holes ahead of the robot, jaws centred on the plate with the axles at x = +-12, a full-unit back wall with 4 rows x 6 columns of holes facing the robot). The block (5 wide x 3 deep x 2 high; 3 with `sensor_mount = "under"`) sits between the plates on the front 3 rows, 10 pin holes down through its back two rows into the top plate (and the bottom plate when 3 high), and its front row given over to two rows of 5 blind holes in its front face that pin into two of the frame's wall rows. The frame's height is which wall rows meet the block's (`stance`: rows 8 apart, so the old 0 / 4.15 / 15.4 drops became 1 / 9 / 17): `"level"` the 2nd and 3rd rows (wall top 43, the floor 0.9 below flush, the top row pins into the top plate's edge holes at x = 0, +-16; cube paddles 16.4 off the ground), `"low"` the top two rows (wall top 35; the bottom row into the bottom plate's edge holes; paddles 8.4), `"front"` the top row on the block's lower row (wall top 27; the 3rd row into the bottom plate's edge holes; paddles 0.4). The caster post (`caster_post.scad`, one per stance with its name etched) pins into the floor's front-face holes at x = +-8 with the caster's beam top 28 over the ground: 16.8 / 17.0 / 17.55 deep. The can arms close clear of the caster in level and low (checked at theta 5 and 4.3); not in front, where the arm layer is under the beam and the ring's rear ends hit the housing's flare however the post is placed, so front is for the cube paddles. `sensor_mount = "top"` (the cans plate, the default; the block clears the sensor's parts) or `"under"` (the 3x4 plate). `part = "frame"` / `"block"` / `"post"` in place, `"print_*"` on the bed, `"clash"` / `"arm_clash"` / `"fit"` / `"caster_fit"` / `"block_fit"` check the arms / the arms against each other / the sensor / the caster / the block (`"clash_view"`, `"ring_view"` as the Cutebot's); `show` exports each component in place; `tools/robot_pics.py` makes `view/block_gripper_stances.png` (the three stances, labelled) and `view/block_gripper_pieces.png` (the prints); viewers `view/block_gripper_{level,low,front}.html` (the can arms unticked; Jaws slider) |
| `cutebot_gripper.scad` | The 9 g gripper on the front of the Elecfreaks Cutebot Pro, with its own caster (2026-10-28, replacing the user's hacked servo-kit gripper). Three prints, each flat, pinned together with 2L friction pins and glued: the frame (the centred 9 g frame turned over: floor of pin holes ahead of the nose, servo up, the full-unit back wall's 4 × 6 holes facing the nose; prints on its back wall; since 2026-10-29 the same print as the block gripper's, unlabelled), the tab (a 5-hole beam-shaped plate on the nose over its two bosses: counterbored M3 holes at x = +-8, pin holes at 0, +-16, and 5 pin holes in its front edge into one wall row, `tab_row`; prints flat) and the caster post (`caster_post.scad`, pinned into the floor's front-face holes at x = +-8, the EV3 caster on its front, "Cutebot" in its top; prints on its back face). Robot coordinates: X across, Y back from the nose's tip, Z up from the ground. `front_h` = 18.6 (the chassis PCB's underside at the front, measured, for level), `nose_t` = 1.5 (the PCB; the tab lies on it) and `boss_h` = 1.5 (the bosses stand proud, inside the tab's holes) set the tab's height, and with `tab_row` (the top row) the frame's height in steps of a wall row (`paddle_z0` echoed: 4.0); `boss_back` (13.5, a guess) the screw holes' row. `part = "frame"` / `"tab"` / `"post"` in place, `"print_*"` on the bed, `"clash"` / `"arm_clash"` / `"caster_fit"` check the arms against the pieces / each other / the caster (`"clash_view"` shows what the arms hit in red on the see-through assembly, `"ring_view"` colours the two swappable arms apart); `show` exports each component in place; `tools/cutebot_pics.py` makes `view/cutebot_gripper.png` (section, iso, the three prints) and `view/cutebot_can_arms.png` (the can arms closed: with `ext = "can"` they close clear of the caster, its post 17.0 deep and the ring ends trimmed, 2026-10-29); viewer `view/cutebot_gripper.html` (the can arms are in it unticked; its Jaws slider turns the arms about the axles). Prints in `grippers/block_gripper/` (frame, cutebot_tab, post_cutebot) |
| `brick_frame.scad` | FIRST DRAFT (2026-11-01/02): a cage round the Nezha brick (`models/nezha_breakout_v2.stl`), the edges of a box, for more attachment points and to turn it any way up, e.g. stood on its motor end at the front of a robot, display and switch forward, the micro:bit's USB end up. 11 x 11 units in plan, 6 high: a ring at the brick's bottom (pinned to it), a copy at its top (4.1 over the ridge) and a post up each corner. Across, the brick's 60 is centred in 88; each side is only its outer unit, leaving 6.2 between it and the brick all round for cables, bridged only by a pad at each of the brick's side pins (2026-11-02); along, its 80 plus one unit at the motor end. The micro:bit end has posts but no bars. Holes alternate along every edge, turned 90 degrees cell to cell: rails out / up from out at each corner, posts across / out, end bars along / up from along at the middle (the posts' tops have out twice, where two alternations meet). Each of the brick's four side holes has an arch in front that is a LEGO beam's rounded end, so the bottom rail's pad at each has a beam end (`tongue_r`, `tongue_clear`) in each arch with the pin's hole through it. Four flat prints pinned with 2L pins: the J and IIC sides (windows: bottom rail, top rail, two posts; mirror images) and the end bar (x2, 9 units, out to the sides; the bottom one pins into three of the brick's five end holes). The brick's own coordinates (x along, -40 the micro:bit end; +y the J side; bottom at z = 0); `stand = true` stands it up. `part` = `"assembly"`, `"side"`, `"end_bar"`, `"print"` (each on its outer face); drawings from `tools/brick_frame_pics.py` (`view/brick_side_holes.png`, `view/brick_frame_cage.png`, `view/brick_frame_plan.png`, `view/brick_frame_stand.png`); viewers `view/brick_frame.html` and `view/brick_frame_stand.html` |
| `tilt_table.scad` | (2026-11-01) A hand-set friction tilt table for small cameras (Pi / Arduino camera boards). Two 5 x 5 plates, the same print twice, the second turned over; each has triangles standing up on its two hinge edges, apex at the axis: a fork (+x: two 2.5 tines, a 3.5 slot, a divot in each tine's inner face) and a tongue (-x, where the slot would be: 2 * `squeeze` (0.1) thicker than the slot, a 45 deg cone bump, r 2.5, 0.4 high, on each face). Turned over, each plate's tongue snaps into the other's fork: the tines clamp it, the bumps in the divots are the pivot, the squeeze is the friction. (The first draft, one ear in and one out per plate, did not clamp: the plates slid apart sideways.) Third version (2026-11-03, after the second print popped apart: the 0.4 bumps never seated, the tongue 0.2 over the slot bowed the tines out, the 0.2 teeth printed as a texture): a hole through each tine on the axis (r 2.75) instead of a divot, buttons 1.2 high (r 2.6, sides 50 deg off the face), `squeeze` 0, and teeth with 35 deg flanks from r 4.5 to r 9 (0.4 to 0.8 high), the grooves `click_clear` 0.1 deeper; between clicks each tine spreads up to 0.74 and the buttons stay 0.46 in. Fourth version (2026-11-03, the third snapped well but locked: barely movable, and not back from the limit without pliers): the teeth half as high, `click_flank` atan(tan 35 / 2) = 19.3 deg (0.2 to 0.4 high); between clicks each tine spreads up to 0.37, the buttons stay 0.83 in. The first print worked as wanted (2026-11-01). Clicks (2026-11-01): `clicks` (24) radial teeth round the axis, 15 deg apart (flat is one), `click_h` (0.2) high, from r 3 to r 7, raised on the tongue's faces and sunk as grooves in the tines'; at a click each ridge sits in a groove (just the squeeze), between clicks they spread each tine another 0.2; `clicks = 0` is the smooth table. Triangle outline (2026-11-01, fit and finish): the room the other plate leaves as it tilts, less `roll_gap` (0.4): an arc r 11.8 round the axis over the top (the other plate's underside rolls round it) and straight sides the other plate lies parallel to at the +-63 limits, landing 19.35 out (the first print had an r 6 apex and sides from the corners). Prints 31.6 tall. Knobs: `click_flank` (click strength), `clicks` (must be even), `squeeze`, `bump_h`, `tine_t`. Plates `pitch` (4) units apart when flat (a 5 x 5 x 5 block), tilt +-63 (the plates meet). Pin holes have Part Designer's taper on the bed (mounting) face; the two columns under the triangles are blind, 8 deep from that face. `part` = `"plate"` (the print), `"print"` (two on the bed), `"assembly"` (at `theta`), `"clash"`, `"bottom"` / `"top"`; prints `grippers/tilt_table/` (`make_parts.sh tilt_table`: plate, plate_x2, plate_smooth); drawing `view/tilt_table.png` (`tools/tilt_table_pics.py`); viewer `view/tilt_table.html` (Tilt slider) |
| `pi_frame.scad` | FIRST DRAFT (2026-11-03): an open frame round a Raspberry Pi, the Nezha cage's 11 x 11 footprint, 5 high, the edges of a box with holes on every face. The Pi lies flat, centred, 13.8 up on four weld posts copied from the user's Yahboom encoder mount (verified to fit: a 6 mm support 6 tall and a 2.4 mm pin 3 tall, melted down over the board; 57.7 x 48.5 apart, a little under the Pi's published 58 x 49), standing on two deck bars across the bottom at y = +-24; its USB and Ethernet face out of the +x end window (0.8 past the face, 1.0 under the top bar), power and HDMI out of a side window. Holes alternate cell to cell as on the cage (5 high lets the posts alternate cleanly). Five flat prints, three designs, pinned with 8 2L pins: the base (end bars, deck bars, weld posts), the window (x2, one print) and the top bar (x2). `part` = `"assembly"`, `"print"`, `"print_base"` / `"print_window"` / `"print_top_bar"`; drawings `tools/pi_frame_pics.py` (`view/pi_frame_views.png`, `view/pi_frame_plate.png`), viewer `view/pi_frame.html` |
| `raspberry_pi.scad` | An approximate Raspberry Pi 4 (board, holes, blocks for the connectors that set clearances) from the published mechanical drawing, for laying out frames: `raspberry_pi4()` |
| `models/` | Reference models the sources import: Nezha frame and motor, standard servo. `servo_9g.stl` is kept for reference only: its heights are wrong, so the 9 g servo is modelled from caliper measurements (`servo_9g_dims.png`). `nezha_breakout_v2.stl` is the ELECFREAKS Nezha Breakout Board V2 (the "brick") with its micro:bit, one low-poly solid for laying out robots (2026-11-01): the envelope caliper-measured, 80 front to back x 60 x 43.7 high, the micro:bit shelf 31.5 and the button's surface 40 up (`nezha_breakout_v2_dims.svg`), its Technic holes (8 mm pitch, 4.0 above the bottom; on each long side two normal holes, each behind an arch open to the bottom edge (all four alike, 2026-11-02), 1.86 deep, the user's measurement, exactly a LEGO beam's rounded end: Technic.scad's beam width, 7.36) and 4P4C sockets (12.8 pitch) measured on a 3D scan; `nezha_breakout_v2.glb` is the same in colour for viewers. Both are made by `tools/nezha_breakout.py` (manifold3d; every dimension is a named constant at its top; the button is modelled off, `BUTTON_ON` for on) |

`cam/` holds the Carvera G-code for the plates' cuts, from `tools/plate_gcode.py`
(the job of `CAM/RobotPlate/robot_plate.nc`: 2 mm corn cutter, T1 since
2026-10-30 (T3 in the first job), 12000 rpm, 500 / 300 mm/min, 0.3 mm passes
through the 7.7 mm plate, contours with 2 mm tabs (the first plate's 1 mm tabs let every slug but the 3x4's pop out); Z probe at X40 Y24 from the
work origin, a cell corner below and ahead of the hole): three one-plate jobs, `plate_hole.nc` (the 3x3 sensor hole at rows 9-11),
`plate_pockets.nc` (the can pockets, the middle two run together) and `plate_hole_and_pockets.nc`
(both). Origin at the plate's front-left corner, front edge on X = 0. The
script can also lay plates out two by two (`--nx 2 --ny 2`, 302.4 x 176 mm)
or stack two (`--layers 2`, unverified: the tabs hold only the bottom piece
and the cutter needs the reach).

`tilt9g/` is the 9 g frame as a tilt table. `tilt9g.scad` includes
`servo_gripper.scad` and adds three LEGO units under the servo: a plate, an
arm layer for a flipped idler arm (`arms/right_arm`) on the spline axis, and a second plate. With
the gripper's idler arm left out, the spline arm folds flat, and a plate
pinned across both stubs tilts about the spline axis (θ −110 to +50, flat at
−90). Since 2026-10-31 the frame holds the bottom 3L axle still in cross holes
(P1, P2) and the bottom arm turns on it, as in the 9 g gripper; the table is a
printable 3 × 7 plate of pin holes. `pan9g.scad` is the camera pan head that
pins to the table's middle 3 × 3 (tilt first, then pan): the 9 g servo upside
down in the pan frame, an L (2026-10-31): a top over the servo's bottom end
with 4 × 5 pin holes for the camera and one side, a unit thick, down the
servo's length with 4 × 5 (the shared corner row alternates top, side, top,
side, top); just a tab-wide leg under each tab for its screw, solid down to
the top, the wire turning out the open side in a groove in the wire-end
leg (`view/tilt_pan9g_wire.png`); prints on the pin side's face. Its spline pressed into a 3 × 3 spline
plate (round 4.65 socket 3.5 deep, a 1.2 shelf, the horn screw from the
table side with its head in a 4.6 counterbore; no tube and recess). The pan
axis is 5.4 off the camera grid's middle column. `bash tilt9g/export.sh`
writes the prints (`frame.stl`, `table.stl`, `pan_frame.stl`,
`spline_plate.stl`, all in print orientation) and the `view/` meshes;
`make_views.sh tiltpan` builds `view/tilt_pan9g.html` (table flat, Pan
slider) and `view/tilt_pan9g.png` is the labelled section. The
`tilt9g-viewer` launch entry (or `python3 -m http.server 8767 --directory
tilt9g`) serves `index.html`, an animated three.js view, at
<http://localhost:8767/>.

`solidcraft/` holds the SolidCraft designs: `gripper_9g.solidcraft` is the 9 g
gripper as a jointed assembly (servo, frame, both gear arms, axle) with a `Grip`
motion study, and `gripper_9g.gif` its animation. The MCP server in
`.mcp.json` may save into this folder.

`tools/` holds the scripts:

| File | What |
|---|---|
| `make_parts.sh` | Exports every STL into `grippers/` (`block_gripper` set, the pinned grippers since 2026-10-29: `grippers/block_gripper/frame.stl` (one frame for every robot, on its back wall), `block.stl` (the two-plate robot's mount, flat), `cutebot_tab.stl` (flat), `post_{level,low,front,cutebot}.stl` (on their back faces); `servo_9g` set also `frame_centred.stl`) |
| `front_plate_body.py` | Builds the front plate's smooth connecting body (distance fields, smooth union, marching cubes) into `scad/models/front_plate_body.stl`; run with `uv run` |
| `plate_sprues.py` | Picks the plate's sprue bars; run it after moving parts on the plate |
| `plate_gcode.py` | Carvera G-code for the robot plates' cuts (`cam/`): `--hole 3x3|3x4|3x3_9|cans|<hole>_cans --nx --ny --layers --gap --tool --tool-number --step --feed --plunge` (defaults: the 2 mm corn cutter job); `3x3_9_cans` is both cuts in one plate |
| `plate_job_pic.py` | A plate job's toolpath drawn on the cell grid (`view/robot_plate_3x4_cans_job.png`) |
| `plate_drawing.py` | `view/robot_plates_drawing.svg/.png`: both plates cell by cell with the sensor, and the Carvera lay-up |
| `robot_pics.py` | Labelled pictures of the block gripper (`uv run --with pillow tools/robot_pics.py [stances] [pieces]`): `view/block_gripper_stances.png` (side section and front view of each stance, which wall rows take the pins, the level assembly from the front-left) and `view/block_gripper_pieces.png` (the prints on the bed) |
| `cutebot_pics.py` | Labelled side section, iso and the three prints of the Cutebot gripper (`uv run --with pillow tools/cutebot_pics.py`): `view/cutebot_gripper[_side|_iso|_parts].png`, and the closed can arms over the caster, `view/cutebot_can_arms[_top|_side].png`; reads the scad's `echo()` values for the dimensions |
| `brick_frame_pics.py` | Labelled drawings of the Nezha brick's side holes and the cage round it, cut from the meshes (`uv run tools/brick_frame_pics.py`): `view/brick_side_holes.png`, `view/brick_frame_cage.png`, `view/brick_frame_plan.png`, `view/brick_frame_stand.png` |
| `pi_frame_pics.py` | Labelled drawings of the Pi frame (`uv run tools/pi_frame_pics.py`): `view/pi_frame_views.png` (above, side, USB end) and `view/pi_frame_plate.png` |
| `scad_view.py` | Live browser viewer: re-exports the parts in `view/targets.txt` whenever a `.scad` file is saved |

Both scripts work from any directory. To rebuild everything, or just some
sets, run:

```bash
bash tools/make_parts.sh
```

```bash
bash tools/make_parts.sh servo_9g extensions
```

### Live viewer

`tools/scad_view.py` serves `view/` with the Buzzkill viewer
(`tools/buzzkill/serve.py`) at <http://localhost:8766/> and watches `scad/`.
On every save it exports each target in `view/targets.txt` to
`view/<name>.stl`, and the page reloads the newest one. The `scad-viewer`
entry in `.claude/launch.json` starts it in the Claude app's browser sidebar.
To run it from a terminal instead:

```bash
python3 tools/scad_view.py
```

`view/targets.txt` takes one `name: file.scad var=value ...` line per part.
Each `var=value` becomes an OpenSCAD `-D` override, and the file is re-read
on every change:

```
left_arm: scad/gripper.scad part="left"
nezha_frame: scad/nezha_gripper.scad part="frame"
```

A failed export prints the OpenSCAD errors and leaves the last good STL in
place.

## Circuit boards: `pcb/`

The Carvera-milled PCBs, brought in on 2026-11-03 from the standalone
`/Volumes/Proj/proj/CAM/nezha-qwiic` repo (its history stays there). See
[pcb/README.md](pcb/README.md): the Nezha 4P4C-to-Qwiic adapter (top level),
`wire-hub/`, and `plug-tail/` (boards that slide into the back of a 4P4C plug,
for servos and Qwiic). KiCad 9, pcb2gcode and the build scripts run on Buzzkill
(`ros@buzzkill.local:~/projects/nezha-qwiic`); copy results back here.
`uv run tools/plug_tail_pics.py [STOCK_MM]` draws the plug tail in the cable
cavity (`view/plug_tail_section.png`); `bash tools/make_views.sh plugtail` builds
`view/plug_tail.html`, both tails in 3D with a checkbox per layer (F.Cu, mask, paste,
silk, fab, courtyard, Edge.Cuts) plus the isolation and outline cuts read back from the
Carvera program. Refresh `pcb/plug-tail/exports/layers.json` with
`scripts/dump_layers.py` on Buzzkill after the boards change.

## `archive/`

Earlier work, kept for reference:

- the one-piece ring arms and their renders
- the old servo arm STLs
- the motor brackets
- the Tinkercad reference files
- the first `stl_swap` export
- a backup of the SCAD files from before the swappable-arm refactor

Paths inside the archived files were not updated.

## Headless SolidCraft on Buzzkill

`.mcp.json` also defines `solidcraft-buzzkill`: the SolidCraft MCP server run
headless on Buzzkill over ssh (`tools/buzzkill/solidcraft-remote.sh`). It reads
and writes `~/designs/gears` there. Meshes exported into
`~/designs/gears/view/` show up live at <http://buzzkill:8765/> (three.js
viewer, follows the newest file). `tools/buzzkill/sync.sh deploy` copies the
scripts to Buzzkill; `sync.sh pull` copies saved designs into
`solidcraft/buzzkill/` to open in the Mac app.

`solidcraft-buzzkill-gui` drives the full SolidCraft app instead, running on
Buzzkill in a virtual display (`tools/buzzkill/gui.sh`: Xvfb `:77`, control
port 7878, x11vnc, noVNC). Everything listens on Buzzkill's localhost;
`tools/buzzkill/sync.sh vnc` starts it and tunnels noVNC to
<http://localhost:6080/vnc.html?autoconnect=1&resize=scale>.
