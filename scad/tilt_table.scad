// A friction tilt table for small cameras (Raspberry Pi / Arduino camera
// boards): two 5 x 5 LEGO plates joined by a hinge of triangles, set to any
// angle by hand and held there by friction (2026-11-01).
//
// One print, made twice. Each plate stands triangles up on its two hinge
// edges (x = +-), its top rounded about the hinge axis:
//   fork (+x)    two tines with a slot between, a hole through each tine on the axis
//   tongue (-x)  one triangle where the slot would be, a button on each face
// Turned over (180 deg about y through the axis), a second copy's tongue
// lands in the first's fork and the first's tongue in its fork. Each fork
// clamps a tongue: the tines spring apart over the buttons, which snap into
// the holes and are the pivot; the click teeth (below) hold the angle.
// (Second print, 2026-11-03: shallow 0.4 bumps in 0.5 divots and a tongue
// 0.2 over the slot did not lock: the tines bowed out over the extra
// material and the bumps never seated, so it popped apart. Now the buttons
// stand 1.2 proud into through holes (you can see them seat), the tongue is
// the slot's width (squeeze 0), and the teeth are deeper and sharper.)
// (A first draft had one ear inside and one
// outside on each plate: the copy then sat to one side of the other on both
// edges, nothing clamped, and it slid apart sideways.)
//
// Clicks (2026-11-01, after the first print): radial teeth round the axis on
// the faces that meet, raised on the tongue's faces and the same teeth sunk
// into the tines' faces, `clicks` round, 360 / clicks apart (flat is one). At
// a click every ridge sits in a groove; between clicks the ridges ride up
// out of the grooves and spread the tines, so the table snaps to the next
// click. The flanks are click_flank off the face at every radius (Hirth-like:
// the teeth grow with the radius, 0.2 high inside to 0.4 outside; the second
// print's 0.2 teeth came out as a texture, the third's 35 deg teeth, 0.4 to
// 0.8, snapped well but locked: it could barely be turned, and not back from
// the limit without pliers, so v4 halves them), and the grooves are click_clear
// deeper than the ridges so printed crests bottom out nowhere. The buttons
// stand taller than the teeth, so they stay in the holes while clicking. The teeth stay
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
click_flank = atan(tan(35) / 2);   // 19.3: the teeth's flanks off the face, deg (constant: the teeth grow with r);
                               // half the height of v3's 35 deg teeth, which locked too hard (2026-11-03)
click_r = [4.5, 9];            // the teeth, inner and outer radius (wide enough at 4.5 to print sharp)
click_clear = 0.1;             // the grooves this much deeper than the ridges
squeeze = 0;                   // per face: how far the tongue is over the slot (0.1 bowed the tines out)
edge_c = 0.6;                  // chamfer on the faces that meet, a lead-in when snapping together
bump_r = 2.6;                  // the button's radius at the face
bump_h = 1.2;                  // how far it stands out
bump_flank = 50;               // its side off the face, deg (steeper holds better; 50 still prints on its side)
hole_clear = 0.15;             // the tine's hole over the button's base, per side
hole_r = bump_r + hole_clear;
// a tooth's height at radius r: half its base (the chord of half a pitch) times tan(flank)
function click_h(r) = clicks > 0 ? r * sin(180 / clicks) * tan(click_flank) : 0;

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
assert(bump_h < tine_t - 0.5, "button inside the tine's hole");
assert(click_r[0] - click_h(click_r[0]) > hole_r + 0.8, "teeth clear of the hole");
assert(clicks == 0 || bump_h > click_h(click_r[1]) + 0.3, "buttons stay in the holes while clicking");
assert(slot_x[0] - tine_t > hole_xy[3] + pd_cb_r, "inner tine clear of the next column's counterbores");
assert(clicks % 2 == 0, "even, so a plate and its turned-over copy click at theta 0");
assert(clicks == 0 || click_h(click_r[1]) + click_clear < tine_t - 1, "grooves leave a wall");
echo(click_deg = clicks > 0 ? 360 / clicks : 0, tooth_base = clicks > 0 ? [for (r = click_r) 2 * r * sin(180 / clicks)] : 0,
     tooth_h = [for (r = click_r) click_h(r)], button = [bump_r, bump_h, bump_flank], hole_r = hole_r);

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

// A cone r at the face (x = 0) on the axis, h out along s * x, its side `flank` off the face.
module cone_x(s, r, h, flank = 45) translate([0, 0, axis_z]) rotate([0, s * 90, 0])
    cylinder(r1 = r, r2 = r - h / tan(flank), h = h);

// The click teeth on a face at x = 0, standing out along s * x: `clicks`
// ridges round the axis, one at each multiple of 360 / clicks (measured in
// the (y, z) plane, so a plate and its turned-over copy agree at theta 0).
// Each is a wedge the full pitch wide (the ridges meet at their feet),
// click_h(r) + extra high along its crest, the crest ramped down at 45 deg at
// both ends; base e behind the face.
module click_teeth(s, e = 0.01, extra = 0) if (clicks > 0) translate([0, 0, axis_z]) rotate([0, s * 90, 0])
    for (k = [0 : clicks - 1]) let(p = 360 / clicks, a = k * p,
                                   rc = [click_r[0] + click_h(click_r[0]), click_r[1] - click_h(click_r[1])]) hull() polyhedron(
        points = [for (r = click_r, da = [-p / 2, p / 2]) [r * cos(a + da), r * sin(a + da), -e],
                  for (r = rc) [r * cos(a), r * sin(a), click_h(r) + extra]],
        faces = [[0, 1, 2], [3, 4, 5]]);

module plate(sq = squeeze) difference() {
    union() {
        translate([-half, -half, 0]) cube([2 * half, 2 * half, plate_t]);
        ear(slot_x[0] - tine_t, slot_x[0], c1 = true);                // fork: inner tine
        ear(slot_x[1], half, c0 = true);                              //       outer tine
        ear(-slot_x[1] - sq, -slot_x[0] + sq, true, true);            // tongue
        for (s = [-1, 1]) translate([s < 0 ? -slot_x[1] - sq + 0.01 : -slot_x[0] + sq - 0.01, 0, 0]) {
            cone_x(s, bump_r, bump_h + 0.01, bump_flank);
            click_teeth(s);
        }
    }
    // the holes, through both tines on the axis
    translate([slot_x[0] - tine_t - 1, 0, axis_z]) rotate([0, 90, 0]) cylinder(r = hole_r, h = half - slot_x[0] + tine_t + 2);
    // the grooves: the teeth sunk into each tine's inner face, click_clear deeper
    for (s = [-1, 1]) translate([s < 0 ? slot_x[1] : slot_x[0], 0, 0]) click_teeth(-s, 0.02, click_clear);
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
