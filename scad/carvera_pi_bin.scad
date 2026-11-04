// A plate for the Makera Carvera's dust-bin bay (2026-11-02): it replaces the
// clear dust bin with a flat plate on the bin's side ridges, so it slides into
// the bay and locks the way the bin does. A Raspberry Pi case gets bolted
// upside down under it (holes drilled to suit the case; the case comes later).
//
// Rev 2 (after the first print): one 3 thick slab, 80.5 across, its outer 2
// on each side being the ridges. At the front (handle) end the ridges hang
// down to 5.7 through a short S-curve: pushed home, that lifts the bin up
// against the machine's filter duct. At the back (the end that goes in
// first) the ridges stop 8.6 short of the edge, with a short lead-in.
//
// Measured by the user (calipers, 2026-11-02): 80.5 across the ridges, 168
// front to back without the handle, ridges 2 out, ridges start 8.6 in from
// the back. On the bin the ridge is 1.5 thick with its top 2.9 below the
// bin's top; he chose a plain 3 slab here instead. 5.7 at the front: his
// pick (the bin measured 5.2). Guessed: the 15 thick length, the 7 S-curve,
// the 2 lead-in.
//
// Datum: the plate's top face at z = 0 (the plate below it), centred in x;
// y = 0 at the front (handle) edge, the back edge at y = len.

/* [Show] */
// "plate" (as it sits in the machine) or "print" (top face down on the bed)
part = "plate";
$fn = 48;

/* [Bin, measured] */
rail_w_total = 80.5;   // across the ridges
len = 168;             // front to back, without the handle
rail_out = 2;          // ridge past each side of the body
rail_setback = 8.6;    // ridges stop this far short of the back edge
rail_t_front = 5.7;    // ridge depth at the front end (the user's pick)

/* [Bin, guessed] */
rail_thick_l = 15;     // full front depth from the front edge for this long
rail_curve_l = 7;      // S-curve from rail_t_front up to plate_t over this length
rail_lead_l = 2;       // the ridge grows from nothing to rail_out over this length

/* [Plate] */
plate_t = 3;           // the whole slab, ridges included
corner_r = 1;          // plate corners, in plan

body_w = rail_w_total - 2 * rail_out;   // 76.5
rail_end = len - rail_setback;          // the ridges' back end, in y
eps = 0.01;

echo(body_w = body_w, rail_end = rail_end, rail_drop_below_plate_at_front = rail_t_front - plate_t);
assert(rail_t_front >= plate_t, "the front of the ridge must be at least the plate's depth");

// Ridge depth along y: rail_t_front at the front, an S (cosine) up to the plate.
function rail_th(y) =
    y <= rail_thick_l ? rail_t_front
  : y >= rail_thick_l + rail_curve_l ? plate_t
  : plate_t + (rail_t_front - plate_t) * (1 + cos(180 * (y - rail_thick_l) / rail_curve_l)) / 2;

// How far the ridge sticks out along y: full, then a short lead-in to nothing
// at its back end.
function rail_reach(y) =
    y <= rail_end - rail_lead_l ? rail_out
  : rail_out * (rail_end - y) / rail_lead_l;

module rail(side) {   // side = +1 / -1
    n = 120;
    ys = [for (i = [0:n]) rail_end * i / n];
    // side profile (y, z) extruded across the ridge, cut to its plan shape;
    // it starts 1 inside the body's side so the two fuse
    intersection() {
        translate([side > 0 ? body_w / 2 - 1 : -body_w / 2 - rail_out - eps, 0, 0])
            rotate([90, 0, 90]) linear_extrude(rail_out + 1 + eps)
                polygon(concat([for (y = ys) [y, 0]], [for (i = [n:-1:0]) [ys[i], -rail_th(ys[i])]]));
        linear_extrude(height = 2 * rail_t_front + 2, center = true)
            polygon(concat([for (y = ys) [side * (body_w / 2 - 1), y]],
                           [for (i = [n:-1:0]) [side * (body_w / 2 + rail_reach(ys[i])), ys[i]]]));
    }
}

module plate() {
    translate([0, 0, -plate_t]) linear_extrude(plate_t)
        hull() for (sx = [-1, 1], yy = [corner_r, len - corner_r])
            translate([sx * (body_w / 2 - corner_r), yy]) circle(r = corner_r);
    rail(1); rail(-1);
}

if (part == "plate") plate();
else if (part == "print") rotate([180, 0, 0]) plate();   // top face on the bed: the deep front ends build up
