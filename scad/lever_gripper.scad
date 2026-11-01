// CONCEPT MOCK-UP (2026-10-26): gearless gripper on a horizontal 9 g servo.
//
// The servo lies on edge with its output shaft horizontal, pointing forward
// (+Y) between the two jaw axles. A double horn stands vertical on the spline
// with a ball on each tip, one above the shaft and one below. Each jaw is a
// lever on a vertical LEGO axle (24 mm apart, as the geared gripper) carrying
// the same swappable-arm stub; it also carries a fork, two fore-aft plates
// that straddle its ball. Turning the servo moves the upper ball one way and
// the lower ball the other, so the two jaws mirror each other with no gears
// and no links: the ball drives the fork sideways while sliding freely along
// it (fore-aft) and up/down inside it. Both jaws are the same part: the
// right jaw is the left one turned over.
//
// World coordinates: X across, Y forward (toward the object), Z up. The jaw
// axles are at (-/+p, 0), the servo shaft is the Y axis, the balls at y = b.
// Jaw angle th from the fork constraint (p - r sin phi) cos th + b sin th = p:
// th = 0 when the horn is vertical (phi = 0); th > 0 opens.

include <servo_gripper.scad>
servo = "9g";
show_part = false;

/* [Pose] */
// servo angle, deg; - closes, + opens
phi = -45 + 90 * (0.5 - 0.5 * cos(360 * $t));
// "all" (assembly), "jaw" (print orientation), "clash" (what the horn and
// servo hit in the jaws; empty = clear), "clash_jaws", or one component in
// place: "left_jaw", "right_jaw", "horn", "servo", "frame", "axles"
show = "all";

/* [Mechanism] */
r = 10;          // horn radius to the ball centres
b = 15;          // balls forward of the axle line
p = 12;          // half the axle spacing (3 studs)
ball_d = 5.85;   // as a LEGO tow ball
horn_t = 3;      // horn thickness along Y; the balls sit in its mid-plane
horn_w = 7;      // horn arm width out to neck_r0
neck_w = 2.4;    // thin neck up to the ball: passes between the fork plates (steel pin in a real part)
neck_r0 = 5;     // the wide arm ends here, flat (clear of the plates' band)
hub_ext = 6;     // horn hub reaches back this far to the spline: servo sits further back
fork_gap = ball_d + 0.45;
plate_t = 2;
fork_y = [10.8, 24];    // plates along the fork (jaw frame), from the axle; ball centre runs 10.2..21.1
fork_z = [6.8, 13.2];   // plate band: ball centre z = r cos(phi), 7.1..10, top of ball 12.9
bridge_z = [13.2, 15.2];
web_z0 = 6.3;           // web bottom, over the servo's gear-head boss and case top
arm_z = [-3.8, 3.8];    // finger layer, one LEGO unit on the shaft height
hub_r = 5.5;
// jaw angle (from th = 0) at which the stub points straight forward = closed
th_closed = -22.2;      // servo at -45 deg

/* [Servo placement] */
horn_y = b;                                   // horn mid-plane
servo_shift = horn_y - (spline_base + 2.5) - hub_ext;   // servo y -> world Y; horn on the outer 3 mm of the spline

function jaw_angle(phi) =
  let (A = p - r * sin(phi), R = sqrt(A * A + b * b))
  atan2(b, A) - acos(p / R);
th = jaw_angle(phi);
echo(phi = phi, jaw = th, jaw_from_closed = th - th_closed);

$fn = 48;

// ---------- components (world coordinates) ----------

module servo_placed() translate([0, servo_shift, 0]) rotate([0, 180, 0]) translate([0, 0, -spline_axis]) servo_model();

module horn() color("#f29a00") rotate([0, -phi, 0]) {
  translate([0, horn_y + horn_t / 2, 0]) rotate([90, 0, 0]) linear_extrude(horn_t) {
    circle(r = 5);
    for (s = [-1, 1]) {
      translate([-horn_w / 2, s > 0 ? 0 : -neck_r0]) square([horn_w, neck_r0]);
      hull() { translate([0, s * neck_r0]) circle(d = neck_w); translate([0, s * r]) circle(d = neck_w); }
    }
  }
  for (s = [-1, 1]) translate([0, horn_y, s * r]) sphere(d = ball_d);
  // hub tube back to the spline
  translate([0, horn_y - horn_t / 2 + 0.01, 0]) rotate([90, 0, 0]) cylinder(r = 5, h = hub_ext);
}

