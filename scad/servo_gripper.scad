// Gripper on a hobby servo: two geared arms, one on the servo spline and one
// on a LEGO cross axle, held by a frame that screws to the servo's mounting
// tabs and carries LEGO pin holes on its back. With jaw = "nub" the arms are
// the gear nubs of swap_gripper.scad, which take the swappable can, cube and
// ball arms; with jaw = "ring" they are gripper.scad's one-piece can arms.
// `servo` picks the standard-size servo (models/standard_servo.stl) or the
// 9 g micro servo (modelled here from caliper measurements; see
// models/servo_9g_dims.png).
//
// Servo coordinates: Y up the output shaft (bottom at y = 0), X across the
// width, Z along the length, body centred on x = z = 0, spline on -Z of
// centre. The idler axle is 24 mm from the spline toward +Z: over the
// standard servo's body, past the end of the 9 g one. The arms are flipped
// relative to gripper.scad (rings open toward -X, the arm's z = 0 face up),
// which puts the spline arm's thin tip on its top face so it still prints
// flat with any hub boss facing up off the bed.
//
// Assembly: slide the idler arm into the frame and push the LEGO axle
// (2 studs, 16 mm; 9 g: 3 studs, 24 mm) down through the top plate and arm
// into the bearing below.
// Press the spline arm onto the servo (a press fit; no horn screw, the socket
// runs through the arm). Lower the frame over the servo so the gears slide
// into mesh and the tube under the top plate drops into the spline arm's top
// recess, then screw up through the tab slots into the frame legs.
// 9 g: the spline-end leg runs to the frame end and holds the spline arm up
// as the bearing block does the idler arm, so both arms push into the frame
// sideways first, the spline arm's recess riding over the tapered tube; then
// the frame goes down over the servo with the spline entering the socket.

use <gripper.scad>
use <swap_gripper.scad>

/* [Pose] */
theta = -6 + 96 * (0.5 - 0.5 * cos(360 * $t));
// "assembly", "spline_arm", "idler_arm", "frame" or "clash" (what the arms
// hit in the frame and servo at theta; empty = clear)
part = "assembly";
// "standard" or "9g"
servo = "standard";
// "nub": gear nubs that take the swappable arms of swap_gripper.scad;
// "ring": the original one-piece can arms
jaw = "nub";
// swappable arm shown in the assembly with jaw = "nub": "can", "cube", "ball"
ext = "can";
show_servo = true;
// swap the swappable arms side to side (each turns over): for the asymmetric
// cube_low this puts the paddles' long ends the other way
ext_swap = false;
// in the assembly: "all" or one component in place (for viewers that colour
// each STL): "spline_arm", "idler_arm", "left_ext", "right_ext", "frame",
// "servo", "axle"
show = "all";
show_can = false;
// false when another file includes this one for its modules (tilt9g.scad)
show_part = true;
// The 9 g frame's 2026-10-28 revision: the hole grid centred on the gear
// mesh (6 columns, the mesh line on the 4th, so the jaws sit on a column of
// the grid: 3 columns on the spline side, 2 on the idler side), the wall
// behind the arm layer a full unit thick with a 4th row of holes, and the top
// plate one row longer ahead of the axles, that row's holes horizontal into
// its front face (a caster, or a part pinned on ahead of the jaws). The
// axles themselves are off the grid (1.5 units either side of the mesh), so
// the axle row keeps only the holes 12 from an axle. false: the original 9 g
// frame (front_plate.scad, tilt9g).
centred = false;

S9 = servo == "9g";

