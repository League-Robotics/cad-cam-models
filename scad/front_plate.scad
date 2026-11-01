// Front plate: the sensor plate with the 9 g gripper frame built onto its
// front, and two ball casters hung under it behind the sensor, one each side
// of the cable.
//
// Sensor coordinates (reflectance_sensor.scad): Z up from the PCB back, the
// robot toward +Y, the sensors along the -Y edge; the floor is floor_z.
//
// Back section: gripper_plate's cells on the unit grid: the top layer
// (z 10.2..17.8) over the sensor and the two arms back into the robot, the
// columns on the brackets' holes, the feet on the PCB, and two caster seats.
//
// Front section, off that grid: servo_gripper.scad's 9 g frame, upside down
// as it is mounted today, built into the part. Its 7.6 mm top plate (the
// arms' bearing, with the tapered pivot under the spline arm and the idler's
// axle hole) is the frame's floor, g_drop below the side brackets' tops:
// just clear of the PCB, so it reaches back over the PCB's front strip
// (pocketed round the button and the sensors' clips) to just ahead of the
// side brackets. The arms, their paddles and the servo all move with it; the
// plate's top layer is cut away in front of the frame's upper wall, where the
// arms swing. The jaws are centred on x = 0; the frame's top-plate pin holes
// are filled.
//
// Casters (caster()): the LEGO EV3 ball caster, from SquareD's parametric
// model (thing:622701, CC BY-SA; models/ev3_ball_caster/): a 1 x 3 beam on
// top, its two pin holes 16 apart running through it horizontally 3.75 below
// the top, over a domed housing round the ball. Turned so the pins point
// across, in toward the cable: each caster's beam face is on its seat's
// outer face (caster_seat_x out), the pins going into the seat, and it slides
// on from outside the plate through a slot in the lid's side.
//
// Print right way up, the frame floor on the bed; the back section (columns,
// feet, caster blocks and the arms into the robot) needs support under it.

include <servo_gripper.scad>
include <lego.scad>
use <reflectance_sensor.scad>
use <gripper_plate.scad>
use <models/ev3_ball_caster/files/BallBearingSmall_1905_offset_4.scad>

servo = "9g";
jaw = "nub";
show_part = false;      // servo_gripper.scad draws nothing itself

/* [View] */
// "assembly", "part", "print", "casters", "floor", "gripper_import", "clash_*"
part = "assembly";
ext = "cube";           // the gripper's arms in the assembly
theta = 0;              // their opening, degrees
gripper_stl = "";       // for part = "gripper_import"

/* [Heights] */
can_gap = 8;            // the sensor's cans above the floor (measured)
sensor_h = 7.3;         // can + lens below the PCB, from reflectance_sensor.scad (a guess there)
pcb_t = 1.6;
floor_z = -(pcb_t + sensor_h + can_gap);   // -16.9

/* [Plate: back section, on the grid] */
grid_z0 = 2.0;
u = pd_unit;
z1 = grid_z0 + u;       // layer 0 / layer 1 boundary
layer1 = [z1 + pd_edge, z1 + u - pd_edge];   // 10.2 .. 17.8
z0 = grid_z0 + pd_edge;                      // 2.2: on the side brackets
plate_x = [-4, 4];
plate_y = [-3, 2];
arm_x = 2;
arm_len = 8;
columns = [[-4, 0], [-3, 0], [-2, 0], [2, 0], [3, 0], [4, 0], [-1, 2], [1, 2]];
feet = [[-1, -1], [1, -1]];   // over bare PCB, level with the frame floor (0.3 up) so they print on the bed
pcb_front = -28.4;
pin_depth = 9.6;        // bracket pin holes, blind from below

