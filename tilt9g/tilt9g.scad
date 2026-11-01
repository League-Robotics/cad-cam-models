// Tilt table on the 9 g servo: the 9 g gripper frame of servo_gripper.scad
// with a second bearing under the servo. Leave the gripper's idler arm out
// and the spline nub can swing over the servo, through 90 deg from closed,
// until the back face of its stub lies parallel to the frame's LEGO wall.
// A second idler nub, turned over, runs on a LEGO 3L axle in a new arm layer
// under the servo, on the spline axis and with its stub lined up with the
// spline nub's. A plate pinned across the back faces of both stubs is then a
// table carried on both sides of the servo, tilting about the spline axis.
//
// Under the servo the frame grows three LEGO units: plate, arm layer, plate.
// Both plates take the top plate's grid of pin holes; the hole on the spline
// axis is the bottom arm's bearing. The arm layers are 6 studs apart, so the
// pins in the two stubs sit on the LEGO grid. The top is unchanged, so the
// frame still works as the gripper. As in the 9 g gripper, the frame holds
// the bottom axle still in cross holes (P1 and P2) and the nub (the idler
// arm, arms/right_arm) turns on it in its plain round hole (2026-10-31).
//
// The table is a 3 x 7 plate of pin holes (rows 2 studs apart on the stubs'
// pins, columns across both stubs), pinned to the stubs at its corners.
// pan9g.scad's pan head pins to its middle 3 x 3, the pan axis through the
// centre hole: tilt first, then pan.
//
// Servo coordinates as servo_gripper.scad: Y up the output shaft (servo
// bottom at y = 0), X across (LEGO wall at +X), Z along the servo. theta is
// the spline arm's angle as in the gripper: 0 closed, -90 the table flat.
//
// Assembly: the bottom closes the frame, so the servo can no longer come up
// from below. Push the spline arm in sideways as for the gripper. The gap
// over P1 lets the servo slide in from the front (-X) with its spline under
// the arm; lift it onto the spline and screw up through the tab slots, by
// way of the access holes in both bottom plates. Then slide the bottom nub
// in and push the 3L axle up through P2, the nub and P1.

include <../scad/servo_gripper.scad>
include <../scad/lego.scad>
use <pan9g.scad>

servo = "9g";
show_part = false;   // servo_gripper.scad draws nothing of its own

/* [Show] */
// "assembly", "clash", "frame" / "table" (print orientation), the meshes
// tilt9g/index.html animates, all in servo coordinates at theta = 0:
// "frame_view", "servo_view", "spline_view", "bottom_view", "table_view",
// "pan_plate_view", "pan_frame_view", "pan_servo_view"; or "world" (one
// component, `show`, at theta and phi, the frame standing on its LEGO wall:
// view/tilt_pan9g.html)
part = "assembly";
theta = -90 + 60 * sin(360 * $t);
phi = 0;                                // pan, as pan9g.scad
show_table = true;
show_pan = true;
// part = "world": "frame", "servo", "spline", "bottom", "table", "pan_plate",
// "pan_frame", "pan_servo"
show = "frame";

/* [Swappable-arm stub, as swap_gripper.scad] */
stub_x = [-17, -9];
stub_y = [5, 38];
pin_y = [17, 33];

/* [Bottom bearing] */
tilt_span = 6;                          // studs between the two arm layers' centres
arm_mid = (arm_y0 + arm_y1) / 2;
b_y0 = arm_mid - 8 * tilt_span - arm_t / 2;   // bottom arm layer
b_y1 = b_y0 + arm_t;
p1_y = [b_y1 + clr, b_y1 + clr + plate_t];    // plate between servo and bottom arm
p2_y = [b_y0 - clr - plate_t, b_y0 - clr];    // outer plate
// In the frame the servo sits tab_standoff low (legs on the tab tops). The gap
// down to P1 has to take the spline's depth in the socket, so the servo can go
// in under the spline arm and then up onto the spline.
servo_y = -tab_standoff;
spline_engage = spline_top + servo_y - arm_y0;
gap_under = servo_y - p1_y[1];
// LEGO wall rows carried on down at 8 mm. The row in the arm layer would open
// into the bottom arm's swing, and the row in P2 has no room for its
// counterbores above P2's outer face, so both are left out (running the wall
// past P2 to make room would cap P2's pin holes).
wall_rows = [for (y = [lego_y[0] - 8 : -8 : p2_y[0] + pin_cb_d / 2 + 1])
  if (abs(y - (b_y0 + b_y1) / 2) > arm_t / 2 + clr + pin_hole / 2) y];
