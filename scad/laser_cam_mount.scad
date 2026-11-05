// Two Arducam USB cameras and a line laser on the Carvera toolhead (first
// draft 2026-11-03), and the bracket it hangs from. Front to back: camera,
// laser, camera, all facing down. The laser is a brass 9 mm module in a bore
// right through the part (wires out the top): turn it to set the line, then
// lock it with a set screw from the side.
//
// History (the user, 2026-11-04): the solid block between the cameras became
// an open trough like the camera pockets; the laser bore goes right through so
// the laser doesn't hang so far down; the whole thing is 160 long so the
// cameras are farther apart, the laser in the middle between them. The back
// end may be at most 75 from the bracket (the machine's back); the front has
// room. Then: one 1/4-20 screw into the old bracket's cap wasn't stable
// enough, so this file has a new bracket. It is the old one (the aluminium
// angle's copy from carvera_angle.scad, same holes, same cap) with its
// two-hole leg grown into a triangle each way, front and back, standing on a
// solid glue pad that runs along the mount's centre line, inside its
// footprint. No screws (the user glues it on, once): the pad's one hole is
// over the laser bore, so a rod or the laser itself through both lines them
// up. The mount's top is flat.
//
// 2026-11-04, after testing (robot-projects/carvera/docs/camera-mount-geometry.md):
// stereo needs the cameras close and parallel, the baseline along the sensors'
// long axis. So the cameras now sit `baseline` apart (52: the closest two 38
// boards go with the 9 mm laser between them; the doc asks 45-50), the laser
// in the rib between their pockets, and both boards are turned 90 degrees so
// the 1280 px side runs front to back (y). That puts the cable slots on the +x
// side, off the centre line; the glue pad is notched clear of them. The user
// also asked for a 1/2 in hole through the front triangle, beside the laser
// hole, to thread the laser's cable through.
//
// Cameras: Arducam 38 x 38 USB boards (B0332, B0385, B0200 ...). Arducam lists
// two hole patterns on them, 34 x 34 (outer, M2.5) and 28 x 28 (inner); the
// user's own mount (Arducam Mount 28mm.stl) uses the 28 pattern in a 39 x 39
// pocket with a 24 x 4.6 cable slot 14.65 off the board's centre, and the
// connector on the back wants about 8 of room. Each board hangs face down
// on four standoffs on the 28 pattern (the user: the posts in his mount are
// the right spacing, 2026-11-03), back up, cable up through the slot.
//
// Datum: the laser's axis is z (the cameras sit on x = 0 too), z = 0 the
// mount's flat top, which is the bracket's underside. +y runs to the back of
// the machine, so the front camera is at -y. The bracket's cap is centred
// bracket_off behind the laser, where the old 1/4-20 screw was, so the mount
// sits where it did on the machine.

/* [Show] */
// "mount" or "bracket" (as mounted), "mount_print" or "bracket_print" (on the bed), "assembly"
part = "assembly";
// in the assembly: "all" or one of mount, bracket, cameras, laser
show = "all";
$fn = 64;

/* [Cameras, Arducam] */
board = 38;            // 38 x 38 board
board_t = 1.6;         // our guess
hole_pitch = 28;       // inner pattern, as in the user's mount (outer is 34)
board_clear = 0.5;     // per side in the pocket: 39 pocket like the user's mount
back_room = 11.5;      // plate to the board's back, as in the user's mount (connector needs ~8)
slot = [24, 4.6];      // cable slot, from the user's mount
slot_off = 14.65;      // slot centre from the board centre, from the user's mount
lens_block = [16, 16, 14];  // stand-in lens holder + lens below the board, guess

/* [Laser] */
laser_d = 9;           // brass module, the user's "about 9 mm"
laser_len = 22;        // not measured
laser_clear = 0.15;    // per side, so it turns but doesn't rattle
m3_ins_d = 4.0;        // M3 heat-set insert hole for the set screw
set_side = -1;         // set screw from -x, away from the cable slots; M3 x 20 reaches the laser through the rib

/* [Mount] */
plate_t = 4;           // top plate
wall = 2;              // camera pocket walls
baseline = 52;         // camera centre to centre, the laser halfway (the doc: 45-50, b >= 22)
max_back = 75;         // the user: at most 7.5 cm from the bracket to the back end
standoff_d = 5;        // the slot clips 0.5 off each one's inner side
standoff_hole_d = 2.2; // M2.5 screws threaded into the plastic
bracket_off = 20;      // laser axis to the bracket's cap centre, toward the back

