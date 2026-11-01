// Can gripper on a hobby servo: the two arms from gripper.scad, one on the
// servo spline and one on a LEGO cross axle, held by a frame that screws to
// the servo's mounting tabs and carries LEGO pin holes on its back.
// `servo` picks the standard-size servo (servo/standard_servo.stl) or the 9 g
// micro servo (servo/servo_9g.stl).
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
// (2 studs, 16 mm) down through the top plate and arm into the bearing below.
// Press the spline arm onto the servo and screw it down. Lower the frame over
// the servo so the gears slide into mesh and the tube under the top plate
// drops into the spline arm's top recess, then screw up through the tab slots
// into the frame legs. The horn screw stays reachable through the tube.

use <gripper.scad>

/* [Pose] */
theta = -6 + 96 * (0.5 - 0.5 * cos(360 * $t));
// "assembly", "spline_arm", "idler_arm" or "frame"
part = "assembly";
// "standard" or "9g"
servo = "standard";
show_servo = true;
show_can = false;

S9 = servo == "9g";

/* [Servo, measured from the STLs] */
spline_axis = S9 ? -5.375 : -10;   // z of the output shaft
// Socket tip dia as designed: the printer makes it ~0.15 small, so designing
// at the spline's own size gives a light interference fit on the plastic
// spline. Standard: splines 5.62..5.74, designed 5.7 (24T, as in the STL).
// 9 g: the STL shaft is a plain 4.74 cylinder; SG90-type splines are 21T.
spline_teeth = S9 ? 21 : 24;
spline_od = S9 ? 4.75 : 5.7;
spline_rd = S9 ? 4.35 : 5.2;
spline_clr = 0;        // per side
spline_top = S9 ? 29.8 : 43.3;
socket_extra = S9 ? 1.5 : 0;      // socket deeper than the modelled spline (9 g: test fit)
// 9 g spline arm prints spline side down (no hub boss to stand on): the socket
// runs straight to the bed with no entry chamfer, and both arms keep their
// thin tips on the bed face (gripper.scad tip_flip).
spline_down = S9;
spline_base = S9 ? 26.8 : 39.4;   // top of the case/boss around the spline
horn_screw = S9 ? 2.2 : 2.8;      // clearance: M2 / M2.5
horn_head = S9 ? 4.5 : 6.0;       // bore for the screw head and driver
screw_floor = S9 ? 1.0 : 1.5;     // under the screw head
body = S9 ? [12.35, 22.8, 22.85] : [20, 35, 40];   // case, x/y/z
tab_y = S9 ? [15.95, 18.55] : [27.0, 29.3];   // mounting tab bottom/top
tab_x = S9 ? 5.98 : 9.35;         // tab half-width
tab_z = S9 ? 16.225 : 27;         // tab end
// 9 g: STL slot centres -14.8 / 14.725, moved 0.6 toward the servo to match
// the real servo (test fit)
tab_holes = S9 ? [[0, -14.8 + 0.6], [0, 14.725 - 0.6]]
               : [for (x = [-4.95, 4.95], z = [-24.83, 24.83]) [x, z]];
tab_pilot = S9 ? 1.6 : 2.5;       // self-tapping M2 / M3 from below through the slots
tab_pilot_h = S9 ? 6.5 : 9;      // from 1 mm below the tab top

