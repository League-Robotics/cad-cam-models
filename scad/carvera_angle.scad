// The aluminium angle on the Carvera (2026-11-03): 1 x 1 in angle, 1/8 in
// wall, three 6-32 clearance holes, two in one leg and one in the other. The
// screws go into threaded inserts in the part it sits on; each insert stands
// 1.1 proud as a 7.5 boss, so the inside faces get a round pocket at each hole.
// The printed camera bracket (part = "bracket") is this angle cut to 56 with a
// 1 x 1 in cap on its lower end; see below.
//
// Measured by the user (calipers, 2026-11-03). Along the length, from the end
// nearest the holes to the near side of each hole: 14 and 45.2 on the
// two-hole leg, 28 on the one-hole leg. Across, from the outside corner to the
// near side of each hole: 14 (first hole), 10.6 (the one-hole leg's hole),
// 14.28 (the far hole). Centres are those plus half a hole.
// Not measured: the length (127 = 5 in, a guess from the photos). Our pick:
// the pocket depth clearance; the user set the pockets to 9 across.
//
// Datum: the outside corner runs along +x, from x = 0 at the measured end.
// The two-hole leg lies flat (z = 0 to t, y = 0 to leg); the one-hole leg
// stands up (y = 0 to t, z = 0 to leg). The inside of the angle is y, z > t.

/* [Show] */
// "angle" (the aluminium), "bracket" (as mounted) or "print" (bracket on the bed)
part = "angle";
$fn = 64;

/* [Angle, measured] */
leg = 25.4;            // 1 in legs, outside
t = 3.28;              // wall (1/8 in nominal)
hole_d = 3.5;          // 6-32 clearance

// measured to the near side of each hole
a1_along = 14;    a1_across = 14;      // two-hole leg, near the end
a2_along = 45.2;  a2_across = 14.28;   // two-hole leg, far
b1_along = 28;    b1_across = 10.6;    // one-hole leg

/* [Angle, guessed] */
len = 127;             // not measured yet

/* [Camera bracket] */
bracket_l = 56;        // the user's: the angle part, top end to the cap
cap_t = 6;             // the user's: 1 x 1 in square cap on the lower end
camera_hole_d = 6.8;   // 1/4-20 clearance, our pick (6.35 screw, prints shrink)

/* [Insert bosses] */
boss_d = 7.5;          // measured
boss_h = 1.1;          // measured, proud of the mating face
pocket_clear_d = 1.5;  // on the diameter: 9 pockets (8 printed tight, 2026-11-03)
pocket_clear_h = 0.3;  // our pick
pocket_d = boss_d + pocket_clear_d;
pocket_h = boss_h + pocket_clear_h;

eps = 0.01;
r = hole_d / 2;

// hole centres: [along, across from the outside corner]
a_holes = [[a1_along + r, a1_across + r], [a2_along + r, a2_across + r]];
b_holes = [[b1_along + r, b1_across + r]];

echo(a_holes = a_holes, b_holes = b_holes, pocket_d = pocket_d, pocket_h = pocket_h);
for (h = concat(a_holes, b_holes))
    assert(h[1] - pocket_d / 2 > t, "pocket runs into the other leg");
for (h = concat(a_holes, b_holes))
    assert(h[1] + pocket_d / 2 < leg, "pocket runs off the leg's edge");

module angle(l = len) {
    difference() {
        union() {
            cube([l, leg, t]);
            cube([l, t, leg]);
        }
        // two-hole leg: holes down z, pockets in its inside (top) face
        for (h = a_holes) translate([h[0], h[1], 0]) {
            translate([0, 0, -eps]) cylinder(d = hole_d, h = t + 2 * eps);
            translate([0, 0, t - pocket_h]) cylinder(d = pocket_d, h = pocket_h + eps);
        }
        // one-hole leg: holes along y, pockets in its inside face (y = t)
        for (h = b_holes) translate([h[0], 0, h[1]]) rotate([-90, 0, 0]) {
            translate([0, 0, -eps]) cylinder(d = hole_d, h = t + 2 * eps);
            translate([0, 0, t - pocket_h]) cylinder(d = pocket_d, h = pocket_h + eps);
        }
    }
}

// The bracket as mounted on the machine (the user's view, 2026-11-03): holes
// at the top, the one-hole leg facing you (y = 0 to t), the two-hole leg on
// your left (x = 0 to t), the outside corner at front left on the z axis.
// It hangs down: z = 0 is the cap's underside, the top end at bracket_h. The
// camera screw goes down through the cap's centre from inside the L.
bracket_h = bracket_l + cap_t;

module bracket() {
    // the angle's frame turned upright: its leg-across z -> x, y -> y, along -> down from the top
    multmatrix([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, bracket_h], [0, 0, 0, 1]])
        angle(bracket_l);
    difference() {
        cube([leg, leg, cap_t + eps]);
        translate([leg / 2, leg / 2, -eps]) cylinder(d = camera_hole_d, h = cap_t + 3 * eps);
    }
}

// on the bed: the two-hole leg's outside face down, so its pockets open
// upwards and the layers run along the bracket
module bracket_print() {
    rotate([0, -90, 0]) bracket();
}

if (part == "angle") angle();
if (part == "bracket") bracket();
if (part == "print") bracket_print();