/* [Bracket] */
// the aluminium angle's copy, as in carvera_angle.scad (bracket_l, cap_t, leg, t there)
bracket_l = 56;        // the angle part, top end to the cap
cap_t = 6;             // the cap under it (now part of the glue pad)
leg = 25.4;            // 1 in legs: the glue pad is as wide, centred on the mount
ang_t = 3.28;          // wall
pad_t = 4;             // glue pad
slot_gap = 1;          // the pad's notch clears the cable slots by this
cable_hole_d = 12.7;   // the user: 1/2 in, through the front triangle beside the laser hole, for its cable
cable_hole_above = 2;  // plastic between the cable hole and the pad
tie_slot = [5, 2.2];   // zip-tie slots through the front triangle: along its top edge, across (ties up to 4.8 wide)
tie_edge = 4;          // plastic between a slot and the edge, for the tie to wrap round
tie_at = [0.25, 0.5, 0.75];  // where along the front triangle's top edge, from the leg down to the pad
tie_at_back = [1 / 3, 2 / 3];   // and along the back one
tie_relief = 1.4;      // the back triangle's inside face lies against a cover (the user): a channel this deep
                       // from each slot over the top edge, so the tie's strap sits below the face

eps = 0.01;

pocket = board + 2 * board_clear;         // 39
pod = pocket + 2 * wall;                  // 43, one camera pod outside
pod_h = plate_t + back_room + board_t;    // pod walls cover the board's edge
cam_y = baseline / 2;                     // camera centres at +-cam_y
total_len = baseline + pod;
rib = baseline - pocket;                  // between the two pockets: holds the laser
bottom = -pod_h;                          // the pods' and rib's underside
bore_d = laser_d + 2 * laser_clear;
end_y = total_len / 2;                    // the mount's ends, at +-end_y
pad_end = end_y;                          // the pad runs the mount's length
bracket_h = bracket_l + cap_t;
// the bracket's own frame (as carvera_angle.scad's bracket()): the cap from (0, 0) to (leg, leg), the
// two-hole leg at x = 0 to t; its cap centre goes over the middle insert
to_mount = [-leg / 2, bracket_off - leg / 2, 0];

echo(overall = 2 * end_y, rib = rib, baseline = 2 * cam_y, laser_to_cam = cam_y, pod = pod, pod_h = pod_h,
     bracket_to_back = end_y - bracket_off, bracket_to_front = end_y + bracket_off, pad = [leg, 2 * pad_end],
     laser_sticks_out = laser_len - pod_h);
assert(end_y - bracket_off <= max_back, "too long behind the bracket");
assert(leg / 2 + bore_d / 2 < bracket_off, "the laser hole runs into the bracket's one-hole leg");
assert(-to_mount[0] - ang_t > bore_d / 2 + 1, "the bracket's leg sits over the laser bore");
assert(slot_off + slot[1] / 2 < pocket / 2, "the cable slot runs into the wall");
assert(rib - bore_d >= 3, "under 1.5 of wall between the laser bore and a camera pocket");

// one camera pod, centred on x = y = 0, hanging down from z = 0. The slot
// side goes to +y; mount() turns it so the slot is at +x.
module pod() {
    difference() {
        union() {
            difference() {
                translate([-pod / 2, -pod / 2, -pod_h]) cube([pod, pod, pod_h]);
                translate([-pocket / 2, -pocket / 2, -pod_h - eps]) cube([pocket, pocket, pod_h - plate_t + eps]);
            }
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * hole_pitch / 2, sy * hole_pitch / 2, 0])
                difference() {
                    translate([0, 0, -plate_t - back_room]) cylinder(d = standoff_d, h = back_room + eps);
                    translate([0, 0, -plate_t - back_room - eps]) cylinder(d = standoff_hole_d, h = back_room);
                }
        }
        // the slot, carried down past the standoffs so the cable has its full width
        translate([-slot[0] / 2, slot_off - slot[1] / 2, -plate_t - back_room - eps])
            cube([slot[0], slot[1], plate_t + back_room + 2 * eps]);
    }
}


module mount() {
    difference() {
        union() {
            for (s = [-1, 1]) translate([0, s * cam_y, 0]) rotate([0, 0, -90]) pod();
            // the rib between the pockets, full depth: the laser bore and its set screw
            translate([-pod / 2, -rib / 2 - eps, bottom]) cube([pod, rib + 2 * eps, pod_h]);
        }
        // laser bore right through; the wires come out the top
        translate([0, 0, bottom - eps]) cylinder(d = bore_d, h = pod_h + 2 * eps);
        // set screw insert from the side, through the rib into the bore, halfway down
        translate([0, 0, bottom / 2]) rotate([0, set_side * 90, 0]) cylinder(d = m3_ins_d, h = pod / 2 + eps);
    }
}

