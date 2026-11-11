// LEGO cases for the Red TT motor (scad/tt_motor_red.scad): MOCKUP (2026-11-08).
// Two heights from one file: cells = 3 (very thin side walls) or cells = 5
// (a rail more than a unit thick above and below the motor).
//
// How it sits on the robot: the motor lies along an 11 x 19 plate, shaft
// pointing out of the side of the robot, connector towards the inside. A back
// row one unit deep, full of pin holes, stands on the plate; the motor itself
// hangs off the plate's edge, which is why the 25 mm bulge can be wider than
// the 3-unit case. The motor drops in from the shaft side and a cap closes it.
//
// Coordinates are the motor's: shaft at the origin, X across the gearbox (the
// case's height), Y along the shaft (shaft side -Y, connector side +Y), Z along
// the motor, motor towards -Z. The "part" views for the viewer turn this so
// that X is up.
//
// The 11 cells along Z are centred on multiples of 8, so the shaft is in line
// with a column of holes.

include <lego.scad>
use <tt_motor_red.scad>

/* [Show] */
cells = 3;            // case height in LEGO units: 3 or 5
retain = "pegs";      // the 3-unit cap: "pegs" (friction) or "screws" (self-tapping M3)
// "body", "cap", "motor", "plates" assembled; "print_body", "print_cap", "print_both";
// "clash_body", "clash_cap" (what hits the motor)
part = "body";
$fn = 48;

/* [Motor, from tt_motor_red.scad] */
gearbox_x = 11;       // half width
gearbox_y = 9.5;      // half thickness
gearbox_top = 11.5;   // the end face
tab_top = 16.5;
tab_x = 2.5;
tab_y = 1.5;
motor_y = 0.5;        // the motor's axis
bulge_r = 12.5;
bulge_flat_y = 10.5;  // its +Y flat
bulge_z = [-34.5, -56.5];   // moved 1 towards the motor after the first print (user, 2026-11-08)
motor_bottom = -63.5;
connector_x = 8.4;    // half width
connector_y = 17.12;  // its +Y face
connector_top = -50.25;
neck_x = 22.35 / 2;
nub_x = 2.42;         // the nubs on the neck: half width
nub_y = 11.675;       // the +Y one's tip
nub_y_front = -10.675; // the -Y one's tip
nub_z_hi = -30.1;     // 41.6 from the top
nub_z_lo = -33.23;    // the base's motor-side edge
nub_fit = 0.3;        // per side: the hole in the cap must clear it

/* [Fit] */
fit = 0.2;            // per side, motor to case

/* [Case] */
unit = pd_unit;
half_h = cells == 3 ? 11.95 : cells * unit / 2 - pd_edge;  // the case's outer X faces
z_cells = [for (i = [2 : -1 : -8]) i * unit];    // 16 ... -64: 11 cells
z_hi = z_cells[0] + unit / 2 - pd_edge;          // 19.8
z_lo = z_cells[10] - unit / 2 + pd_edge;         // -67.8
y_front = -gearbox_y - fit;                      // the open side, where the cap seats: -9.7
y_inner = gearbox_y + fit;                       // the back row's motor-side face: 9.7
y_row = 13.6;                                    // the back row's holes
y_back = y_row + unit / 2 - pd_edge;             // its outer face: 17.4
x_rows = [for (i = [-(cells - 1) / 2 : (cells - 1) / 2]) i * unit];
blind = unit;                                    // half a 2L pin
shaft_bore = 6;       // the shaft's other end goes through the back row
rail_y = [5.6, -2.4]; // the 5-unit case's up-and-down holes, beyond the back row

/* [Cap] */
cap_t = 1.7;
shaft_hole = 6.2;
nub_hole = 4.5;
nub_z = -10.5;
// 3 units: pegs (or screws) into the end blocks, past each end of the motor
end_top = (gearbox_top + fit + z_hi) / 2;
end_bottom = (motor_bottom - fit + z_lo) / 2;
fix_x = 7.5;
fix_at = [[-fix_x, end_top], [fix_x, end_top], [-fix_x, end_bottom], [fix_x, end_bottom]];
peg_d = 2.8;
socket_d = 3.05;      // a light press. At 2.9 these printed 2.5-2.6 and the pegs 2.65: too tight
socket_depth = 8;
peg_len = 7.5;
screw_pilot = 2.7;    // M3 self-tapping
screw_clear = 3.4;
// 5 units: a hook down each rail at two places, each side
hook_z = [8, -64];
hook_w = 6.4;
hook_x = [13.4, 15];  // the arm
barb = 0.9;           // what it stands out past the arm
hook_tip_y = 5;
barb_y = 1.5;         // its catching edge
slot_x = [12.6, 15.2];
window_y = [1.2, 5.5];

