// Can gripper: two printed arms, each with its 24-tooth gear molded in.
// The gears replace the stock LEGO 24T gears (module 1, 24 mm centers) and keep
// teeth only on the sector that meshes over the -6..90 deg range.
// Left arm sits on the Nezha motor axle, right arm on the idler axle; both use a
// LEGO cross axle. The two arms are mirror images except for the tooth phase
// (half a tooth apart so they mesh) and the tip, which is thinned on opposite
// faces so the tips lap past each other.

/* [Pose] */
// Opening angle, deg: 0 = neutral 65 mm ring, negative squeezes.
theta = -6 + 96 * (0.5 - 0.5 * cos(360 * $t));
// "assembly", "left", "right" (printable arms) or "frame" (notched frame)
part = "assembly";
show_can = true;

/* [Arm] */
ring_id = 65;          // hole at neutral
ring_wall = 5;
arm_t = 7.6;           // part thickness, gear and arm together (1 unit, as the frame)
ring_cx = 12;          // ring center relative to the gear axis (part frame)
ring_cy = 52;
tip_gap_deg = 9;       // gap at the tips at neutral
tip_len = 10;          // tip length thinned so the two tips can lap past each other
tip_bevel = 3;         // 45 deg lead-in on the end of the thin tip
tip_t = 3;             // tip thickness; left arm keeps the gear-side face, right
                       // arm the front face, so the tips slide past each other
end_deg = 259;         // lower end of the ring arc
link_deg = 257;        // where the link meets the ring (leans inward to clear the frame)
hub_d = 20;
link_w = 9;            // link width where it meets the ring
fillet = 9;            // blend radius between link, hub and ring
round_r = 1.5;         // edge rounding of convex corners

/* [Gear] */
cd = 24;               // gear center distance (3 LEGO studs)
teeth = 24;
mod = 1;
pa = 20;
backlash = 0.1;        // mm removed from each tooth flank, for printing
tooth_margin = 25;     // extra teeth (deg) past the swept range on each side
cross_len = 5.0;       // LEGO cross axle 4.8 x 1.8 + clearance
cross_w = 2.0;
// Technic pin holes, profile measured from nezha_frame.stl: 4.88 bore with a
// 6.4 x 0.9 counterbore (the collar lip) on both faces. Same pattern as the
// LEGO 24T gear: (+-4, +-4) around the axle.
pin_hole = 4.9;
pin_cb_d = 6.4;
pin_cb_h = 0.9;
// Arms print with z = 0 on the bed; a cone from that counterbore back to the
// pin bore replaces the flat overhanging step (as partdesigner's
// basePinTaperAngle). Angle from the hole axis; 35.9 deg gives a 1 mm taper.
base_pin_taper_angle = 35.9;
pins = [for (x = [-4, 4], y = [-4, 4]) [x, y]];

$fn = 72;
rc = ring_id / 2 + ring_wall / 2;
C = [ring_cx, ring_cy];
function P(a, r = rc) = C + r * [cos(a), sin(a)];

rp = teeth * mod / 2;
rb = rp * cos(pa);
ro = rp + mod;
rr = rp - 1.25 * mod;

function inv(a) = tan(a) - a * PI / 180;          // involute, radians
function half_ang(r) =                             // tooth half-angle, degrees
  (PI / (2 * teeth) + inv(pa) - inv(acos(rb / r)) - backlash / r) * 180 / PI;

module tooth() {
  steps = 8;
  flank = [for (i = [0:steps]) let(r = rb + (ro - rb) * i / steps) [r, half_ang(r)]];
  a0 = half_ang(rb);
  polygon(concat([(rr - 0.5) * [cos(-a0), sin(-a0)]],
                 [for (p = flank) p[0] * [cos(-p[1]), sin(-p[1])]],
                 [for (i = [steps:-1:0]) flank[i][0] * [cos(flank[i][1]), sin(flank[i][1])]],
                 [(rr - 0.5) * [cos(a0), sin(a0)]]));
}

