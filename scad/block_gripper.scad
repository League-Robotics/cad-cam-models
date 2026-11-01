// Block gripper: the 9 g servo gripper (servo_gripper.scad) on the front of
// the two-plate robot, built from the Cutebot gripper's pieces (2026-10-29,
// the user's redesign: one frame print for every robot, a mount per robot,
// a caster post per height; the one-piece prints with their bars, bracket
// and breakaway tilt base are gone).
//
// The robot: two 11 x 19 plates (robot_plate.scad) stacked with the Nezha
// motors between them, 3 units apart, the motors along the length with the
// wheels out the sides. The reflectance sensor stands on top of the bottom
// plate (its cans down in the "cans" plate's pockets) or hangs under it
// with its jack up through the 3x4 hole (`sensor_mount`). The front rows
// between the plates are free, and that's where the mount goes.
//
// Three prints, each flat on the bed, pinned together with 2L friction
// pins and glued:
//   frame  the centred 9 g frame (servo_gripper.scad `centred`) turned over:
//          its top plate is a floor of pin holes ahead of the robot, the
//          servo standing up from it, the hole grid centred on the jaws
//          (axles at x = +-12, the grid on the plates' columns), a full-unit
//          back wall with 4 rows x 6 columns of holes facing the robot, and
//          6 holes forward out of the floor's front face. The same print as
//          the Cutebot gripper's (cutebot_gripper.scad), unlabelled; prints
//          on its back wall.
//   block  the mount: 5 wide x 3 deep x 2 high (3 with the sensor under the
//          plate) between the plates on the front 3 rows, with pin holes
//          down through its back two rows (10, up into the top plate's
//          holes; "under": and down into the bottom plate's), and its front
//          row given over to horizontal holes: two rows of 5 blind holes in
//          its front face, one per unit of height, that take pins into two
//          of the frame's wall rows. Prints flat.
//   post   the caster post (caster_post.scad): pins into the two floor
//          front-face holes between the jaws (x = +-8) and carries the EV3
//          ball caster on its front, just ahead of the gear teeth, its beam
//          top at caster_h over the ground. One per stance, its name
//          etched in its top; prints on its back face.
//
// Heights: the block hangs from the top plate, so its two rows of holes are
// at z 28 and 20 (4 and 12 under the top plate's cell), and the frame's
// height is which of its wall rows (8 apart) meet them (`stance`):
//   "level"  the 2nd and 3rd rows: wall top 43, the floor 0.9 below flush
//            with the bottom plate; the wall's top row is at the top plate's
//            front-edge holes (z 36), so 3 more pins go straight into those
//            (x = 0, +-16: the plate's even edge cells on the wall's columns)
//   "low"    the top two rows: wall top 35, the gripper 8 lower; the wall's
//            bottom row (behind the arm layer) is at the bottom plate's
//            edge holes (z 4): 3 pins into those
//   "front"  the top row on the block's lower row (the block's upper row
//            stands above the frame): wall top 27, 16 lower, the cube
//            paddles 0.4 off the ground; the wall's 3rd row at the bottom
//            plate's edge holes: 3 pins
// (the old stances, one-piece prints with a bracket or a tongue, had drops
// of 0, 4.15 and 15.4; the pinned block quantises them to the wall rows).
// The post then holds the frame at that height: its holes are placed for
// the caster's beam top at caster_h over the ground, as deep as its holes
// and the housing need (post_depth_for), and at least ring_post_depth
// where the beam is in the arm layer (the closed can arms' ring ends).
// The can arms close clear of the caster in "level" and "low" (checked at
// theta 5 and 4.3, where they are closed); not in "front": there the arm
// layer lies mostly under the beam, where the housing flares 5.65 ahead of
// and behind it, so the ring's rear ends hit the housing however the post
// is placed (deeper, and more of it is in the ring; shallower, and the beam
// is). "front" is for the cube paddles.
//
// Robot coordinates (robot_plate.scad): X across, Y back from the plates'
// front edge, Z up from the bottom plate's cell; the bottom plate's cell is
// z 0..8, the motors 8..32, the top plate 32..40, the ground at floor_z.
//
// part: "assembly" (the whole robot front), "frame" / "block" / "post" (one
// piece in place), "print_frame" / "print_block" / "print_post" (on the
// bed), "clash" (what the arms hit in the pieces, pins, plates and caster at
// theta; empty = clear), "clash_view" (the same in red on the see-through
// assembly), "arm_clash" (the two arms against each other), "ring_view"
// (the two swappable arms in their own colours), "fit" (what the sensor
// hits in the pieces, plates, motors and caster; empty = clear),
// "caster_fit" (what the caster hits; empty = clear), "block_fit" (what the
// block hits in the plates, motors and sensor; empty = clear), "section"
// (the assembly cut at x = section_x, for a side view).
// show: in the assembly, "all" or one component in place: "frame", "block",
// "post", "pins", "servo", "spline_arm", "idler_arm", "left_ext",
// "right_ext", "axle", "caster", "bottom_plate", "top_plate", "motors",
// "pcb", "brackets", "back_parts", "sensors", "floor"; hide: components
// left out of "all" (pictures).

