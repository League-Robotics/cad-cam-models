// Swappable arms for the geared gripper. The part that stays in the frame is
// the "nub": the 24T gear sector, the hub and a short stub. Whole arms pin
// onto the stub's inner face with two standard 2L LEGO friction pins whose
// axes point at the other jaw, so squeezing an object pushes the arm further
// onto its pins. Everything near the hub stays in the 1U arm layer; only the
// end effector, ~4 cm out, is taller than the layer.
//
// Arms (`arm`):
//   "can"  - the 65 mm ring of gripper.scad, now on a pinned base
//   "cube" - straight arm, flat 38 mm tall textured paddle; parallel and
//            26 mm apart at theta = 0
//   "cube_low" - the cube arm with its paddle run on past the 38 mm: pad_ext
//            further down and up. Left and right are a mirror pair, both
//            with the long end down; swap them side to side and each turns
//            over, putting the short end down: two reach heights.
//   "cube_short" - the cube arm with pad_trim off both ends of the paddle,
//            for low mounts, where the full paddle would reach the floor
//   "ball" - curved arm, 38 mm tall cylindrical cup for the 40 mm ball,
//            closed on the ball at theta = 0
//
// Part frame (as gripper.scad): gear axis on z, arm layer z 0..arm_t, left
// arm (side -1) with its axis at the origin, forward +y, the other jaw +x.
// The right-hand parts are the left mirrored (x -> -x) and flipped
// (z -> arm_t - z), as gripper.scad does with its arms.

use <gripper.scad>

/* [Show] */
// "nub", "arm", "jaw" (nub + arm, left), "exploded", "pair",
// "print" (arm `arm`, hand `side`) or "nub_print" (LEGO-axle gear arm, grippers/arms, hand `side`)
part = "pair";
arm = "cube";         // "can", "cube", "cube_low", "cube_short", "ball"
side = -1;            // -1 left, 1 right
theta = 0;

/* [Gear, as gripper.scad] */
cd = 24;
arm_t = 7.6;
hub_d = 20;
theta_min = -6;
theta_max = 90;
tooth_margin = 25;
pin_hole = 4.9;
pin_cb_d = 6.4;
pin_cb_h = 0.9;
round_r = 1.5;

/* [Nub and arm base] */
stub_x = [-17, -9];   // stub across x; its inner face carries the arm
stub_y = [5, 38];
pin_y = [17, 33];     // the two pin stations, 2 studs apart
base_x = [-9, -1.2];  // arm base: one LEGO unit deep for the pins
base_y = [12.5, 38];  // clears the gear root (r 10.75)
zc = arm_t / 2;
clr = 0.3;            // nub cut back around the arm base
// The idler (right, s > 0) turns on its axle in a round hole; the frame holds
// the axle in cross holes. The driven (left) nub keeps the cross. The idler
// also drops the four pin holes around its hub: just the one hole in the centre.
idler_round = true;
idler_hub_pins = false;

/* [Hand labels] */
// "L" or "R" engraved in the stub's top face between the pin holes, so each
// gear arm pairs with the right extension arm and the right partner
label_size = 5;
label_depth = 0.6;
label_y = (pin_y[0] + pin_y[1]) / 2;