// Left jaw in its own frame: axle at the origin, +X toward the other jaw,
// th = 0 pose. Stub as swap_gripper.scad (x -17..-9, y 5..38, pins at y 17, 33).
module jaw_body() {
  // finger layer: hub, stub, hull between (rotated so the stub is straight at th_closed)
  translate([0, 0, arm_z[0]]) rotate(-th_closed) linear_extrude(arm_z[1] - arm_z[0]) union() {
    circle(r = hub_r);
    hull() { circle(r = hub_r - 1); translate([-17, 5]) square([8, 8]); }
    translate([-17, 5]) square([8, 33]);
  }
  // riser over the hub, then the web out to the fork's inner plate. The web
  // starts at web_z0 to clear the servo's gear head, and its front edge
  // clears the servo's upper mounting tab when the jaw is closed.
  translate([0, 0, arm_z[1] - 0.01]) linear_extrude(web_z0 - arm_z[1] + 0.02)
    polygon([[-5, -2], [2.5, -2], [2.5, 4.5], [-5, 4.5]]);
  translate([0, 0, web_z0]) linear_extrude(bridge_z[1] - web_z0)
    polygon([[-6, 2], [2.5, 2], [2.5, 6], [p - fork_gap / 2 - plate_t, fork_y[0] + 0.2],
             [p - fork_gap / 2 - plate_t, fork_y[1]], [-6, fork_y[1]]]);
  // fork: two plates and the bridge over them
  for (x = [p - fork_gap / 2 - plate_t, p + fork_gap / 2])
    translate([x, fork_y[0], fork_z[0]]) cube([plate_t, fork_y[1] - fork_y[0], bridge_z[1] - fork_z[0]]);
  translate([p - fork_gap / 2 - plate_t, fork_y[0], bridge_z[0]])
    cube([fork_gap + 2 * plate_t, fork_y[1] - fork_y[0], bridge_z[1] - bridge_z[0]]);
}
module jaw() difference() {
  jaw_body();
  // LEGO cross axle through the hub, pin holes along X through the stub
  translate([0, 0, arm_z[0] - 1]) linear_extrude(web_z0 - arm_z[0] + 2) cross2d();
  rotate(-th_closed) for (y = [17, 33]) translate([-18, y, 0]) rotate([0, 90, 0]) cylinder(d = 4.9, h = 10);
}

module left_jaw()  color("#3cb371") translate([-p, 0, 0]) rotate(th) jaw();
module right_jaw() color("#4169e1") translate([p, 0, 0]) rotate(-th) rotate([0, 180, 0]) jaw();

module axles() color("#222") for (s = [-1, 1]) translate([s * p, 0, -16]) linear_extrude(32) cross2d();   // 4L axles

// sketch frame: two plates with LEGO pin holes, side and back walls
module frame() color("#c8c8c8", 0.55) difference() {
  union() {
    for (z = [15.8, -18.4]) translate([-21, -26, z]) cube([42, 32, 2.6]);
    for (s = [-1, 1]) translate([s * 19.7 - 1.3, -26, -15.8]) cube([2.6, 30, 31.6]);
    translate([-21, -26, -15.8]) cube([42, 2.6, 31.6]);
    translate([-7, -4.5, -22.6]) cube([14, 4.6, 4.3]);   // pocket for the lower tab
  }
  for (s = [-1, 1]) translate([s * p, 0, -20]) cylinder(d = 4.9, h = 40);
  for (x = [-16 : 8 : 16], y = [-22, -14]) translate([x, y, -20]) cylinder(d = 4.9, h = 40);
  translate([0, servo_shift, 0]) rotate([0, 180, 0]) translate([0, 0, -spline_axis]) servo_clearance();
}

module shown(c) if (show == "all" || show == c) children();

if (show == "jaw") translate([0, 0, -arm_z[0]]) jaw();
else if (show == "clash") intersection() { union() { horn(); servo_placed(); } union() { left_jaw(); right_jaw(); } }
else if (show == "clash_jaws") intersection() { left_jaw(); right_jaw(); }
else {
  shown("left_jaw") left_jaw();
  shown("right_jaw") right_jaw();
  shown("horn") horn();
  shown("servo") color("dimgray") servo_placed();
  shown("frame") frame();
  shown("axles") axles();
}
