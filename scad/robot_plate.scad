// Robot plate: the bought 11 x 19 Technic panel plate (the shape of LEGO
// 39369, one unit thick) with the hole we cut in it on the Carvera for the
// reflectance sensor's jack. The plate is modelled from the LDraw part: pin
// holes down through every cell, and round the outside edge every other cell
// has a horizontal hole in from the face instead (the corners and the odd
// cells keep the vertical hole, the even cells get the horizontal one: 9 along
// each long edge, 5 along each short edge). The underside's honeycomb is
// not modelled (solid slab).
//
// Robot coordinates: X across the plate (0 on the centre column, 11 columns
// at -40..40), Y back from the front edge (19 rows at 4..148), Z up from the
// bottom face. Cells are numbered from the front-left corner as the user
// counts them, holding the plate with the 19 side up and down: column c =
// 1..11 left to right, row r = 1..19 top (front) to bottom.
//
// Holes (`hole`): "cans" is for the sensor mounted the other way up, on top
// of the bottom plate standing on its brackets (pins up from under the
// plate): no jack hole, just a pocket through the plate for each of the four
// sensor cans, which hang 7 below the PCB. The brackets pin at row can_row
// (5), which puts the cans one row behind the front edge (centred at y 15.55,
// the pockets 9.45..21.65: row 2 and 5.7 into row 3), so row 1's vertical and
// horizontal holes stay free. "3x3" is the plate we already cut: 3 columns x 3 rows,
// first cut cell at column 5, row 6 (so columns 5-7, rows 6-8: centred across
// the plate). "3x4" is the same hole one row taller toward the front (rows
// 5-8, the sensor's PCB edge at the plate's front edge). "3x3_9" is the one
// the user cuts since 2026-10-30: 3x3 at rows 9-11, walked back from 5-8
// over four plates. The hole is cut exactly on the cell edges (the existing
// job ran 1.65 past the front cell edge and nicked the row above; front_ext
// is 0 now).
//
// part: "plate" (robot coordinates), "cam" (the plate as it sits on the
// Carvera: its length along X from the front edge, across along Y, the top
// face at Z = 0, as tools/plate_gcode.py and the existing CAM/RobotPlate job),
// "assembly" (plate with the reflectance sensor under it, its side brackets
// on the plate's bottom face), "cut" (the hole alone, 2D), or one component
// of the assembly in place: "sensor_pcb", "sensor_brackets",
// "sensor_back_parts", "sensor_sensors".

include <lego.scad>
use <reflectance_sensor.scad>

/* [View] */
part = "plate";
// "none", "3x3", "3x4", "3x3_9", "cans"
hole = "3x3_9";
// row of the sensor's side-bracket holes in the assembly: 5 under the 3x3
// plate, 4 under the 3x4, 8 under the 3x3_9 (its jack and middle bracket up
// through the hole), can_row on top of the "cans" plate
sensor_row = hole == "3x3" ? 5 : hole == "cans" ? 5 : hole == "3x3_9" ? 8 : 4;
// "under" the plate (brackets' tops on its bottom face) or on "top" of it
// (brackets standing on its top face, cans down in their pockets)
sensor_mount = hole == "cans" ? "top" : "under";

/* [Plate] */
cols = 11;
rows = 19;
u = technic_beam_hole_spacing;      // 8
plate_t = technic_height_in_mm;     // 7.8 (the bought plates measure 7.6; the CAM stock)
edge_hole_depth = u;                // horizontal edge holes: through the edge cell

/* [Hole] */
hole_cols = [5, 7];
function hole_rows(h) = h == "3x3" ? [6, 8] : h == "3x4" ? [5, 8] : h == "3x3_9" ? [9, 11] : [0, -1];
front_ext = 0;       // past the front cell edge: 0, cut on the cell edges (the existing job had 1.65 and nicked the row above)

/* [Can pockets (hole = "cans")] */
// the sensor's cans, from reflectance_sensor.scad: centres x, their y from
// the side-bracket hole row (on the solder-pad columns of the top scan,
// 2026-10-29), body x by y (TCRT5000's size, from a photo: not measured, so
// the pockets get a generous clearance)
can_x = [-30, -6, 6, 30];
can_y_off = -20.45;
can_body = [5.8, 10.2];
can_clear = 1.0;     // per side
can_front_ext = 1.5; // the pockets' front edge further forward: the cans did not clear it on the first plate (2026-10-30)
can_back_ext = 0.5;  // and the back edge further back (2026-10-30)
can_row = 5;         // the side brackets' hole row when the sensor stands on the plate