/* [Effectors] */
eff_h = 38;           // effector height along the axle, centred on the layer
beam_x = [-9, -3];    // in-layer beam from base to effector
// cube paddle
pad_y = [42, 72];
face_x = -1;          // texture tips: 26 mm apart at theta 0
tex_h = 0.8;
tex_p = 2;
// cube_low: paddle beyond eff_h / 2 [down, up] in the assembly (z up), so the
// arms reach further toward the floor; swapped side to side, down and up trade
pad_ext = [16, 8];
pad_y_low = [32, 82];  // 1 cm longer than pad_y at each end
// cube_short: paddle cut back at both ends (32 mm tall)
pad_trim = 3;
// cube_low racket: a rim and a diagonal lattice of ribs, the rest open
rim = 3;
rib = 1.6;
rib_p = 9;             // rib spacing, square to the ribs
// ball cup: axis on the centre line at theta 0
ball_d = 40;
cup_r = 20.5;
cup_wall = 4;
cup_yc = 58;
cup_span = 56;        // half-angle of the cup either side of -x
// can ring: gripper.scad ring (65 ID, wall 5), moved forward from (12, 52)
// so the can clears the stubs
ring_id = 65;
ring_wall = 5;
ring_c = [12, 76];
// the ring's rear end (where it "completes the circle" inboard of the beam)
// cut flat ring_trim up from its lowest point, so the closed arms clear the
// caster beam of the Cutebot gripper (cutebot_gripper.scad, 2026-10-29); 0
// for the full ring
ring_trim = 3.1;
ring_trim_r = 2;      // the fillet where the cut meets the base's inner face
ring_rear_y = ring_c.y - ring_id / 2 - ring_wall - 2;   // the ring's lowest point (its thinned-tip annulus, r + 2)
// The ring turned can_ring_rot on the arm (2026-10-29, the user: "the
// circle never completely forms ... it's a 15 degree rotation"): the tips
// of gripper.scad's ring (tip_gap_deg 9 short of the top, tip_len 10 thinned
// to tip_t on opposite faces so they lap) are unchanged, they just reach
// the centre line sooner, at theta_tips_meet, and lap fully (the thinned
// 10 mm, 2.6 degrees of theta later) at the closed position; beyond that
// the thick parts meet and the tips jam, which is the closing limit. The
// rear ends stay where they were (the base's sector).
can_ring_rot = 15;
rc_ = ring_id / 2 + ring_wall / 2;
can_tip_gap = 9 - can_ring_rot;                            // -6: 6 past the top
// Then the ring is turned about the axle relative to the stub (the user,
// 2026-10-29: "hold the two ring halves in position, open the gripper by
// 5 degrees, reattach"): the ring (its arc, rear-end trim and all) is
// rotated -can_ring_open in the arm's frame, so the arms stand can_ring_open
// open when the halves are concentric; the base and the beam stay.
can_ring_open = 5;
// the left tip's x at theta t, from the centre line (the lap is twice it)
function tip_x(t) = let(a = 90 + can_tip_gap, p = ring_c + rc_ * [cos(a), sin(a)], u = t - can_ring_open)
    p.x * cos(u) - p.y * sin(u) - ring_c.x;
function theta_at_lap(lap, t = 15) = t < -10 ? t : 2 * tip_x(t) >= lap ? t : theta_at_lap(lap, t - 0.1);
theta_tips_meet = theta_at_lap(0);
theta_tips_lapped = theta_at_lap(10);
echo(can_tip_gap = can_tip_gap, can_ring_open = can_ring_open, theta_tips_meet = theta_tips_meet, theta_tips_lapped = theta_tips_lapped,
     tip_lap = [for (t = [theta_min, -4, 0, 4, 5, 6]) [t, 2 * tip_x(t)]]);

$fn = 48;
ez = [zc - eff_h / 2, zc + eff_h / 2];

module box(x, y, z) translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
module sq(x, y) translate([x[0], y[0]]) square([x[1] - x[0], y[1] - y[0]]);