/* [Servo: standard measured from its STL, 9 g with calipers] */
body = S9 ? [12.35, 22.2, 22.85] : [20, 35, 40];   // case, x/y/z (9 g x, z with clearance)
// 9 g: tab bottom 18.0 over the case bottom, case top 1.62 over the tab top
tab_y = S9 ? [18.0, 22.2 - 1.62] : [27.0, 29.3];   // mounting tab bottom/top
spline_axis = S9 ? -5.375 : -10;   // z of the output shaft
// Socket tip dia as designed: the printer makes it ~0.15 small, so designing
// at the spline's own size gives a light interference fit on the plastic
// spline. Standard: splines 5.62..5.74, designed 5.7 (24T, as in the STL).
// 9 g: 21T, 4.5 across the teeth (4.55 measured).
spline_teeth = S9 ? 21 : 24;
spline_od = S9 ? 4.5 : 5.7;
spline_rd = S9 ? 4.1 : 5.2;
spline_clr = 0;        // per side
// 9 g: a plain round socket instead; the spline cuts its own teeth as it is
// pressed in. 4.65 as designed was the best fit on the hole gauge
// (grippers/gauges/spline_hole_gauge.stl). 0 = toothed socket.
spline_hole_d = S9 ? 4.65 : 0;
// 9 g heights are measured from the tab top: gear head (flat) 7.3, spline top 11.3
spline_top = S9 ? tab_y[1] + 11.3 : 43.3;
// 9 g spline arm prints spline side down (no hub boss to stand on): the socket
// runs straight to the bed with no entry chamfer, and both arms keep their
// thin tips on the bed face (gripper.scad tip_flip).
spline_down = S9;
spline_base = S9 ? tab_y[1] + 7.3 : 39.4;   // top of the case/boss around the spline
horn_head = S9 ? 4.5 : 6.0;       // frame: hole down the tube over the spline
tab_x = S9 ? 5.98 : 9.35;         // tab half-width
tab_z = S9 ? 16.225 : 27;         // tab end
// 9 g: holes 2.25, inner edges 25.5 apart, taken as centred on the body
tab_hole_d = 2.25;
tab_holes = S9 ? [for (s = [-1, 1]) [0, s * (25.5 + tab_hole_d) / 2]]
               : [for (x = [-4.95, 4.95], z = [-24.83, 24.83]) [x, z]];
tab_pilot = S9 ? 1.6 : 2.5;       // self-tapping M2 / M3 from below through the slots
tab_pilot_h = S9 ? 6.5 : 9;      // from 1 mm below the leg bottom
// The legs reach this far below the tab top, so screwed tight the frame sits
// that much higher on the servo (9 g: at 0 the arms bound up).
tab_standoff = S9 ? 0.9 : 0;
leg_y0 = tab_y[1] - tab_standoff;  // bottom of the legs, against the tabs

/* [Layout] */
cd = 24;
idler_axis = spline_axis + cd;
arm_t = 7.6;           // as gripper.scad
hub_boss_h = S9 ? 0 : 2.2;        // spline arm boss reaching down onto the spline
arm_y0 = spline_base + 0.3 + hub_boss_h;   // bottom of the arm layer
arm_y1 = arm_y0 + arm_t;
clr = 0.4;             // between arms and frame
// 9 g: the top is a squared block one LEGO unit thick on the stud grid
// through both axes (cd = 3 studs), with pin holes down through it
square_top = S9;
plate_t = square_top ? 7.6 : 2.6;
top_y0 = arm_y1 + clr;
top_y1 = top_y0 + plate_t;
// idler's lower bearing: a thin ledge over the standard servo's lid, a block
// standing on the tab past the end of the 9 g servo
ledge_y = [S9 ? leg_y0 : 38.3, arm_y0 - clr];
upper_wall_x0 = 13.8;  // in the arm layer the wall steps back to clear the teeth
wall_t = 8;            // centred: the upper wall a full unit
gear_r = cd / 2 + 1;   // the 24T mod 1 gears' outside radius, 13
// square top: rows of holes 3.9 in from the back face at 8 pitch (x = 0, 8,
// 16; centred: 1.9, 9.9, 17.9, the axles 1.9 ahead of the first row); centred:
// the front face one unit further out, at the gear teeth's reach plus 1
top_x = centred ? [-(gear_r + 1), upper_wall_x0 + wall_t] : [-3.9, 19.9];
top_rows_x = centred ? [top_x[1] - 3.9 - 16, top_x[1] - 3.9 - 8, top_x[1] - 3.9] : [0, 8, 16];
mesh_z = (spline_axis + idler_axis) / 2;
// the hole columns (z): centred, 6 about the mesh; else 5 from one past the spline to the idler
grid_z = centred ? [for (i = [-3 : 2]) mesh_z + 8 * i] : [for (z = [spline_axis - 8 : 8 : idler_axis]) z];
// square top: hole positions [x, z] left out (a file that includes this one
// puts its own holes there, e.g. block_gripper.scad's horizontal edge holes)
top_skip = [];
function top_skipped(x, z) = len([for (s = top_skip) if (abs(s[0] - x) < 0.01 && abs(s[1] - z) < 0.01) 1]) > 0;
top_holes_z = grid_z;
top_z = [grid_z[0] - 5.9, grid_z[len(grid_z) - 1] + 5.9];   // 2 mm past a beam end, as wall_ext
// a hole in the top plate: not the idler's axle hole; centred: nothing in
// the axle row within 6.5 of an axle (the tube and the axle boss are there)
function top_hole_ok(x, z) = centred
  ? !(abs(x - top_rows_x[0]) < 0.01 && (abs(z - spline_axis) < 6.5 || abs(z - idler_axis) < 6.5))
  : (abs(x) > 0.01 || abs(z - idler_axis) > 0.01);