include <servo_gripper.scad>
include <lego.scad>
include <caster_post.scad>
use <reflectance_sensor.scad>
use <robot_plate.scad>

servo = "9g";
jaw = "nub";
centred = true;
show_part = false;      // servo_gripper.scad draws nothing itself

/* [View] */
part = "assembly";
show = "all";
hide = [];
section_x = 0;
ext = "cube";           // the swappable arms shown
theta = 0;

/* [Robot] */
stance = "level";               // "level", "low" or "front" (see above)
u = 8;
lego_plate_t = 7.8;             // the bought plates (plate_t is the frame's floor in servo_gripper.scad)
gap_units = 3;                  // the Nezha motors between the plates
top_z0 = u + gap_units * u;     // 32: the top plate's cell
sensor_mount = "top";           // "top" or "under" (see above)
TOP = sensor_mount == "top";
hole = TOP ? "cans" : "3x3_9";  // the bottom plate's cutout (robot_plate.scad)
top_hole = "none";              // the top plate's
sensor_row = TOP ? 5 : 8;       // the sensor's side-bracket hole row: under: the hole is 3x3 at rows 9-11 since 2026-10-30 (was 4, the 3x4 at rows 5-8); top: cans one row behind the front
motor_row = TOP ? 6 : 4;        // the motors' front end: rows 1-3 free for the block; the top-mounted sensor takes rows 1-5
deck_h = 24.5;                  // the bottom plate's underside above the ground, on the wheels (measured)
floor_z = (u - lego_plate_t) / 2 - deck_h;   // the ground, -24.4
sensor_z0 = (u - lego_plate_t) / 2 + (TOP ? lego_plate_t + 4.2 + 1.6 : -2.2);   // the PCB back: brackets standing on the plate / hanging under it
can_bottom = sensor_z0 - 1.6 - 7;
edge_x = [-32, -16, 0, 16, 32]; // the plates' front-edge holes (every even edge cell)

/* [Block] */
block_w = 5;
block_d = 3;
block_h = TOP ? 2 : 3;          // units; "under": down to the bottom plate
block_z1 = top_z0 - pd_edge;    // against the top plate
block_z0 = block_z1 - (block_h * u - 2 * pd_edge);   // 16.2 (top) / 8.2 (under)
block_x = [for (i = [0 : block_w - 1]) (i - (block_w - 1) / 2) * u];   // its columns, -16..16: the frame's wall columns
block_row_z = [for (i = [0 : block_h - 1]) top_z0 - u / 2 - i * u];    // its rows of horizontal holes: 28, 20 (, 12)

/* [Stance] */
// the wall row (an index into lego_y, 0 the top row) that meets the block's
// upper row; -1: the top row meets the block's lower row
frame_row = stance == "level" ? 1 : stance == "low" ? 0 : -1;
wall_top_z = frame_row >= 0 ? block_row_z[0] + lego_y[frame_row] : block_row_z[1] + lego_y[0];
z_servo0 = wall_top_z;                          // robot z of servo y = 0 (the frame's top)

/* [Gripper placement] */
// servo coordinates -> robot: servo x runs back (the axles, servo x = 0, at
// axle_y; the frame's back face, servo x = top_x[1], at back_y, just ahead
// of the plates' edge and the block); servo y runs down from the frame's
// top at z_servo0; servo z across, with the jaws (midway between the axles)
// on x = 0. The wall's hole rows are at servo y = lego_y, so at robot
// z = z_servo0 - lego_y.
back_y = -0.1;                                  // the frame's back face
axle_y = back_y - top_x[1];                     // the axles, -21.9
frame_x = mesh_z;                               // 6.625: robot x of servo z = 0
frame_x0 = frame_x - top_z[1];                  // the frame's -x end, -21.9
frame_x1 = frame_x - top_z[0];                  // its +x end, 29.9
floor_y0 = axle_y + top_x[0];                   // the floor's front face, -35.9: the gear teeth's reach
teeth_y = axle_y - gear_r - 1;                  // = floor_y0
module on_servo() multmatrix([[0, 0, -1, frame_x], [1, 0, 0, axle_y], [0, -1, 0, z_servo0], [0, 0, 0, 1]]) children();
floor_z0 = z_servo0 - top_y1;   // the floor's bed face
floor_z1 = floor_z0 + plate_t;  // its top
arm_z = [z_servo0 - arm_y1, z_servo0 - arm_y0];   // the arm layer
paddle_h = 38;                  // the cube paddles, centred on the arm layer (measured)
paddle_z0 = (arm_z[0] + arm_z[1]) / 2 - paddle_h / 2;   // the paddles' bottom
axle_len = 24;
axle_y0 = top_y1 - axle_len;    // the idler axle: the axle 3 down to the bed face
wall_rows_z = [for (y = lego_y) z_servo0 - y];  // the wall's hole rows
grid_x = [for (z = grid_z) frame_x - z];        // the hole columns across: 24, 16, 8, 0, -8, -16
function on_row(z, rows) = len([for (r = rows) if (abs(r - z) < 0.01) 1]) > 0;
block_rows = [for (z = block_row_z) if (on_row(z, wall_rows_z)) z];      // the block rows that meet a wall row
edge_rows = [for (z = wall_rows_z) if (on_row(z, [u / 2, top_z0 + u / 2])) z];   // the wall rows at a plate's edge holes
edge_pin_x = [for (x = edge_x) if (on_row(x, grid_x)) x];                 // the edge holes the wall's columns reach: 0, +-16

