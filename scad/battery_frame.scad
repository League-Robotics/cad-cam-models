// A LEGO frame round the USB battery (models/usb_battery.stl, the user's
// "USB Battery Holder.stl": a rounded box 103 x 27.25 x 25.25) that the
// battery slips into, with pin holes on every face so things attach anywhere
// (FIRST DRAFT, 2026-11-03, the user's sketch in words).
//
// 6 x 6 units across, 11 along: "a hot dog in a bun", the battery standing
// 7.6 out of each open end. The user would rather have 5, but 5 leaves 6.4 of
// wall beside the battery, too thin to take a pin hole across or a pin along
// (a pin in from the face would reach the battery); 6 leaves about 10.
//
// A full grid of holes on every face (the user, 2026-11-03: "in the middle
// of the field, you just do all the holes"): top and bottom at y = +-4, +-12,
// the sides at z = 12 ... 36, every cell, each from its face into the
// battery's space. Only the corner holes alternate, as on the Nezha cage
// (the user 2026-11-02): the even cells (both ends and every other one, 6)
// up through the top and bottom, the odd cells (5, the middle one too) out
// through the sides; blind, half a 2L pin deep, so they stop short of the
// field holes.
//
// Two halves split down the middle (y = 0), the same piece twice (each is
// the other turned 180 about z). Each prints on its outer side, a U lying
// open upward. Four 2L pins join them, across the split on the corner rows
// (z = 4 and 44) in the second cell from each end, in line with that cell's
// corner holes; there the two field holes beside the split (y = +-4) give
// way (the user: "except where you need to put pins to join the halves").
// Two ribs along each side's inner face grip the battery.
//
// Coordinates: x along (the cells at -40 ... 40), y across (+y half A), z up,
// the frame's cell box on z = 0 ... 48, the battery centred in it.

include <lego.scad>

/* [Show] */
// "assembly" (battery, both halves, pins), "half_a" / "half_b" / "pins" /
// "battery" in place for the viewer, "print" (one half on the bed, on its
// outer side) or "print_x2" (both)
part = "assembly";
$fn = 32;

/* [Battery] */
batt = [103, 27.25, 25.25];    // along, across, up: the STL's bounding box
batt_r = 2;                    // the rounding on its long edges
batt_stl_c = [-61.625, -33.5, 14];   // its centre in the STL (length along the STL's y)
clear = 0.3;                   // per side, battery to frame

/* [Frame] */
unit = pd_unit;
cells_x = 11;
cells_yz = 6;
len_x = cells_x * unit - 2 * pd_edge;        // 87.6
half_w = cells_yz * unit / 2 - pd_edge;      // 23.8: the outer faces
height = cells_yz * unit;                    // 48: the cells
zc = height / 2;                             // 24: the battery's centre
cell_x = [for (i = [0 : cells_x - 1]) (i - (cells_x - 1) / 2) * unit];   // -40 ... 40
cav_w = batt[1] / 2 + clear;                 // 13.925
cav_z = [zc - batt[2] / 2 - clear, zc + batt[2] / 2 + clear];   // 11.075, 36.925
cav_r = batt_r + clear;
field = [4, 12];               // top and bottom holes, y = +-
out_z = [12, 20, 28, 36];      // side holes
corner_y = 20;                 // the corner holes: up in the up cells,
corner_z = [4, 44];            // out in the others
blind = unit;                  // the corner holes' depth: half a 2L pin
joint_cells = [1, cells_x - 2];   // pins across the split, on the corner rows
function up_cell(i) = i % 2 == 0;
function joint(i) = len([for (j = joint_cells) if (j == i) j]) > 0;
into = 0.5;                    // the field holes run on into the battery's space

/* [Ribs] */
rib_z = [16, 32];              // between the side holes
rib_r = 0.6;
rib_in = 0.45;                 // stands in from the cavity's wall: 0.15 into the battery
rib_end = 4;                   // short of each end, rounded, a lead-in

echo(frame = [len_x, 2 * half_w, height - 2 * pd_edge], overhang = (batt[0] - len_x) / 2,
     side_wall = half_w - cav_w, top_wall = cav_z[0] - pd_edge, grip = rib_in - clear);
