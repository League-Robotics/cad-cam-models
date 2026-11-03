// A friction tilt table for small cameras (Raspberry Pi / Arduino camera
// boards): two 5 x 5 LEGO plates joined by a hinge of triangles, set to any
// angle by hand and held there by friction (2026-11-01).
//
// One print, made twice. Each plate stands triangles up on its two hinge
// edges (x = +-), its top rounded about the hinge axis:
//   fork (+x)    two tines with a slot between, a divot in each tine's inner face
//   tongue (-x)  one triangle where the slot would be, a bump on each face
// Turned over (180 deg about y through the axis), a second copy's tongue
// lands in the first's fork and the first's tongue in its fork. Each fork
// clamps a tongue: the tines spring apart over the bumps, which snap into the
// divots and are the pivot; the tongue is 2 * squeeze thicker than the slot,
// so the tines stay sprung against its faces, and that preload is the
// friction that holds the angle. (A first draft had one ear inside and one
// outside on each plate: the copy then sat to one side of the other on both
// edges, nothing clamped, and it slid apart sideways.)
//
// Clicks (2026-11-01, after the first print): radial teeth round the axis on
// the faces that meet, raised on the tongue's faces and the same teeth sunk
// into the tines' faces, `clicks` round, 360 / clicks apart (flat is one). At
// a click every ridge sits in a groove and the fit is the plain squeeze;
// between clicks the ridges ride up out of the grooves and spread the tines
// another click_h, so the table snaps to the next click. The teeth stay
// inside the apex circle, which the tongue and tines always share, so all of
// them are engaged at every angle. clicks = 0 is the smooth table.
//
// The triangles' outline (2026-11-01, the user's fit and finish): the room
// the other plate leaves as it tilts, less roll_gap. Its underside is always
// axis_z - plate_t from the axis, so it rolls round an arc of that radius over
// the top, and at the limits (+-tilt_max, where the plates' edges meet) it
// lies along the triangle's straight sides: tilted all the way, the other
// plate sits parallel to the triangle's edge. (The first print had a small
// r 6 apex and the sides from the plate's corners.)
//
// Assembly: put one plate on the other, each tongue over a fork, and push
// (chamfered tine and tongue edges lead in). Tilt by hand.
//
// The faces that face the bed (each plate's outer face: the bottom plate's
// underside, the top plate's camera face) are the mounting faces; their pin
// holes have Part Designer's taper. The holes in the two columns under the
// triangles are blind from the outer face, 8 deep (half a 2L pin); the middle
// three columns go through.
//
// Datum: the plate's bed face at z = 0, centred in x and y; the hinge axis is
// along x through y = 0, z = axis_z. The plates are on the 8 mm grid when
// flat: `pitch` units apart, so the pair is a 5 x 5 x (pitch + 1) block.

include <lego.scad>

/* [Show] */
// "plate" (the print, as on the bed), "print" (two on the bed), "assembly"
// (both at theta), "clash" (the two plates at theta, squeeze off; empty or
// zero volume = clear), or one component in place for the viewer: "bottom", "top"
part = "assembly";
theta = 30;                    // tilt of the top plate about the hinge axis
$fn = 64;

/* [Plate] */
unit = pd_unit;
cells = 5;
half = cells * unit / 2 - pd_edge;                       // 19.8
plate_t = pd_cell;                                       // 7.6
hole_xy = [for (i = [0 : cells - 1]) -(cells - 1) * unit / 2 + unit * i];   // -16 ... 16
blind = unit;                  // half a 2L pin: 0.4 into the triangles' roots

/* [Hinge] */
pitch = 4;                     // units, plate to plate when flat: tilt range about +-63
axis_z = (pitch * unit) / 2 + unit / 2 - pd_edge;       // 19.8: midway between the plates
tine_t = 2.5;                  // each of the fork's two tines
slot = 3.5;                    // between the tines
slot_x = [half - tine_t - slot, half - tine_t];          // 13.8 .. 17.3
clicks = 24;                   // teeth round the axis: a click every 15 deg; 0 = smooth (the first print)
click_h = 0.2;                 // tooth height: the extra spread between clicks
squeeze = 0.1;                 // per face: how far the tongue is over the slot (the friction)
edge_c = 0.6;                  // chamfer on the faces that meet, a lead-in when snapping together
bump_r = 2.5;                  // the bump's radius at the face
bump_h = 0.4;                  // how far it stands out; a 45 deg cone (prints on its side)
divot_clear = 0.1;             // the divot is this much bigger all round and deeper
click_r = [bump_r + divot_clear + 0.4, 7];   // the teeth: from outside the divot's rim (as the click print)
click_taper = 0.4;             // each tooth's ends ramp down over this, so they slide in on assembly

gap = 2 * (axis_z - plate_t);
tilt_max = 180 - 2 * atan(half / (axis_z - plate_t));
roll_gap = 0.4;                // the triangles' outline to the other plate's underside
apex_r = axis_z - plate_t - roll_gap;    // 11.8: the arc the other plate rolls round
// where the straight sides meet the plate: the other plate at tilt_max, moved roll_gap toward the axis
ear_half = (apex_r + (axis_z - plate_t) * cos(tilt_max)) / sin(tilt_max);
echo(gap = gap, axis_z = axis_z, tilt_max = tilt_max, height = 2 * axis_z, fork = [slot_x[0] - tine_t, half],
     apex_r = apex_r, ear_half = ear_half);
