// Red TT motor with its encoder cover: DRAFT (2026-11-08).
// The user's checked gearbox (models/tt_motor/tt_gearbox.stl) with a modelled
// motor end. The Blue TT is the same motor without the cover.
//
// Frame (the gearbox's): origin on the output shaft at the gearbox's
// mid-thickness, X across the gearbox, Y along the shaft (nub on -Y), Z along
// the motor with the motor towards -Z. "From the top" means from the gearbox's
// end face, the one with the tab on it, at Z = top_z.
//
// Set show = "gearbox" or "motor" for one component.

show = "all";
$fn = 96;

eps = 0.01;            // overlap between solids that touch

top_z = 11.5;          // gearbox end face (checked gearbox)
gearbox_end_z = -25.21;  // where the gearbox stops (checked gearbox)
gearbox_face_y = -9.5;   // the gearbox's -Y face (checked gearbox)

overall = 75;          // top of the gearbox to the bottom (user)

// The neck and bulge are each a circle cut by two flats. The rounds are
// measured along X (looking at the front), the flats along Y (from the side).
neck_round = 22.35;    // the section right below the gearbox (user)
neck_flats = 17.25;    // (user)
bulge_round = 25;      // the motor bulge (user)
bulge_flats = 20;      // (user)

// The motor's axis is off the gearbox's centre: in the side photo the bulge's
// -Y flat is flush with the gearbox's -Y face, which makes this 0.5.
motor_y = gearbox_face_y + bulge_flats / 2;   // ESTIMATE, from the side photo

bulge_start = 46;      // from the top: the first case print showed it 1 lower than the photos (user)
bulge_end = 68.16;     // from the top: the bulge is 22.16 long (user)

// Encoder cover: a circle on the motor axis, its -Y side cut flat.
cover_round = 19;      // (user)
cover_inset = 1.12;    // its -Y flat, in from the gearbox's -Y face (user)

// Connector block on the cover's +Y side, overhanging beside the bulge.
connector_w = 16.8;    // across X (user; also measured 16.7)
cover_depth = 25.5;    // the cover's -Y flat to the block's +Y face (user)
connector_len = 13.25; // along Z, up from the bottom (user)

// The white connector, seen from +Y as an opening in the block.
plug_h = 4.75;         // along Z (user)
plug_top = 2;          // its top, down from the block's top (user)
plug_w = 14;           // across X: ESTIMATE, from the photo
plug_depth = 6;        // into the block: ESTIMATE

// A nub on each flat of the neck, between the gearbox and the bulge. From the
// side it has a straight back on the gearbox side; on the motor side it drops
// straight from the tip to halfway, then flares out to the base (user).
nub_w = 4.84;          // across X (user)
nub_base = 3.13;       // along Z, where it meets the neck (user)
nub_tip = 2.16;        // along Z, at its outer end (user)
nub_proud = 2.55;      // off the flat (user)
nub_from_top = 41.6;   // its gearbox-side edge, from the top (user)

bottom_z = top_z - overall;
cover_flat_y = gearbox_face_y + cover_inset;
block_end_y = cover_flat_y + cover_depth;
block_top_z = bottom_z + connector_len;

assert(bottom_z < top_z - bulge_end, "the bulge runs past the bottom");
assert(neck_flats < neck_round && bulge_flats < bulge_round);
assert(plug_top + plug_h < connector_len, "the plug runs out of the block");
echo(bottom_z = bottom_z, motor_y = motor_y, cover_flat_y = cover_flat_y, block_end_y = block_end_y, block_top_z = block_top_z);

// A circle of diameter `round_d` with flats `flats` apart, from z_hi down to z_lo.
module flatted(round_d, flats, z_hi, z_lo) {
    translate([0, motor_y, z_lo])
        linear_extrude(z_hi - z_lo)
            intersection() {
                circle(d = round_d);
                square([round_d + 1, flats], center = true);
            }
}

module cover() {
    translate([0, 0, bottom_z])
        linear_extrude(top_z - bulge_end + eps - bottom_z)
            intersection() {
                translate([0, motor_y]) circle(d = cover_round);
                translate([-cover_round, cover_flat_y]) square([2 * cover_round, 2 * cover_round]);
            }
}

// One nub on the flat at y = flat_y, standing out towards side (+1 or -1).
module neck_nub(flat_y, side) {
    z_top = top_z - nub_from_top;
    translate([-nub_w / 2, 0, 0])
        rotate([90, 0, 90])
            linear_extrude(nub_w)
                polygon([
                    [flat_y - side * eps, z_top],
                    [flat_y + side * nub_proud, z_top],
                    [flat_y + side * nub_proud, z_top - nub_tip],
                    [flat_y + side * nub_proud / 2, z_top - nub_tip],
                    [flat_y - side * eps, z_top - nub_base],
                ]);
}