// centred: front-face holes (z) left out, e.g. where something else's pins pass
front_skip = [];
function front_skipped(z) = len([for (s = front_skip) if (abs(s - z) < 0.01) 1]) > 0;
front_hole_depth = 8;   // half a 2L pin
wall_x = [body[0] / 2 + 0.3, square_top ? top_x[1] : max(body[0] / 2 + 0.3 + 7.8, upper_wall_x0 + 4.3)];
frame_z = [-tab_z, square_top ? top_z[1] : max(tab_z, idler_axis + 6)];   // frame ends
// The LEGO face prints on the bed. The 9 g wall is 11.65 thick and lifted at
// its corners when the counterbores came within ~1 mm of the edges, so its
// wall runs past the frame ends and the hole grid keeps a solid border.
wall_ext = S9 ? 2 : 0;
wall_z = square_top ? top_z : [frame_z[0] - wall_ext, frame_z[1] + wall_ext];
// LEGO axle 2 (16 mm) resting on the standard servo's lid; on the 9 g frame an
// axle 3 (24 mm) flush with the top, in a hole through the bearing block so it
// can be pushed back out (axle_y0 is where the assembly view draws it)
axle_len = S9 ? 24 : 16;
axle_y0 = S9 ? top_y1 - axle_len : 37.95;

/* [Hubs] */
hub_boss_d = 11;
tube_od = S9 ? 7.8 : 9;   // tube under the top plate, runs in the arm's top recess
recess_d = tube_od + 0.6;
recess_h = S9 ? 1.9 : 2.6;
// tube and recess sides lean in by this from the axis (0: straight), so the
// spline arm can be pushed in under the tube; 9 g: tip od 5.9 around the 4.9 bore
tube_taper = S9 ? 32 : 0;
// tube od at depth y below the top plate; the recess is 0.6 over it
function tube_d(y) = tube_od - 2 * y * tan(tube_taper);
full_leg = S9;         // spline-end leg to the frame end, up to the ledge
// The full leg's top slopes down from the upper wall (where it stays at the
// ledge) to leg_slope_drop lower at its front face: the triangle the spline
// arm tips into while its recess rides over the tube on the way in.
leg_slope_drop = 2;
axle_hole = 4.95;      // round hole a LEGO cross axle turns in
// 9 g: the frame holds the idler's axle still in cross holes (top plate and
// bearing block) and the idler arm turns on it. Part Designer's print-tuned
// axle hole: the cross's arms axle_cross_w wide, clipped to the pin bore.
axle_fixed = S9;
axle_cross_w = 2.02;
axle_cross_r = 2.475;
module axle_cross2d() intersection() {
  circle(r = axle_cross_r);
  union() {
    square([2 * axle_cross_w / 2, 2 * axle_cross_r + 1], center = true);
    square([2 * axle_cross_r + 1, 2 * axle_cross_w / 2], center = true);
  }
}
idler_boss_d = 9;
idler_boss_top = axle_y0 + 16.35;