assert(ear_half < half, "the sides land on the plate");
assert(click_r[1] + edge_c + 0.4 < apex_r, "teeth inside the apex");
assert(bump_h + divot_clear < tine_t - 1, "divot leaves a wall");
assert(slot_x[0] - tine_t > hole_xy[3] + pd_cb_r, "inner tine clear of the next column's counterbores");
assert(clicks % 2 == 0, "even, so a plate and its turned-over copy click at theta 0");
assert(clicks == 0 || click_r[1] - click_r[0] > 2 * click_taper + 1, "room for the teeth");
assert(clicks == 0 || click_h + divot_clear < tine_t - 1.5, "grooves leave a wall");
echo(click_deg = clicks > 0 ? 360 / clicks : 0, tooth_base = clicks > 0 ? [for (r = click_r) 2 * r * sin(180 / clicks)] : 0);

// ---- the print ------------------------------------------------------------
// A triangle's outline in the (y, z) plane: +-ear_half at the plate's top
// face (carried 1 down into the plate), up to the arc round the axis; the
// sides are the other plate at +-tilt_max.
module ear_profile() hull() {
    translate([-ear_half, plate_t - 1]) square([2 * ear_half, 1]);
    translate([0, axis_z]) circle(r = apex_r);
}

// A triangle from x = x0 to x1, its x0 / x1 face chamfered by edge_c where c0 /
// c1 (the outline is convex, so the hull is exact).
module ear(x0, x1, c0 = false, c1 = false) translate([x0, 0, 0]) rotate([90, 0, 90]) hull() {
    translate([0, 0, c0 ? edge_c : 0]) linear_extrude(x1 - x0 - (c0 ? edge_c : 0) - (c1 ? edge_c : 0)) ear_profile();
    linear_extrude(x1 - x0) offset(delta = -edge_c) ear_profile();
}

// A 45 deg cone r at the face (x = 0) on the axis, h out along s * x.
module cone_x(s, r, h) translate([0, 0, axis_z]) rotate([0, s * 90, 0]) cylinder(r1 = r, r2 = r - h, h = h);

// The click teeth on a face at x = 0, standing out along s * x: `clicks`
// ridges round the axis, one at each multiple of 360 / clicks (measured in
// the (y, z) plane, so a plate and its turned-over copy agree at theta 0).
// Each is a wedge the full pitch wide (the ridges meet at their feet), click_h
// high along its crest, ramped down at both ends; base e behind the face.
module click_teeth(s, e = 0.01) if (clicks > 0) translate([0, 0, axis_z]) rotate([0, s * 90, 0])
    for (k = [0 : clicks - 1]) let(p = 360 / clicks, a = k * p) hull() polyhedron(
        points = [for (r = click_r, da = [-p / 2, p / 2]) [r * cos(a + da), r * sin(a + da), -e],
                  for (r = [click_r[0] + click_taper, click_r[1] - click_taper]) [r * cos(a), r * sin(a), click_h]],
        faces = [[0, 1, 2], [3, 4, 5]]);

module plate(sq = squeeze) difference() {
    union() {
        translate([-half, -half, 0]) cube([2 * half, 2 * half, plate_t]);
        ear(slot_x[0] - tine_t, slot_x[0], c1 = true);                // fork: inner tine
        ear(slot_x[1], half, c0 = true);                              //       outer tine
        ear(-slot_x[1] - sq, -slot_x[0] + sq, true, true);            // tongue
        for (s = [-1, 1]) translate([s < 0 ? -slot_x[1] - sq + 0.01 : -slot_x[0] + sq - 0.01, 0, 0]) {
            cone_x(s, bump_r, bump_h + 0.01);
            click_teeth(s);
        }
    }
    for (s = [-1, 1]) translate([s < 0 ? slot_x[1] - 0.01 : slot_x[0] + 0.01, 0, 0]) {
        cone_x(-s, bump_r + divot_clear, bump_h + divot_clear + 0.01);
        translate([s < 0 ? 0.01 : -0.01, 0, 0]) click_teeth(-s, 0.02);
    }
    for (x = hole_xy, y = hole_xy) translate([x, y, 0])
        if (abs(x) > half - unit) pd_blind_pin_hole(blind); else pd_pin_hole(plate_t);
}

// ---- in place ---------------------------------------------------------------
// The top plate: the print turned over about y through the axis, then tilted.
module top_place(t = theta) translate([0, 0, axis_z]) rotate([t, 0, 0]) rotate([0, 180, 0])
    translate([0, 0, -axis_z]) children();

if (part == "plate" || part == "bottom") plate();
else if (part == "print") for (y = [-1, 1]) translate([0, y * (half + 4), 0]) plate();
else if (part == "top") top_place() plate();
else if (part == "assembly") { color("#3cb371") plate(); color("#e8c22a") top_place() plate(); }
else if (part == "clash") intersection() { plate(0); top_place() plate(0); }
