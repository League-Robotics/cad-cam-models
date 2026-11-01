// The caster post: a separate print that pins into the front face of the
// centred 9 g frame (servo_gripper.scad, `centred`) ahead of the jaws and
// carries the LEGO EV3 ball caster. Included by the grippers that stand on
// a caster ahead of the gripper (block_gripper.scad, cutebot_gripper.scad:
// since 2026-10-29 every stance has one, with its name etched in its top). 2026-10-28: the user wants the grippers in parts
// that print flat and pin together (2L friction pins, then glue), instead
// of one print with overhangs.
//
// Robot coordinates of the caller: X across (the jaws centred on x = 0), Y
// back (ahead is negative), Z up from the ground. The piece's back face is
// the frame's front face (y_face: the gear teeth's reach, so the post can
// stand in the arm layer), with two blind pin holes at the frame's
// front-face holes (x = pin_x, the floor's mid-height), and the caster's
// pins go into its front face: the two blind holes at x = +-8,
// caster_pin_down below the caster's beam top. The piece is a box from the
// floor's bed face (or the beam's bottom, whichever is lower) to the beam's
// top, with a pocket in its front for the caster's housing, which widens
// behind the beam face below the beam (housing_prof, from SquareD's model;
// the user measured its widest, 8.3, 2026-10-28). The post is as shallow as
// the mating holes allow: post_depth_for() keeps pin_wall between their
// bottoms and the pocket (2026-10-29: the caster moved back as far as that
// allows, so the closed can arms clear its beam; the rest of that clearance
// is a trim on the arms, swap_gripper.scad ring_trim: wherever the beam is
// in the arm layer the post is at least ring_post_depth deep for them,
// post_min_depth()). The piece reaches up to the floor's top where that is
// above the beam (the mating holes need the wall). The back face is flat
// across the whole piece, so it prints on that face with every hole
// vertical and nothing overhanging.
//
//     include <caster_post.scad>   (after lego.scad)
//     caster_post(y_face, [floor_z0, floor_z1], [-8, 8], caster_top_z, post_min_depth(arm_z, caster_top_z), "level");

use <models/ev3_ball_caster/files/BallBearingSmall_1905_offset_4.scad>

/* [EV3 ball caster, measured] */
caster_beam_t = 7.8;            // the one-unit beam on top
caster_pin_sp = 16;             // its two pins, 16 apart
caster_pin_down = 3.75;         // pin row below the beam's top
caster_h = 28;                  // beam top to the ball's bottom (measured; the model is 29.3)
housing_back = 8.3;             // the housing reaches this far behind the beam face below the beam (from 3.4 under it)
housing_back_hi = 5.3;          // ... and this far in the first 3.4 under the beam
housing_hi_h = 3.4;

/* [Post] */
post_w = 23;                    // between the closed paddles (inner faces at x = +-13)
mating_depth = 8;               // the mating pins' half, as the frame's front-face holes
caster_pin_depth = 8;           // the caster's pins (7.8) into the post's front
pin_wall = 0.8;                 // between a mating hole's bottom and the housing's pocket
housing_clr = 0.4;              // the pocket around the housing
ring_post_depth = 17;           // with the beam in the arm layer, the closed can arms' trimmed ring ends need the caster this far ahead
post_label_size = 4;            // the label etched in the top face ("Cutebot" just fits the width)
post_label_depth = 0.6;
caster_x = [-caster_pin_sp / 2, caster_pin_sp / 2];
// the housing's rear behind the beam face, by depth below the beam's bottom
// (SquareD's model, the max over its width, in 0.5 bands; 0.5 right under
// the beam covers the model's rounded junction)
housing_prof = [[0, 0.5], [0.7, 1.9], [1.7, 3.5], [2.7, 4.7], [3.7, 5.6], [4.7, 6.3], [5.7, 6.9], [6.7, 7.4], [7.7, 7.8],
                [8.7, 8.05], [10.2, 8.35], [40, 8.35]];
function housing_rear(dz) = dz <= 0 ? 0 : lookup(dz, housing_prof);
// The post's depth (the beam face ahead of the back face): the mating holes
// (mating_depth) end pin_wall short of the pocket at their lowest edge, and
// clear the caster's pin holes when the two share a height band.
function post_depth_for(floor_z, caster_top_z, min_depth = 0) = let(
    z_mid = (floor_z[0] + floor_z[1]) / 2,
    dz = caster_top_z - caster_beam_t - (z_mid - pd_pin_r),
    same_band = abs(caster_top_z - caster_pin_down - z_mid) < 2 * pd_pin_r + 1)
  max(mating_depth + pin_wall + housing_rear(dz) + housing_clr, same_band ? mating_depth + pin_wall + caster_pin_depth : 0, min_depth);