/* [Caster] */
// the caster's own dimensions, the post and the caster model: caster_post.scad
caster_top_z = floor_z + caster_h;              // the beam top, the ball on the ground: 3.6
caster_pin_z = caster_top_z - caster_pin_down;  // -0.15
post_pin_x = [-8, 8];                           // the post's mating pins: the floor's front-face holes between the jaws
post_depth_min = 0;                             // a deeper post than the holes need (experiments: -D post_depth_min=...)
post_min = max(post_min_depth(arm_z, caster_top_z), post_depth_min);   // 17 where the beam is in the arm layer ("low", "front"): the can arms
post_d = post_depth_for([floor_z0, floor_z1], caster_top_z, post_min);   // the post's depth
caster_y = floor_y0 - post_d;                   // the caster's beam face

$fn = 48;

/* [Label] */
// the stance's name etched in the post's top, reading the right way up for
// someone standing behind the robot (the frame is unlabelled: it is the same
// print everywhere and nothing else looks like it)
post_label = stance;

// ---------- the pieces ----------

module gripper_frame() on_servo() frame();

module block() difference() {
    translate([-block_w * u / 2 + pd_edge, pd_edge, block_z0]) cube([block_w * u - 2 * pd_edge, block_d * u - 2 * pd_edge, block_z1 - block_z0]);
    // down through the back two rows: into the top plate ("under": and the bottom plate, so tapered both ways)
    for (x = block_x, j = [1 : block_d - 1]) translate([x, (j + 0.5) * u, block_z0]) pd_pin_hole(block_z1 - block_z0, taper = !TOP, ext = 2);
    // the front row: blind holes in from the front face, one row per unit of height, 8 deep
    for (x = block_x, z = block_row_z) translate([x, pd_edge, z]) rotate([-90, 0, 0]) pd_blind_pin_hole(8, ext = 2);
}

module post() caster_post(floor_y0, [floor_z0, floor_z1], post_pin_x, caster_top_z, post_min, post_label);

// the 2L pins: block to frame, frame to the plates' edge holes, post to frame
module pins() {
    for (x = block_x, z = block_rows) translate([x, back_y, z]) pin_2l();
    for (x = edge_pin_x, z = edge_rows) translate([x, back_y, z]) pin_2l();
    caster_post_pins(floor_y0, [floor_z0, floor_z1], post_pin_x);
}

// what the arms hit in the pieces, pins, plates and caster at theta; empty = clear
module clash() intersection() {
    on_servo() arms(theta);
    union() { gripper_frame(); block(); post(); pins(); on_plate() robot_plate(hole); on_plate(true) robot_plate(top_hole); caster_placed(); }
}

// ---------- the robot around it ----------

module on_plate(top = false) translate([0, 0, (top ? top_z0 : 0) + (u - lego_plate_t) / 2]) children();
module on_sensor() translate([0, (sensor_row - 0.5) * u, sensor_z0]) children();

// models/nezha_motor.stl: 71.6 long (x), 31.6 wide (y), z 7.6..31.2 as it
// sits in its frame; turned to run along y, outer face on the plate's edge
module motors() for (s = [-1, 1]) mirror([s < 0 ? 1 : 0, 0, 0])
    translate([-44 + 53, (motor_row - 1) * u - 42.4, 0]) rotate([0, 0, 90]) import("models/nezha_motor.stl");

// on the post, its ball on the ground
module caster_placed() caster_on_post(floor_y0, [floor_z0, floor_z1], caster_top_z, post_min);

function shown(c) = (show == "all" || show == c) && len([for (h = hide) if (h == c) 1]) == 0;

module pieces() {
    if (shown("frame")) color("lightgray") gripper_frame();
    if (shown("block")) color("burlywood") block();
    if (shown("post")) color("darkseagreen") post();
}