/* [Plate stand-in] */
plate_t = 7.7;
plate_rows = 11;
plate_cols = [for (j = [-9 : 9]) -24 + j * unit];

echo(cells = cells, half_h = half_h, side_wall = half_h - (gearbox_x + fit), y_front = y_front, y_back = y_back, z_hi = z_hi, z_lo = z_lo);
assert(cells == 3 || cells == 5);
assert(y_back > connector_y + fit - 0.1, "the connector stays inside the back row");
assert(half_h - gearbox_x - fit >= 0.7, "side walls too thin to print");

// ---- the holes ----
// A pin hole through the back row, in from its +Y face (the bed).
module hole_y(x, z) translate([x, y_back, z]) rotate([90, 0, 0]) pd_pin_hole(y_back - y_inner, taper = true);
// A blind pin hole going in from the top (side = 1) or bottom (side = -1) face.
module hole_x(side, y, z, depth = blind)
    translate([side * half_h, y, z]) rotate([0, side > 0 ? -90 : 90, 0]) pd_blind_pin_hole(depth, taper = false);

function up_cell(z) = z % 16 == 0;              // the edge rows alternate
function edge_row(x) = abs(x) == x_rows[len(x_rows) - 1];
// Holes the connector's opening takes out.
function in_notch(x, z) = z < connector_top && abs(x) < connector_x + fit + 3.2;
function hook_cell(z) = cells == 5 && len([for (h = hook_z) if (h == z) h]) > 0;

module row_holes() {
    for (z = z_cells) for (x = x_rows) {
        shaft = z == 0 && x == 0;
        if (!shaft && !in_notch(x, z) && !(edge_row(x) && up_cell(z))) hole_y(x, z);
    }
    for (z = z_cells) for (side = [-1, 1]) if (up_cell(z) && !in_notch(side * (half_h - blind / 2), z))
        hole_x(side, y_row, z);
}

module rail_holes() if (cells == 5)
    for (z = z_cells) if (!hook_cell(z)) for (y = rail_y) for (side = [-1, 1]) hole_x(side, y, z);

// ---- the space the motor takes ----
module motor_space() {
    // gearbox, neck and cover: open towards the shaft side
    translate([-gearbox_x - fit - 0.01, -40, motor_bottom - fit])
        cube([2 * (gearbox_x + fit + 0.01), 40 + y_inner, gearbox_top - motor_bottom + 2 * fit]);
    // the bulge: its round, and everything towards the shaft side so it can drop in
    translate([0, 0, bulge_z[1] - fit]) linear_extrude(bulge_z[0] - bulge_z[1] + 2 * fit)
        intersection() {
            union() {
                translate([0, motor_y]) circle(r = bulge_r + fit);
                translate([-bulge_r - fit, -40]) square([2 * (bulge_r + fit), 40 + motor_y]);
            }
            translate([-40, -41]) square([80, 41 + bulge_flat_y + fit]);
        }
    // the nubs on the neck
    translate([-nub_x - nub_fit, -40, nub_z_lo - nub_fit]) cube([2 * (nub_x + nub_fit), 40 + nub_y + nub_fit, nub_z_hi - nub_z_lo + 2 * nub_fit]);
    // the tab
    translate([-tab_x - fit - 0.1, -40, gearbox_top - 1]) cube([2 * (tab_x + fit + 0.1), 40 + tab_y + fit + 0.1, tab_top - gearbox_top + 1 + fit]);
    // the shaft's far end
    translate([0, 0, 0]) rotate([-90, 0, 0]) cylinder(d = shaft_bore, h = 30);
    // the connector, open to the inside of the robot for the plug
    translate([-connector_x - fit, 0, motor_bottom - fit]) cube([2 * (connector_x + fit), 30, connector_top - motor_bottom + 2 * fit]);
}

