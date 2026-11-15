// Caster drop plate (draft 2026-11-14): a 3 x 3 LEGO plate standing up, with
// its middle row squeezed from a full unit to mid_h (3.5): a full unit row of
// three pin holes, a 3.5 web, another full unit row. The two rows are
// 8 + 3.5 = 11.5 apart instead of 16: for the caster at the front of the
// robot on 86 mm wheels (the user's numbers).
//
// Datum: X across (0 .. 24), Y through the plate (the holes' axis, 0 .. 8),
// Z up from the bottom row's cell edge. Prints flat on a hole face.
include <lego.scad>

/* [Show] */
part = "plate";           // "plate", "print", "print_x4"
$fn = 32;

/* [Plate] */
unit = pd_unit;           // 8
cols = 3;                 // holes across
mid_h = 3.5;              // the squeezed middle row (a full plate has 8)
thick_units = 1;          // through the holes

w = cols * unit;                  // 24
h = 2 * unit + mid_h;             // 19.5
t = thick_units * unit;           // 8
row_z = [unit / 2, unit + mid_h + unit / 2];   // 4, 15.5
row_pitch = row_z[1] - row_z[0];  // 11.5
web = row_pitch - 2 * pd_cb_r;    // between the two rows' counterbores

echo(size = [w - 2 * pd_edge, t - 2 * pd_edge, h - 2 * pd_edge], row_z = row_z, row_pitch = row_pitch, web = web);
assert(web > 1, "the rows' counterbores need a wall between them");

module plate() difference() {
    translate([pd_edge, pd_edge, pd_edge]) cube([w - 2 * pd_edge, t - 2 * pd_edge, h - 2 * pd_edge]);
    for (z = row_z, i = [0 : cols - 1])
        translate([unit / 2 + i * unit, pd_edge, z]) rotate([-90, 0, 0]) pd_pin_hole(pd_cell, taper = true);   // cone on the y = 0 face, the bed face in "print"
}

module print1() translate([-w / 2, h / 2, -pd_edge]) rotate([90, 0, 0]) plate();   // flat, holes upright

if (part == "plate") plate();
else if (part == "print") print1();
else if (part == "print_x4") for (i = [0, 1], j = [0, 1]) translate([(i - 0.5) * (w + 8), (j - 0.5) * (h + 8), 0]) print1();