/* [LEGO] */
pin_hole = 4.9;
pin_cb_d = 6.4;
pin_cb_h = 0.9;
// The counterbore on the LEGO face prints against the bed; a cone from it back
// to the pin bore replaces the flat overhanging step (as partdesigner's
// basePinTaperAngle). Angle from the hole axis; 35.9 deg gives a 1 mm taper.
base_pin_taper_angle = 35.9;
lego_z = centred ? grid_z : let(zc = (wall_z[0] + wall_z[1]) / 2, n = floor((wall_z[1] - wall_z[0] - 6) / 8))
  [for (i = [0:n]) zc + 8 * (i - n / 2)];
// centred: a 4th row through the full-unit wall behind the arm layer
lego_y = centred ? [7, 15, 23, 31] : S9 ? [7, 15, 23] : [4, 12, 20, 28, 36];
// A through hole that comes out half under a leg would leave a part-circle
// overhang where the leg covers it; those holes are left out. Rows below the
// legs and above the ledge are clear of them. The centred grid's columns
// either miss the legs' inner faces by at most a 0.1 sliver of the bore or
// lie wholly inside a leg (a blind hole), so there the bore is the test.
function lego_hole_ok(y, z) = !lego_through || y + pin_hole / 2 < leg_y0 || y - pin_hole / 2 > ledge_y[1]
  || abs(abs(z) - (body[2] / 2 + 0.3)) > (centred ? pin_hole / 2 - 0.2 : pin_cb_d / 2);
// pin holes through the whole wall (the 9 g wall is thicker than one unit;
// through holes take solid out of it), or one unit deep
lego_through = S9;

$fn = 72;

// ---------- arms ----------

// Spline tooth profile of the shaft, at angle 0 a tooth.
module spline2d() {
  p = 360 / spline_teeth;
  ro = spline_od / 2;
  ri = spline_rd / 2;
  polygon([for (i = [0:spline_teeth - 1], f = [[-0.5, ri], [-0.25, ri], [-0.12, ro], [0.12, ro], [0.25, ri]])
    let(a = (i + f[0]) * p) f[1] * [cos(a), sin(a)]]);
}

// Spline arm. The part's z runs down the servo axis from the top of the arm
// layer; any hub boss reaches past z = arm_t down onto the spline. Printed
// z = 0 on the bed with the boss up (standard), or spline side down (9 g).
z_boss = arm_t + hub_boss_h;              // end of the hub, 0.3 over the case
module spline_arm() spline_hub() if (jaw == "nub") nub_body(-1); else arm_body(-1, spline_down);

// Hub boss, spline socket (through the whole arm) and top recess, added to
// and cut from children() (an arm body with its gear axis on z).
module spline_hub() {
  difference() {
    union() {
      children();
      if (hub_boss_h > 0)
        translate([0, 0, arm_t - 0.01]) cylinder(d = hub_boss_d, h = hub_boss_h + 0.01);
    }
    translate([0, 0, -1]) linear_extrude(z_boss + 2)
      if (spline_hole_d > 0) circle(d = spline_hole_d); else offset(delta = spline_clr) spline2d();
    if (!spline_down)
      translate([0, 0, z_boss - 0.6]) cylinder(d1 = spline_od + 0.2, d2 = spline_od + 1.4, h = 0.61);
    translate([0, 0, -1]) cylinder(d1 = tube_d(clr - 1) + 0.6, d2 = tube_d(clr + recess_h) + 0.6, h = recess_h + 1);
  }
}

module idler_arm() if (jaw == "nub") nub_arm(1); else arm(1, spline_down);

// Part frame (gear axis = z, z = 0 at the top of the arm layer) to servo
// coordinates: part x -> +Z, part y -> -X, part z -> -Y.
module on_axis(z) multmatrix([[0, -1, 0, 0], [0, 0, -1, arm_y1], [1, 0, 0, z], [0, 0, 0, 1]]) children();

// ---------- servos ----------