/* [The board's top, from models/reflectance_sensor_top_scan.stl] */
// What stands on the PCB under the frame floor (0.3 over it), measured on
// the scan: pocketed from below with board_clear all round and over.
board_clear = 0.4;
clip_xy = [for (x = [2.9, 9.2, 26.7, 33.3], s = [-1, 1]) [s * x, -20.05]];   // sensors' black clips
clip_w = 2.5;           // square
clip_h = 1.5;
button_box = [[-2.0, -26.1], [1.9, -22.8]];   // the button, as scanned (the sensor model has it 0.9 to -x)
button_h = 2.55;
lead_rows = [[-6.2, -26.0, -15.0], [5.8, -26.0, -15.0]];   // solder rows: x, y0, y1
lead_w = 0.6;
lead_h = 0.85;

/* [Gripper: front section, off the grid] */
g_drop = 1.9;           // frame floor below the side brackets' tops: 0.3 over the PCB
g_floor = z0 - g_drop;  // the frame's top-plate face (its lowest face)
frame_back = -9.4 - 0.35;  // the frame's back face, just ahead of the side brackets' clearance (off its plane)
g_mid = (spline_axis + idler_axis) / 2;
g_axis_y = frame_back - top_x[1];
arm_front = g_axis_y + upper_wall_x0;   // the plate's top layer is cut away ahead of this
// Under the arms everything is shaped about the two axles, so a paddle
// reaching down keeps the same distance from it however far it opens:
//   the frame floor is symmetric, floor_w each side; ahead of the axles its
//   outline is two arcs of floor_r about them (tangent to its sides) and the
//   straight run between;
//   outside the floor's width the plate is cut back, top to bottom, to an arc
//   of plate_arc_r about each axle, past where the arms reach as they open.
axle_x = [g_mid - idler_axis, g_mid - spline_axis];   // -12, 12
frame_x = [g_mid - top_z[1], g_mid - top_z[0]];       // the old frame's width in x
floor_w = max(abs(frame_x[0]), abs(frame_x[1]));      // half-width, the wider side
floor_r = floor_w - axle_x[1];
plate_arc_r = 30;

module floor_shape() {
    translate([-floor_w, g_axis_y]) square([2 * floor_w, frame_back - g_axis_y]);
    hull() for (x = axle_x) translate([x, g_axis_y]) circle(r = floor_r, $fn = 96);
}

/* [Casters] */
caster_w = 23.5;        // the beam's length (along y here); the housing is 24.5 across
caster_beam_t = 7.8;    // the beam's thickness (across x), pin face to back
caster_beam_h = 7.5;    // the beam's height
caster_h = 29;          // top to floor (measured on the real ones; the model's is 29.3)
caster_pin_sp = 16;
caster_pin_down = caster_beam_h / 2;   // pin row below the top, 3.75
caster_seat_x = 21;     // the seat's outer face, each side: the beam clear of the horn (to 19.8), the dome of the middle bracket (12.3)
caster_y = 16.2;        // the caster's centre along y: its dome clear of the side bracket (to 3.7)
caster_drop = 5;        // the casters set this much lower than the robot's floor line, so they bear on every robot
caster_top = floor_z + caster_h - caster_drop;
caster_pin_z = caster_top - caster_pin_down;
caster_blocks = [[-4, 1], [-3, 1], [-2, 1], [2, 1], [3, 1], [4, 1]];   // the old seats, for part = "required"
caster_block_z0 = caster_top - caster_beam_h - 0.3;   // clear of the dome below the beam
// a caster's pin hole, its counterbore on the seat face: [x, y, the way in (+-1 along x)]
caster_holes = [for (s = [-1, 1], p = [-1, 1]) [s * caster_seat_x, caster_y + p * caster_pin_sp / 2, s]];
module caster_hole(h) translate([h[0], h[1], caster_pin_z]) rotate([0, -h[2] * 90, 0]) pd_pin_hole(8, ext = 2);

$fn = 48;

// Servo coordinates (servo_gripper.scad) to sensor coordinates: servo X -> +Y
// (the jaws open toward servo -X: forward), servo Y -> -Z (upside down),
// servo Z -> -X; top plate face on g_floor, jaws centred on x = 0.
module on_servo() multmatrix([[0, 0, -1, g_mid],
                              [1, 0, 0, g_axis_y],
                              [0, -1, 0, g_floor + top_y1],
                              [0, 0, 0, 1]]) children();