// The bracket, in carvera_angle.scad's bracket() frame: holes at the top, the
// one-hole leg at the front (y = 0 to t), the two-hole leg on the left
// (x = 0 to t), z = 0 the cap's underside. The triangles are the two-hole
// leg's plane carried front and back along the glue pad to its ends.
module new_bracket() {
    yf = -pad_end - to_mount[1];          // the pad's ends in this frame
    yb = pad_end - to_mount[1];
    tuck = 0.05;
    difference() {
        union() {
            multmatrix([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, bracket_h], [0, 0, 0, 1]])
                angle(bracket_l);
            cube([leg, leg, cap_t]);
            // the triangles: (y, z) in the leg's plane, extruded across x = 0 to t; each slope runs
            // from the leg's top corner to the pad's top corner at its end (both ends tuck in by
            // `tuck`, far under a print's resolution: exactly on the corners the mesh breaks), and the
            // triangle reaches 1 into the leg (clear of its pockets)
            rotate([90, 0, 90]) linear_extrude(ang_t) {
                polygon([[yf + tuck, 0], [1, 0], [1, bracket_h - tuck], [tuck, bracket_h - tuck], [yf + tuck, pad_t - tuck]]);
                polygon([[leg - 1, 0], [yb - tuck, 0], [yb - tuck, pad_t - tuck], [leg - tuck, bracket_h - tuck],
                         [leg - 1, bracket_h - tuck]]);
            }
            translate([0, yf, 0]) cube([leg, yb - yf, pad_t]);
        }
        // the one hole: over the laser bore, to line the two up
        translate([leg / 2, -to_mount[1], -eps]) cylinder(d = bore_d, h = pad_t + 2 * eps);
        // the laser cable's hole through the front triangle, level with the laser hole, just above the pad
        translate([-eps, -to_mount[1], pad_t + cable_hole_above + cable_hole_d / 2]) rotate([0, 90, 0])
            cylinder(d = cable_hole_d, h = ang_t + 2 * eps);
        // the pad notched clear of the camera cable slots (+x side, in the mount's frame)
        for (s = [-1, 1])
            translate([slot_off - slot[1] / 2 - slot_gap - to_mount[0],
                       s * cam_y - slot[0] / 2 - slot_gap - to_mount[1], -eps])
                cube([leg, slot[0] + 2 * slot_gap, pad_t + 2 * eps]);
        // zip-tie slots under the triangles' top edges, for strain relief on the cables
        tie_slots([0, bracket_h], [yf, pad_t], tie_at);
        tie_slots([leg, bracket_h], [yb, pad_t], tie_at_back, relief = true);
    }
}

// slots through the leg's plane under a triangle's slope from p0 to p1 ((y, z)), at fractions `at` along it;
// with relief, a channel in the inside face (x = t) from each slot out over the edge for the strap
module tie_slots(p0, p1, at, relief = false) {
    u = (p1 - p0) / norm(p1 - p0);
    n = u[0] < 0 ? [-u[1], u[0]] : [u[1], -u[0]];   // into the triangle (downwards)
    h = (tie_slot[0] + 0.5) / 2;                     // half the channel's width
    for (f = at) {
        e = p0 + f * norm(p1 - p0) * u;              // on the edge
        c = e + (tie_edge + tie_slot[1] / 2) * n;    // the slot's centre
        rotate([90, 0, 90]) translate([0, 0, -eps]) linear_extrude(ang_t + 2 * eps)
            translate(c) rotate(atan2(u[1], u[0])) square(tie_slot, center = true);
        if (relief) rotate([90, 0, 90]) translate([0, 0, ang_t - tie_relief]) linear_extrude(tie_relief + eps)
            polygon([c + h * u, c - h * u, e - n - h * u, e - n + h * u]);
    }
}

// on the bed: the two-hole leg's outside face down (as carvera_angle.scad's
// bracket_print), so the triangles lie flat and their layers run along them
module new_bracket_print() {
    rotate([0, -90, 0]) new_bracket();
}

// stand-ins, as mounted
module camera() {
    z_back = -plate_t - back_room;
    color("#1f7a3a") translate([-board / 2, -board / 2, z_back - board_t]) cube([board, board, board_t]);
    color("#222") translate([-lens_block[0] / 2, -lens_block[1] / 2, z_back - board_t - lens_block[2]])
        cube(lens_block);
}

module laser() {
    color("#c9a227") translate([0, 0, -laser_len]) cylinder(d = laser_d, h = laser_len);
}

use <carvera_angle.scad>

function shown(c) = show == "all" || show == c;

if (part == "mount") mount();
if (part == "mount_print" || part == "print") rotate([180, 0, 0]) mount();
if (part == "bracket") translate(to_mount) new_bracket();
if (part == "bracket_print") new_bracket_print();
if (part == "assembly") {
    if (shown("mount")) mount();
    if (shown("bracket")) color("#888") translate(to_mount) new_bracket();
    if (shown("cameras")) for (s = [-1, 1]) translate([0, s * cam_y, 0]) camera();
    if (shown("laser")) laser();
}