/* [Layout] */
cd = 24;
idler_axis = spline_axis + cd;
arm_t = 7.6;           // as gripper.scad
hub_boss_h = S9 ? 0 : 2.2;        // spline arm boss reaching down onto the spline
arm_y0 = spline_base + 0.3 + hub_boss_h;   // bottom of the arm layer
arm_y1 = arm_y0 + arm_t;
clr = 0.4;             // between arms and frame
plate_t = 2.6;
top_y0 = arm_y1 + clr;
top_y1 = top_y0 + plate_t;
// idler's lower bearing: a thin ledge over the standard servo's lid, a block
// standing on the tab past the end of the 9 g servo
ledge_y = [S9 ? tab_y[1] : 38.3, arm_y0 - clr];
upper_wall_x0 = 13.8;  // in the arm layer the wall steps back to clear the teeth
wall_x = [body[0] / 2 + 0.3, max(body[0] / 2 + 0.3 + 7.8, upper_wall_x0 + 4.3)];
frame_z = [-tab_z, max(tab_z, idler_axis + 6)];   // frame ends
// The LEGO face prints on the bed. The 9 g wall is 11.65 thick and lifted at
// its corners when the counterbores came within ~1 mm of the edges, so its
// wall runs past the frame ends and the hole grid keeps a solid border.
wall_ext = S9 ? 2 : 0;
wall_z = [frame_z[0] - wall_ext, frame_z[1] + wall_ext];
// LEGO axle 2 (16 mm): resting on the standard servo's lid; on the 9 g frame
// the hole runs through the bearing block so the axle can go deeper or be
// pushed back out (axle_y0 is where the assembly view draws it)
axle_y0 = S9 ? top_y1 + 1 - 16 : 37.95;

/* [Hubs] */
hub_boss_d = 11;
tube_od = 9;           // tube under the top plate, runs in the arm's top recess
recess_d = tube_od + 0.6;
recess_h = S9 ? 1.9 : 2.6;        // must stay above the screw head seat
axle_hole = 4.95;      // round hole a LEGO cross axle turns in
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
lego_z = let(zc = (wall_z[0] + wall_z[1]) / 2, n = floor((wall_z[1] - wall_z[0] - 6) / 8))
  [for (i = [0:n]) zc + 8 * (i - n / 2)];
lego_y = S9 ? [7, 15, 23] : [4, 12, 20, 28, 36];
// A through hole that comes out half under a leg would leave a part-circle
// overhang where the leg covers it; those holes are left out.
function lego_hole_ok(y, z) = !lego_through || y + pin_hole / 2 < tab_y[1]
  || abs(abs(z) - (body[2] / 2 + 0.3)) > pin_cb_d / 2;
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
z_socket = arm_y1 - (spline_top + 0.3) - socket_extra;   // part z of the socket ceiling
z_floor = z_socket - screw_floor;         // screw head seat
assert(z_floor > recess_h, "screw head seat breaks into the top recess");
z_boss = arm_t + hub_boss_h;              // end of the hub, 0.3 over the case
module spline_arm() {
  difference() {
    union() {
      arm_body(-1, spline_down);
      if (hub_boss_h > 0)
        translate([0, 0, arm_t - 0.01]) cylinder(d = hub_boss_d, h = hub_boss_h + 0.01);
    }
    translate([0, 0, z_socket]) linear_extrude(z_boss) offset(delta = spline_clr) spline2d();
    if (!spline_down)
      translate([0, 0, z_boss - 0.6]) cylinder(d1 = spline_od + 0.2, d2 = spline_od + 1.4, h = 0.61);
    translate([0, 0, -1]) cylinder(d = horn_screw, h = z_boss + 2);
    translate([0, 0, -1]) cylinder(d = horn_head, h = z_floor + 1);
    translate([0, 0, -1]) cylinder(d = recess_d, h = recess_h + 1);
  }
}

module idler_arm() arm(1, spline_down);

// Part frame (gear axis = z, z = 0 at the top of the arm layer) to servo
// coordinates: part x -> +Z, part y -> -X, part z -> -Y.
module on_axis(z) multmatrix([[0, -1, 0, 0], [0, 0, -1, arm_y1], [1, 0, 0, z], [0, 0, 0, 1]]) children();

// ---------- servos ----------

// The servo model in servo coordinates.
module servo_model() {
  if (S9)   // servo_9g.stl also holds a standard servo; take the 9 g one at x 45..58
    multmatrix([[1, 0, 0, -51.44], [0, 0, 1, 0], [0, -1, 0, 5.625], [0, 0, 0, 1]])
      intersection() {
        import("servo/servo_9g.stl");
        translate([40, -50, -1]) cube([30, 100, 50]);
      }
  else import("servo/standard_servo.stl");
}

