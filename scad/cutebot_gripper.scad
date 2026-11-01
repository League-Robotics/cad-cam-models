// Cutebot gripper: the 9 g servo gripper (servo_gripper.scad, the centred
// frame) on the front of the Elecfreaks Cutebot Pro, with its own ball
// caster, replacing the user's hacked-together one (the old servo-kit
// gripper on a red Technic plate, 2026-10-28).
//
// Three prints, each flat on the bed, pinned together with 2L friction
// pins and glued (the user's 2026-10-28 review: the one-piece grippers
// needed support or odd angles and printed badly). The frame and the post
// are the same design as the two-plate robot's (block_gripper.scad, since
// 2026-10-29: one frame print for every robot; a post per height), the tab
// is this robot's mount; the prints are in grippers/block_gripper/:
//   frame  the centred 9 g frame (servo_gripper.scad `centred`) turned
//          over: its top plate is a floor of pin holes ahead of the nose,
//          the servo standing up from it, the hole grid centred on the
//          jaws, a full-unit back wall with 4 rows x 6 columns of holes on
//          the nose's side, and 6 holes forward out of the floor's front
//          face. Prints on its back wall, as the original 9 g frame did.
//   tab    the mount: a 5-hole beam-shaped plate lying on the nose over its
//          two bosses (M3 threads in Technic-sized holes, Technic-spaced one
//          unit either side of the centreline, about a unit and a half
//          behind the tip: counterbored M3 holes at x = +-8, pin holes at
//          0, +-16), with 5 pin holes in its front edge that take pins into
//          one row of the frame's back wall (tab_row). Prints flat.
//   post   the caster post (caster_post.scad): pins into the two floor
//          front-face holes between the jaws (x = +-8) and carries the EV3
//          ball caster on its front, just ahead of the gear teeth, as close
//          as its housing lets the pins sit (2026-10-29: the can arms' ring
//          end is trimmed to clear the caster's beam when closed). Prints
//          on its back face.
//
// Heights: the chassis is a 1.5 thick PCB whose underside at the front is
// front_h above the ground with the robot level (measured 18.6); the
// bosses stand boss_h (1.5) proud of its top and sit inside the tab's
// holes, so the tab lies on the PCB. Its pins fix which wall row it meets,
// and that sets the frame's height over the ground in steps of a row: pick
// tab_row so the paddles clear the ground (paddle_z0 echoed; 4.0 with the
// top row). The caster then holds the frame there: the post's holes are
// placed for the caster's beam top at caster_h over the ground.
//
// Robot coordinates: X across (the jaws centred on x = 0), Y back from the
// nose's tip (ahead is negative), Z up from the ground.
//
// part: "assembly" (everything), "frame" / "tab" / "post" (one piece in
// place), "print_frame" / "print_tab" / "print_post" (on the bed),
// "clash" (what the arms hit in the pieces and caster at theta; empty =
// clear), "clash_view" (the same in red on the see-through assembly), "arm_clash" (the two arms against each other), "ring_view" (the assembly with the two swappable arms in their own colours), "caster_fit" (what the caster hits; empty = clear), "section"
// (the assembly cut at x = section_x). show / hide: "frame", "tab",
// "post", "servo", "spline_arm", "idler_arm", "left_ext", "right_ext",
// "axle", "caster", "pins", "cutebot", "floor".

include <servo_gripper.scad>
include <lego.scad>
include <caster_post.scad>

servo = "9g";
jaw = "nub";
centred = true;
show_part = false;      // servo_gripper.scad draws nothing itself

/* [View] */
part = "assembly";
show = "all";
hide = [];
section_x = 0;
ext = "cube";           // the swappable arms shown
theta = 0;

/* [Cutebot] */
u = 8;
front_h = 18.6;         // the chassis's underside at the front above the ground, level (measured 2026-10-28)
nose_t = 1.5;           // the chassis PCB's thickness: the tab lies on its top (user, 2026-10-28)
boss_z = front_h + nose_t;
boss_x = [-8, 8];       // one unit either side of the centreline
boss_back = 13.5;       // the bosses' centres behind the nose's tip   TODO measure
boss_d = 4.9;           // a Technic hole slips over the boss
boss_h = 1.5;           // the boss stands this far proud of the PCB, inside the tab's hole (user, 2026-10-28)
nose_w = 64;            // the nose's width at the bosses (the stand-in only)
nose_gap = 0.5;         // the frame's back face this far ahead of the nose's tip