// Root disc plus teeth whose centers fall in [a0, a1]; teeth at phase + k*360/teeth.
module sector_gear2d(phase, a0, a1) {
  circle(r = rr);
  for (i = [0:teeth - 1]) let(a = phase + i * 360 / teeth)
    for (k = [-360, 0, 360]) if (a + k >= a0 && a + k <= a1) rotate(a + k) tooth();
}

module ring_arc(a0, a1) {
  intersection() {
    translate(C) difference() {
      circle(d = ring_id + 2 * ring_wall, $fn = 180);
      circle(d = ring_id, $fn = 180);
    }
    polygon(concat([C], [for (i = [0:40]) P(a0 + (a1 - a0) * i / 40, 200)]));
  }
}

// 2D outline of the arm (left-hand arm, gear axis at origin).
module arm2d() {
  a_tip = 90 + tip_gap_deg;
  difference() {
    // round convex corners, then fill concave ones for the smooth blend
    offset(r = round_r) offset(delta = -round_r)
    offset(r = -fillet) offset(r = fillet) union() {
      ring_arc(a_tip, end_deg);
      translate(P(a_tip)) circle(d = ring_wall);
      translate(P(end_deg)) circle(d = ring_wall);
      circle(d = hub_d);
      hull() {
        circle(d = hub_d - 4);
        translate(P(link_deg)) circle(d = link_w);
      }
    }
    // keep the gripping surface a true circle
    translate(C) circle(d = ring_id, $fn = 180);
  }
}

module cross2d() {
  square([cross_len, cross_w], center = true);
  square([cross_w, cross_len], center = true);
}

// Arm layer (left-hand geometry, gear axis at origin, z 0..arm_t). The tip is
// thinned to tip_t on the z=0 face; the bevel is on the face that meets the
// other tip.
module arm_layer() {
  a_tip = 90 + tip_gap_deg;
  difference() {
    linear_extrude(arm_t) arm2d();
    translate([0, 0, tip_t]) linear_extrude(arm_t) intersection() {
      translate(C) difference() {
        circle(r = rc + ring_wall);
        circle(r = rc - ring_wall);
      }
      polygon(concat([C], [for (i = [0:20]) P(a_tip - 15 + (tip_len / rc * 180 / PI + 15) * i / 20, 200)]));
    }
    // 45 deg bevel on the end of the thin tip. t points out of the tip; E is the end.
    t = [sin(a_tip), -cos(a_tip)];
    E = P(a_tip) + ring_wall / 2 * t;
    intersection() {
      translate([E.x, E.y, -1]) cylinder(r = tip_bevel + 1, h = arm_t + 2);
      translate([E.x, E.y, tip_t - tip_bevel]) rotate(atan2(t.y, t.x)) rotate([0, 45, 0])
        translate([-50, -50, 0]) cube([100, 100, 50]);
    }
  }
}

// Mesh point is at +x for the left gear, 180 for the right. Over theta in
// [-6, 90] the left gear's body angles -90..6 pass it, the right's 174..270.
// Left teeth at 0 + k*15; the right needs a gap facing the left's tooth, so
// its teeth are offset half a tooth (7.5 deg).
theta_min = -6;
theta_max = 90;

// Printable arm in its own frame: gear teeth and arm share one 1U layer
// (z 0..arm_t, z = 0 on the motor side). side = -1 left (motor), +1 right (idler).
// Gear and arm without the hub holes (servo_gripper.scad adds its own hub).
// tip_flip keeps each tip on the other face (left arm: z = arm_t, right arm:
// z = 0); the tips still lap past each other, and the face that keeps the tip
// is the one to print on.
module arm_body(side, tip_flip = false) {
  linear_extrude(arm_t) if (side < 0)
    sector_gear2d(0, -theta_max - tooth_margin, -theta_min + tooth_margin);
  else
    sector_gear2d(7.5, 180 + theta_min - tooth_margin, 180 + theta_max + tooth_margin);
  if (side < 0) flip_z(tip_flip) arm_layer();
  else translate([0, 0, arm_t]) rotate([0, 180, 0]) flip_z(tip_flip) arm_layer();
}