arm_layer = [g_floor + top_y1 - arm_y1, g_floor + top_y1 - arm_y0];
echo(floor_z = floor_z, g_axis_y = g_axis_y, g_floor = g_floor,
     arm_layer_above_floor = [for (z = arm_layer) z - floor_z],
     caster_pin_z = caster_pin_z, caster_top = caster_top);

// ---------- the part ----------

// ---------- required surfaces ----------
//
// Only what mates with something keeps its shape: the horns (the two beams
// into the robot, with their pin holes); the columns and feet standing on the
// sensor's brackets and PCB, with the pins down into the brackets; the caster
// blocks with their pin holes; and the gripper's frame (the floor the arms
// bear on, its pivot and the idler's axle, the idler's upper bearing, the
// legs the servo's tabs screw to). Everything between them is lofted.

arm_end_y = arm_len * u - u / 2 - pd_edge;      // the horns' far ends, 59.8
horn_y0 = (plate_y[1] + 1) * u - u / 2 + pd_edge;   // the horns' near ends, 20.2
horn_holes = [for (s = [-1, 1], j = [plate_y[1] + 1 : arm_len - 1]) [s * arm_x * u, j * u]];
// pins down into the side brackets only: the jack covers the top of the middle
// bracket's two holes, so the middle columns just bear flat on its top
bracket_holes = [for (c = [[-4, 0], [-2, 0], [2, 0], [4, 0]]) [c[0] * u, c[1] * u, z0]];
middle_columns = [[-1, 2], [1, 2]];
side_columns = [for (c = columns) if (abs(c[0]) > 1) c];

module horns() for (s = [-1, 1]) {
    aw = u / 2 - pd_edge;
    translate([0, 0, layer1[0]]) linear_extrude(layer1[1] - layer1[0]) hull() {
        translate([s * arm_x * u - aw, horn_y0]) square([2 * aw, 1]);
        translate([s * arm_x * u, arm_end_y - aw]) circle(r = aw, $fn = 48);
    }
}

// The columns, feet and caster blocks are part of the blended body (their
// mating faces flat there); the rest is exact geometry here.
module mates() {
    horns();
    intersection() {
        union() {
            translate([0, 0, g_floor]) linear_extrude(plate_t) floor_shape();
            on_servo() frame_trimmed();
            frame_plugs();
            head_fill();
        }
        frame_envelope();
    }
}

// The frame's outside, rounded: everything of the frame stays inside this, so
// only its outer edges and corners change; the faces the arms bear on, the
// pivot, the axle, the servo's pocket and seat and the screws' holes are all
// inside it. The floor's top edges are rolled by floor_edge_r (its bottom is on the bed); the block
// over it (the back wall and the head the servo screws to), symmetric to the
// floor's width, by frame_r at its corners and top edges. The blend's
// stand-ins for the frame (tools/front_plate_body.py) use the same radius.
floor_edge_r = 1.5;
frame_r = 2;
frame_head_top = g_floor + top_y1 - leg_y0;          // the servo tabs' seat, 24.4
module frame_envelope() {
    rounded_slab(g_floor, g_floor + plate_t, floor_edge_r) floor_shape();   // bottom edge crisp: it is on the bed
    rounded_slab(g_floor + plate_t - 0.01, frame_head_top, frame_r)
        offset(r = frame_r) offset(delta = -frame_r)
            translate([-floor_w, g_axis_y - tab_x]) square([2 * floor_w, frame_back - g_axis_y + tab_x]);
}

