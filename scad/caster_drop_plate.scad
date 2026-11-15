// Caster drop plate (v2, 2026-11-14): a 1 x 5 LEGO beam whose middle three
// holes sit drop (3.5) lower than its two end holes: one hole, down 3.5,
// three holes, back up, one hole. For the caster at the front of the robot
// on 86 mm wheels (the user's numbers). v1 (two rows of three, 11.5 apart)
// was wrong; four were printed on verlet the same day.
//
// Datum: X across (0 .. 40), Y through the beam (the holes' axis, 0 .. 8),
// Z up from the middle section's bottom cell edge. Prints flat on a hole face.
include <lego.scad>

/* [Show] */
part = "plate";           // "plate", "print", "print_x4"
$fn = 32;

/* [Plate] */
unit = pd_unit;           // 8
cols = 5;                 // holes across; the first and last are the raised ends
drop = 3.5;               // the middle holes below the end holes
thick_units = 1;          // through the holes

w = cols * unit;                  // 40
h = unit + drop;                  // 11.5 overall
t = thick_units * unit;           // 8
mid_z = unit / 2;                 // 4: the middle three holes
end_z = mid_z + drop;             // 7.5: the two end holes
function hole_z(i) = i == 0 || i == cols - 1 ? end_z : mid_z;
step_wall = sqrt(unit * unit + drop * drop) - 2 * pd_cb_r;   // between an end hole's counterbore and its neighbour's

echo(size = [w - 2 * pd_edge, t - 2 * pd_edge, h - 2 * pd_edge], mid_z = mid_z, end_z = end_z, step_wall = step_wall);
assert(step_wall > 1, "the end holes' counterbores need a wall to the middle holes'");

module plate() difference() {
    union() {
        translate([unit, pd_edge, pd_edge]) cube([w - 2 * unit, t - 2 * pd_edge, unit - 2 * pd_edge]);   // middle three cells
        for (x = [pd_edge, w - unit - 0.01]) translate([x, pd_edge, drop + pd_edge]) cube([unit - pd_edge + 0.01, t - 2 * pd_edge, unit - 2 * pd_edge]);   // raised ends
    }
    for (i = [0 : cols - 1])
        translate([unit / 2 + i * unit, pd_edge, hole_z(i)]) rotate([-90, 0, 0]) pd_pin_hole(pd_cell, taper = true);   // cone on the y = 0 face, the bed face in "print"
}

module print1() translate([-w / 2, h / 2, -pd_edge]) rotate([90, 0, 0]) plate();   // flat, holes upright

if (part == "plate") plate();
else if (part == "print") print1();
else if (part == "print_x4") for (j = [0 : 3]) translate([0, (j - 1.5) * (h + 6), 0]) print1();
