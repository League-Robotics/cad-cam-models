// Gripper plate: a flat plate over the reflectance sensor for mounting a
// gripper, with two arms that reach back to pin into the robot. Built from
// Part Designer cells (lego.scad): 8 mm cells with pd_edge margins on outside
// faces and printed pin holes.
//
// Sensor coordinates (reflectance_sensor.scad): Z up from the PCB back, the
// robot toward +Y. The cell grid is centred on the sensor's holes, so cells
// at (±16, 0), (±32, 0) and (±8, 16) sit right over the six bracket holes,
// with pins straight down into them.
//
// Layers: layer 1 (z 10..18) is the plate and the arms, top at 17.8, above
// the RJ11 plug (14.9). Layer 0 (z 2..10) has the columns that stand on the
// side brackets (2.2), the middle columns trimmed down to the middle bracket
// (5.15), and feet that reach on down to the PCB.
// Print upside down: the plate's top face on the bed, so the pin-hole tapers
// (bed face) are on top.

include <lego.scad>
use <reflectance_sensor.scad>

/* [View] */
// "assembly" (plate on the sensor), "plate", "print" (plate, upside down)
part = "assembly";
explode = 0;          // lift the plate off the sensor in the assembly

/* [Layout, in grid units of 8 mm] */
grid_z0 = 2.0;        // bottom of layer 0: its outside face (+pd_edge) rests on the side brackets
plate_x = [-4, 4];    // plate columns (x = 8 i)
plate_y = [-3, 2];    // plate rows: front edge of the board to over the middle bracket
arm_x = 2;            // arms on the side brackets' inner holes (x = ±16); 4 = outer holes
arm_len = 8;          // holes per arm, starting at the bracket hole
columns = [[-4, 0], [-3, 0], [-2, 0], [2, 0], [3, 0], [4, 0], [-1, 2], [1, 2]];
feet = [[-3, -2], [3, -2], [-1, -1], [1, -1]];   // stand on bare PCB

/* [Clearance] */
clear = 0.3;          // around the sensor's brackets, jack and button
plug_clear = 0.6;     // around the RJ11 jack and plug
// pocket over the clips on the PCB back that hold the outer sensors' barrels
// (~1.5 tall): +x corner [x, y] min/max, mirrored to -x; height incl. 0.5 clearance
clip_pocket = [[24, -24], [32, -16]];
clip_h = 2.0;

$fn = 64;
u = pd_unit;

function cells() = concat(
    [for (i = [plate_x[0] : plate_x[1]], j = [plate_y[0] : plate_y[1]]) [i, j, 1]],
    [for (s = [-1, 1], j = [plate_y[1] + 1 : arm_len - 1]) [s * arm_x, j, 1]],
    [for (c = columns) [c[0], c[1], 0]],
    [for (f = feet) [f[0], f[1], 0]]);

// A layer of cells: their union in plan, pulled in by pd_edge all round (Part
// Designer's edge margin), extruded between z0 and z1.
module layer(ij, z0, z1) {
    translate([0, 0, z0]) linear_extrude(z1 - z0)
        offset(delta = -pd_edge) union() for (c = ij) translate([c[0] * u - u / 2, c[1] * u - u / 2]) square(u + 0.001);
}

// What the plate must clear: the brackets, the jack and plug (with a slot
// out the back for the cable), the button.
module keep_out() {
    // brackets: clear at the sides, but the columns sit right on their tops
    for (s = [-1, 1]) translate([s * 24 - 12 - clear, -9.4 - clear, -10]) cube([24 + 2 * clear, 12.8 + 2 * clear, 12.2]);
    // middle bracket; runs on past its back edge so the columns over it don't
    // leave a sliver hanging down behind it
    translate([-12 - clear, 5.6 - clear, -10]) cube([24 + 2 * clear, 13.8 + clear + 10, 15.15]);
    translate([-5 - plug_clear, 5.2 - plug_clear, -10]) cube([10.4 + 2 * plug_clear, 40, 40]);
    translate([-0.9 - 1.8 - clear, -25 - 1.8 - clear, -10]) cube([3.6 + 2 * clear, 3.6 + 2 * clear, 12.4 + clear]);
    // the black clips holding the outer sensors' barrels, ~1.5 tall, under
    // the outer feet's front corners
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([clip_pocket[0][0], clip_pocket[0][1], -10])
            cube([clip_pocket[1][0] - clip_pocket[0][0], clip_pocket[1][1] - clip_pocket[0][1], 10 + clip_h]);
}

module plate() {
    cs = cells();
    top = [for (c = cs) if (c[2] == 1) [c[0], c[1]]];
    low = [for (c = cs) if (c[2] == 0) [c[0], c[1]]];
    z1 = grid_z0 + u;   // layer 0 / layer 1 boundary
    difference() {
        union() {
            layer(top, z1 + pd_edge, z1 + u - pd_edge);
            layer(columns, grid_z0 + pd_edge, z1 + pd_edge + 0.1);
            layer(feet, 0, z1 + pd_edge + 0.1);
        }
        keep_out();
        // pin holes down every cell, bed (tapered) face up: the plate prints upside down
        for (xy = top) {
            z0 = len([for (f = feet) if (f == xy) 1]) > 0 ? 0
                : len([for (c = low) if (c == xy) 1]) > 0 ? grid_z0 + pd_edge : z1 + pd_edge;
            h = z1 + u - pd_edge - z0;
            translate([xy[0] * u, xy[1] * u, z0 + h]) mirror([0, 0, 1]) pd_pin_hole(h, ext = 3);
        }
    }
}

if (part == "assembly") {
    reflectance_sensor();
    color("mediumpurple") translate([0, 0, explode]) plate();
} else if (part == "plate") plate();
else if (part == "print") rotate([180, 0, 0]) plate();
