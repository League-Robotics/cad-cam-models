// Pan head on the 9 g servo, for a camera on the tilt table (tilt9g.scad):
// tilt first, then pan. The servo hangs upside down. Its spline presses into
// a 3 x 3 spline plate that pins flat to the tilt table, and its body sits in
// the pan frame, an L: a top over the servo's bottom end (a 4 x 5 grid of
// pin holes for the camera) and one side down the servo's length (4 x 5). The servo turns its own body, frame and
// camera about the spline, against the plate.
//
// No tube and recess here (the gripper arms' conical bearing). The spline is
// a press fit in the plate's round 4.65 socket, bottoms on a shelf, and the
// horn screw comes down through the shelf into the spline from the plate's
// table face, its head in a counterbore. The table's centre hole is over it.
//
// Servo coordinates as servo_gripper.scad: Y up the output shaft (servo
// bottom at y = 0), X across, Z along the servo, spline at z = spline_axis.
// Mounted, Y points into the table. phi is the pan angle.
//
// Pan frame (2026-10-31, the user's L): the top is 4 holes across (x = +-4,
// +-12) and 5 along (z = 0, +-8, +-16), centred on the servo body (the spline,
// and so the pan axis, is 5.4 off the middle column toward the wire end). The
// side (+X) is one unit thick, 4 rows down from the top by 5 along, all blind
// 8 deep. The corner row is shared, so its holes alternate along the edge:
// top, side, top, side, top. Under each tab only a leg the tab's width, with
// the screw's pilot hole, down to the top. The -X side is open: the wire
// (out of the case's end at y 4.0..5.6, under the -Z tab) turns in a groove
// in the -Z leg's inner face and leaves that way. A top hole lies wholly over
// the servo or the open side (through) or wholly under a leg or the side
// (8 deep, blind).
// The tabs sit on the legs, screwed down into them. Prints on the side's
// face, so everything stands up off it.
//
// Assembly: drop the servo in with its wire out the open side, screw down
// through the tabs. Press the spline plate onto the spline, screw down
// through the shelf into the spline (the 9 g kit's short horn screw), then
// pin the plate to the table with 2L pins.

include <../scad/servo_gripper.scad>
include <../scad/lego.scad>

servo = "9g";
show_part = false;   // servo_gripper.scad draws nothing of its own

/* [Show] */
// "assembly" (spline down, camera face up), "frame" / "spline_plate"
// (print orientation), "clash" (frame and servo at phi against the plate;
// empty = clear), or in place in servo coordinates at phi = 0 for the
// viewers: "frame_view", "plate_view", "servo_view", "screw_view"
part = "assembly";
phi = 60 * sin(360 * $t);
show_servo = true;

/* [Pan frame] */
floor_t = 7.6;                 // one unit, the servo's bottom end on it
floor_gap = 0.3;               // servo bottom to the top plate
pocket = [6.5, 11.4];          // half-sizes x, z: case +-6 / +-11.075; x wide enough that the top holes at x = +-4 lie wholly in it
hole_x = [-12, -4, 4, 12];
hole_z = [-16, -8, 0, 8, 16];
pf_half = [16 - pd_edge, 20 - pd_edge];    // x, z: the holes 3.8 in from the edges
side_rows = 4;                 // down the side from the camera face, the corner row first
side_rows_y = [for (i = [0 : side_rows - 1]) -floor_gap - floor_t + 3.8 + 8 * i];
pf_y = [-floor_gap - floor_t, side_rows_y[side_rows - 1] + 4 - pd_edge];   // camera face, side's far edge
side_x0 = pocket[0];           // side's inner face, beside the case
leg_y1 = tab_y[0];             // legs up to the tabs' bottoms
// the corner row (x = 12 on top, y = side_rows_y[0] on the side): which way each column goes
function corner_on_top(i) = i % 2 == 0;
blind_depth = 8;               // half a 2L pin
// groove for the wire in the -Z leg's inner face, out to the open side
wire_groove_y = [3.2, 6.4];    // the exit is 4.0..5.6
wire_groove_x1 = 2.6;          // the exit is x +-1.9
wire_groove_d = 3;             // into the leg, room to turn the wire
pilot_depth = 7;               // tab screws down into the legs

/* [Spline plate] */
sp_gap = 0.5;                  // plate face over the gear head (the head turns under it)
sp_y = [spline_base + sp_gap, spline_base + sp_gap + pd_cell];
socket_depth = spline_top - sp_y[0];       // the spline bottoms on the shelf
shelf_t = 1.2;                 // under the screw head
screw_d = 2.2;                 // M2 horn screw clearance
screw_head_d = 4.6;
sp_half = 12 - pd_edge;

