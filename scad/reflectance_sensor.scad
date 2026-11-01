// 4-channel reflectance (line) sensor board for the robots, with its three
// white LEGO brackets. Modelled from a Revopoint scan of the back
// (models/reflectance_sensor_scan.stl, already aligned to these coordinates)
// and photos of both sides.
//
// Coordinates: Z = 0 on the back face of the PCB (the side with the button
// and the blue block). The sensors face -Z, toward the floor. X runs along the
// board. The origin is midway between the two side brackets, on their hole row.
// The middle bracket sits on a tab toward +Y. The sensors are along the -Y
// edge.
//
// Holes: each bracket is three LEGO units long (24 mm) with pin holes in
// positions 1 and 3 (16 mm apart). The side brackets' holes are on Y = 0,
// the middle bracket's on Y = 16: two rows on the 8 mm grid with one empty
// row between them. Every hole runs along Z and is a Technic pin hole from
// Technic.scad (via lego.scad).
//
// From the scan (good to ~0.2 mm): hole X/Y, bracket outlines, the back
// heights (side brackets 2.2, middle bracket 5.15, blue block 14.9), the PCB
// outline and tab notches, and the button.
// Guessed (the scan only saw the back; measure and correct): PCB thickness,
// how far the brackets reach below the PCB, the sensor positions and size.

/* [View] */
// "assembly", "scan" (the aligned scan), "overlay" (both, scan in red), or
// one component: "pcb", "brackets", "back_parts", "sensors"
part = "assembly";
// false when another file includes this one for its modules
show_part = true;

include <lego.scad>

/* [Grid] */
lego = technic_beam_hole_spacing;
// hole centres [x, y]: side brackets' row, then the middle bracket's
rs_holes = [[-32, 0], [-16, 0], [16, 0], [32, 0], [-8, 16], [8, 16]];

/* [PCB] */
pcb_t = 1.6;            // guess
pcb_x = 72;             // as long as the bracket span (scan 71.4 + edge loss)
pcb_y = [-28.4, -3.1];  // main body, -Y edge to the edge under the side brackets
tab_x = 24;             // the tab that carries the middle bracket
tab_y = 19.4;           // tab end, flush with the middle bracket
notch_r = 3.15;         // U-notches into the tab's sides, on the side hole row
notch_x = 8.6;          // centre of the notch's round end

/* [Brackets] */
br_len = 3 * lego;
side_br_y = [-9.4, 3.4];   // hole 3.4 from the outer edge
side_br_top = 2.2;         // over the PCB back
mid_br_y = [5.6, 19.4];
mid_br_top = 5.15;
// below the PCB front face (guesses: side brackets 8 thick overall)
side_br_below = 8 - side_br_top - pcb_t;
mid_br_below = side_br_below;
br_r = 1.5;                // corner rounding in plan
// Bottom of the holes: all six share one 1-unit band, centred in the side
// brackets' 8 mm (the library's unit is technic_height_in_mm = 7.8).
hole_z0 = side_br_top - 8 + (8 - technic_height_in_mm) / 2;

/* [Parts on the back] */
block = [[-5, 5.2], [5.4, 17.6]];   // blue block on the middle bracket, x/y corners
block_top = 14.9;
button_c = [-0.9, -25];
button = [3.6, 3.6, 2.4];

/* [Sensors, front] */
// centred on their solder-pad columns in the top scan (a line of 4 pads
// along y at each, 2026-10-29: x +-6.0 / +-30.0, y -25.3..-15.6); the body
// size is TCRT5000's, from photo 1
sensor_x = [-30, -6, 6, 30];
sensor_y = -20.45;
sensor = [5.8, 10.2, 7];        // TCRT5000-size body: x, y, height below the PCB
lens_d = 4.6;                   // lens spacing along y is half the body

$fn = 64;

module rrect(p0, p1, r) {
    translate([p0[0] + r, p0[1] + r]) offset(r) square([p1[0] - p0[0] - 2 * r, p1[1] - p0[1] - 2 * r]);
}

module pcb_outline() {
    difference() {
        union() {
            translate([-pcb_x / 2, pcb_y[0]]) square([pcb_x, pcb_y[1] - pcb_y[0]]);
            translate([-tab_x / 2, pcb_y[1] - 0.01]) square([tab_x, tab_y - pcb_y[1] + 0.01]);
        }
        for (s = [-1, 1]) hull() {
            translate([s * notch_x, 0]) circle(notch_r);
            translate([s * (tab_x / 2 + 1), 0]) circle(notch_r);
        }
    }
}

module pcb() {
    // the tab is drilled through for the middle bracket's pins
    color("deepskyblue") difference() {
        translate([0, 0, -pcb_t]) linear_extrude(pcb_t) pcb_outline();
        pin_holes();
    }
}

module bracket(cx, y, top, below) {
    translate([0, 0, -pcb_t - below])
        linear_extrude(top + pcb_t + below)
            rrect([cx - br_len / 2, y[0]], [cx + br_len / 2, y[1]], br_r);
}

module brackets() {
    color("whitesmoke") difference() {
        union() {
            for (s = [-1, 1]) bracket(s * 3 * lego, side_br_y, side_br_top, side_br_below);
            bracket(0, mid_br_y, mid_br_top, mid_br_below);
        }
        pin_holes();
    }
}

// All six holes; also for parts built around the sensor. `top` carries the
// counterbore out past both faces (the middle bracket stands 3 mm above the
// band).
module pin_holes(top = 5) {
    for (h = rs_holes) translate([h[0], h[1], hole_z0]) technic_pin_hole(1, top);
}

module back_parts() {
    color("royalblue") translate([block[0][0], block[0][1], 0])
        cube([block[1][0] - block[0][0], block[1][1] - block[0][1], block_top]);
    color("silver") translate([button_c[0] - button[0] / 2, button_c[1] - button[1] / 2, 0]) cube(button);
}

module sensors() {
    for (x = sensor_x) translate([x, sensor_y, -pcb_t]) {
        color("#222") translate([-sensor[0] / 2, -sensor[1] / 2, -sensor[2]]) cube(sensor);
        color("#555") for (s = [-1, 1]) translate([0, s * sensor[1] / 4, -sensor[2] - 0.3]) cylinder(d = lens_d, h = 0.3);
    }
}

module reflectance_sensor() {
    pcb();
    brackets();
    back_parts();
    sensors();
}

module scan() { import("models/reflectance_sensor_scan.stl"); }

if (show_part) {
    if (part == "assembly") reflectance_sensor();
    else if (part == "scan") scan();
    else if (part == "overlay") { reflectance_sensor(); color("red", 0.5) scan(); }
    // one component at a time, for apps that colour each import (Tinkercad)
    else if (part == "pcb") pcb();
    else if (part == "brackets") brackets();
    else if (part == "back_parts") back_parts();
    else if (part == "sensors") sensors();
}
