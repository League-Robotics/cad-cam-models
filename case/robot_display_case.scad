// Case for the Waveshare ESP32-S3-Touch-LCD-1.69 as a robot display.
//
// Two printed parts: the SHELL, a frame the display drops into from the back
// (its lip holds the glass from the front), and the LID, which plugs into the
// back of the shell and carries a 5 x 4 grid of LEGO Technic pin holes so the
// display pins onto a robot. Also a thin flat lid for gluing or velcro.
//
// Datum: the frame of Waveshare's STEP model (ref/waveshare/ESP32-S3-Touch-LCD-1_69.stp),
// so ref/waveshare/board.stl drops straight in for the viewer: X along the
// SHORT (33.13) axis, Y along the LONG (41.13) axis, Z up out of the screen.
// Its origin is near the middle: the glass centre is at y = -1.275 (glass_cy)
// and the PCB centre at y = -1.19; the case is centred on the glass. In this frame:
//   +X edge: the three side buttons (RST, BOOT, PWR), -X edge: the USB-C port,
//   -Y edge: the 11 header pads (18 17 3 2 SCL SDA TX RX 3V3 G 5V) and the
//   display's flex connector, +Y edge: nothing.
// Viewed from the front with the USB port at the bottom, the buttons are at
// the top and the header pads on the left, as in Waveshare's photos.
//
// Every number under [Measured] was read from Waveshare's STEP model (sliced
// in FreeCAD, 2026-11-14), not measured on the part: the glass is the widest
// thing at 41.13 x 33.13; it is 1.75 thick with a 2 mm chamfer round its top
// edge; the PCB (37.14 x 29.85 x 1.0) is centred under it within 0.1; the
// deepest component on the back is 4.4 below the PCB (the battery connector).
// Nothing has been measured on the real board yet.

include </Volumes/Proj/proj/CAD/gears/scad/lego.scad>

part = "assembly";      // shell | lid | lid_flat | shell_print | lid_print | lid_flat_print | assembly | board
show = "all";           // for the assembly: all | shell | lid | board
lid_kind = "lego";      // lego | flat, the lid the assembly shows

$fn = 64;
eps = 0.01;

/* [Measured: from the STEP model] */
glass_x = 33.13;        // glass, short axis
glass_y = 41.13;        // glass, long axis
glass_r = 5.4;          // glass corner radius, full-width part
glass_top_r = 4.97;     // corner radius of its flat top face
glass_cy = -1.275;      // y of the glass centre (x centre is 0)
glass_top = 3.80;       // z of the glass face
glass_full_top = 2.70;  // z where the 2 mm edge chamfer starts (full width below this)
glass_bot = 2.05;       // z of the glass underside at its edge
module_x = 30.07;       // the LCD module under the glass, widest part (z 0.5..1.5)
module_y = 38.00;
module_cy = -1.52;      // y of the module centre: it sits 0.33 further -y than the PCB, and the
                        // flex folds under it to y = -20.3, so the cavity is centred on the module
pcb_x = 29.85;
pcb_y = 37.14;
pcb_top = -1.50;        // z of the PCB top face (components face -z)
pcb_bot = -2.50;
pcb_cy = -1.19;         // y of the PCB and module centre: 0.085 off the glass centre
back_z = -6.90;         // z of the deepest thing on the back (battery connector)
usb_cy = -1.02; usb_cz = -3.77;  usb_w = 8.34; usb_h = 3.56; // USB-C receptacle, on the -x edge
btn_cy = [-9.75, -0.85, 8.07];   // the three side buttons, on the +x edge
btn_cz = -3.20; btn_w = 4.55; btn_h = 2.2;
hdr_x0 = -12.7; hdr_x1 = 12.7;   // the 11 header pads along the -y edge, 2.54 pitch (a guess: 11 x 2.54 centred)

/* [Guessed] */
cavity_r = 2.5;         // corner radius of the pocket under the glass: the PCB corners aren't in the model, so small
glass_chamfer_in = 2.0; // how far in from the edge the top chamfer runs (from the slices: 41.13 at z 2.7, 37.13 at z 3.8)

/* [Our picks] */
wall = 1.6;             // side walls
lip_t = 1.2;            // the front lip over the glass edge
lip_over = 1.5;         // how far the lip overlaps the glass edge (on its chamfer)
glass_clear = 0.2;      // each side, glass pocket
cavity_clear = 0.3;     // each side, the pocket round the PCB/module
back_clear = 0.5;       // between the deepest component and the lid
lid_plug_h = 2.0;       // how far the lid's plug goes into the shell
lid_plug_clear = 0.15;  // each side, plug in the shell (friction fit; glue if loose)
ledge_flat = 0.6;       // the flat part of the ledge under the glass; below it a 45 deg chamfer, so the
                        // shell prints face down without an overhang
