// Two Arducam USB cameras and a line laser on the Carvera toolhead (first
// draft 2026-11-03). It hangs under the camera bracket's cap
// (carvera_angle.scad, part = "bracket") on the one 1/4-20 screw that comes
// down through the cap's hole into a heat-set insert here. Front to back:
// camera, laser, camera, all facing down; the laser sits on the screw's axis.
// The laser is a brass 9 mm module in a bore: turn it to set the line, then
// lock it with a set screw from the side.
//
// Cameras: Arducam 38 x 38 USB boards (B0332, B0385, B0200 ...). Arducam lists
// two hole patterns on them, 34 x 34 (outer, M2.5) and 28 x 28 (inner); the
// user's own mount (Arducam Mount 28mm.stl) uses the 28 pattern in a 39 x 39
// pocket with a 24 x 4.6 cable slot 14.65 off the board's centre, and the
// connector on the back wants about 8 of room. Each board hangs face down
// on four standoffs on the 28 pattern (the user: the posts in his mount are
// the right spacing, 2026-11-03), back up, cable up through the slot.
//
// Datum: the screw's axis is z, z = 0 the cap's underside (the bracket's own
// z = 0). +y runs to the back of the machine, so the front camera is at -y.
// The cap nests in a square recess sunk into the flat top (2026-11-03; it was
// a raised rim, which left the part standing on that rim to print), so the
// top is at z = socket_h, the part hangs below it, and the part can't turn
// about the one screw.

/* [Show] */
// "mount" (as mounted), "print" (on the bed), "assembly" (with the bracket, cameras, laser)
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
laser_grip = 16;       // length of the bore that holds it; the rest sticks out below
boss_d = 20;           // the round boss round the laser
wire_d = 4;            // channel for the laser's wires, out the -x side
set_insert_d = 4.0;    // M3 heat-set insert hole for the set screw
set_insert_len = 5;    // M3 insert length, our pick

/* [Mount] */
plate_t = 4;           // top plate
wall = 2;              // camera pocket walls
gap = 30;              // between the two camera pockets (holds the insert and the laser)
standoff_d = 5;        // the slot clips 0.5 off each one's inner side
standoff_hole_d = 2.2; // M2.5 screws threaded into the plastic
ins_d = 6.35;          // heat-set insert hole: the insert's smooth end, measured by the user
ins_len = 13.5;        // 1/2 in insert + room
cap = 25.4;            // the bracket's cap
socket_clear = 0.2;    // per side
socket_h = 3;          // recess depth into the top face

eps = 0.01;

pocket = board + 2 * board_clear;         // 39
pod = pocket + 2 * wall;                  // 43, one camera pod outside
pod_h = plate_t + back_room + board_t;    // pod walls cover the board's edge
cam_y = gap / 2 + pod / 2;                // camera centres at +-cam_y
total_len = gap + 2 * pod;
laser_top = -(ins_len + 1.5 + wire_d);    // the bore starts below the insert and the wire channel
bore_d = laser_d + 2 * laser_clear;
boss_bottom = laser_top - laser_grip;
socket_in = cap + 2 * socket_clear;

echo(total_len = total_len, baseline = 2 * cam_y, pod = pod, pod_h = pod_h, boss_bottom = boss_bottom,
     laser_sticks_out = laser_len - laser_grip);
assert(boss_bottom < socket_h - pod_h, "the boss must reach below the camera pods");
assert(ins_len + 1.5 <= -(laser_top + wire_d - 0.5), "the insert runs into the wire channel");
assert(socket_in < gap && socket_in < pod, "the recess runs into the camera pockets or out the sides");
assert(ins_len + socket_h < pod_h, "the insert runs out the block's underside");
assert(slot_off + slot[1] / 2 < pocket / 2, "the cable slot runs into the wall");

// one camera pod, centred on x = y = 0, hanging down from z = 0. The slot
// side goes to +y; the pod is turned for the front camera.
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
            translate([0, 0, socket_h]) {
                for (s = [-1, 1]) translate([0, s * cam_y, 0]) rotate([0, 0, s > 0 ? 0 : 180]) pod();
                // the block between the pods: the cap recess, the insert and the top of the laser
                translate([-pod / 2, -gap / 2 - eps, -pod_h]) cube([pod, gap + 2 * eps, pod_h]);
            }
            translate([0, 0, boss_bottom]) cylinder(d = boss_d, h = socket_h - boss_bottom - pod_h + eps);
        }
        // recess for the cap
        translate([-socket_in / 2, -socket_in / 2, 0]) cube([socket_in, socket_in, socket_h + eps]);
        // 1/4-20 insert from the top
        translate([0, 0, -ins_len]) cylinder(d = ins_d, h = ins_len + eps);
        // laser bore from the bottom, through to the wire channel
        translate([0, 0, boss_bottom - eps]) cylinder(d = bore_d, h = laser_top - boss_bottom + eps);
        // wires out the -x side
        translate([0, 0, laser_top + wire_d / 2 - 0.5]) rotate([0, -90, 0]) cylinder(d = wire_d, h = pod);
        // set screw insert into the bore from -x, halfway down the grip
        translate([0, 0, boss_bottom + laser_grip / 2]) rotate([0, -90, 0])
            cylinder(d = set_insert_d, h = boss_d);
    }
}

// stand-ins, as mounted
module camera() {
    z_back = socket_h - plate_t - back_room;
    color("#1f7a3a") translate([-board / 2, -board / 2, z_back - board_t]) cube([board, board, board_t]);
    color("#222") translate([-lens_block[0] / 2, -lens_block[1] / 2, z_back - board_t - lens_block[2]])
        cube(lens_block);
}

module laser() {
    color("#c9a227") translate([0, 0, laser_top - laser_len + eps]) cylinder(d = laser_d, h = laser_len);
}

use <carvera_angle.scad>
module bracket_on_cap() {
    // the bracket's cap centre is at (12.7, 12.7); its front (y = 0) is our -y
    translate([-cap / 2, -cap / 2, 0]) bracket();
}

function shown(c) = show == "all" || show == c;

if (part == "mount") mount();
if (part == "print") rotate([180, 0, 0]) translate([0, 0, -socket_h]) mount();
if (part == "assembly") {
    if (shown("mount")) mount();
    if (shown("bracket")) color("#888") bracket_on_cap();
    if (shown("cameras")) for (s = [-1, 1]) translate([0, s * cam_y, 0]) camera();
    if (shown("laser")) laser();
}