// LEGO pin hole along local +z from z0 to z1, counterbored at both ends.
module pin_hole_z(z0, z1) {
  translate([0, 0, z0 - 1]) cylinder(d = pin_hole, h = z1 - z0 + 2);
  translate([0, 0, z0 - 1]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
  translate([0, 0, z1 - pin_cb_h]) cylinder(d = pin_cb_d, h = pin_cb_h + 1);
}
// The pin holes along x through [x0, x1] at both stations.
module cross_holes(x0, x1) for (y = pin_y) translate([0, y, zc]) rotate([0, 90, 0]) pin_hole_z(x0, x1);

// Engraves the hand letter of side s in the z = arm_t face of children() over
// the stub, a gear arm in print orientation: stub on -x (left) or +x (right),
// running toward +y, or toward -y when flip_y (the 9 g spline arm, printed
// turned over).
module hand_label(s, flip_y = false) difference() {
  children();
  translate([s * (stub_x[0] + stub_x[1]) / -2, flip_y ? -label_y : label_y, arm_t - label_depth])
    linear_extrude(label_depth + 1)
      text(s < 0 ? "L" : "R", size = label_size, font = "Liberation Sans:style=Bold",
           halign = "center", valign = "center");
}

// ---------- nub ----------

module nub2d() difference() {
  offset(r = round_r) offset(delta = -round_r)
  offset(r = -5) offset(r = 5) union() {
    circle(d = hub_d);
    hull() {
      circle(d = hub_d - 6);
      sq(stub_x, [stub_y[0], stub_y[0] + 8]);
    }
    sq(stub_x, stub_y);
  }
  offset(delta = clr) sq([base_x[0], 40], base_y);
}

module nub_layer() difference() {
  linear_extrude(arm_t) nub2d();
  cross_holes(stub_x[0], stub_x[1]);
}

// Left-hand nub without hub holes; nub_arm adds the hub hole (cross, or round
// on the idler) and pin
// holes, servo_gripper.scad's spline_hub the servo hub.
module nub_body(s) {
  linear_extrude(arm_t) if (s < 0)
    sector_gear2d(0, -theta_max - tooth_margin, -theta_min + tooth_margin);
  else
    sector_gear2d(7.5, 180 + theta_min - tooth_margin, 180 + theta_max + tooth_margin);
  handed(s) nub_layer();
}
module nub_arm(s) arm_holes(round_hub = s > 0 && idler_round, hub_pins = !(s > 0 && idler_round && !idler_hub_pins)) nub_body(s);

module handed(s) if (s < 0) children(); else translate([0, 0, arm_t]) rotate([0, 180, 0]) children();

// ---------- arms (left-hand) ----------

// Pyramid texture on the plane x = x0, tips at x0 + tex_h.
module texture(x0, y, z) {
  n_y = floor((y[1] - y[0] - 1) / tex_p);
  n_z = floor((z[1] - z[0] - 1) / tex_p);
  for (i = [0:n_y - 1], j = [0:n_z - 1])
    translate([x0 - 0.01, y[0] + (y[1] - y[0] - n_y * tex_p) / 2 + (i + 0.5) * tex_p,
               z[0] + (z[1] - z[0] - n_z * tex_p) / 2 + (j + 0.5) * tex_p])
      rotate([0, 90, 0]) linear_extrude(tex_h + 0.01, scale = 0.1) square(tex_p, center = true);
}

// 2D annular sector around c, radii r0..r1, angles a0..a1.
module sector(c, r0, r1, a0, a1) translate(c) difference() {
  polygon(concat([[0, 0]], [for (i = [0:32]) let(a = a0 + (a1 - a0) * i / 32) 2 * r1 * [cos(a), sin(a)]]));
  circle(r = r0, $fn = 120);
  difference() { circle(r = 3 * r1); circle(r = r1, $fn = 120); }
}

// ext: paddle beyond eff_h / 2 at [-z, +z] of the part frame; py: paddle
// y span; racket: open the paddle into a rim and a diagonal rib lattice.
module cube_arm(ext = [0, 0], py = pad_y, racket = false) {
  pz = [ez[0] - ext[0], ez[1] + ext[1]];   // paddle z span
  x1 = face_x - tex_h;
  e = 1.5;   // lead-in chamfer at the tip
  // base and beam in the layer, rounded in plan
  linear_extrude(arm_t) offset(r = 1) offset(delta = -1) union() {
    sq(base_x, base_y);
    sq(beam_x, [base_y[0], py[0] + 1]);
  }
  // gusset from the beam up to the full paddle height (45 deg faces); the
  // racket opens it to a frame
  g = [[py[0] - 14, 0], [py[0] - 14, arm_t], [py[0], pz[1]], [py[0], pz[0]]];
  difference() {
    hull() {
      box(beam_x, [py[0] - 14, py[0]], [0, arm_t]);
      box([beam_x[0], beam_x[0] + 4], [py[0], py[0] + 0.01], pz);
    }
    if (racket) translate([beam_x[0] - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(20) difference() {
      offset(delta = -rim) polygon(g);
      translate([0, -rim]) square([base_y[1] + rim, arm_t + 2 * rim]);   // keep the beam
    }
  }
  difference() {
    union() {
      hull() {
        box([beam_x[0], x1], [py[0], py[1] - e], pz);
        box([beam_x[0], x1 - e], [py[0], py[1]], pz);
      }
      texture(x1, [py[0], py[1] - e], pz);
    }
    if (racket) racket_holes(py, pz);
  }
}

// The openings of the racket paddle, through x: the inside of the rim less a
// lattice of ribs at +-45 deg (self-supporting either way up).
module racket_holes(py, pz) {
  w = py[1] - py[0];
  h = pz[1] - pz[0];
  n = ceil((w + h) / rib_p) + 1;
  translate([beam_x[0] - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(20) difference() {
    translate([py[0] + rim, pz[0] + rim]) square([w - 2 * rim, h - 2 * rim]);
    // keep a solid band round the arm base, which the paddle now overlaps
    translate([0, -rim]) square([base_y[1] + rim, arm_t + 2 * rim]);
    translate([(py[0] + py[1]) / 2, (pz[0] + pz[1]) / 2]) for (a = [45, -45]) rotate(a)
      for (k = [-n : n]) translate([k * rib_p, 0]) square([rib, 4 * (w + h)], center = true);
  }
}

cup_c = [cd / 2, cup_yc];
cup_a = [180 - cup_span, 180 + cup_span];
module ball_arm() {
  // where the cup's lower end meets the base
  a_lo = cup_a[1];
  difference() {
    union() {
      linear_extrude(arm_t) offset(r = 1) offset(delta = -1) union() {
        sq(base_x, base_y);
        sector(cup_c, cup_r, cup_r + cup_wall, a_lo - 25, a_lo);
      }
      translate([0, 0, ez[0]]) linear_extrude(eff_h) sector(cup_c, cup_r, cup_r + cup_wall, cup_a[0], cup_a[1]);
      // gusset from the base up to full height at the cup's lower end
      hull() {
        box(base_x, [base_y[1] - 8, base_y[1]], [0, arm_t]);
        intersection() {
          translate([0, 0, ez[0]]) linear_extrude(eff_h) sector(cup_c, cup_r, cup_r + cup_wall, a_lo - 6, a_lo);
          box([-50, 50], [-50, 200], [-50, 50]);
        }
      }
    }
    translate([cup_c.x, cup_c.y, -50]) cylinder(r = cup_r, h = 100, $fn = 120);
    // circumferential grooves: ridges that stop the ball sliding up or down
    for (z = [ez[0] + 3 : 3 : ez[1] - 2])
      translate([cup_c.x, cup_c.y, z - 0.6]) cylinder(r = cup_r + 0.7, h = 1.2, $fn = 120);
  }
}

module can_arm() difference() {
  can_arm_full();
  // the rear end's trim: everything inboard of the base's inner face and
  // below the flat (ring_rear_y + ring_trim in the ring's own frame, turned
  // with it), the cut's corner at the base rounded (ring_trim_r) so the
  // base's face runs into the flat with a fillet
  if (ring_trim > 0) translate([0, 0, -1]) linear_extrude(arm_t + 2)
    offset(r = ring_trim_r) offset(delta = -ring_trim_r) intersection() {
      rotate(-can_ring_open) sq([-60, 60], [-10, ring_rear_y + ring_trim]);
      sq([base_x[1] + 0.01, 60], [-10, 60]);
    }
}

module can_arm_full() {
  // the ring from gripper.scad, tips thinned so the two lap past each
  // other, turned about the axle (can_ring_open)
  rotate(-can_ring_open) intersection() {
    translate([0, ring_c.y - 52, 0]) arm_layer(can_tip_gap);
    translate([0, 0, -1]) linear_extrude(arm_t + 2) translate(ring_c) difference() {
      circle(d = ring_id + 2 * ring_wall + 4, $fn = 180);
      circle(d = ring_id - 0.01, $fn = 180);
    }
  }
  // base and beam, blended into the ring's lower end
  linear_extrude(arm_t) difference() {
    offset(r = round_r) offset(delta = -round_r) offset(r = -6) offset(r = 6) union() {
      sq(base_x, base_y);
      sq(beam_x, [base_y[0], ring_c.y - 24]);
      rotate(-can_ring_open) sector(ring_c, ring_id / 2, ring_id / 2 + ring_wall, 215, 259);
    }
    rotate(-can_ring_open) translate(ring_c) circle(d = ring_id, $fn = 180);
  }
}

// s: the hand, for the asymmetric cube_low (the right arm's part frame is
// turned over, so its ends swap)
module arm_part(a, s = -1) difference() {
  if (a == "can") can_arm();
  else if (a == "ball") ball_arm();
  else if (a == "cube_low") cube_arm(s < 0 ? pad_ext : [pad_ext[1], pad_ext[0]], pad_y_low, true);
  else if (a == "cube_short") cube_arm([-pad_trim, -pad_trim]);
  else cube_arm();
  cross_holes(base_x[0], base_x[1]);
}

// Arms as printed. The right arm prints as the left mirrored in the plane
// of the bed, so its thin can-ring tip also ends up on the bed.
//   can:  z = 0 face down, flat
//   cube, cube_short: outer face (x = -9: base, beam and paddle back) down, texture up
//   cube_low: as cube; the right arm is the left's mirror image, not a copy
//   ball: standing on the cup's lower end, cup axis vertical; the in-layer
//         base starts 15 mm up and needs support under it
module print_arm(a, s)
  if (a == "cube_low") translate([0, 0, -base_x[0]]) rotate([0, -90, 0]) arm_part(a, s);
  else mirror([0, s > 0 ? 1 : 0, 0])
  if (a == "can") arm_part(a);
  else if (a == "cube" || a == "cube_short") translate([0, 0, -base_x[0]]) rotate([0, -90, 0]) arm_part(a);
  else translate([0, 0, -ez[0]]) arm_part(a);

// ---------- views ----------

module lego_pin() color("dimgray") {
  translate([0, 0, -7.9]) cylinder(d = 4.8, h = 15.8);
  translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
module pins(explode = 0) for (y = pin_y) translate([base_x[0] - explode, y, zc]) rotate([0, 90, 0]) lego_pin();

function arm_color(a) = a == "can" ? "tomato" : a == "ball" ? "mediumpurple" : "mediumseagreen";

module jaw(s, a, explode = 0) {
  color("orange") nub_body(s);
  handed(s) {
    color(arm_color(a)) translate([explode, 0, 0]) arm_part(a, s);
    pins(explode * 0.45);
  }
}

module pair(a, t) {
  translate([-cd / 2, 0, 0]) rotate(t) jaw(-1, a);
  translate([cd / 2, 0, 0]) rotate(-t) jaw(1, a);
}

if (part == "nub") nub_body(side);
else if (part == "arm") handed(side) arm_part(arm, side);
else if (part == "jaw") jaw(side, arm);
else if (part == "exploded") jaw(-1, arm, 16);
else if (part == "print") print_arm(arm, side);
else if (part == "nub_print") hand_label(side) nub_arm(side);   // grippers/arms, z = 0 on the bed
else if (part == "pair") {
  pair(arm, theta);
  if (arm == "ball") %translate([0, cup_yc, zc]) sphere(d = ball_d);
  else if (arm == "cube" || arm == "cube_low" || arm == "cube_short") %translate([0, (pad_y[0] + pad_y[1]) / 2, zc - 7]) cube(26, center = true);
  else %translate([0, ring_c.y, -40]) cylinder(d = 66, h = 115, $fn = 96);
}
