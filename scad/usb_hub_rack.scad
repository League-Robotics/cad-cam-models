// A rack for the Waveshare USB hub behind the Carvera's back panel (first
// draft 2026-11-05). The hub hangs on the back face of the machine's power
// supply, its bottom plate against a printed plate.
//
// Three prints, superglued:
//   plate  3 thick, the PSU's height, flat against the PSU's back face. Six
//          hooks stand out of it, one through each of the hub's six slots.
//   angle  hooks over the top of the PSU: a 40 leg that sits on top, 4 thick,
//          and a 20 leg, 3 thick, that comes down over the plate's top. Glued
//          to the plate's front face.
//   (the third is the user's call)
//
// The hooks: put the hub over the six heads, push it flat on the plate, and
// slide it down `slide`. Each slot's top edge then rests on its hook's neck
// and the head's top lip sits in front of the hub's sheet, so it can't come
// off forward. Lift it `slide` to take it off.
//
// Measured by the user: hub slots 10 long x 3.6 wide, 20 apart along a row,
// the two rows 80 apart; the hub's sheet 2 thick (his estimate); PSU 210
// across and 132 tall; 8 between the hub and the back panel with the hub
// straight on the PSU. His picks: hub's bottom edge 130 below the PSU's top,
// plate 3, angle legs 40 x 4 and 20 x 3, slide 0.75 to 1.
// Guessed: the hub's outline (63 x 86.6 plate, 66 x 73 x 25 body, scaled
// from his photo), slot centre 3.3 in from the plate's ends, the hub's depth.
//
// Datum: the PSU's top at z = 0, its back face at y = 0 (+y toward the
// machine's back panel), x across the PSU, centred on the plate.

/* [Show] */
// plate, angle, hub, hub_up (hub before sliding down), psu, panel (as
// assembled); print_plate, print_angle (laid on the bed)
part = "plate";
$fn = 48;

/* [Hub, measured] */
slot_l = 10;        // slot, end to end
slot_w = 3.6;       // slot, across
slot_pitch = 20;    // along a row
row_gap = 80;       // between the two rows
sheet_t = 2;        // the hub's plate (estimate)

/* [Hub, guessed] */
hub_plate_w = 63;
hub_plate_h = 86.6;
slot_in = 3.3;      // slot centre from the hub plate's end
hub_body_w = 66;
hub_body_h = 73;
hub_body_d = 25;

/* [Placement, the user's picks] */
psu_h = 132;
psu_w = 210;
hub_bottom = 130;   // hub's bottom edge, below the PSU's top
clear_back = 8;     // hub straight on the PSU -> back panel

/* [Plate] */
plate_t = 3;
plate_w = 70;
plate_r = 3;        // corners, face-on

/* [Hooks] */
slide = 1.0;        // the hub slides down this far to lock
clr = 0.2;          // head to slot, each side
neck_gap = 0.3;     // neck longer than the sheet is thick
head_t = 2;         // head, front to back
head_chamfer = 0.5; // lead-in on the head's front edges

/* [Angle] */
angle_top_l = 40;   // on top of the PSU, from its back face inward
angle_top_t = 4;
angle_down_l = 20;  // down over the plate
angle_down_t = 3;
angle_w = plate_w;

eps = 0.01;
head_l = slot_l - 2 * clr;
head_h = slot_w - 2 * clr;
neck_h = slot_w - slide - clr;     // slot top rests on the neck's top
catch_ = slide - clr;              // head lip above the slot's top edge, locked
neck_d = sheet_t + neck_gap;
hub_top = -hub_bottom + hub_plate_h;
rows_z = [-hub_bottom + slot_in, -hub_bottom + slot_in + row_gap];
cols_x = [-slot_pitch, 0, slot_pitch];

echo(head_l = head_l, head_h = head_h, neck_h = neck_h, catch = catch_,
     hook_out = neck_d + head_t, rows_z = rows_z, hub_top = hub_top,
     back_clear_with_plate = clear_back - plate_t);