module flip_z(f) if (f) translate([0, 0, arm_t]) mirror([0, 0, 1]) children(); else children();

module arm(side, tip_flip = false) {
  difference() {
    arm_body(side, tip_flip);
    translate([0, 0, -1]) linear_extrude(arm_t + 2) cross2d();
    for (p = pins) translate(p) {
      translate([0, 0, -1]) cylinder(d = pin_hole, h = arm_t + 2);
      for (z = [-1, arm_t - pin_cb_h]) translate([0, 0, z]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
      taper_h = (pin_cb_d - pin_hole) / 2 / tan(base_pin_taper_angle);
      translate([0, 0, pin_cb_h - 0.01]) cylinder(d1 = pin_cb_d, d2 = pin_hole, h = taper_h + 0.01);
    }
  }
}

// ---------- assembly in the Nezha motor / frame coordinates ----------
// From the Tinkercad layout (Y is the axle direction, Z up):
// The frame's 1U channel (y 13.0..21.4, see frame_1u) sits between its front
// wall and the motor's output face; the arms (y 13.4..21.0) reach up out of the
// channel's open top.
// The channel's right end wall (x 90..98) is notched where the idler arm
// sweeps through it, so the arms open a full 90 deg.
motor_axis = [54.3, 19.7];     // x, z of the motor-driven gear
idler_axis = [78.3, 19.7];
gear_y = 21.0;                 // world y of the part's motor-side face (0.4 clearance)

// Frame, regenerated with a 1U gripper channel: nezha_frame.stl has a 2U channel
// (front wall y -2.6..5.0, motor face y 21.4). Drop the 8 mm slab y 5.2..13.2
// (halfway between hole rows, so the 8 mm hole grid stays continuous) and move
// the front part back 8 mm: front wall y 5.4..13.0, channel y 13.0..21.4.
module frame_1u() {
  big = 1000;
  union() {
    intersection() { import("nezha_frame.stl"); translate([-big / 2, 13.2, -big / 2]) cube(big); }
    translate([0, 8, 0])
      intersection() { import("nezha_frame.stl"); translate([-big / 2, 5.21 - big, -big / 2]) cube(big); }
  }
}

// Cuts from the swept volume of both arms over -6..92 deg:
// - notch in the right end wall where the right arm passes (x 90.4..98,
//   z 11.3..31.6), ~1 mm clearance;
// - pocket in the bottom plate under the gear teeth: the tooth tips reach
//   z 6.7 and the plate top is z 7.6 (the stock gears overlapped it the same way).
module frame() {
  difference() {
    frame_1u();
    translate([89, 13.0, 10]) cube([10, 21.4 - 13.0, 25]);
    translate([46.5, 13.0, 5.6]) cube([86 - 46.5, 21.4 - 13.0, 5]);
  }
}

// Place a gear-frame stack (axis = local z) on the horizontal y axis.
module on_axis(p) translate([p[0], gear_y, p[1]]) rotate([90, 0, 0]) children();

// axle from the motor face out through the arm and the frame's front wall
module axle() { color("black") translate([0, 0, -0.4]) linear_extrude(gear_y + 0.4 - 5.4) cross2d(); }

module left_arm(t)  on_axis(motor_axis) rotate(t) arm(-1);
module right_arm(t) on_axis(idler_axis) rotate(-t) arm(1);

if (part == "left") arm(-1);
else if (part == "right") arm(1);
else if (part == "none") {}
else if (part == "frame") frame();
else {
  color("orange") left_arm(theta);
  color("royalblue") right_arm(theta);
  on_axis(motor_axis) axle();
  on_axis(idler_axis) axle();
  color("hotpink") import("nezha_motor.stl");
  color("lightgray") frame();
  if (show_can) %on_axis((motor_axis + idler_axis) / 2 + [0, ring_cy]) translate([0, 0, -40])
    cylinder(d = 66, h = 115, $fn = 96);
}
