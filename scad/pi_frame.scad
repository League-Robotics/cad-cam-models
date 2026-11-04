// An open frame round a Raspberry Pi (raspberry_pi.scad, a Pi 4), the same
// 11 x 11 footprint as the Nezha brick's cage (brick_frame.scad) and 5 high:
// the edges of a box, holes on every face so things attach anywhere (FIRST
// DRAFT, 2026-11-03, the user's sketch in words).
//
// The Pi lies flat, centred, on four weld posts copied from the Yahboom
// encoder mount (the user's, verified to fit a Pi): a 6 mm support 6 tall
// and a 2.4 mm pin 3 tall through the board's hole, melted down over it. The
// posts are 57.7 x 48.5 apart, a little under the Pi's published 58 x 49.
// They stand on two bars across the bottom at y = +-24 (the holes' 48.5 is
// 6 units), the mounting spot; one pair lands on the end bar. The board is
// 13.8 up, so its ports face out through the open windows: USB and Ethernet
// out of the +x end (2.4 past the frame's face), power and HDMI out of the -y
// side, the SD card out of the -x end; the USB tops clear the top bar by 0.8.
//
// Holes turn 90 degrees cell to cell along every edge (the rule from the
// brick's cage): the side windows' rails out (y) at the corners, up (z)
// between; their posts out at the corners and across (x), out, across
// between; the end bars along their axis at the joints, then x, z, x, z; the
// deck bars z, y, z ... (one z hole dropped where a weld post stands on it).
//
// Five flat prints, three designs, pinned with 2L pins: the base (the two
// bottom end bars, the two deck bars and the weld posts; prints on its
// bottom), the side window (x2, the same print: bottom rail, top rail, two
// posts; prints on its outer face) and the top end bar (x2; prints on its top).
// Weld the Pi on, then slide each window on from its side onto pins in the
// base's and the top bars' ends.
//
// Coordinates: x along the Pi (+x its USB end), y across (-y its power and
// HDMI edge), z up, the frame's bottom at z = 0, centred. Cell centres at
// x, y = 0, +-8 ... +-40, z = 4 ... 36.

include <lego.scad>
include <raspberry_pi.scad>

/* [Show] */
// "assembly" (Pi, frame, pins), "print" (the five pieces on one bed), one
// piece on the bed ("print_base", "print_window", "print_top_bar"), or one
// component in place for the viewer: "base", "window_a" (+y), "window_b",
// "top_bars", "pins", "pi"
part = "assembly";
$fn = 32;

/* [Frame] */
unit = pd_unit;
cells = 11;
height_cells = 5;
half = cells * unit / 2;                   // 44: the cells' outer edge
height = height_cells * unit;              // 40
cell = [for (i = [0 : cells - 1]) (i - (cells - 1) / 2) * unit];   // -40 ... 40
ring_z = [unit / 2, height - unit / 2];    // 4, 36
post_z = [for (i = [1 : height_cells - 2]) unit / 2 + unit * i];   // 12, 20, 28
gap = 0.2;                                 // window to the bars' ends
win_y = [half - unit + pd_edge, half - pd_edge];    // 36.2 .. 43.8: the windows
col = half - unit / 2;                     // 40: the outer column of cells
bar_half = win_y[0] - gap;                 // 36: the end bars reach to the windows
bar_cells = [for (y = cell) if (abs(y) < bar_half - unit / 2 + 0.01) y];   // -32 ... 32
deck_y = 24;                               // the deck bars' cells, under the posts
blind = unit;                              // half a 2L pin

/* [Weld posts] (the Yahboom mount's, measured) */
post_dx = 57.71;
post_dy = 48.47;
post_r = 3;                                // support, 6 across
post_h = 6;
pin_r = 1.2;                               // weld pin, 2.4 across
pin_h = 3;                                 // through the 1.4 - 1.6 board, the rest melted down
hole_cx = -10;                             // the holes' centre: the board centred along x
post_xy = [for (sx = [-1, 1], sy = [-1, 1]) [hole_cx + sx * post_dx / 2, sy * post_dy / 2]];
deck_top = unit - pd_edge;                 // 7.8
board_z = deck_top + post_h;               // 13.8: the board's underside

// the alternation
function rail_out(i) = i % 2 == 0;         // window rail cell i (x = cell[i]): out (y), else up (z)
function wpost_across(k) = k % 2 == 0;     // window post cell k (post_z[k]): across (x), else out (y)
function bar_x_hole(y) = round(abs(y) / unit) % 2 == 1;   // end bar cell: x, else z
function deck_z_hole(x) = round((x - bar_cells[0]) / unit) % 2 == 0;   // deck bar cell: z, else y
function under_post(x) = len([for (p = post_xy) if (abs(p[0] - x) < post_r + pd_cb_r) 1]) > 0;

pi_origin = [hole_cx - (pi_holes[0][0] + pi_holes[1][0]) / 2, -(pi_holes[0][1] + pi_holes[2][1]) / 2, board_z];
usb_top = board_z + max([for (p = pi_parts) p[5]]);
echo(frame = [2 * half, 2 * half, height], board_z = board_z, usb_clear = height - unit + pd_edge - usb_top,
     ports_past_face = pi_origin[0] + max([for (p = pi_parts) p[1]]) - (half - pd_edge), posts = post_xy);
assert(rail_out(0) && rail_out(cells - 1), "the windows' corners are out: the end bars' joints");
assert(bar_x_hole(deck_y), "the end bars' cells at the deck bars are x");
assert(usb_top < height - unit + pd_edge, "the USB ports clear the top bar");

