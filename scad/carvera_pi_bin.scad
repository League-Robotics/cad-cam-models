// A plate for the Makera Carvera's dust-bin bay (2026-11-02): it replaces the
// clear dust bin with a flat plate on the bin's side rails, so it slides into
// the bay and locks the way the bin does. A Raspberry Pi case gets bolted
// upside down under it (holes drilled to suit the case; the case comes later).
//
// The rails are 2 out from each side, their tops flush with the plate's top,
// 1.25 thick for most of their length. At the front (handle) end they
// thicken downward to 5.2 through a short S-curve: pushed home, that lifts
// the bin up against the machine's filter duct. Their back ends narrow so
// they lead into the bay's slots.
//
// Measured by the user (calipers, 2026-11-02): 80.5 across the rails, 168
// front to back without the handle, rails 2 out, 1.25 thick, 5.2 at the
// front. Guessed (the user: "not critical"): the S-curve's place and its
// 7 mm length, the 10 mm back taper.
//
// Datum: the plate's top face at z = 0 (the plate below it), centred in x;
// y = 0 at the front edge, the back edge at y = len.

/* [Show] */
// "plate" (as it sits in the machine) or "print" (top face down on the bed)
part = "plate";
$fn = 48;

/* [Bin, measured] */
rail_w_total = 80.5;   // across the rails
len = 168;             // front to back, without the handle
rail_out = 2;          // rail past each side
rail_t = 1.25;         // rail thickness, most of its length
rail_t_front = 5.2;    // at the front end

/* [Bin, guessed] */
rail_thick_l = 15;     // full 5.2 thickness from the front for this long
rail_curve_l = 7;      // S-curve from 5.2 down to 1.25 over this length
rail_taper_l = 10;     // back end: the rail narrows over this length ...
rail_taper_to = 0.6;   // ... to this far out

/* [Plate] */
plate_t = 3;           // under the rails: the rails' tops are flush with the plate's
corner_r = 1;          // plate corners, in plan

body_w = rail_w_total - 2 * rail_out;   // 76.5
eps = 0.01;

echo(body_w = body_w, rail_drop_below_plate_at_front = rail_t_front - plate_t);
assert(rail_t <= plate_t, "the rail must fit within the plate's thickness where it is thin");

// Rail thickness along y: 5.2 at the front, an S (cosine) down to 1.25.
function rail_th(y) =
    y <= rail_thick_l ? rail_t_front
  : y >= rail_thick_l + rail_curve_l ? rail_t
  : rail_t + (rail_t_front - rail_t) * (1 + cos(180 * (y - rail_thick_l) / rail_curve_l)) / 2;

// How far the rail sticks out along y: full, then narrowing at the back end.
function rail_reach(y) =
    y <= len - rail_taper_l ? rail_out
  : rail_out - (rail_out - rail_taper_to) * (y - (len - rail_taper_l)) / rail_taper_l;

module rail(side) {   // side = +1 / -1
    n = 120;
    ys = [for (i = [0:n]) len * i / n];
    // side profile (y, z) extruded across the rail, cut to the plan taper;
    // it starts 1 inside the plate's side so the two fuse
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
else if (part == "print") rotate([180, 0, 0]) plate();   // top face on the bed: rails print flat, the thick ends build up