// The servo model in servo coordinates. The 9 g one is built from the
// measurements (models/servo_9g.stl has its heights wrong): case, tabs with
// their holes, flat-topped gear head with the lobe toward the middle, spline.
module servo_model() {
  if (S9) {
    difference() {
      union() {
        box([-6, 6], [0, body[1]], [-11.075, 11.075]);
        box([-tab_x, tab_x], tab_y, [-tab_z, tab_z]);
      }
      for (h = tab_holes) translate([h[0], tab_y[0] - 1, h[1]]) rotate([-90, 0, 0])
        cylinder(d = tab_hole_d, h = tab_y[1] - tab_y[0] + 2);
    }
    plate(body[1] - 0.01, spline_base - body[1] + 0.01) hull() {
      translate([0, -spline_axis]) circle(r = 5.7);
      translate([0, -0.35]) circle(r = 2.8);
    }
    translate([0, spline_base - 0.01, spline_axis]) rotate([-90, 0, 0]) difference() {
      cylinder(d = spline_od, h = spline_top - spline_base + 0.01);
      translate([0, 0, spline_top - spline_base - 3]) cylinder(d = 1.9, h = 4);
    }
  }
  else import("models/standard_servo.stl");
}

module box(x, y, z) translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);

// Room for the servo, with clearance.
module servo_clearance() {
  c = 0.25;
  bx = body[0] / 2 + c;
  bz = body[2] / 2 + c;
  box([-bx, bx], [-1, body[1] + c], [-bz, bz]);
  box([-tab_x - c, tab_x + c], [tab_y[0] - 1, leg_y0], [-tab_z - c, tab_z + c]);
  translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = spline_od / 2 + 0.3, h = spline_top + 1);
  if (S9) {
    // gear tower around the spline and the small boss beside it
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = 5.75 + c, h = spline_base + 0.3);
    box([-2.8, 2.8], [0, spline_base + 0.3], [spline_axis, 0.72 + 2.8]);
    box([-1.9, 1.9], [4.0, 5.6], [-bz - 5.5, -bz + 1]);   // wire exit, spline end
  } else {
    box([-9.6 - c, 9.6 + c], [0, 37.0 + c], [-19.6 - c, 19.6 + c]);   // lid
    box([-8.9 - c, 8.9 + c], [0, 37.9 + c], [-1.2 - c, 14.2 + c]);    // raised lid
    for (s = [-1, 1])   // gussets between tab and case, x = 0
      box([-1, 1], [tab_y[1] - 0.1, tab_y[1] + 1.3], s > 0 ? [bz - c, tab_z + 1] : [-tab_z - 1, -bz + c]);
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = 6.45 + 0.4, h = spline_base + 0.3);
  }
}

// ---------- frame ----------

