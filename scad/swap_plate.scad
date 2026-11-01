// One print plate of the gripper parts (../grippers/*/*.stl), packed
// close together and tied to each other on the first layer by thin sprues so
// no single part can peel off the bed on its own. Snap or clip the sprues off
// after printing.
//
// The two can rings face each other as one ring with a nub inside it; the
// other parts pack around them. The ball arms stand on their cups and need
// supports under their bases; the space under those bases is kept clear.
//
// part = "plate" (parts + sprues), "parts", "sprues" (sprues only), "check"
// (any overlap of the parts' keep-out zones; empty = every gap >= gap) or
// "check_sprues" (sprues running into a part they don't join; expect only
// the bites at their ends).

part = "plate";
gap = 3;              // minimum gap between parts (full plan outline)
sprue_h = 0.3;        // first layer
sprue_w = 2;          // in the middle of a bar
sprue_neck = 1;       // where a bar meets a part
sprue_bite = 0.6;     // how far a bar runs into the part it joins

d = "../grippers/";

// Parts are placed by the centre of their plan bounding box (rotated about
// it); the can rings keep their own coordinates so they close into one ring.
// [file, plan bbox [[x0, x1], [y0, y1]] as exported, centre on the plate, rotation]
nub_bb = [[-17, 13], [-13, 38]];
P = [
  ["extensions/can_arm_left",     [[-25.5, 9], [12.5, 113]],    [-8.25, 62.75],  0],
  ["extensions/can_arm_right",    [[-25.5, 9], [-113, -12.5]],  [32.25, 62.75], 180],
  ["servo_9g/spline_arm",     [[-17, 13], [-38, 13]],         [12, 76],      180],   // inside the ring
  ["extensions/cube_arm_left",    [[-22.8, 15.2], [12.5, 72]],  [71.5, 42.25],   0],
  ["extensions/cube_arm_right",   [[-22.8, 15.2], [-72, -12.5]], [71.5, 104.75], 0],
  ["extensions/ball_arm_left",    [[-12.5, 0.5], [12.5, 78.3]], [100, 45.4],     0],
  ["extensions/ball_arm_right",   [[-12.5, 0.5], [-78.3, -12.5]], [116, 45.4],   0],
  ["arms/left_arm",   nub_bb,                       [119, 97.5],    90],
  ["arms/right_arm",        [[-12.9, 17], [-12.9, 38]],   [131.85, 45.35], 0],   // gear in the ball cup
];

function ctr(b) = [(b[0][0] + b[0][1]) / 2, (b[1][0] + b[1][1]) / 2];
module part_i(i) translate(P[i][2]) rotate(P[i][3]) translate(-ctr(P[i][1]))
  import(str(d, P[i][0], ".stl"));
// plan outline of the whole part (the keep-out zone, incl. space for supports)
module plan(i) projection() part_i(i);
// what actually touches the bed
module bed(i) projection(cut = true) translate([0, 0, -0.1]) part_i(i);

// Sprue bars from tools/plate_sprues.py (rerun it after moving parts): each
// joins the closest points of two neighbouring parts, necked down where it
// meets a part so it snaps off clean.
include <swap_plate_sprues.scad>

module sprue2d(p, q) {
  u = (q - p) / norm(q - p);
  a = p - u * sprue_bite;
  b = q + u * sprue_bite;
  m = (p + q) / 2;
  hull() { translate(a) circle(d = sprue_neck, $fn = 12); translate(m) circle(d = sprue_w, $fn = 16); }
  hull() { translate(m) circle(d = sprue_w, $fn = 16); translate(b) circle(d = sprue_neck, $fn = 12); }
}
// Bars added by hand: a strap across the feet of the can arms' legs.
EXTRA_SPRUES = [[[-1.2, 14], [25.2, 14]]];
module sprues2d() for (s = concat(SPRUES, EXTRA_SPRUES)) sprue2d(s[0], s[1]);

n = len(P);

if (part == "check")
  for (i = [0:n - 2], j = [i + 1:n - 1]) intersection() {
    offset(delta = gap / 2 - 0.01) plan(i);
    offset(delta = gap / 2 - 0.01) plan(j);
  }
else if (part == "check_sprues")
  for (i = [0:n - 1]) intersection() { sprues2d(); offset(delta = -sprue_bite - sprue_neck / 2 - 0.1) bed(i); }
else if (part == "parts") for (i = [0:n - 1]) color(i % 2 ? "steelblue" : "tomato") part_i(i);
else if (part == "sprues") linear_extrude(sprue_h) sprues2d();
else {
  for (i = [0:n - 1]) part_i(i);
  color("gold") linear_extrude(sprue_h) sprues2d();
}