// ---- holes --------------------------------------------------------------
// From the face at x0 / y0 / z0 into the part along dir (+-1); taper on the
// face the piece prints on (Part Designer's cone).
module hole_x(y, x0, dir, z, h, is_blind = false, taper = false)
    translate([x0, y, z]) rotate([0, dir > 0 ? 90 : -90, 0])
        if (is_blind) pd_blind_pin_hole(h, taper = taper); else pd_pin_hole(h, taper = taper);
module hole_y(x, y0, dir, z, h, is_blind = false, taper = false)
    translate([x, y0, z]) rotate([dir > 0 ? -90 : 90, 0, 0])
        if (is_blind) pd_blind_pin_hole(h, taper = taper); else pd_pin_hole(h, taper = taper);
module hole_z(x, y, z0, dir, h, taper = false)
    translate([x, y, z0]) mirror([0, 0, dir > 0 ? 0 : 1]) pd_pin_hole(h, taper = taper);

// ---- the pieces ----------------------------------------------------------
// An end bar at x = sx * 40, its cells' centre height zc; its z holes start
// from the face at bed_z (the face it prints on).
module end_bar_body(sx, zc) translate([sx * col - pd_cell / 2, -bar_half, zc - pd_cell / 2]) cube([pd_cell, 2 * bar_half, pd_cell]);
module end_bar_holes(sx, zc, bed_z, deck = false) {
    for (y = bar_cells)
        if (bar_x_hole(y)) {
            if (deck && abs(y) == deck_y) hole_x(y, sx * (col + pd_cell / 2), -sx, zc, pd_cell, is_blind = true);   // the deck bar behind
            else hole_x(y, sx * col - pd_cell / 2, 1, zc, pd_cell);
        }
        else hole_z(sx * col, y, bed_z, bed_z < zc ? 1 : -1, pd_cell, taper = true);
    for (sy = [-1, 1]) hole_y(sx * col, sy * bar_half, -sy, zc, blind, is_blind = true);   // the joints
}

module weld_post(p) translate([p[0], p[1], deck_top - 0.01]) {
    cylinder(r = post_r, h = post_h + 0.01);
    cylinder(r = pin_r, h = post_h + pin_h);
}

module base() {
    difference() {
        union() {
            for (sx = [-1, 1]) end_bar_body(sx, ring_z[0]);
            for (sy = [-1, 1])
                translate([-col, sy * deck_y - pd_cell / 2, pd_edge]) cube([2 * col, pd_cell, pd_cell]);
        }
        for (sx = [-1, 1]) end_bar_holes(sx, ring_z[0], pd_edge, deck = true);
        for (sy = [-1, 1], x = bar_cells)
            if (deck_z_hole(x)) { if (!under_post(x)) hole_z(x, sy * deck_y, pd_edge, 1, pd_cell, taper = true); }
            else hole_y(x, sy * deck_y - pd_cell / 2, 1, ring_z[0], pd_cell);
    }
    for (p = post_xy) weld_post(p);
}

// The +y window; the -y one is the same print turned 180 about z.
module window() difference() {
    union() {
        for (zc = ring_z) translate([-half + pd_edge, win_y[0], zc - pd_cell / 2]) cube([2 * half - 2 * pd_edge, pd_cell, pd_cell]);
        for (sx = [-1, 1]) translate([sx * col - pd_cell / 2, win_y[0], pd_edge]) cube([pd_cell, pd_cell, height - 2 * pd_edge]);
    }
    for (zc = ring_z, i = [0 : cells - 1])
        if (rail_out(i)) hole_y(cell[i], win_y[1], -1, zc, pd_cell, taper = true);
        else hole_z(cell[i], col, zc - pd_cell / 2, 1, pd_cell);
    for (sx = [-1, 1], k = [0 : len(post_z) - 1])
        if (wpost_across(k)) hole_x(col, sx * col - pd_cell / 2, 1, post_z[k], pd_cell);
        else hole_y(sx * col, win_y[1], -1, post_z[k], pd_cell, taper = true);
}

module top_bar(sx) difference() {
    end_bar_body(sx, ring_z[1]);
    end_bar_holes(sx, ring_z[1], height - pd_edge);
}

// A 2L friction pin (16 long) centred on a mating plane at the origin, along +z.
module pin_2l() color("dimgray") {
    translate([0, 0, -8]) cylinder(d = 4.8, h = 16);
    translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
}
module pins() for (sx = [-1, 1], sy = [-1, 1], zc = ring_z)
    translate([sx * col, sy * (bar_half + gap / 2), zc]) rotate([-90, 0, 0]) pin_2l();

module pi() translate(pi_origin) raspberry_pi4();

// ---- views ---------------------------------------------------------------
module frame() {
    color("#3cb371") base();
    color("#f29a00") window();
    color("#4169e1") rotate([0, 0, 180]) window();
    color("#2e8b57") for (sx = [-1, 1]) top_bar(sx);
}

// On the bed: the base on its bottom, the windows on their outer faces, the top bars on their tops.
module print_base() translate([0, 0, -pd_edge]) base();
module print_window(i = 0) translate([0, bar_half + 6 + i * (height + 6), win_y[1]]) rotate([-90, 0, 0]) window();
module print_top_bar(i = 0) translate([half + 8 + i * 14, 0, height - pd_edge]) rotate([180, 0, 0]) translate([-col, 0, 0]) top_bar(1);

if (part == "assembly") { pi(); frame(); pins(); }
else if (part == "print") { print_base(); for (i = [0, 1]) { print_window(i); print_top_bar(i); } }
else if (part == "print_base") print_base();
else if (part == "print_window") print_window();
else if (part == "print_top_bar") print_top_bar();
else if (part == "base") base();
else if (part == "window_a") window();
else if (part == "window_b") rotate([0, 0, 180]) window();
else if (part == "top_bars") for (sx = [-1, 1]) top_bar(sx);
else if (part == "pins") pins();
else if (part == "pi") pi();