assert(neck_h >= 2, "neck too thin: less slide or less clearance");
assert(catch_ > 0.3, "the head barely catches: more slide");
assert(hub_top < -angle_down_l, "the hub runs into the angle's leg");

// obround in x-z, l long (x) and h tall (z), centred
module obround(l, h) {
    hull() for (s = [-1, 1]) translate([s * (l - h) / 2, 0]) circle(d = h);
}

// face-on (x-z) shape -> solid from y0 to y1
module xz_solid(y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
}

// one hook for a slot whose centre (hub locked) is at (x, z)
module hook(x, z) {
    head_c = z - slot_w / 2 + slide + clr + head_h / 2;
    neck_top = z + slot_w / 2;
    translate([x, 0, 0]) {
        // neck: the head's outline, cut off at the slot's (locked) top edge
        intersection() {
            xz_solid(plate_t - eps, plate_t + neck_d + eps) translate([0, head_c]) obround(head_l, head_h);
            translate([-head_l, plate_t - 1, neck_top - 50]) cube([2 * head_l, neck_d + 2, 50]);
        }
        // head, with a chamfered front
        hull() {
            xz_solid(plate_t + neck_d, plate_t + neck_d + head_t - head_chamfer)
                translate([0, head_c]) obround(head_l, head_h);
            xz_solid(plate_t + neck_d, plate_t + neck_d + head_t)
                translate([0, head_c]) obround(head_l - 2 * head_chamfer, head_h - 2 * head_chamfer);
        }
    }
}

module plate() {
    xz_solid(0, plate_t) translate([0, -psu_h / 2]) offset(plate_r) offset(-plate_r)
        square([plate_w, psu_h], center = true);
    for (x = cols_x, z = rows_z) hook(x, z);
}

module angle() {
    y1 = plate_t + angle_down_t;
    translate([-angle_w / 2, -angle_top_l, 0]) cube([angle_w, angle_top_l + y1, angle_top_t]);
    translate([-angle_w / 2, plate_t, -angle_down_l]) cube([angle_w, angle_down_t, angle_down_l + eps]);
}

// stand-in hub, locked (dz = 0) or before sliding down (dz = slide)
module hub(dz = 0) {
    translate([0, 0, dz]) {
        difference() {
            xz_solid(plate_t, plate_t + sheet_t) translate([0, -hub_bottom + hub_plate_h / 2])
                offset(2) offset(-2) square([hub_plate_w, hub_plate_h], center = true);
            for (x = cols_x, z = rows_z) translate([x, 0, z])
                xz_solid(plate_t - 1, plate_t + sheet_t + 1) obround(slot_l, slot_w);
        }
        zc = -hub_bottom + hub_plate_h / 2;
        translate([-hub_body_w / 2, plate_t + sheet_t - eps, zc - hub_body_h / 2])
            cube([hub_body_w, hub_body_d, hub_body_h]);
        // green power terminal, on the side it is in the photo (mirrored: the photo is of the bottom)
        translate([hub_body_w / 2, plate_t + sheet_t + 6, zc - 22 - 6]) cube([7, 9, 12]);
    }
}

module psu() { translate([-psu_w / 2, -60, -psu_h]) cube([psu_w, 60, psu_h]); }

// the machine's back panel, 8 past the hub as it would sit straight on the PSU
module panel() {
    translate([-psu_w / 2 - 20, sheet_t + hub_body_d + clear_back, -psu_h - 10]) cube([psu_w + 40, 1.5, psu_h + 30]);
}

if (part == "plate") plate();
else if (part == "angle") angle();
else if (part == "hub") hub();
else if (part == "hub_up") hub(slide);
else if (part == "psu") psu();
else if (part == "panel") panel();
else if (part == "print_plate") rotate([90, 0, 0]) translate([0, 0, psu_h / 2]) plate();   // back face down, hooks up
else if (part == "print_angle") rotate([180, 0, 0]) translate([0, 0, -angle_top_t]) angle(); // top face down, short leg up
