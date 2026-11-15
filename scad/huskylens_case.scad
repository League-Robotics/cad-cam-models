// FIRST DRAFT (2026-11-14): a LEGO tray for the DFRobot HuskyLens (SEN0305).
//
// The user: drop the HuskyLens in, screw it down through the two holes in its
// bottom tab, leave the USB and UART ports and the buttons on the top free,
// the camera looks out of the back, and the screen and the camera sides stay
// clear, so the pin holes go on a part that reaches out past the board.
//
// One print. The board drops in screen up between two columns (5 x 1 pin
// holes each, front to back) and lies camera down on two ledges and the neck
// behind its tab, where two M3 screws hold it. Below the tab, between the two
// cables, a 3 x 2 bar carries the bottom holes: four from underneath, to stand
// it on a plate, and one front to back (the bar's cells alternate, its holes
// would cross). The floor is a thin plate behind the board with a notch for
// the camera and stops below the two buttons; the columns stand beside them.
//
// Coordinates: as you look at the screen with the tab down, x to the right,
// y up, origin on the board's centre line (y = 0 is the STEP model's, 4 below
// the middle of the board's main rectangle), z = 0 the case's back face (the
// bed), z up towards you. The STEP model (scad/models/huskylens, from GrabCAD,
// someone's drawing, not checked against the real board) is turned over into
// this frame by board_place().
// Prints as modelled, back face down: pocket open upward, no supports.

include <lego.scad>

/* [Show] */
// "case", "print" (the same, on the bed), "assembly" (with `show`), "clash"
part = "assembly";
// assembly: "all", or one of "case", "board", "parts", "screws"
show = "all";
$fn = 64;
eps = 0.01;

/* [From the STEP model, not yet checked on the real board] */
board_w = 52;             // across
board_top = 22.25;        // y of the top edge
board_bot = -14.25;       // y of the bottom edge, either side of the tab
tab_half = 11;            // the tab's half width
tab_bot = -22.25;         // y of the tab's end
screw_x = 7.4;            // the tab's two M3 holes, +-x
screw_y = -18.65;
pcb_t = 1.0;              // board thickness
screen_t = 3.5;           // the screen stands this far off the board's front
back_h = 5.62;            // tallest thing behind the board under the floor (the UART socket), off the board
cam = [0, 10.27];         // the lens
cam_half = 4.25;          // half the camera's square holder
cam_h = 5.0;              // camera off the board's back
usb_x = [-24.09, -16.32]; // micro USB, opens downward
uart_x = [12.64, 24.54];  // 4-pin UART socket, opens downward
sd_y = [-2.62, 8.78];     // microSD slot on the right edge (x = +26)
learn = [15.71, 23.21, 15.24];   // learn button: x0, x1, its lowest y (it stands 7.38 off the board's back)
dial = [-24.83, -10.92, 13.45];  // function dial: x0, x1, lowest y

/* [Our picks] */
unit = pd_unit;           // 8
clear = 0.3;              // board to pocket wall, per side
floor_t = 1.6;            // the plate behind the board
back_gap = 0.38;          // floor to the UART socket
depth_cells = 2;          // front to back
col_x = 32;               // the columns' hole line, +-x: cells 28 ... 36
col_rows = [-12, -4, 4, 12, 20];   // their holes' y: 5 cells, -16 ... 24 (the user, 2026-11-14: "5 units high"; 4 at first, stopping below the buttons); the top cell stands beside the buttons, 1.6 over the board's top edge
bar_cols = [-8, 0, 8];    // the bottom bar's cells, between the cables
bar_y = -28;              // its row: cells -32 ... -24, under the tab
ledge_w = 1.0;            // ledges under the board's side edges
insert_d = 4.0;           // M3 heat-set insert (guidelines), or an M3 bolt and nut: right through
cam_gap = 0.75;           // camera holder to its notch, per side
plug_room = 2.0;          // cut in the left column for the micro USB plug's body
floor_top = 14.8;         // the floor stops here, under the learn button

/* [Derived] */
lo = pd_edge;                              // outer faces sit 0.2 in from the cells
depth = depth_cells * unit - 2 * lo;       // 15.6
pcb_back = floor_t + back_gap + back_h;    // 7.6: z of the board's back (camera side) face
pcb_front = pcb_back + pcb_t;
screen_z = pcb_front + screen_t;           // the screen's face
wall_x = board_w / 2 + clear;              // 26.3: pocket wall
col_out = col_x + unit / 2 - lo;           // 35.8
col_y0 = col_rows[0] - unit / 2 + lo;
col_y1 = col_rows[len(col_rows) - 1] + unit / 2 - lo;
bar_half = (len(bar_cols) * unit) / 2 - lo;   // 11.8
bar_y0 = bar_y - unit / 2 + lo;            // -31.8
bar_y1 = bar_y + unit / 2 - lo;            // -24.2
row_z = [unit / 2 - lo, 3 * unit / 2 - lo];   // 3.8, 11.8: the bar's two rows, front to back