module motor_end() {
    difference() {
        union() {
            flatted(neck_round, neck_flats, gearbox_end_z + eps, top_z - bulge_start - eps);
            flatted(bulge_round, bulge_flats, top_z - bulge_start, top_z - bulge_end);
            cover();
            translate([-connector_w / 2, motor_y, bottom_z])
                cube([connector_w, block_end_y - motor_y, connector_len]);
            neck_nub(motor_y + neck_flats / 2, 1);
            neck_nub(motor_y - neck_flats / 2, -1);
        }
        // the connector's opening, in the block's +Y face
        translate([-plug_w / 2, block_end_y - plug_depth, block_top_z - plug_top - plug_h])
            cube([plug_w, plug_depth + 1, plug_h]);
    }
}

module gearbox() {
    import("models/tt_motor/tt_gearbox.stl", convexity = 6);
}

// ---- Four-part print (2026-11-08): split front and back on the plane Y = 0,
// and gearbox from motor at gearbox_end_z. Each part prints with its cut face
// on the bed. The halves are located by loose square pins in sockets in the
// cut faces; a tongue on the motor end, half on each motor half, goes into a
// slot in the gearbox. All glued.

clearance = 0.2;       // per side, on the pins and the tongue

pin_side = 3;          // the loose pins' square section
socket_depth = 5.2;    // into each half
pin_length = 2 * socket_depth - 0.8;  // so the cut faces seat
gearbox_pins = [[-7, 4], [7, 4], [0, -14]];      // [x, z] of the sockets
motor_pins = [[-8, -40], [8, -40], [0, -58]];

tongue_w = 12;         // across X
tongue_t = 3;          // each motor half's share, along Y
tongue_l = 7;          // into the gearbox, along Z

// `side` is -1 for the front (nub side, -Y) and +1 for the back (connector side).
module half(side) {
    intersection() {
        children();
        translate([-50, side > 0 ? 0 : -50, -100]) cube([100, 50, 200]);
    }
}

module pin_sockets(pins, side) {
    s = pin_side + 2 * clearance;
    for (p = pins)
        translate([p[0] - s / 2, side > 0 ? -1 : -socket_depth, p[1] - s / 2])
            cube([s, socket_depth + 1, s]);
}

module gearbox_half(side) {
    w = tongue_w + 2 * clearance;
    t = tongue_t + clearance;
    difference() {
        half(side) gearbox();
        pin_sockets(gearbox_pins, side);
        translate([-w / 2, side > 0 ? -1 : -t, gearbox_end_z - 1])
            cube([w, t + 1, tongue_l + clearance + 1]);
    }
}

module motor_half(side) {
    difference() {
        union() {
            half(side) motor_end();
            translate([-tongue_w / 2, side > 0 ? 0 : -tongue_t, gearbox_end_z - 1])
                cube([tongue_w, tongue_t, tongue_l + 1]);
        }
        pin_sockets(motor_pins, side);
    }
}

module pins_in_place() {
    for (p = concat(gearbox_pins, motor_pins))
        translate([p[0] - pin_side / 2, -pin_length / 2, p[1] - pin_side / 2])
            cube([pin_side, pin_length, pin_side]);
}

// A part on the bed: cut face down at Z = 0, with two loose pins beside it.
module on_bed(side) {
    rotate([side > 0 ? 90 : -90, 0, 0]) children();
    for (i = [0, 1])
        translate([24, i * 6 - 3 - pin_side / 2, 0])
            cube([pin_length, pin_side, pin_side]);
}

part = "";             // "" for the assembly, or one of the names below

assert(socket_depth < 8, "a socket would break through a half");
echo(pin_length = pin_length);

if (part == "") {
    if (show == "all" || show == "gearbox") color("#b03030") gearbox();
    if (show == "all" || show == "motor") color("#d94040") motor_end();
}
else if (part == "gearbox_front") gearbox_half(-1);
else if (part == "gearbox_back") gearbox_half(1);
else if (part == "motor_front") motor_half(-1);
else if (part == "motor_back") motor_half(1);
else if (part == "pins") pins_in_place();
else if (part == "print_gearbox_front") on_bed(-1) gearbox_half(-1);
else if (part == "print_gearbox_back") on_bed(1) gearbox_half(1);
else if (part == "print_motor_front") on_bed(-1) translate([0, 0, 48]) motor_half(-1);
else if (part == "print_motor_back") on_bed(1) translate([0, 0, 48]) motor_half(1);
else assert(false, str("unknown part: ", part));