lego_lid_t = 9.0;       // lid plate: an 8-deep blind pin hole plus a 1 mm floor
flat_lid_t = 2.5;
usb_cut = [13.0, 7.5];  // USB-C plug overmould is about 12.2 x 6.5
btn_cut = [7.0, 4.0];   // slots to press the side buttons
hdr_slot = [28.0, 4.0]; // slot on the -y side for a right-angle header or wires, below the PCB
lego_cols = 5; lego_rows = 4;   // pin-hole grid on the lid (40 x 32 over a 36.7 x 44.7 lid)

// ---- Derived -----------------------------------------------------------------
pocket_x = glass_x + 2 * glass_clear;          // glass pocket
pocket_y = glass_y + 2 * glass_clear;
pocket_r = glass_r + glass_clear;
outer_x = pocket_x + 2 * wall;
outer_y = pocket_y + 2 * wall;
outer_r = pocket_r + wall;
window_x = glass_x - 2 * lip_over;             // the opening in the lip
window_y = glass_y - 2 * lip_over;
window_r = max(1, glass_r - lip_over);
// The lip's underside sits where the chamfer has risen to meet it, so the lip
// bears on the chamfer just inside its inner edge and the glass face ends up
// recessed behind the lip.
lip_bot = glass_full_top + (glass_top - glass_full_top) * (lip_over / glass_chamfer_in) + 0.05;
lip_top = lip_bot + lip_t;                     // the front face of the case
cavity_x = max(module_x, pcb_x) + 2 * cavity_clear;  // pocket below the glass
cavity_y = max(module_y, pcb_y) + 2 * cavity_clear;
ledge_z = glass_bot - 0.15;                    // the step the glass edge rests on
floor_z = back_z - back_clear;                 // the lid's inner face
shell_bot = floor_z - lid_plug_h;              // the shell's back edge
plug_x = cavity_x - 2 * lid_plug_clear;
plug_y = cavity_y - 2 * lid_plug_clear;
lego_lid_bot = shell_bot - lego_lid_t;
flat_lid_bot = shell_bot - flat_lid_t;
case_h_lego = lip_top - lego_lid_bot;
case_h_flat = lip_top - flat_lid_bot;
ledge_w_x = (pocket_x - cavity_x) / 2;
ledge_w_y = (pocket_y - cavity_y) / 2 - abs(module_cy - glass_cy);
chamfer_h = max((pocket_x - 2 * ledge_flat - cavity_x) / 2, (pocket_y - 2 * ledge_flat - cavity_y) / 2);  // 45 deg

echo(str("outer ", outer_x, " x ", outer_y, "; front face z=", lip_top, "; lip underside z=", lip_bot,
         "; ledge z=", ledge_z, " width x/y ", ledge_w_x, "/", ledge_w_y,
         "; cavity ", cavity_x, " x ", cavity_y, " to z=", floor_z, "; shell back z=", shell_bot,
         "; case height lego/flat ", case_h_lego, "/", case_h_flat));
assert(lip_bot > glass_full_top, "lip underside must clear the glass's full-width part");
assert(ledge_w_x > 1.0 && ledge_w_y > 1.0, "the glass needs at least 1 mm of ledge to rest on");
assert(ledge_flat < ledge_w_x && ledge_flat < ledge_w_y, "the flat ledge must be narrower than the ledge");
assert(lego_cols * pd_unit <= outer_y - 2 && lego_rows * pd_unit <= outer_x - 2, "LEGO grid wider than the lid");

module rrect(x, y, r) { offset(r = r) offset(delta = -r) square([x, y], center = true); }
module rbox(x, y, r, z0, z1) { translate([0, 0, z0]) linear_extrude(z1 - z0) rrect(x, y, r); }
module gbox(x, y, r, z0, z1) { translate([0, glass_cy, 0]) rbox(x, y, r, z0, z1); }   // centred on the glass
module mbox(x, y, r, z0, z1) { translate([0, module_cy, 0]) rbox(x, y, r, z0, z1); }  // centred on the module (the cavity)
module pbox(x, y, r, z0, z1) { translate([0, pcb_cy, 0]) rbox(x, y, r, z0, z1); }     // centred on the PCB

// ---- The shell ---------------------------------------------------------------
module shell() {
    difference() {
        gbox(outer_x, outer_y, outer_r, shell_bot, lip_top);
        // window in the lip
        gbox(window_x, window_y, window_r, lip_bot - 1, lip_top + 1);
        // glass pocket, from the lip underside down to the ledge
        gbox(pocket_x, pocket_y, pocket_r, ledge_z, lip_bot);
        // the pocket round the module and PCB, open at the back, with the 45 deg
        // chamfer up to the ledge's flat part
        mbox(cavity_x, cavity_y, cavity_r, shell_bot - 1, ledge_z - chamfer_h + eps);
        hull() {
            gbox(pocket_x - 2 * ledge_flat, pocket_y - 2 * ledge_flat, pocket_r, ledge_z - eps, ledge_z + eps);
            mbox(cavity_x, cavity_y, cavity_r, ledge_z - chamfer_h, ledge_z - chamfer_h + eps);
        }
        // USB-C on the -x wall
        translate([-outer_x / 2 - 1, usb_cy, usb_cz]) rotate([0, 90, 0])
            linear_extrude(wall + 3) rrect(usb_cut[1], usb_cut[0], 2);
        // button slots on the +x wall
        // (they start inside the cavity: the button caps reach 0.2 into the wall)
        for (y = btn_cy) translate([cavity_x / 2 - 1, y, btn_cz]) rotate([0, 90, 0])
            linear_extrude(wall + cavity_clear + 3) rrect(btn_cut[1], btn_cut[0], 1.2);
        // header / wire slot on the -y wall, just below the PCB
        translate([(hdr_x0 + hdr_x1) / 2, glass_cy - outer_y / 2 - 1, pcb_bot - hdr_slot[1] / 2 - 0.3]) rotate([-90, 0, 0])
            linear_extrude(wall + 3) rrect(hdr_slot[0], hdr_slot[1], 1.2);
    }
}