// the depth the can arms need: ring_post_depth when the beam is in the arm layer (arm_z: its bottom and top)
function post_min_depth(arm_z, caster_top_z) = caster_top_z > arm_z[0] && caster_top_z - caster_beam_t < arm_z[1] ? ring_post_depth : 0;

module cp_box(x, y, z) translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);

// The piece in place. y_face: the frame's front face; floor_z: the floor's
// bed face and top (the mating holes at its mid-height); pin_x: the mating
// holes' x; caster_top_z: the caster's beam top; min_depth: at least this
// deep (post_min_depth); label: etched in the top face, reading from behind.
module caster_post(y_face, floor_z, pin_x, caster_top_z, min_depth = 0, label = "") {
    depth = post_depth_for(floor_z, caster_top_z, min_depth);
    post_y0 = y_face - depth;
    beam_z0 = caster_top_z - caster_beam_t;
    z0 = min(floor_z[0], beam_z0);
    z1 = max(caster_top_z, floor_z[1]);
    z_mid = (floor_z[0] + floor_z[1]) / 2;
    ld = min(post_label_depth, z1 - z_mid - pd_cb_r - 0.2);   // the label stays out of the mating holes' counterbores
    zd = beam_z0 - z0 + 1;
    // the pocket's outline in (behind the beam face, over the beam's bottom)
    pocket = concat([[-1, -zd], [8.35 + housing_clr + 1, -zd]],
                    [for (i = [len(housing_prof) - 1 : -1 : 0]) [housing_prof[i][1] + housing_clr, -housing_prof[i][0]]],
                    [[-1, 0]]);
    difference() {
        cp_box([-post_w / 2, post_w / 2], [post_y0, y_face], [z0, z1]);
        translate([-post_w / 2 - 1, post_y0, beam_z0]) rotate([90, 0, 90]) linear_extrude(post_w + 2) polygon(pocket);
        for (x = pin_x) translate([x, y_face, z_mid]) rotate([90, 0, 0]) pd_blind_pin_hole(mating_depth, ext = 2);
        for (x = caster_x) translate([x, post_y0, caster_top_z - caster_pin_down]) rotate([-90, 0, 0]) pd_blind_pin_hole(caster_pin_depth, ext = 2);
        if (label != "") translate([0, (post_y0 + y_face) / 2, z1 - ld]) linear_extrude(ld + 1) rotate(180)
            text(label, size = post_label_size, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}

// The piece on the bed: its back (mating) face down, every hole vertical.
module caster_post_print(y_face, floor_z, pin_x, caster_top_z, min_depth = 0, label = "")
    translate([0, 0, y_face]) rotate([-90, 0, 0]) caster_post(y_face, floor_z, pin_x, caster_top_z, min_depth, label);

// The EV3 caster (SquareD's model, as front_plate.scad): beam face at y = 0,
// pins pointing -y, top at z = 0, centred on x; the ball drawn at the
// measured height (caster_h).
module caster() {
    top = 24.775;
    translate([0, caster_beam_t / 2, -top]) {
        color("#4a4f55") drawBallBearing();
        color("silver") translate([0, 0, 5 + 29.3 - caster_h]) sphere(d = 19.05, $fn = 48);
    }
    color("#2a2a2a") for (p = [-1, 1]) translate([p * caster_pin_sp / 2, 0, -caster_pin_down]) rotate([90, 0, 0]) {
        cylinder(d = 4.8, h = 7.8);
        translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
    }
}
// The caster on the post: its beam face on the post's front, pins into it.
module caster_on_post(y_face, floor_z, caster_top_z, min_depth = 0)
    translate([0, y_face - post_depth_for(floor_z, caster_top_z, min_depth), caster_top_z]) rotate([0, 0, 180]) caster();

// A 2L friction pin (16 long) centred on a mating face at the origin, along y.
module pin_2l() color("dimgray") rotate([90, 0, 0]) {
    translate([0, 0, -8]) cylinder(d = 4.8, h = 16);
    translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
// The post's mating pins, in place.
module caster_post_pins(y_face, floor_z, pin_x) for (x = pin_x) translate([x, y_face, (floor_z[0] + floor_z[1]) / 2]) pin_2l();