assert(up_cell(0) && up_cell(cells_x - 1), "both ends up cells, so the halves are the same piece");
for (j = joint_cells) assert(!up_cell(j) && joint(cells_x - 1 - j), "joints in out cells, symmetric");
assert(cav_z[0] - pd_edge >= unit && half_w - cav_w >= unit - 2 * pd_edge, "walls take half a 2L pin");
assert(height - pd_edge - blind > out_z[3] + pd_pin_r, "up corner holes stop short of the side holes");
assert(half_w - blind > field[1] + pd_pin_r, "out corner holes stop short of the top and bottom holes");
assert(blind < field[1] - pd_pin_r, "joint holes stop short of the y = 12 holes");
for (z = rib_z) assert(len([for (h = out_z) if (abs(z - h) < pd_pin_r + rib_r) h]) == 0, "ribs between the side holes");

// ---- holes: pd_blind_pin_hole runs along +z from its face at z = 0; these turn it ----
// Each starts at a face (y0 / z0) and goes into the part along dir (+-1).
// taper: Part Designer's cone, for holes from the outer side (the bed).
module hole_y(x, y0, dir, z, h, taper = false)
    translate([x, y0, z]) rotate([dir > 0 ? -90 : 90, 0, 0]) pd_blind_pin_hole(h, taper = taper);
module hole_z(x, y, z0, dir, h) translate([x, y, z0]) mirror([0, 0, dir > 0 ? 0 : 1]) pd_blind_pin_hole(h, taper = false);

// ---- the halves ----
// The battery's space, along x, rounded as the battery.
module cavity() rotate([90, 0, 90]) translate([0, 0, -len_x / 2 - 1]) linear_extrude(len_x + 2)
    translate([0, zc]) offset(r = cav_r) square([2 * (cav_w - cav_r), cav_z[1] - cav_z[0] - 2 * cav_r], center = true);

module ribs(s) for (z = rib_z) hull() for (x = [-1, 1] * (len_x / 2 - rib_end))
    translate([x, s * (cav_w - rib_in + rib_r), z]) sphere(r = rib_r);

module half(s) difference() {
    union() {
        difference() {
            translate([-len_x / 2, s > 0 ? 0 : -half_w, pd_edge]) cube([len_x, half_w, height - 2 * pd_edge]);
            cavity();
        }
        ribs(s);
    }
    for (i = [0 : cells_x - 1]) {
        x = cell_x[i];
        for (y = field) if (!(joint(i) && y == field[0])) {
            hole_z(x, s * y, pd_edge, 1, cav_z[0] - pd_edge + into);
            hole_z(x, s * y, height - pd_edge, -1, height - pd_edge - cav_z[1] + into);
        }
        for (z = out_z) hole_y(x, s * half_w, -s, z, half_w - cav_w + into, taper = true);
        if (up_cell(i)) {
            hole_z(x, s * corner_y, pd_edge, 1, blind);
            hole_z(x, s * corner_y, height - pd_edge, -1, blind);
        } else for (z = corner_z) {
            hole_y(x, s * half_w, -s, z, blind, taper = true);
            if (joint(i)) hole_y(x, 0, s, z, blind);   // from the split face: the joint pin's half, its collar in the counterbore
        }
    }
}

// A 2L friction pin (16 long) centred on a mating plane at the origin, along +z.
module pin_2l() color("dimgray") {
    translate([0, 0, -8]) cylinder(d = 4.8, h = 16);
    translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
module pins() for (i = joint_cells, z = corner_z)
    translate([cell_x[i], 0, z]) rotate([-90, 0, 0]) pin_2l();

module battery() color("white", 0.9) translate([0, 0, zc]) rotate([0, 0, 90]) translate(-batt_stl_c)
    import("models/usb_battery.stl");

// On the bed on its outer side: the out holes vertical, the U open upward.
module print_half(k = 0) translate([0, k * (height + 6), half_w]) rotate([-90, 0, 0]) half(1);

if (part == "print") print_half();
else if (part == "print_x2") { print_half(0); print_half(1); }
else if (part == "assembly") { battery(); color("#f29a00") half(1); color("#4169e1") half(-1); pins(); }
else if (part == "half_a") half(1);
else if (part == "half_b") half(-1);
else if (part == "pins") pins();
else if (part == "battery") battery();