// ---- The lids ---------------------------------------------------------------
module lid_body(t) {
    gbox(outer_x, outer_y, outer_r, shell_bot - t, shell_bot);
    mbox(plug_x, plug_y, cavity_r, shell_bot - eps, floor_z);
}
module lid_lego() {
    difference() {
        lid_body(lego_lid_t);
        for (i = [0 : lego_cols - 1], j = [0 : lego_rows - 1])
            translate([(j - (lego_rows - 1) / 2) * pd_unit, glass_cy + (i - (lego_cols - 1) / 2) * pd_unit, lego_lid_bot])
                pd_blind_pin_hole(depth = pd_unit);
    }
}
module lid_flat() { lid_body(flat_lid_t); }

// ---- The board ------------------------------------------------------------------------
// Waveshare's model, for the viewer (not watertight, so useless for booleans).
module board() { import("../ref/waveshare/board.stl"); }
// A clean envelope of the board for the fit check: boxes round every solid in
// the STEP model bigger than a chip (sliced in FreeCAD, 2026-11-14).
board_boxes = [   // [x0, x1, y0, y1, z0, z1]
    [-15.93, -8.88, -5.19, 3.15, -5.55, -1.99],   // USB-C receptacle (-x edge)
    [-6.12, 6.18, -16.26, -10.26, -4.60, -2.50],  // display flex connector (-y edge)
    [-13.82, -8.18, -11.65, -6.36, -4.50, -2.50],
    [5.82, 11.22, -7.25, -0.25, -4.50, -2.50],    // ESP32-S3
    [2.45, 9.45, 3.22, 10.22, -3.50, -2.50],
    [-13.92, -8.72, 4.97, 12.62, -6.00, -2.60],   // battery connector
    [-11.41, -8.41, -16.63, -12.33, -6.90, -2.50],// RTC battery connector (the deepest thing)
    [11.92, 15.57, -12.03, -7.48, -4.30, -2.10],  // side buttons (+x edge)
    [11.92, 15.57, -3.12, 1.43, -4.30, -2.10],
    [11.91, 15.56, 5.79, 10.34, -4.30, -2.10],
    [2.92, 8.92, 15.24, 17.24, -3.50, -2.50],
    [-8.92, -5.77, 11.83, 14.93, -3.40, -2.52],
];
module board_env() {
    gbox(glass_x, glass_y, glass_r, glass_bot, glass_full_top);                       // glass, full width
    gbox(glass_x - 2 * glass_chamfer_in, glass_y - 2 * glass_chamfer_in, glass_top_r, glass_full_top - eps, glass_top); // its chamfered top
    mbox(module_x, module_y, 2, 0.5, glass_bot + eps);                                // LCD module
    translate([0, -2.9, 0]) pbox(28.0, 32.3, 1, pcb_top - eps, 0.5 + eps);           // flex and backing (-20.3 .. 12.0)
    pbox(pcb_x, pcb_y, 1, pcb_bot, pcb_top);                                          // PCB
    for (b = board_boxes) translate([b[0], b[2], b[4]]) cube([b[1] - b[0], b[3] - b[2], b[5] - b[4]]);
}

// ---- Parts and print orientations ----------------------------------------------
if (part == "shell") shell();
else if (part == "lid") lid_lego();
else if (part == "lid_flat") lid_flat();
else if (part == "board") board();
else if (part == "board_env") board_env();
else if (part == "shell_print") translate([0, 0, lip_top]) mirror([0, 0, 1]) shell();        // face down, pocket up
else if (part == "lid_print") translate([0, 0, -lego_lid_bot]) lid_lego();                    // LEGO face down, plug up
else if (part == "lid_flat_print") translate([0, 0, -flat_lid_bot]) lid_flat();
else if (part == "assembly") {
    if (show == "all" || show == "shell") color("SteelBlue") shell();
    if (show == "all" || show == "lid") color("DarkOrange") { if (lid_kind == "lego") lid_lego(); else lid_flat(); }
    if (show == "all" || show == "board") color("LightGreen") board();
    if (show == "env") color("LightGreen") board_env();
}