access_d = 4.4;                         // screwdriver and M2 head, up to the tab slots
// Grid holes an access hole cuts into (counterbore included) are left out, so
// the idler end has just the screw hole and prints without support. The
// spline-end access hole is within 1 mm of its grid hole and only widens it.
function access_cut(x, z) = len([for (h = tab_holes) let(d = norm([x - h[0], z - h[1]]))
  if (d > 1 && d < (pin_cb_d + access_d) / 2) h]) > 0;
bottom_axle_len = 24;                   // LEGO axle 3
dz_bottom = arm_y1 - b_y1;              // bottom arm in the spline arm's part frame

/* [Table] */
table_t = pd_cell;
table_x0 = stub_x[0] - table_t;         // outer face, where the pan head pins on
table_rows_y = [pin_y[0], (pin_y[0] + pin_y[1]) / 2, pin_y[1]];
table_cols_z = [for (k = [0 : tilt_span]) arm_t / 2 + 8 * k];
table_mid = [table_rows_y[1], table_cols_z[tilt_span / 2]];   // pan axis
pan_pins = [for (i = [-1, 1], j = [-1, 1]) table_mid + 8 * [i, j]];   // the spline plate's corners
assert(gap_under > spline_engage + 0.3, "servo can't clear the spline arm going in");
echo(bottom_arm_layer = [b_y0, b_y1], p1 = p1_y, p2 = p2_y, gap_under = gap_under,
     spline_engage = spline_engage, wall_rows = wall_rows, stub_pitch = arm_y1 - b_y1);

// ---------- frame ----------