$fn = 24;

function col_x(c) = (c - (cols + 1) / 2) * u;
function row_y(r) = (r - 0.5) * u;
// an edge cell with the horizontal hole: even position along its edge
function h_cell(c, r) = (r == 1 || r == rows) ? (c % 2 == 0) : (c == 1 || c == cols) ? (r % 2 == 0) : false;

// the hole's extent in robot coordinates: [[x0, x1], [y0, y1]]
function hole_box(h = hole) = [[col_x(hole_cols[0]) - u / 2, col_x(hole_cols[1]) + u / 2],
                       [row_y(hole_rows(h)[0]) - u / 2 - front_ext, row_y(hole_rows(h)[1]) + u / 2]];

module cut2d(h = hole) {
    if (h == "3x3" || h == "3x4" || h == "3x3_9") let(b = hole_box(h))
        translate([b[0][0], b[1][0]]) square([b[0][1] - b[0][0], b[1][1] - b[1][0]]);
    if (h == "cans") {
        // the middle two cans' pockets run together: the 4.2 web between them did not survive the first cut (2026-10-30)
        for (x = [can_x[0], can_x[3]]) can_pocket(x);
        hull() for (x = [can_x[1], can_x[2]]) can_pocket(x);
    }
}
module can_pocket(x) {
    translate([x, row_y(can_row) + can_y_off + (can_back_ext - can_front_ext) / 2]) square([can_body[0] + 2 * can_clear, can_body[1] + 2 * can_clear + can_front_ext + can_back_ext], center = true);
}

module edge_holes() {
    for (c = [1 : cols], r = [1 : rows]) if (h_cell(c, r)) {
        x = col_x(c); y = row_y(r);
        // from the face the cell sits on, pointing in
        if (r == 1) translate([x, 0, plate_t / 2]) rotate([-90, 0, 0]) technic_blind_pin_hole(edge_hole_depth);
        else if (r == rows) translate([x, rows * u, plate_t / 2]) rotate([90, 0, 0]) technic_blind_pin_hole(edge_hole_depth);
        else if (c == 1) translate([-cols * u / 2, y, plate_t / 2]) rotate([0, 90, 0]) technic_blind_pin_hole(edge_hole_depth);
        else translate([cols * u / 2, y, plate_t / 2]) rotate([0, -90, 0]) technic_blind_pin_hole(edge_hole_depth);
    }
}

module robot_plate(h = hole) {
    difference() {
        translate([-cols * u / 2, 0, 0]) cube([cols * u, rows * u, plate_t]);
        for (c = [1 : cols], r = [1 : rows]) if (!h_cell(c, r))
            translate([col_x(c), row_y(r), 0]) technic_pin_hole_fast(1);
        edge_holes();
        translate([0, 0, -1]) linear_extrude(plate_t + 2) cut2d(h);
    }
}

// Robot coordinates to the Carvera job's: X along the plate from the front
// edge, Y across (0 at the left edge), the top face at Z = 0.
module on_cam() multmatrix([[0, 1, 0, 0], [-1, 0, 0, cols * u / 2], [0, 0, 1, -plate_t], [0, 0, 0, 1]]) children();

// The sensor under the plate: its side brackets' tops (2.2 over the PCB
// back) on the plate's bottom face, pins up into the plate; or on top of it,
// the brackets' bottoms (4.2 below the PCB front, plus the PCB) standing on
// the plate's top face, pins up from under the plate. The side brackets'
// hole row at row sensor_row either way.
side_br_top = 2.2;
side_br_below = 8 - side_br_top - 1.6;   // as reflectance_sensor.scad (a guess there)
pcb_t = 1.6;
module on_sensor() translate([0, row_y(sensor_row), sensor_mount == "top" ? plate_t + side_br_below + pcb_t : -side_br_top]) children();

if (part == "plate") robot_plate();
else if (part == "cam") on_cam() robot_plate();
else if (part == "cut") cut2d();
else if (part == "assembly") { color("gold") robot_plate(); on_sensor() reflectance_sensor(); }
else if (part == "sensor_pcb") on_sensor() pcb();
else if (part == "sensor_brackets") on_sensor() brackets();
else if (part == "sensor_back_parts") on_sensor() back_parts();
else if (part == "sensor_sensors") on_sensor() sensors();

echo(hole = hole, hole_box = hole == "cans" ? "cans" : hole_box(), sensor_row = sensor_row, sensor_mount = sensor_mount);