// A slab of a 2D outline from z0 to z1, its top edges (and with both, its
// bottom edges) rounded over by r.
module rounded_slab(z0, z1, r, n = 14, both = false) {
    b = both ? r : 0;
    translate([0, 0, z0 + b]) linear_extrude(z1 - r - z0 - b + 0.01) children();
    for (i = [1 : n]) {
        inset = r - sqrt(r * r - pow(r * i / n, 2));
        translate([0, 0, z1 - r + r * (i - 1) / n]) linear_extrude(r / n + 0.01) offset(r = -inset) children();
        if (both) translate([0, 0, z0 + r - r * i / n]) linear_extrude(r / n + 0.01) offset(r = -inset) children();
    }
}

// ---------- the connecting body ----------
//
// Everything between the mating surfaces is one smooth blended mesh, made by
// tools/front_plate_body.py (`uv run tools/front_plate_body.py`): soft boxes
// over the frame's back wall, the sensor's middle and feet, the side columns
// and caster blocks, the middle bracket's columns and the horns' roots,
// melted together by a smooth union of their distance fields, so every join
// is a fillet and every change of height an S-curve; with a rounded U taken
// out round the cable jack, 1 mm off it. Re-run the script after changing
// any of the surfaces it wraps.
module body() import("models/front_plate_body.stl", convexity = 8);

// The frame's head reaches floor_w out on the idler side but stops at the
// spline arm's leg (head_fill_x) on the other, which left a notch beside the
// lid; filled to floor_w so the head is symmetric (clear of the arms at every
// angle, the servo and its clearance), from the leg's underside up.
head_fill_x = -17.9;
head_fill_z0 = 16.3;
module head_fill() translate([-floor_w - 1, g_axis_y - tab_x - 1, head_fill_z0])
    cube([floor_w + 1 + head_fill_x + 0.5, frame_back - g_axis_y + tab_x + 1, frame_head_top - head_fill_z0]);

// the frame's top-plate pin holes, refilled (not over the axes)
module frame_plugs() on_servo()
    for (x = [0 : 8 : 16], z = top_holes_z)
        if (x != 0 || (abs(z - spline_axis) > 1 && abs(z - idler_axis) > 1))
            translate([x, top_y0, z]) rotate([-90, 0, 0]) cylinder(d = pin_cb_d + 0.4, h = plate_t);

// The 9 g frame as used here: the servo is held by the screws through its
// tabs, so the frame's LEGO wall down the servo's back (the backstop, below
// the tab legs) is cut off, and the pin holes left in the wall between the
// legs are filled.
module frame_trimmed() {
    intersection() {
        frame();
        box([-50, 50], [leg_y0, 100], [-50, 50]);
    }
    // stays inside the wall's outer face; reaches 1.5 into the tab leg, where the
    // holes ran 1 mm on (servo_clearance is cut after)
    for (z = lego_z) translate([wall_x[0] - 1.5, lego_y[2], z]) rotate([0, 90, 0])
        cylinder(d = pin_cb_d + 0.2, h = wall_x[1] - wall_x[0] + 1.49);
}

module front_plate() {
    difference() {
        union() {
            mates();
            difference() {
                body();
                // where the arms swing, ahead of the frame's upper wall: the arm slot's
                // height, up to the top of the frame's own slope over the spline arm
                slot = [g_floor + top_y1 - arm_y1 - clr, g_floor + top_y1 - ledge_y[1] + leg_drop + 0.2];
                translate([-60, -100, slot[0]]) cube([120, 100 + arm_front, slot[1] - slot[0]]);
            }
        }
        keep_out();
        board_relief();
        on_servo() servo_clearance();
        // the servo's gear head (spline boss and lobe), which the old frame left open round
        on_servo() plate(body[1] - 0.5, spline_base - body[1] + 0.8) hull() {
            translate([0, -spline_axis]) circle(r = 5.7 + 0.35);
            translate([0, -0.35]) circle(r = 2.8 + 0.35);
        }
        on_servo() for (h = tab_holes) translate([h[0], leg_y0 - 1, h[1]]) rotate([-90, 0, 0])
            cylinder(d = tab_pilot, h = tab_pilot_h);
        on_servo() translate([0, min(axle_y0, ledge_y[0]) - 1, idler_axis]) rotate([-90, 0, 0]) cylinder(d = axle_hole, h = 100);
        // the horns' pin holes, through
        for (h = horn_holes) translate([h[0], h[1], layer1[1]]) mirror([0, 0, 1]) pd_pin_hole(layer1[1] - layer1[0], ext = 3);
        // pins down into the sensor's brackets, blind from below
        for (h = bracket_holes) translate([h[0], h[1], h[2]]) pd_pin_hole(pin_depth, ext = 0.5);
        // casters: their beams' path in from the side (exact), pin holes into the seats
        // (the beam and the slab under it, the caster's whole height)
        for (s = [-1, 1]) translate([s > 0 ? caster_seat_x : -60, caster_y - caster_w / 2 - 0.3, caster_top - caster_h - 1])
            cube([60 - caster_seat_x, caster_w + 0.6, caster_h + 1.3]);
        for (h = caster_holes) caster_hole(h);
    }
}