echo(outside = [2 * col_out, col_y1 - bar_y0, depth], pcb_back = pcb_back, screen_z = screen_z,
     screen_below_front = depth - screen_z, camera_below_back = pcb_back - cam_h);
assert(pcb_back - cam_h > 0, "the lens stays inside the back face");
assert(screen_z <= depth, "the screen is not proud of the columns");
assert(bar_half + 2 < -usb_x[1], "the bar clears the USB plug");
assert(bar_half < uart_x[0], "the bar clears the UART plug");
assert(tab_bot - clear > bar_y1, "the tab ends above the bar");
assert(floor_top < learn[2], "the floor stops under the learn button");
assert(col_x - pd_cb_r - wall_x > 2, "wall between the pocket and the column holes");

// ---- the HuskyLens -------------------------------------------------------
// STEP frame: camera towards +z, the board z = 0 ... 1, turned over
// about y so the screen faces +z and x runs left to right seen from the screen.
module board_place() translate([0, 0, pcb_back + pcb_t]) rotate([0, 180, 0]) children();
module board() color("#20304a") board_place() import("models/huskylens/huskylens_board.stl", convexity = 6);
module board_parts() color("silver") board_place() import("models/huskylens/huskylens_parts.stl", convexity = 6);
module screws() color("dimgray") for (s = [-1, 1]) translate([s * screw_x, screw_y, 0]) {   // M3 x 8 pan head
    translate([0, 0, pcb_front]) cylinder(d = 5.6, h = 2.2);
    translate([0, 0, pcb_front - 8]) cylinder(d = 3, h = 8 + eps);
}

// ---- the case --------------------------------------------------------------
// pd_pin_hole runs along +z from z = 0 (the bed face, where its taper is).
module hole_z(x, y) translate([x, y, 0]) pd_pin_hole(depth);
// up from the bar's underside: through, or blind (the back row runs into the neck)
module hole_up(x, z, through) translate([x, bar_y0, z]) rotate([-90, 0, 0])
    if (through) pd_pin_hole(bar_y1 - bar_y0, taper = false); else pd_blind_pin_hole(unit, taper = false);

module body() {
    for (s = [-1, 1]) translate([s > 0 ? wall_x : -col_out, col_y0, 0])
        cube([col_out - wall_x, col_y1 - col_y0, depth]);                                     // columns
    translate([-wall_x - eps, col_y0, 0]) cube([2 * wall_x + 2 * eps, floor_top - col_y0, floor_t]);   // floor
    translate([-bar_half, bar_y0, 0]) cube([2 * bar_half, bar_y1 - bar_y0, depth]);           // bar
    translate([-bar_half, bar_y1 - eps, 0]) cube([2 * bar_half, col_y0 + 2 - bar_y1, pcb_back]);   // neck, behind the tab
    // ledges under the side edges, clear of the SD slot on the right
    translate([-wall_x - eps, board_bot + 0.75, 0]) cube([ledge_w + clear + eps, 12.5 - board_bot - 0.75, pcb_back]);
    for (y = [[board_bot + 0.75, sd_y[0] - 1], [sd_y[1] + 1, floor_top]])
        translate([wall_x - ledge_w - clear, y[0], 0]) cube([ledge_w + clear + eps, y[1] - y[0], pcb_back]);
}

module case() difference() {
    body();
    for (s = [-1, 1], y = col_rows) hole_z(s * col_x, y);
    for (x = bar_cols) if (x == 0) hole_z(x, bar_y);                       // the middle cell: front to back
        else { hole_up(x, row_z[0], false); hole_up(x, row_z[1], true); }  // the outer cells: from underneath
    for (s = [-1, 1]) translate([s * screw_x, screw_y, -1]) cylinder(d = insert_d, h = pcb_back + 2);
    // camera notch, open to the top, widening 45 deg to the back face for the view
    hull() {
        translate([cam[0] - cam_half - cam_gap, cam[1] - cam_half - cam_gap, floor_t]) cube([2 * (cam_half + cam_gap), 30, eps]);
        translate([cam[0] - cam_half - cam_gap - floor_t, cam[1] - cam_half - cam_gap - floor_t, -eps]) cube([2 * (cam_half + cam_gap + floor_t), 30, eps]);
    }
    // room for the micro USB plug's body beside the left column's foot
    translate([-wall_x - plug_room, col_y0 - 1, floor_t + 0.4]) cube([plug_room + eps, board_bot - col_y0 + 1, depth]);
}

function shown(c) = show == "all" || show == c;
if (part == "case" || part == "print") case();
else if (part == "assembly") {
    if (shown("case")) color("#e8c547") case();
    if (shown("board")) board();
    if (shown("parts")) board_parts();
    if (shown("screws")) screws();
}
else if (part == "clash") intersection() { case(); union() { board_place() import("models/huskylens/huskylens_board.stl"); board_place() import("models/huskylens/huskylens_parts.stl"); } }
