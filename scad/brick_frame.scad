// A cage round the Nezha Breakout Board V2 (the "brick",
// models/nezha_breakout_v2.stl from tools/nezha_breakout.py) for more
// attachment points: the edges of a box, so it can be turned any way up and
// connected in different places, e.g. stood on its motor end at the front of
// a robot, display and switch facing forward, the micro:bit's USB end up
// (FIRST DRAFT, 2026-11-01/02, the user's sketch in words).
//
// 11 x 11 units in plan, 6 high: a ring at the brick's bottom, a copy of it
// at its top, and a post up each corner. Across, the brick's 60 is centred in
// 88; each side is one unit, its outer one, leaving 6.2 between it and the
// brick all round for the cables (the user, 2026-11-02: the part against the
// brick wasn't full size and its holes were on no grid). Only a pad at each
// of the brick's side pins bridges the gap. Along, the brick's 10 units plus
// one at the motor end, where the end bars (9 units, out to the sides) stand
// proud of the M1-M4 sockets. The micro:bit end has posts but no
// bars: the bottom is flush with the brick and the top keeps the micro:bit
// free to slide out. The top ring's top face is 4.1 over the brick's highest
// point (the ridge, 43.7), so a plate across it clears the button.
//
// Holes alternate along every edge, turned 90 degrees cell to cell (the
// user, 2026-11-02): the rails out (y) and up (z), from out at each corner;
// the posts across (x) and out (y), from across over the corner; the end bars
// along (x) and up (z), from along at the middle. At a brick pin the out hole
// is its hole too, through the pad. Corners where two alternations meet: the
// top of each post (36 and 44 both out).
//
// The brick's four side holes each have an arch in front (open to its bottom
// edge, 1.86 deep) that is exactly a LEGO beam's rounded end: the bottom
// rail's pad at each has a beam end on its face that fits it, with the pin
// hole through it.
//
// Four flat prints, pinned with 2L pins: the J side and the IIC side
// (windows: bottom rail, top rail and the two corner posts; mirror images,
// so two prints) and the end bar (x2, the
// motor end's bottom and top; the bottom one pins into three of the brick's
// five end holes, the alternation's along holes). Assembly: the bottom bar
// onto the brick; pins in the brick's side holes and in both bars' ends; then
// each side slides on from its side, taking all four at once.
//
// Coordinates: the brick's own, Z up: x along it (-40 the micro:bit end, +40
// the motor end), y across (+y the J side, -y the IIC side), its bottom at
// z = 0. Cell centres at x = -36 ... 44, y = 0, +-8 ... +-40, z = 4 ... 44.

include <lego.scad>

/* [Show] */
// "assembly" (brick, cage, pins), "side" (J) / "end_bar" in place, "print"
// (the four pieces on the bed, each on its outer face), or one component in
// place for the viewer: "side_j", "side_iic", "bar_bottom", "bar_top", "pins", "brick"
part = "assembly";
// in place parts stood up as on a robot: motor end down on z = 0, display facing +x (forward)
stand = false;
$fn = 32;

/* [Brick] */
brick_x = [-40, 40];
brick_half_w = 30;
brick_top = 43.7;              // the ridge over the micro:bit
end_hole_y = [-16, -8, 0, 8, 16];
side_hole_x = 28;
arch_d = 1.86;                 // the arches in front of all four side holes
beam_end_r = technic_pin_connector_outer_diameter / 2;   // 3.68: the arch is a beam's end
brick_bot = 20.1;              // the STL's bottom is at -20.1 (Y up)