module robot() {
    if (shown("bottom_plate")) color("gold") on_plate() robot_plate(hole);
    if (shown("top_plate")) color("khaki") on_plate(true) robot_plate(top_hole);
    if (shown("motors")) color("hotpink") motors();
    if (shown("pcb")) on_sensor() pcb();
    if (shown("brackets")) on_sensor() brackets();
    if (shown("back_parts")) on_sensor() back_parts();
    if (shown("sensors")) on_sensor() sensors();
    if (shown("floor")) color("gainsboro", 0.4) translate([-80, -90, floor_z - 1]) cube([160, 260, 1]);
}

module assembly() {
    on_servo() arms(theta);
    if (shown("axle")) on_servo() axle();
    if (shown("servo")) on_servo() color("dimgray") servo_model();
    pieces();
    if (shown("caster")) caster_placed();
    if (shown("pins")) pins();
    robot();
}

if (part == "assembly") assembly();
else if (part == "frame") gripper_frame();
else if (part == "block") block();
else if (part == "post") post();
else if (part == "print_frame") translate([0, 0, back_y]) rotate([-90, 0, 0]) gripper_frame();   // on its back wall
else if (part == "print_block") translate([0, 0, -block_z0]) block();                            // flat
else if (part == "print_post") caster_post_print(floor_y0, [floor_z0, floor_z1], post_pin_x, caster_top_z, post_min, post_label);   // on its back face
else if (part == "section") difference() {
    assembly();
    color("#d8dde2") translate([section_x, -300, -100]) cube([300, 600, 300]);
}
else if (part == "clash") clash();
else if (part == "clash_view") {   // the assembly with the arms see-through and what they hit in red
    color("red") clash();
    color("mediumseagreen", 0.35) on_servo() arms(theta);
    if (shown("axle")) on_servo() axle();
    if (shown("servo")) on_servo() color("dimgray") servo_model();
    pieces();
    if (shown("caster")) color("#4a4f55", 0.4) caster_placed();
    if (shown("pins")) pins();
    robot();
}
else if (part == "ring_view") {   // the assembly with the two swappable arms in their own colours (the can tips lapping)
    on_servo() {
        on_axis(spline_axis) rotate(theta) { color("orange") spline_arm(); color("seagreen") arm_part(ext, -1); }
        on_axis(idler_axis) rotate(-theta) { color("royalblue") idler_arm(); color("darkorange") handed(1) arm_part(ext, 1); }
        axle();
    }
    pieces(); caster_placed(); pins(); robot();
}
else if (part == "arm_clash") intersection() {   // the two swappable arms against each other at theta (the can tips lap); empty = clear
    on_servo() on_axis(spline_axis) rotate(theta) arm_part(ext, -1);
    on_servo() on_axis(idler_axis) rotate(-theta) handed(1) arm_part(ext, 1);
}
else if (part == "fit") intersection() {   // the sensor against the pieces, plates, motors and caster; empty = clear
    on_sensor() reflectance_sensor();
    union() { gripper_frame(); block(); post(); on_plate() robot_plate(hole); on_plate(true) robot_plate(top_hole); motors(); caster_placed(); }
}
else if (part == "caster_fit") intersection() {   // the caster against the pieces, pins and the idler axle; empty = clear
    caster_placed();
    union() { gripper_frame(); block(); post(); pins(); on_servo() axle(); }
}
else if (part == "block_fit") intersection() {   // the block against the plates, motors and sensor; empty = clear
    block();
    union() { on_plate() robot_plate(hole); on_plate(true) robot_plate(top_hole); motors(); on_sensor() reflectance_sensor(); }
}

echo(sensor_mount = sensor_mount, stance = stance, wall_top_z = wall_top_z, wall_rows_z = wall_rows_z, block_rows = block_rows, edge_rows = edge_rows, edge_pin_x = edge_pin_x,
     floor_z = [floor_z0, floor_z1], floor_flush_drop = (u - lego_plate_t) / 2 - floor_z0, arm_z = arm_z, paddle_z0 = paddle_z0, paddles_over_ground = paddle_z0 - floor_z,
     back_y = back_y, floor_y0 = floor_y0, servo_back_y = axle_y + body[0] / 2, post_y = [caster_y, floor_y0], post_d = post_d, post_min = post_min,
     caster_top_z = caster_top_z, caster_pin_z = caster_pin_z, ground_z = floor_z, block_z = [block_z0, block_z1], block_row_z = block_row_z,
     frame_x = [frame_x0, frame_x1], grid_x = grid_x, can_bottom_z = can_bottom, cans_over_ground = can_bottom - floor_z);
assert(paddle_z0 >= floor_z, "the paddles reach the ground");
assert(len(block_rows) > 0, "no wall row meets the block");