// ---- the case ----
module hook_slots() if (cells == 5) for (z = hook_z) for (side = [-1, 1]) {
    w = hook_w + 0.6;
    // the arm's slot, open towards the cap
    translate([side > 0 ? slot_x[0] : -slot_x[1], y_front - 1, z - w / 2]) cube([slot_x[1] - slot_x[0], hook_tip_y + 0.5 - y_front + 1, w]);
    // the window the barb clicks into; a small screwdriver presses it back
    translate([side > 0 ? slot_x[1] - 0.2 : -half_h - 1, window_y[0], z - w / 2]) cube([half_h - slot_x[1] + 1.2, window_y[1] - window_y[0], w]);
}

module fix_holes() if (cells == 3)
    for (p = fix_at) translate([p[0], y_front - 1, p[1]]) rotate([-90, 0, 0])
        cylinder(d = retain == "pegs" ? socket_d : screw_pilot, h = socket_depth + 1);

module body() difference() {
    translate([-half_h, y_front, z_lo]) cube([2 * half_h, y_back - y_front, z_hi - z_lo]);
    motor_space();
    row_holes();
    rail_holes();
    hook_slots();
    fix_holes();
}

// One hook arm on the cap, standing up from its inner face towards +Y.
module hook(z, side) {
    translate([0, 0, z - hook_w / 2]) linear_extrude(hook_w) mirror([side > 0 ? 0 : 1, 0])
        polygon([
            [hook_x[0], y_front - 0.5], [hook_x[1], y_front - 0.5], [hook_x[1], barb_y],
            [hook_x[1] + barb, barb_y], [hook_x[1], hook_tip_y], [hook_x[0], hook_tip_y]]);
}

module cap() {
    difference() {
        translate([-half_h, y_front - cap_t, z_lo]) cube([2 * half_h, cap_t, z_hi - z_lo]);
        translate([0, y_front - cap_t - 1, 0]) rotate([-90, 0, 0]) cylinder(d = shaft_hole, h = cap_t + 2);
        translate([0, y_front - cap_t - 1, nub_z]) rotate([-90, 0, 0]) cylinder(d = nub_hole, h = cap_t + 2);
        // the -Y nub on the neck comes through the cap
        translate([-nub_x - nub_fit, y_front - cap_t - 1, nub_z_lo - nub_fit]) cube([2 * (nub_x + nub_fit), cap_t + 2, nub_z_hi - nub_z_lo + 2 * nub_fit]);
        if (cells == 3 && retain == "screws")
            for (p = fix_at) translate([p[0], y_front - cap_t - 1, p[1]]) rotate([-90, 0, 0]) cylinder(d = screw_clear, h = cap_t + 2);
    }
    if (cells == 3 && retain == "pegs")
        for (p = fix_at) translate([p[0], y_front - 0.5, p[1]]) rotate([-90, 0, 0]) cylinder(d = peg_d, h = peg_len + 0.5);
    if (cells == 5) for (z = hook_z) for (side = [-1, 1]) hook(z, side);
}

module motor() union() { gearbox(); motor_end(); }

// Stand-ins for the 11 x 19 plates, above and below the back row.
module plates() for (side = [-1, 1]) difference() {
    x0 = side > 0 ? half_h + 0.05 : -half_h - 0.05 - plate_t;
    translate([x0, y_row - unit / 2, plate_cols[0] - unit / 2]) cube([plate_t, plate_rows * unit, 19 * unit]);
    for (j = plate_cols) for (i = [0 : plate_rows - 1])
        translate([x0 - 1, y_row + i * unit, j]) rotate([0, 90, 0]) cylinder(d = 4.8, h = plate_t + 2, $fn = 20);
}

// Motor coordinates to the viewer's: X up.
module view() rotate([0, -90, 0]) children();

if (part == "body") view() body();
else if (part == "cap") view() cap();
else if (part == "motor") view() motor();
else if (part == "plates") view() plates();
else if (part == "print_body") translate([0, 0, y_back]) rotate([-90, 0, 0]) body();
else if (part == "print_cap") translate([0, 0, cap_t - y_front]) rotate([90, 0, 0]) cap();
else if (part == "print_both") {   // body and cap on one plate
    translate([0, 0, y_back]) rotate([-90, 0, 0]) body();
    translate([2 * half_h + 6, 0, cap_t - y_front]) rotate([90, 0, 0]) cap();
}
else if (part == "clash_body") intersection() { body(); motor(); }
else if (part == "clash_cap") intersection() { cap(); motor(); }
else assert(false, str("unknown part: ", part));