/* [Cage] */
unit = pd_unit;
cells = 11;                    // in plan, both ways
height_cells = 6;
frame_x = [brick_x[0], brick_x[0] + cells * unit];      // -40 .. 48
frame_half_w = cells * unit / 2;                         // 44
height = height_cells * unit;                            // 48
ring_z = [unit / 2, height - unit / 2];                  // the rings' hole heights: 4 (the brick's holes) and 44
post_z = [for (i = [1 : height_cells - 2]) unit / 2 + unit * i];   // 12 ... 36
gap = 0.2;                     // brick face to cage face
side_y = [frame_half_w - unit + pd_edge, frame_half_w - pd_edge];   // 36.2 .. 43.8: one unit
pad_y0 = brick_half_w + gap;   // 30.2: the pads' faces at the brick's side pins
col_y = frame_half_w - unit / 2;                         // 40: the side's column of holes
bar_x = [brick_x[1] + gap, frame_x[1] - pd_edge];        // 40.2 .. 47.8
bar_half_w = side_y[0] - gap;  // 36: its ends face the sides across gap
joint_x = frame_x[1] - unit / 2;                         // 44
post_x = [frame_x[0] + unit / 2, joint_x];               // -36, 44
cell_x = [for (i = [0 : cells - 1]) frame_x[0] + unit / 2 + unit * i];
bar_cell_y = [-24, -16, -8, 0, 8, 16, 24];              // +-32 are the joints' cells
// the alternation
function rail_out(i) = i % 2 == 0;                       // rail cell i: out (y), else up (z)
function post_across(k) = k % 2 == 0;                    // post cell k (post_z[k]): across (x), else out (y)
function bar_along(y) = round(abs(y) / unit) % 2 == 0;   // end bar cell: along (x), else up (z)
// The beam end in the arch: its face gap off the arch's floor, its radius
// tongue_clear under the beam's.
tongue_clear = 0.1;
tongue_r = beam_end_r - tongue_clear;
tongue_face = brick_half_w - arch_d + gap;               // 28.34
// The brick's side pins: collar at the arch's floor, half (7.8)
// out from it, so they reach 35.94; where the cell is up, not out, the
// blind hole stops at 37.4, short of the up hole (bore from 37.5).
blind_pin_end = 37.4;
blind = unit;                  // half a 2L pin

echo(cage = [frame_x, [-frame_half_w, frame_half_w], [0, height]], cable_gap = side_y[0] - brick_half_w,
     over_brick = height - pd_edge - brick_top, tongue = [tongue_r, pad_y0 - tongue_face]);
assert(abs(frame_x[1] - frame_x[0] - 2 * frame_half_w) < 1e-6, "square in plan");
assert(len([for (x = cell_x) if (abs(abs(x) - side_hole_x) < 1e-6) x]) == 2, "side holes on the cage's grid");
assert(height - pd_edge > brick_top, "top ring over the brick");
assert(rail_out(cells - 1), "the motor-end corner is out: the end bars' joint");
assert(bar_along(end_hole_y[2]), "the bar's middle pins into the brick");

// ---- holes --------------------------------------------------------------
// pd_pin_hole / pd_blind_pin_hole run along +z from z = 0; these turn them.
module hole_y(x, y0, dir, z, h, is_blind = false)  // from the face at y0, into the part along dir (+-1)
    translate([x, y0, z]) rotate([dir > 0 ? -90 : 90, 0, 0])
        if (is_blind) pd_blind_pin_hole(h, taper = false); else pd_pin_hole(h, taper = false);
module hole_x(y, x0, z, h) translate([x0, y, z]) rotate([0, 90, 0]) pd_pin_hole(h, taper = false);
module hole_z(x, y, z0, dir, h) translate([x, y, z0]) mirror([0, 0, dir > 0 ? 0 : 1]) pd_pin_hole(h);

// ---- the pieces ----------------------------------------------------------
// The beam ends on the bottom rail's pads, s the side (+1 J, -1 IIC).
module tongue(s) for (x = [-side_hole_x, side_hole_x]) {
    y0 = s > 0 ? tongue_face : -pad_y0 - 0.01;
    translate([0, y0, 0]) rotate([90, 0, 0]) mirror([0, 0, 1])     // extrude along +y
        linear_extrude(pad_y0 - tongue_face + 0.01) hull() {
            translate([x, ring_z[0]]) circle(r = tongue_r);
            translate([x - tongue_r, pd_edge]) square([2 * tongue_r, ring_z[0] - pd_edge]);
        }
}

// where the bottom rail's hole at x starts: a beam end's face or the side's inner face
function pin_face(s, x) = abs(x) == side_hole_x ? tongue_face : side_y[0];

module side_body(s) {
    y0 = s > 0 ? side_y[0] : -side_y[1];
    for (zc = ring_z)
        translate([frame_x[0] + pd_edge, y0, zc - unit / 2 + pd_edge])
            cube([frame_x[1] - frame_x[0] - 2 * pd_edge, side_y[1] - side_y[0], pd_cell]);
    for (x = post_x)
        translate([x - unit / 2 + pd_edge, y0, pd_edge]) cube([pd_cell, side_y[1] - side_y[0], height - 2 * pd_edge]);
    for (x = [-side_hole_x, side_hole_x])      // pads across the cable gap at the brick's side pins
        translate([x - unit / 2 + pd_edge, s > 0 ? pad_y0 : -side_y[0] - 0.01, pd_edge])
            cube([pd_cell, side_y[0] - pad_y0 + 0.01, pd_cell]);
    tongue(s);
}

