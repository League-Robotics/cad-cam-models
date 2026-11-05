// A 5 x 5 LEGO L bracket (the user, 2026-11-04): two legs, each one unit
// thick with a full 5 x 5 grid of pin holes, meeting at a right angle. From
// outside each leg looks like a 5 x 5 plate of holes.
//
// The holes run the whole unit (a 2L pin goes all the way in, its far half
// standing out of the outer face), and a 1 mm skin on the inside, outside the
// unit, covers them over, so the inside faces are flat. The holes run 0.3
// past the unit so a pin's tip doesn't bottom on the skin.
//
// The corner row is in both legs. Its cells alternate (the user: "on the edge
// you do the thing where you alternate holes"): cells 0, 2, 4 up through the
// base's outer face, 1 and 3 in through the wall's. They are blind, one unit
// deep, so they stop short of the other leg's holes.
//
// Coordinates: the cell grid's outer corner at the origin, the corner edge
// along y. The base lies on z = 0 ... 8 over x, y = 0 ... 40; the wall stands
// on x = 0 ... 8 over y, z = 0 ... 40. Outer faces sit pd_edge in from the
// cells, as in Part Designer.
// Prints on the base's outer face: the base's holes vertical (their skin
// bridges 5 mm), the wall's horizontal.

include <lego.scad>

/* [Show] */
// "bracket" in place, "pins" (2L pins in a few holes, for the viewer),
// "print" (on the bed, base's outer face down), "print_x2" (two side by side)
part = "bracket";
$fn = 32;

/* [Bracket] */
unit = pd_unit;           // 8
cells = 5;                // each leg 5 x 5
skin = 1;                 // the inside skin over the holes, beyond the unit
tip_room = 0.3;           // the holes run this far past the unit: a pushed-in pin's tip, the skin's sag
side = cells * unit;      // 40: the cells
lo = pd_edge;             // outer faces, 0.2 in from the cells
hi = side - pd_edge;      // 39.8: the far edges
thick = unit + tip_room + skin;   // 9.3: each leg, cell edge to inside face
hole = unit - pd_edge + tip_room;   // 8.1: every hole, outer face to the skin
cell = [for (i = [0 : cells - 1]) unit / 2 + i * unit];   // 4, 12 ... 36
function up_cell(j) = j % 2 == 0;   // corner row: up through the base, else in through the wall

echo(bracket = [hi - lo, hi - lo, hi - lo], legs = thick - lo, hole = hole, skin = skin);
assert(up_cell(0) && up_cell(cells - 1), "both ends of the corner row open on the base");
assert(cell[1] - pd_cb_r > unit, "the next row's holes clear the corner row's");
assert(cell[1] - pd_pin_r > unit + tip_room, "corner holes stop short of the next row's");

// pd_blind_pin_hole runs along +z from its face at z = 0, counterbore and
// taper at that face only; these turn it.
module hole_z(x, y) translate([x, y, lo]) pd_blind_pin_hole(hole, taper = true);           // base, from below
module hole_x(y, z) translate([lo, y, z]) rotate([0, 90, 0]) pd_blind_pin_hole(hole, taper = false);   // wall, from outside

module bracket() difference() {
    union() {
        translate([lo, lo, lo]) cube([hi - lo, hi - lo, thick - lo]);   // base
        translate([lo, lo, lo]) cube([thick - lo, hi - lo, hi - lo]);   // wall
    }
    for (j = [0 : cells - 1]) {
        y = cell[j];
        for (i = [1 : cells - 1]) { hole_z(cell[i], y); hole_x(y, cell[i]); }   // the fields
        if (up_cell(j)) hole_z(cell[0], y); else hole_x(y, cell[0]);           // the corner row
    }
}

// A 2L friction pin (16 long) centred on a mating plane at the origin, along +z.
module pin_2l() color("dimgray") {
    translate([0, 0, -8]) cylinder(d = 4.8, h = 16);
    translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
// A few pins pushed in from outside, their collars at the outer faces.
module pins() {
    for (p = [[12, 12], [28, 28], [cell[0], cell[0]]]) translate([p[0], p[1], 0]) pin_2l();
    for (p = [[20, 20], [cell[1], cell[0]]]) translate([0, p[0], p[1]]) rotate([0, 90, 0]) pin_2l();
}

if (part == "bracket") bracket();
else if (part == "pins") pins();
else if (part == "print") translate([-side / 2, -side / 2, -lo]) bracket();
else if (part == "print_x2") for (k = [0, 1]) translate([-side / 2 + k * (side + 10), -side / 2, -lo]) bracket();