/* [Tab] */
tab_w = 5 * u;          // five holes across
tab_t = 7.8;            // a beam
tab_y1 = boss_back + u / 2 + 0.9;   // the tab's back edge, just past a beam's end
tab_pin_x = [-16, 0, 16];           // plain pin holes between and outside the screws
tab_edge_x = [-16, -8, 0, 8, 16];   // the mating pins in its front edge
// the wall row the tab's pins go into: an index into lego_y (servo y, from
// the servo's bottom), so 0 is the lowest row on the robot and 3 the top one
tab_row = 3;
m3_hole = 3.4;
m3_cb_d = 6.5;          // socket head
m3_cb_h = 3.2;

/* [Gripper placement] */
// servo coordinates -> robot: servo x runs back (the axles, servo x = 0, at
// axle_y; the frame's back face, servo x = top_x[1], at y = -nose_gap);
// servo y runs down from the frame's top at z_servo0; servo z across, with
// the jaws (midway between the axles) on x = 0. The wall's hole rows are at
// servo y = lego_y, so at robot z = z_servo0 - lego_y.
paddle_h = 38;          // the cube paddles, centred on the arm layer (measured)
tab_zc = boss_z + tab_t / 2;                    // the tab's mid-height, on the nose
z_servo0 = tab_zc + lego_y[tab_row];            // robot z of servo y = 0 (the frame's top)
arm_zc = z_servo0 - (arm_y0 + arm_y1) / 2;      // the arm layer's centre
paddle_z0 = arm_zc - paddle_h / 2;              // the paddles' bottoms over the ground
axle_y = -nose_gap - top_x[1];                  // -22.3
frame_x = mesh_z;                               // 6.625: robot x of servo z = 0
frame_x0 = frame_x - top_z[1];                  // the frame's -x end, -21.9
frame_x1 = frame_x - top_z[0];                  // its +x end, 29.9
floor_y0 = axle_y + top_x[0];                   // the floor's front face, -36.3: the gear teeth's reach
back_y = axle_y + top_x[1];                     // the frame's back face, -nose_gap
teeth_y = axle_y - gear_r - 1;                  // = floor_y0
module on_servo() multmatrix([[0, 0, -1, frame_x], [1, 0, 0, axle_y], [0, -1, 0, z_servo0], [0, 0, 0, 1]]) children();
floor_z0 = z_servo0 - top_y1;   // the floor's bed face
floor_z1 = floor_z0 + plate_t;  // its top
wall_top_z = z_servo0;
arm_z = [z_servo0 - arm_y1, z_servo0 - arm_y0];   // the arm layer
axle_len = 24;
axle_y0 = top_y1 - axle_len;    // the idler axle: the axle 3 down to the bed face
wall_rows_z = [for (y = lego_y) z_servo0 - y];  // the wall's hole rows over the ground
grid_x = [for (z = grid_z) frame_x - z];        // the hole columns across: 24, 16, 8, 0, -8, -16

/* [Caster] */
caster_top_z = caster_h;        // the beam top, the ball on the ground
post_pin_x = [-8, 8];           // the post's mating pins: the floor's front-face holes between the jaws
post_min = post_min_depth(arm_z, caster_top_z);                // 17: the beam is in the arm layer, the can arms need it
post_d = post_depth_for([floor_z0, floor_z1], caster_top_z, post_min);   // the post's depth, 17.0: the housing wants as much

$fn = 48;

/* [Label] */
// "Cutebot" etched in the post's top, reading the right way up for someone
// standing behind the robot. The frame is unlabelled: it is the same print for
// every robot since 2026-10-29 (block_gripper.scad uses it too) and nothing
// else looks like it
post_label = "Cutebot";

// ---------- the pieces ----------

module gripper_frame() on_servo() frame();

module tab() difference() {
    translate([-tab_w / 2, back_y, boss_z]) cube([tab_w, tab_y1 - back_y, tab_t]);
    for (x = boss_x) translate([x, boss_back, boss_z]) {
        translate([0, 0, -1]) cylinder(d = m3_hole, h = tab_t + 2);
        translate([0, 0, tab_t - m3_cb_h]) cylinder(d = m3_cb_d, h = m3_cb_h + 1);
        if (boss_h > 0) translate([0, 0, -1]) cylinder(d = boss_d, h = boss_h + 1);
    }
    for (x = tab_pin_x) translate([x, boss_back, boss_z]) pd_pin_hole(tab_t, ext = 2);
    // the mating pins: in from the front edge, 8 deep, on the wall row
    for (x = tab_edge_x) translate([x, back_y, tab_zc]) rotate([-90, 0, 0]) pd_blind_pin_hole(8, ext = 2);
}

// what the arms hit in the pieces and the caster at theta; empty = clear
module clash() intersection() {
    on_servo() arms(theta);
    union() { gripper_frame(); tab(); post(); caster_placed(); pins(); }
}

module post() caster_post(floor_y0, [floor_z0, floor_z1], post_pin_x, caster_top_z, post_min, post_label);