module side(s) difference() {
    side_body(s);
    for (i = [0, 1]) {
        zc = ring_z[i];
        z0 = i == 0 ? pd_edge : height - pd_edge;      // the ring's outer face
        dir = i == 0 ? 1 : -1;
        for (j = [0 : cells - 1]) {
            x = cell_x[j];
            // out holes start at the inner face, or the pad's or beam end's face
            face = i == 0 ? pin_face(s, x) : side_y[0];
            if (rail_out(j)) hole_y(x, s * face, s, zc, side_y[1] - face);
            else hole_z(x, s * col_y, z0, dir, pd_cell);
        }
    }
    // the brick's side pins where the cell is up: blind
    for (x = [-side_hole_x, side_hole_x]) {
        j = round((x - cell_x[0]) / unit);
        face = pin_face(s, x);
        if (!rail_out(j)) hole_y(x, s * face, s, ring_z[0], blind_pin_end - face, is_blind = true);
    }
    for (x = post_x, k = [0 : len(post_z) - 1])
        if (post_across(k)) hole_x(s * col_y, x - unit / 2 + pd_edge, post_z[k], pd_cell);
        else hole_y(x, s * side_y[0], s, post_z[k], side_y[1] - side_y[0]);
}

module end_bar(zc) difference() {
    translate([bar_x[0], -bar_half_w, zc - unit / 2 + pd_edge]) cube([pd_cell, 2 * bar_half_w, pd_cell]);
    for (y = bar_cell_y)
        if (bar_along(y)) hole_x(y, bar_x[0], zc, pd_cell);
        else hole_z(joint_x, y, zc - unit / 2 + pd_edge, 1, pd_cell);
    for (s = [-1, 1]) hole_y(joint_x, s * bar_half_w, -s, zc, blind, is_blind = true);
}

// A 2L friction pin (16 long) centred on a mating plane at the origin, along +z.
module pin_2l() color("dimgray") {
    translate([0, 0, -8]) cylinder(d = 4.8, h = 16);
    translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
module pins() {
    for (y = end_hole_y) if (bar_along(y)) translate([brick_x[1], y, ring_z[0]]) rotate([0, 90, 0]) pin_2l();
    // side pins: collar on the arch's floor
    for (s = [-1, 1], x = [-side_hole_x, side_hole_x])
        translate([x, s * (brick_half_w - arch_d), ring_z[0]]) rotate([-90, 0, 0]) pin_2l();
    for (s = [-1, 1], zc = ring_z) translate([joint_x, s * (bar_half_w + gap / 2), zc]) rotate([-90, 0, 0]) pin_2l();
}

module brick() color("white", 0.9) translate([0, 0, brick_bot]) rotate([90, 0, 0]) import("models/nezha_breakout_v2.stl");

// ---- views ---------------------------------------------------------------
module cage() {
    color("#f29a00") side(1);
    color("#4169e1") side(-1);
    color("#3cb371") for (zc = ring_z) end_bar(zc);
}

module placed() if (stand) translate([0, 0, frame_x[1]]) rotate([0, 90, 0]) children(); else children();

if (part == "print") {
    // each on its outer face: the sides' out holes and the bars' along holes vertical
    translate([0, 0, side_y[1]]) rotate([-90, 0, 0]) side(1);
    translate([0, 2 * height + 6, side_y[1]]) rotate([90, 0, 0]) side(-1);
    for (i = [0, 1]) translate([-60 - i * 14, height / 2, bar_x[1]]) rotate([0, 90, 0]) end_bar(ring_z[0]);
}
else placed() {
    if (part == "assembly") { brick(); cage(); pins(); }
    else if (part == "side" || part == "side_j") side(1);
    else if (part == "side_iic") side(-1);
    else if (part == "end_bar" || part == "bar_bottom") end_bar(ring_z[0]);
    else if (part == "bar_top") end_bar(ring_z[1]);
    else if (part == "pins") pins();
    else if (part == "brick") brick();
}