module box(x, y, z) translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);

// Room for the servo, with clearance.
module servo_clearance() {
  c = 0.25;
  bx = body[0] / 2 + c;
  bz = body[2] / 2 + c;
  box([-bx, bx], [-1, body[1] + c], [-bz, bz]);
  box([-tab_x - c, tab_x + c], [tab_y[0] - 1, tab_y[1]], [-tab_z - c, tab_z + c]);
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
      box([-tab_x, wall_x[1]], [tab_y[1], ledge_y[1]], [frame_z[0], -zb]);
      box([-tab_x, wall_x[1]], [tab_y[1], ledge_y[1]], [zb, tab_z]);
      // lower bearing for the idler axle
      plate(ledge_y[0], ledge_y[1] - ledge_y[0]) hull() {
        translate([0, -idler_axis]) circle(d = 12);
        translate([wall_x[0], -frame_z[1]]) square([wall_x[1] - wall_x[0], frame_z[1] - idler_axis + 8]);
        if (S9) translate([-tab_x, -frame_z[1]]) square([1, frame_z[1] - zb]);
      }
      // top plate over both arms
      plate(top_y0, plate_t) hull() {
        translate([0, -spline_axis]) circle(d = 18);
        translate([0, -idler_axis]) circle(d = 14);
        translate([upper_wall_x0, -frame_z[1]]) square([wall_x[1] - upper_wall_x0, frame_z[1] - frame_z[0]]);
      }
      // tube into the spline arm's top recess, boss around the idler axle
      translate([0, top_y0 - (recess_h - clr), spline_axis]) rotate([-90, 0, 0])
        cylinder(d = tube_od, h = recess_h - clr + 0.01);
      translate([0, top_y1 - 0.01, idler_axis]) rotate([-90, 0, 0])
        cylinder(d = idler_boss_d, h = idler_boss_top - top_y1 + 0.01);
    }
    servo_clearance();
    // driver access to the horn screw
    translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(d = horn_head + 0.4, h = 100);
    // idler axle, through the whole frame
    translate([0, min(axle_y0, ledge_y[0]) - 1, idler_axis]) rotate([-90, 0, 0]) cylinder(d = axle_hole, h = 100);
    // spline-end leg dropped below the arm's swing, top edges bevelled
    spline_leg_cut();
    // pilot holes for the tab screws
    for (h = tab_holes) translate([h[0], tab_y[1] - 1, h[1]]) rotate([-90, 0, 0])
      cylinder(d = tab_pilot, h = tab_pilot_h);
    // LEGO pin holes, counterbored on the outside
    for (y = lego_y, z = lego_z) if (lego_hole_ok(y, z)) translate([0, y, z])
      lego_hole_x(lego_through ? wall_x[0] : wall_x[1] - 7.8, wall_x[1]);
  }
}

// ---------- assembly ----------

module axle() {   // LEGO axle 2
  color("black") translate([0, axle_y0, idler_axis]) rotate([-90, 0, 0])
    linear_extrude(16) {
      square([4.8, 1.8], center = true);
      square([1.8, 4.8], center = true);
    }
}

if (part == "spline_arm")   // spline side down when spline_down
  if (spline_down) translate([0, 0, z_boss]) rotate([180, 0, 0]) spline_arm(); else spline_arm();
else if (part == "idler_arm") idler_arm();
else if (part == "frame") translate([0, 0, wall_x[1]]) rotate([0, 90, 0]) frame();   // LEGO face on the bed
else rotate([90, 0, 0]) {   // servo Y up on screen
  color("orange") on_axis(spline_axis) rotate(theta) spline_arm();
  color("royalblue") on_axis(idler_axis) rotate(-theta) idler_arm();
  axle();
  color("lightgray") frame();
  if (show_servo) color("dimgray") servo_model();
  if (show_can) %translate([-52, 0, (spline_axis + idler_axis) / 2]) rotate([-90, 0, 0])
    translate([0, 0, -20]) cylinder(d = 66, h = 115, $fn = 96);
}