module tilt_frame() {
  e = 0.01;
  difference() {
    union() {
      frame();
      // LEGO wall carried down past P2; stepped back like the upper wall in
      // the bottom arm layer to clear the nub's teeth
      box([upper_wall_x0, wall_x[1]], [p2_y[0], e], wall_z);
      box(wall_x, [p1_y[0], e], wall_z);
      box(wall_x, p2_y, wall_z);
      for (y = [p1_y, p2_y]) box(top_x, y, top_z);
    }
    // pin holes through both plates: P1 plain, P2 counterbored outside
    for (x = [0 : 8 : top_x[1] - 3.9], z = top_holes_z) if (!access_cut(x, z)) translate([x, 0, z]) rotate([90, 0, 0]) {
      translate([0, 0, -p1_y[1] - 1]) cylinder(d = pin_hole, h = plate_t + 2);
      translate([0, 0, -p2_y[1] - 1]) cylinder(d = pin_hole, h = plate_t + 2);
      translate([0, 0, -p2_y[0] - pin_cb_h]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
    }
    // the bottom nub's axle, held still in cross holes; the nub turns on it
    translate([0, p2_y[0] - 1, spline_axis]) rotate([-90, 0, 0]) linear_extrude(p1_y[1] - p2_y[0] + 2) axle_cross2d();
    // screwdriver access up to the tab slots
    for (h = tab_holes) translate([h[0], p2_y[0] - 1, h[1]]) rotate([-90, 0, 0])
      cylinder(d = access_d, h = p1_y[1] - p2_y[0] + 2);
    for (y = wall_rows, z = lego_z) translate([0, y, z]) lego_hole_x(wall_x[0], wall_x[1]);
  }
}

// ---------- moving parts, in the spline arm's part frame ----------

module bottom_arm() translate([0, 0, dz_bottom]) handed(1) idler_arm();

// The table: a plate pinned to the back faces of both stubs, the outer face
// (on the bed) a 3 x 7 grid of pin holes.
module table() {
  difference() {
    box([table_x0, stub_x[0]], stub_y, [0, dz_bottom + arm_t]);
    for (y = table_rows_y, z = table_cols_z) translate([table_x0, y, z])
      rotate([0, 90, 0]) pd_pin_hole(table_t, ext = 2);
  }
}
// 2L pins along x, centred on the face at x
module pins_x(x, yz) for (p = yz) translate([x, p[0], p[1]]) rotate([0, 90, 0]) {
  translate([0, 0, -7.9]) cylinder(d = 4.8, h = 15.8);
  translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
module table_pins() pins_x(stub_x[0], [for (y = pin_y, z = [arm_t / 2, dz_bottom + arm_t / 2]) [y, z]]);

// pan9g.scad's servo coordinates onto the table: the spline plate's table
// face on the table's outer face, the pan axis (servo Y, into the table)
// through the table's centre hole, the servo's length along the tilt axis.
module on_table() multmatrix([[0, 1, 0, table_x0 - pan_mount_y()], [-1, 0, 0, table_mid[0]],
                              [0, 0, 1, table_mid[1] - spline_axis], [0, 0, 0, 1]]) children();
module pan_fixed() on_table() { spline_plate(); horn_screw(); }

module bottom_axle() translate([0, p2_y[0], spline_axis]) rotate([-90, 0, 0])
  linear_extrude(bottom_axle_len) { square([4.8, 1.8], center = true); square([1.8, 4.8], center = true); }

module moving(t, tbl = true) on_axis(spline_axis) rotate(t) {
  color("orange") spline_arm();
  color("royalblue") bottom_arm();
  if (tbl) {
    color("mediumseagreen", 0.85) table();
    color("dimgray") { table_pins(); if (show_pan) pins_x(table_x0, pan_pins); }
  }
  if (show_pan) {
    color("mediumpurple") pan_fixed();
    on_table() pan_turn(phi) {
      color("gold") pan_frame();
      if (show_servo) color("dimgray", 0.9) servo_model();
    }
  }
}

// The frame standing on its LEGO wall (+X down), the tilt axis level: the
// table is flat and the pan axis upright at theta = -90.
module world() rotate([0, 90, 0]) children();
// at theta = -90 the pan axis in world x, y (for the viewer's pivot)
pan_axis_world = [table_mid[0] + spline_axis, arm_y1 - table_mid[1]];

echo(pan_axis_world = pan_axis_world);

if (part == "frame") translate([0, 0, wall_x[1]]) rotate([0, 90, 0]) tilt_frame();   // LEGO face on the bed
else if (part == "table") translate([0, 0, -table_x0]) rotate([0, 90, 0]) table();   // outer face on the bed
else if (part == "pan_plate_view") on_axis(spline_axis) union() { pan_fixed(); pins_x(table_x0, pan_pins); }
else if (part == "pan_frame_view") on_axis(spline_axis) on_table() pan_frame();
else if (part == "pan_servo_view") on_axis(spline_axis) on_table() servo_model();
else if (part == "world") world() {
  if (show == "frame") tilt_frame();
  if (show == "servo") translate([0, servo_y, 0]) servo_model();
  if (show == "bottom") bottom_axle();
  on_axis(spline_axis) rotate(theta) {
    if (show == "spline") spline_arm();
    if (show == "bottom") bottom_arm();
    if (show == "table") { table(); table_pins(); }
    if (show == "pan_plate") { pan_fixed(); pins_x(table_x0, pan_pins); }
    if (show == "pan_frame") on_table() pan_turn(phi) pan_frame();
    if (show == "pan_servo") on_table() pan_turn(phi) servo_model();
  }
}
else if (part == "frame_view") tilt_frame();
else if (part == "servo_view") translate([0, servo_y, 0]) servo_model();
else if (part == "spline_view") on_axis(spline_axis) spline_arm();
else if (part == "bottom_view") union() { on_axis(spline_axis) bottom_arm(); bottom_axle(); }
else if (part == "table_view") on_axis(spline_axis) union() { table(); table_pins(); }
else if (part == "clash") rotate([90, 0, 0]) intersection() {
  moving(theta, show_table);
  difference() {   // the spline sits in the socket by design
    union() { tilt_frame(); translate([0, servo_y, 0]) servo_model(); }
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = spline_od / 2 + 0.3, h = 100);
  }
}
else rotate([90, 0, 0]) {   // servo Y up on screen
  moving(theta, show_table);
  color("black") bottom_axle();
  color("lightgray") tilt_frame();
  if (show_servo) color("dimgray") translate([0, servo_y, 0]) servo_model();
}