// Pockets over what stands on the board's top (clips, button, solder rows).
module board_relief() {
    c = board_clear;
    for (p = clip_xy) translate([p[0] - clip_w / 2 - c, p[1] - clip_w / 2 - c, -1]) cube([clip_w + 2 * c, clip_w + 2 * c, 1 + clip_h + c]);
    translate([button_box[0][0] - c, button_box[0][1] - c, -1])
        cube([button_box[1][0] - button_box[0][0] + 2 * c, button_box[1][1] - button_box[0][1] + 2 * c, 1 + button_h + c]);
    for (r = lead_rows) translate([r[0] - lead_w / 2 - c, r[1] - c, -1]) cube([lead_w + 2 * c, r[2] - r[1] + 2 * c, 1 + lead_h + c]);
}

// The required surfaces alone, holes cut, for comparison.
module required_only() difference() {
    union() {
        mates();
        layer(side_columns, z0, layer1[0] + 0.1);
        layer(middle_columns, z0, layer1[0] + 0.1);
        layer(feet, 0, layer1[0] + 0.1);
        layer(caster_blocks, caster_block_z0, layer1[0] + 0.1);
    }
    keep_out();
    board_relief();
    on_servo() servo_clearance();
    for (h = horn_holes) translate([h[0], h[1], layer1[1]]) mirror([0, 0, 1]) pd_pin_hole(layer1[1] - layer1[0], ext = 3);
    for (h = bracket_holes) translate([h[0], h[1], h[2]]) pd_pin_hole(pin_depth, ext = 0.5);
    for (h = caster_holes) caster_hole(h);
}

// The control surfaces alone, in place, holes cut: the gripper frame (the
// floor the arms bear on, its pivot and idler axle, the head the servo's tabs
// screw to), the horns, the sensor's pads with their pin holes, and the caster
// seats (the pin depth in from each seat face, the beam's length, bed to the
// caster's top). No feet (they stand 0.3 off the PCB) and no body.
// The sensor's attachment pads: the columns standing on the side brackets
// (over both pins) and on the middle bracket (flat, no pins), their bottoms
// the bracket tops, each pin_depth + pad_cap tall, in plan as the body's
// posts (side_pads).
pad_cap = 1.2;          // over the blind pin holes' ends
side_pads = [[[12.2, 36.4], [-3.8, 3.8], z0], [[4.2, 11.8], [12.2, 19.8], 5.15]];
module sensor_pads() for (p = side_pads, s = [-1, 1]) {
    x = s > 0 ? p[0] : [-p[0][1], -p[0][0]];
    translate([0, 0, p[2]]) linear_extrude(pin_depth + pad_cap)
        offset(r = 2) offset(delta = -2) translate([x[0], p[1][0]]) square([x[1] - x[0], p[1][1] - p[1][0]]);
}