module pins() {
    for (x = tab_edge_x) translate([x, back_y, tab_zc]) pin_2l();
    caster_post_pins(floor_y0, [floor_z0, floor_z1], post_pin_x);
}

// ---------- the robot around it ----------

module caster_placed() caster_on_post(floor_y0, [floor_z0, floor_z1], caster_top_z, post_min);

// a stand-in for the Cutebot Pro's nose: a rounded slab at the bosses'
// height, the chassis's underside at front_h, the two bosses
module cutebot() {
    r = nose_w / 2;
    color("whitesmoke") difference() {
        translate([0, 0, front_h]) linear_extrude(nose_t) hull() {
            translate([0, r]) circle(r = r);
            translate([-r, r]) square([2 * r, 60]);
        }
        for (x = boss_x) translate([x, boss_back, front_h + nose_t - 6]) cylinder(d = m3_hole, h = 7);
    }
    color("goldenrod") for (x = boss_x) translate([x, boss_back, front_h + nose_t - 0.01]) difference() {
        cylinder(d = boss_d - 0.1, h = boss_h + 0.01);
        translate([0, 0, -1]) cylinder(d = m3_hole, h = boss_h + 2);
    }
}

function shown(c) = (show == "all" || show == c) && len([for (h = hide) if (h == c) 1]) == 0;

module pieces() {
    if (shown("frame")) color("lightgray") gripper_frame();
    if (shown("tab")) color("burlywood") tab();
    if (shown("post")) color("darkseagreen") post();
}

module assembly() {
    on_servo() arms(theta);
    if (shown("axle")) on_servo() axle();
    if (shown("servo")) on_servo() color("dimgray") servo_model();
    pieces();
    if (shown("caster")) caster_placed();
    if (shown("pins")) pins();
    if (shown("cutebot")) cutebot();
    if (shown("floor")) color("gainsboro", 0.4) translate([-80, -90, -1]) cube([160, 260, 1]);
}

if (part == "assembly") assembly();
else if (part == "frame") gripper_frame();
else if (part == "tab") tab();
else if (part == "post") post();
else if (part == "print_frame") translate([0, 0, back_y]) rotate([-90, 0, 0]) gripper_frame();   // on its back wall
else if (part == "print_tab") translate([0, 0, -boss_z]) tab();                                  // flat, screw heads up
else if (part == "print_post") caster_post_print(floor_y0, [floor_z0, floor_z1], post_pin_x, caster_top_z, post_min, post_label);   // on its back face
else if (part == "section") difference() {
    assembly();
    color("#d8dde2") translate([section_x, -300, -100]) cube([300, 600, 300]);
}
else if (part == "clash") clash();
else if (part == "clash_view") {   // the assembly with the arms see-through and what they hit in red
    color("red") clash();
    color("mediumseagreen", 0.35) on_servo() arms(theta);
    if (shown("axle")) on_servo() axle();
    if (shown("servo")) on_servo() color("dimgray") servo_model();
    pieces();
    if (shown("caster")) color("#4a4f55", 0.4) caster_placed();
    if (shown("pins")) pins();
}
else if (part == "ring_view") {   // the assembly with the two swappable arms in their own colours (the can tips lapping)
    on_servo() {
        on_axis(spline_axis) rotate(theta) { color("orange") spline_arm(); color("seagreen") arm_part(ext, -1); }
        on_axis(idler_axis) rotate(-theta) { color("royalblue") idler_arm(); color("darkorange") handed(1) arm_part(ext, 1); }
        axle();
    }
    pieces(); caster_placed(); pins();
}
else if (part == "arm_clash") intersection() {   // the two swappable arms against each other at theta (the can tips lap); empty = clear
    on_servo() on_axis(spline_axis) rotate(theta) arm_part(ext, -1);
    on_servo() on_axis(idler_axis) rotate(-theta) handed(1) arm_part(ext, 1);
}
else if (part == "caster_fit") intersection() {   // the caster against the pieces, pins and the idler axle; empty = clear
    caster_placed();
    union() { gripper_frame(); post(); pins(); on_servo() axle(); }
}

echo(boss_z = boss_z, tab_z = [boss_z, boss_z + tab_t], tab_zc = tab_zc, wall_rows_z = wall_rows_z, wall_top_z = wall_top_z,
     floor_z = [floor_z0, floor_z1], arm_z = arm_z, paddle_z0 = paddle_z0, back_y = back_y, floor_y0 = floor_y0,
     servo_back_y = axle_y + body[0] / 2, teeth_y = teeth_y, post_y = [floor_y0 - post_d, floor_y0],
     caster_pin_z = caster_top_z - caster_pin_down, frame_x = [frame_x0, frame_x1], grid_x = grid_x, tab_y1 = tab_y1);
assert(paddle_z0 >= 0, "the paddles reach the ground: pick a higher tab_row (a lower lego_y index)");