// Pin hole along +x from x0 to x1, counterbored at x1 (the bed side), with
// the step tapered.
module lego_hole_x(x0, x1) {
  taper_h = (pin_cb_d - pin_hole) / 2 / tan(base_pin_taper_angle);
  rotate([0, 90, 0]) {
    translate([0, 0, x0 - 1]) cylinder(d = pin_hole, h = x1 - x0 + 2);
    translate([0, 0, x1 - pin_cb_h]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
    translate([0, 0, x1 - pin_cb_h - taper_h]) cylinder(d1 = pin_hole, d2 = pin_cb_d, h = taper_h + 0.01);
  }
}

// Blind pin hole into a face: counterbored and tapered at the face (x = 0),
// the bore `depth` along +x, no counterbore at the far end.
module lego_blind_hole_x(depth) {
  taper_h = (pin_cb_d - pin_hole) / 2 / tan(base_pin_taper_angle);
  rotate([0, 90, 0]) {
    translate([0, 0, -1]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
    translate([0, 0, pin_cb_h - 0.01]) cylinder(d1 = pin_cb_d, d2 = pin_hole, h = taper_h + 0.01);
    translate([0, 0, -1]) cylinder(d = pin_hole, h = depth + 1);
  }
}

// Removes the top of the spline-end leg (and the wall beside it, in front of
// the upper wall) down to leg_drop below the ledge, with a 45 deg bevel on the
// edges facing the arm: the inner (+Z) and front (-X) top edges.
leg_drop = 2;
leg_bevel = 1.5;
module spline_leg_cut() {
  y0 = ledge_y[1] - leg_drop;
  z_in = -(body[2] / 2 + 0.3);          // inner face of the leg
  x_fr = -tab_x;                        // front face
  e = 0.01;
  box([x_fr - 3, upper_wall_x0], [y0, top_y0 - e], [frame_z[0] - 3, z_in + 1]);
  hull() {
    box([x_fr - 3, upper_wall_x0], [y0, top_y0 - e], [z_in - leg_bevel, z_in + 1]);
    box([x_fr - 3, upper_wall_x0], [y0 - leg_bevel, top_y0 - e], [z_in - e, z_in + 1]);
  }
  hull() {
    box([x_fr - 3, x_fr + leg_bevel], [y0, top_y0 - e], [frame_z[0] - 3, z_in + 1]);
    box([x_fr - 3, x_fr + e], [y0 - leg_bevel, top_y0 - e], [frame_z[0] - 3, z_in + 1]);
  }
}

// 2D in the plane of the plates: (x, -z), so it extrudes up +Y after rotate([-90, 0, 0]).
module plate(y0, h) translate([0, y0, 0]) rotate([-90, 0, 0]) linear_extrude(h) children();

module frame() {
  zb = body[2] / 2 + 0.3;
  difference() {
    union() {
      // LEGO wall down the servo's back (+X) face
      box(wall_x, [0, ledge_y[1]], wall_z);
      // the same wall, stepped back, through the arm layer up to the top plate
      box([upper_wall_x0, wall_x[1]], [0, top_y1], wall_z);
      // legs standing on the tabs
      box([-tab_x, wall_x[1]], [leg_y0, ledge_y[1]], [full_leg ? wall_z[0] : frame_z[0], -zb]);
      box([-tab_x, wall_x[1]], [leg_y0, ledge_y[1]], [zb, tab_z]);
      // lower bearing for the idler axle (kept behind the legs' front face)
      intersection() {
        plate(ledge_y[0], ledge_y[1] - ledge_y[0]) hull() {
          translate([0, -idler_axis]) circle(d = square_top ? 2 * (frame_z[1] - idler_axis) : 12);
          // 9 g: from the servo's end clearance like the front strip, so the
          // block's inner face is flat rather than sloping into the wall
          translate([wall_x[0], -frame_z[1]]) square([wall_x[1] - wall_x[0], frame_z[1] - (S9 ? zb : idler_axis - 8)]);
          if (S9) translate([-tab_x, -frame_z[1]]) square([1, frame_z[1] - zb]);
        }
        box([-tab_x, wall_x[1] + 1], [ledge_y[0] - 1, ledge_y[1] + 1], [frame_z[0] - 1, frame_z[1] + 1]);
      }
      // top plate over both arms
      if (square_top) plate(top_y0, plate_t) translate([top_x[0], -top_z[1]])
        square([top_x[1] - top_x[0], top_z[1] - top_z[0]]);
      else plate(top_y0, plate_t) hull() {
        translate([0, -spline_axis]) circle(d = 18);
        translate([0, -idler_axis]) circle(d = 14);
        translate([upper_wall_x0, -frame_z[1]]) square([wall_x[1] - upper_wall_x0, frame_z[1] - frame_z[0]]);
      }
      // tube into the spline arm's top recess, boss around the idler axle
      translate([0, top_y0 - (recess_h - clr), spline_axis]) rotate([-90, 0, 0])
        cylinder(d1 = tube_d(recess_h - clr), d2 = tube_od, h = recess_h - clr + 0.01);
      if (!square_top) translate([0, top_y1 - 0.01, idler_axis]) rotate([-90, 0, 0])
        cylinder(d = idler_boss_d, h = idler_boss_top - top_y1 + 0.01);
    }
    servo_clearance();
    // driver access to the horn screw
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(d = horn_head + 0.4, h = 100);
    // idler axle, through the whole frame: held in cross holes, or turning in round ones
    translate([0, min(axle_y0, ledge_y[0]) - 1, idler_axis]) rotate([-90, 0, 0])
      if (axle_fixed) linear_extrude(100) axle_cross2d(); else cylinder(d = axle_hole, h = 100);
    // spline-end leg dropped below the arm's swing, top edges bevelled
    if (!full_leg) spline_leg_cut();
    else {   // across the spline arm's half of the frame, out to its end
      x0 = upper_wall_x0;
      x1 = -tab_x - 1;
      dy = leg_slope_drop * (x0 - x1) / (x0 + tab_x);
      translate([0, 0, wall_z[0] - 1]) linear_extrude(spline_axis + cd / 2 - wall_z[0] + 1)
        polygon([[x0, ledge_y[1]], [x1, ledge_y[1] - dy], [x1, ledge_y[1] + 0.01], [x0, ledge_y[1] + 0.01]]);
    }
    // pilot holes for the tab screws
    for (h = tab_holes) translate([h[0], leg_y0 - 1, h[1]]) rotate([-90, 0, 0])
      cylinder(d = tab_pilot, h = tab_pilot_h);
    // square top: pin holes down through it, counterbored on top; those over
    // the upper wall end 1 mm into it. The idler's place is the axle hole.
    if (square_top) for (x = top_rows_x, z = top_holes_z)
      if (top_hole_ok(x, z) && !top_skipped(x, z)) translate([x, top_y0 - 1, z]) rotate([-90, 0, 0]) {
        cylinder(d = pin_hole, h = plate_t + 2);
        translate([0, 0, plate_t + 1 - pin_cb_h]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
      }
    // centred: the front row's holes go in from the top plate's front face
    if (centred) for (z = grid_z) if (!front_skipped(z))
      translate([top_x[0], top_y0 + plate_t / 2, z]) lego_blind_hole_x(front_hole_depth);
    // LEGO pin holes, counterbored on the outside
    for (y = lego_y, z = lego_z) if (lego_hole_ok(y, z)) translate([0, y, z])
      lego_hole_x(lego_through ? wall_x[0] : wall_x[1] - 7.8, wall_x[1]);
  }
}

// ---------- assembly ----------

module axle() {   // LEGO axle 2
  color("black") translate([0, axle_y0, idler_axis]) rotate([-90, 0, 0])
    linear_extrude(axle_len) {
      square([4.8, 1.8], center = true);
      square([1.8, 4.8], center = true);
    }
}

// Both arms at theta, with the swappable arms on the nubs.
function shown(c) = show == "all" || show == c;

module arms(t) {
  on_axis(spline_axis) rotate(t) {
    if (shown("spline_arm")) color("orange") spline_arm();
    if (jaw == "nub" && shown("left_ext")) color("mediumseagreen") arm_part(ext, ext_swap ? 1 : -1);
  }
  on_axis(idler_axis) rotate(-t) {
    if (shown("idler_arm")) color("royalblue") idler_arm();
    if (jaw == "nub" && shown("right_ext")) color("mediumseagreen") handed(1) arm_part(ext, ext_swap ? -1 : 1);
  }
}

if (!show_part) {}
else if (part == "spline_arm")   // spline side down when spline_down
  hand_label(-1, spline_down)
    if (spline_down) translate([0, 0, z_boss]) rotate([180, 0, 0]) spline_arm(); else spline_arm();
else if (part == "idler_arm") idler_arm();
else if (part == "frame") translate([0, 0, wall_x[1]]) rotate([0, 90, 0]) frame();   // LEGO face on the bed
else if (part == "clash") rotate([90, 0, 0]) intersection() {
  arms(theta);
  difference() {   // the spline itself sits in the socket by design
    union() { frame(); servo_model(); }
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = spline_od / 2 + 0.3, h = 100);
  }
}
else rotate([90, 0, 0]) {   // servo Y up on screen
  arms(theta);
  if (shown("axle")) axle();
  if (shown("frame")) color("lightgray") frame();
  if (show_servo && shown("servo")) color("dimgray") servo_model();
  if (show_can) %translate([-52, 0, (spline_axis + idler_axis) / 2]) rotate([-90, 0, 0])
    translate([0, 0, -20]) cylinder(d = 66, h = 115, $fn = 96);
}