module control_surfaces() difference() {
    union() {
        mates();
        sensor_pads();
        for (s = [-1, 1]) translate([s > 0 ? caster_seat_x - 8 : -caster_seat_x, caster_y - caster_w / 2, g_floor])
            cube([8, caster_w, caster_top - g_floor]);
    }
    keep_out();
    board_relief();
    on_servo() servo_clearance();
    on_servo() plate(body[1] - 0.5, spline_base - body[1] + 0.8) hull() {
        translate([0, -spline_axis]) circle(r = 5.7 + 0.35);
        translate([0, -0.35]) circle(r = 2.8 + 0.35);
    }
    on_servo() for (h = tab_holes) translate([h[0], leg_y0 - 1, h[1]]) rotate([-90, 0, 0])
        cylinder(d = tab_pilot, h = tab_pilot_h);
    on_servo() translate([0, min(axle_y0, ledge_y[0]) - 1, idler_axis]) rotate([-90, 0, 0]) cylinder(d = axle_hole, h = 100);
    for (h = horn_holes) translate([h[0], h[1], layer1[1]]) mirror([0, 0, 1]) pd_pin_hole(layer1[1] - layer1[0], ext = 3);
    for (h = bracket_holes) translate([h[0], h[1], h[2]]) pd_pin_hole(pin_depth, ext = 0.5);
    for (h = caster_holes) caster_hole(h);
}

// ---------- reference models ----------

// The EV3 caster as modelled by SquareD (its top at z 24.775, the ball's
// centre at z 5), turned so its beam face is at y = 0 with the pins pointing
// -y, top at z = 0, centred on x; with its 19 mm ball and the two pins.
module caster() {
    top = 24.775;
    translate([0, caster_beam_t / 2, -top]) {
        color("#4a4f55") drawBallBearing();
        color("silver") translate([0, 0, 5]) sphere(d = 19.05, $fn = 48);
    }
    color("#2a2a2a") for (p = [-1, 1]) translate([p * caster_pin_sp / 2, 0, -caster_pin_down]) rotate([90, 0, 0]) {
        cylinder(d = 4.8, h = 7.8);
        translate([0, 0, -0.4]) cylinder(d = 6.2, h = 0.8);
    }
}

// pins pointing in toward the cable, body outward; out = how far out from seated (for the way in)
module casters(out = 0) for (s = [-1, 1]) translate([s * (caster_seat_x + out), caster_y, caster_top]) rotate([0, 0, -s * 90]) caster();

module gripper_ref() on_servo() {
    arms(theta);
    axle();
    color("dimgray") servo_model();
}

if (part == "assembly") {
    reflectance_sensor();
    color("mediumseagreen") front_plate();
    casters();
    gripper_ref();
    %translate([-70, -150, floor_z - 0.5]) cube([140, 230, 0.5]);
} else if (part == "part") front_plate();
else if (part == "print") translate([0, 0, -g_floor]) front_plate();
else if (part == "casters") casters();
else if (part == "required") required_only();
else if (part == "control") control_surfaces();
else if (part == "control_print") translate([0, 0, -g_floor]) control_surfaces();
else if (part == "floor") translate([-70, -150, floor_z - 0.5]) cube([140, 230, 0.5]);
// a component exported by servo_gripper.scad (servo = "9g", its assembly
// orientation: rotate([90, 0, 0]) of servo coordinates), placed; for tools/make_views.sh
else if (part == "gripper_import") on_servo() rotate([-90, 0, 0]) import(gripper_stl);
// clash checks: each should come out empty, or only touching faces
else if (part == "clash_sensor") intersection() { front_plate(); reflectance_sensor(); }
else if (part == "clash_casters") intersection() {
    casters();
    union() { front_plate(); reflectance_sensor(); }
}
else if (part == "clash_arms") intersection() {
    for (t = [-6, 10, 25, 40, 55, 66]) on_servo() arms(t);
    union() { front_plate(); reflectance_sensor(); casters(); translate([-70, -150, floor_z - 5]) cube([140, 230, 5]); }
}
else if (part == "clash_servo") intersection() {
    on_servo() servo_model();
    union() { front_plate(); reflectance_sensor(); }
}