echo(pan_frame = [2 * pf_half[0], pf_y[1] - pf_y[0], 2 * pf_half[1]], side_rows_y = side_rows_y, spline_plate_y = sp_y,
     socket_depth = socket_depth, screw_reach = shelf_t + socket_depth - (spline_top - sp_y[0]),
     pan_axis_off_centre = spline_axis, sweep_r = norm([pf_half[0], pf_half[1] - spline_axis]));
assert(socket_depth > 2.5, "spline barely in the plate");
assert(wire_groove_y[1] + 2 < leg_y1 - pilot_depth, "the wire groove runs into the tab screw's pilot hole");
assert(pf_y[1] < sp_y[0] - 2, "the side reaches the spline plate");

module pan_frame() {
  e = 0.01;
  top_y = [pf_y[0], -floor_gap];
  difference() {
    union() {
      box([-pf_half[0], pf_half[0]], top_y, [-pf_half[1], pf_half[1]]);   // top
      box([side_x0, pf_half[0]], [top_y[0], pf_y[1]], [-pf_half[1], pf_half[1]]);   // side
      for (s = [-1, 1])   // legs under the tabs
        box([-pocket[0], side_x0 + e], [top_y[1] - e, leg_y1], s < 0 ? [-pf_half[1], -pocket[1]] : [pocket[1], pf_half[1]]);
    }
    // the wire's groove
    box([-pocket[0] - 1, wire_groove_x1], wire_groove_y, [-pocket[1] - wire_groove_d, -pocket[1] + e]);
    // tab screw pilots, down from the legs' tops
    for (h = tab_holes) translate([h[0], leg_y1 - pilot_depth, h[1]]) rotate([-90, 0, 0])
      cylinder(d = tab_pilot, h = pilot_depth + 1);
    // camera face: under a leg or in the side 8 deep, else through the top
    for (x = hole_x, i = [0 : len(hole_z) - 1]) let(z = hole_z[i])
      if (x < side_x0 || corner_on_top(i)) translate([x, pf_y[0], z]) rotate([-90, 0, 0])
        if (x > side_x0 || abs(z) > pocket[1] && abs(x) < pocket[0]) pd_blind_pin_hole(blind_depth, ext = 2);
        else pd_pin_hole(floor_t, ext = 2);
    // side face, the corner row's holes between the top's
    for (j = [0 : side_rows - 1], i = [0 : len(hole_z) - 1]) if (j > 0 || !corner_on_top(i))
      translate([pf_half[0], side_rows_y[j], hole_z[i]]) rotate([0, -90, 0]) pd_blind_pin_hole(blind_depth, ext = 2);
  }
}

module spline_plate() {
  difference() {
    box([-sp_half, sp_half], sp_y, [spline_axis - sp_half, spline_axis + sp_half]);
    for (i = [-1 : 1], j = [-1 : 1]) if (i != 0 || j != 0)
      translate([8 * i, sp_y[0], spline_axis + 8 * j]) rotate([-90, 0, 0]) pd_pin_hole(pd_cell, ext = 2);
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) {
      // round press-fit socket (9g-spline-fit), straight from the bed face
      translate([0, 0, sp_y[0] - 1]) cylinder(d = spline_hole_d, h = socket_depth + 1);
      translate([0, 0, sp_y[0] - 1]) cylinder(d = screw_d, h = pd_cell + 2);
      translate([0, 0, sp_y[0] + socket_depth + shelf_t]) cylinder(d = screw_head_d, h = pd_cell);
    }
  }
}

// M2 x 4 pan head, for the views
module horn_screw() translate([0, sp_y[0] + socket_depth + shelf_t, spline_axis]) rotate([90, 0, 0]) {
  translate([0, 0, -1.5]) cylinder(d = 3.8, h = 1.5);
  cylinder(d = 2, h = 4);
}

// The body side turned through p about the spline.
module pan_turn(p) translate([0, 0, spline_axis]) rotate([0, p, 0]) translate([0, 0, -spline_axis]) children();

module pan_unit(p) {
  color("mediumpurple") spline_plate();
  color("dimgray") horn_screw();
  pan_turn(p) {
    color("gold") pan_frame();
    if (show_servo) color("dimgray", 0.9) servo_model();
  }
}

if (part == "frame") translate([0, 0, pf_half[0]]) rotate([0, 90, 0]) pan_frame();      // the side's face on the bed
else if (part == "spline_plate") translate([0, spline_axis, -sp_y[0]]) rotate([90, 0, 0]) spline_plate();   // servo face on the bed
else if (part == "frame_view") pan_frame();
else if (part == "plate_view") spline_plate();
else if (part == "servo_view") servo_model();
else if (part == "screw_view") horn_screw();
else if (part == "clash") intersection() {
  spline_plate();
  pan_turn(phi) union() { pan_frame(); servo_model(); }
}
else if (part == "assembly") rotate([-90, 0, 0]) pan_unit(phi);   // spline down

// for tilt9g.scad (which uses this file): the spline plate's table face
function pan_mount_y() = sp_y[1];
