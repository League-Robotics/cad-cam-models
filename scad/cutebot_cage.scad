// LEGO cage round the Elecfreaks Cutebot Pro, from the laser scan of
// 2026-11-04: /Volumes/Proj/proj/robot-projects/carvera/docs/cutebot-pro-mounting.md
// (features.json there wins if anything here disagrees).
//
// The user's brief (2026-11-04): printed LEGO-compatible parts, several
// prints, screwed to the robot's bosses through half-height cells (nothing
// directly above a boss), working round the lights, the battery and the
// micro:bit; a front mount for the LEGO ball caster (the robot's own casters
// come off) and grippers; fenders round the wheels.
// v2, after the first draft ("very spare"): the area over the wheels is a
// flat LEGO grid, not round fenders; large flat surfaces, horizontal and
// vertical, to attach things to; the battery stays exposed, so the
// batteries are easy to change; and make use of the grid fit below.
// v3 (same day): "extend it around the front of the robot; we don't really
// need to see the front of the micro:bit": a full-width front wall, sides
// and a deck in front of the micro:bit close the frame into a ring.
//
// The grid fit: every boss and hole on the robot is on one 8 mm grid, and
// the two decks are 15.9 apart, two units. So the whole cage is one 3D grid
// of cells (i, j, k), centred on x = 8 i, y = 8 j, z = 24 + 8 k: k = 0 is a
// plate lying on the lower deck, k = 2 one on the upper deck (39.9, 0.1
// under the grid), and every part pins to its neighbours on that grid. The
// lower front lobes, the upper rails, the bulkheads, skirts and decks are
// one frame. z = 24 (k = 0) is also the ball caster's pin row with its ball
// on the ground, and the row the 9 g gripper frame's back wall pinned into.
//
// The pieces (18 prints; _l / _r are mirror pairs; every cell has a Part
// Designer hole, edges alternate as the hole-grid rule):
//   nose      5 x 2 on the lower deck, M3 into B2 / B3 (+-8, 80); its front
//             face pins into the front wall's bottom row (5 pins)
//   fwall     front wall, the full width (17 x 5, y = 92 ... 100, k = 0 ...
//             4), 6 ahead of the PCB's tip: the caster pins into its bottom
//             row at x = +-8, the 9 g gripper frame into the same row (the
//             old tab's 5); windows (1 x 2 cells) in front of the headlights
//   fside     the sides of the front (x = -68 ... -60, y = 44 ... 92, k = 0 ...
//             4), from the front bulkhead to the front wall
//   fdeck     the front deck, full width (17 x 7, y = 44 ... 100, k = 5), with
//             an opening over the micro:bit (x = +-28, y = 44 ... 60), so it
//             still lifts out; a 2.5 hex key reaches the lower deck's four
//             screws through the deck's holes (every screw is on the grid)
//   lobe      on the front lobe, M3 into B1 / B4 (+-32, 64), notched round
//             the micro:bit connector's end (~10 tall at |x| 26 ... 28.5);
//             its back face pins into the front bulkhead's bottom row
//   rail      2 x 7 on the upper deck, M3 into L3 L5 / R3 R5, through holes
//             over the deck's pin holes, recesses over the battery holder's
//             screw heads
//   wall      on the rail's outer column, 2 high (k = 3, 4), under the deck
//   front     bulkhead 5 wide x 5 high, in front of the wheel (y = 36 ... 44,
//             x = -68 ... -28, k = 0 ... 4): a forward-facing grid
//   skirt     9 long x 4 high outside the wheel (x = -68 ... -60, k = 1 ... 4),
//             5 clear of the tyre: a sideways-facing grid
//   deck      6 x 11 over the wheel (x = -68 ... -20, y = -44 ... 44, k = 5,
//             9 over the tyre): the big flat top
//   rear      bulkhead the full width behind the robot (17 x 4, y = -44 ... -36,
//             k = 1 ... 4): a rear-facing grid
// Rear bulkhead, skirts, front sides and front wall make a closed ring.
// The middle, x = -20 ... 20 over the battery (battery x -7.75 ... 10.5,
// top 58.8), is open from the upper deck up, and the rail screws are in the
// open too.
//
// Screw cells: M3 (assumed; the user's nose bosses were M3, 2026-10-28), a
// 3.4 hole through a floor 4 up from the plate's bottom face (half height),
// a 7.2 pocket above for the head and the key, a 7.2 x 1.8 recess below for
// the insert's flange. M3 x 6.
//
// Robot frame (as the scan): +x the robot's right, +y forward, +z up from the
// ground, mm.
//
// part: "all" (pieces, robot, caster, pins, screws), a piece in place (names
// in `pieces`), "robot", "caster", "pins", "screws", "clash" (pieces and
// caster against the robot stand-in: empty = clear), "print_<piece>" (on the bed).

include <lego.scad>
include <caster_post.scad>
include <cutebot_outline.scad>

/* [View] */
part = "all";
$fn = 32;

/* [Grid] */
u = pd_unit;            // 8
e = pd_edge;            // 0.2: faces sit this far in from the cells
deck_lo = 20.2;         // lower deck's top (scan)
deck_hi = 36.1;         // upper deck's top (scan)
z_k0 = deck_lo - e + u / 2;     // 24.0: k = 0, a plate lying on the lower deck
rail_dz = deck_hi - e + u / 2 - (z_k0 + 2 * u);   // -0.1: the rails sit on the upper deck, a hair under k = 2
function cc(c) = [u * c[0], u * c[1], z_k0 + u * c[2]];   // a cell's centre

/* [Screws] */
m3_d = 3.4;
screw_floor = 4;        // the half-height floor's top, up from the plate's bottom face
screw_pocket_d = 7.2;
boss_recess_d = 7.2;    // the insert's flange (scan rings 6.4 ... 7.1 across)
boss_recess_h = 1.8;    // standing 1 ... 1.5 proud
head_recess_d = 7.5;    // under the rails: the battery holder's screw heads
head_recess_h = 3.0;

/* [Robot, from the scan] */
axle_z = 25.5;
wheel_r = 25.5;
battery = [[-7.75, 10.5], [-33.54, 37.34], 58.8];
lights_xy = [[-32, 73], [32, 73]];      // headlights: where the scan photo shows them lit; flat (the scan sees the deck there)
caster_top = caster_h;                  // 28: the caster's beam top, its ball on the ground
nose_face = u * 12 + u / 2 - e;         // 99.8

// ---------- the plate maker ----------
// A one-cell-thick plate of cells lo ... hi ([i, j, k]); lo and hi agree on
// one axis, the thin one, and every cell has a pin hole through it along
// that axis, except:
//   edges  [[face, "all"] | [face, "alt", p]]: cells on that face take a
//          blind hole in from it instead (8 deep, half a 2L pin): every
//          cell ("all"), or those whose coordinate along the edge has
//          parity p ("alt"); the first face that claims a cell wins. The
//          parities are global, so mating parts agree: a vertical joint
//          pin goes where the edge's own holes don't.
//   screws M3 screw cells (z-thin plates), heads (a recess under the hole
//          for a screw head on the robot), skip (cells left out)
//   grow   [[face, mm]]: the body reaches this much further past a face
//          (to join another plate)
//   dz     shifts the whole plate (the rails)

function has(list, c) = len([for (l = list) if (l[0] == c[0] && l[1] == c[1] && (len(l) < 3 || l[2] == c[2])) 1]) > 0;
function fax(f) = f[1] == "x" ? 0 : f[1] == "y" ? 1 : 2;
function on_face(f, c, lo, hi) = f[0] == "-" ? c[fax(f)] == lo[fax(f)] : c[fax(f)] == hi[fax(f)];
function claims(ed, c, lo, hi, t) = let(a = 3 - t - fax(ed[0]))
    on_face(ed[0], c, lo, hi) && (ed[1] == "all" || abs(c[a]) % 2 == ed[2]);
function claim(edges, c, lo, hi, t) = let(l = [for (ed = edges) if (claims(ed, c, lo, hi, t)) ed[0]]) len(l) ? l[0] : "";
function grown(grow, f) = let(l = [for (g = grow) if (g[0] == f) g[1]]) len(l) ? l[0] : 0;
// turns +z into the direction going in from face f / along axis t
module into(f) rotate(f == "-x" ? [0, 90, 0] : f == "+x" ? [0, -90, 0] : f == "-y" ? [-90, 0, 0] : f == "+y" ? [90, 0, 0] : f == "+z" ? [180, 0, 0] : [0, 0, 0]) children();
function low(t) = t == 0 ? "-x" : t == 1 ? "-y" : "-z";

module screw_cut(c, z0, z1) translate([c[0], c[1], 0]) {
    translate([0, 0, z0 - 1]) cylinder(d = m3_d, h = z1 - z0 + 2);
    translate([0, 0, z0 + screw_floor]) cylinder(d = screw_pocket_d, h = z1 - z0);
    translate([0, 0, z0 - 1]) cylinder(d = boss_recess_d, h = boss_recess_h + 1);
}

module gplate(lo, hi, edges = [], screws = [], heads = [], skip = [], grow = [], dz = 0) {
    t = lo[0] == hi[0] ? 0 : lo[1] == hi[1] ? 1 : 2;
    p0 = cc(lo) - [u / 2 - e, u / 2 - e, u / 2 - e];
    p1 = cc(hi) + [u / 2 - e, u / 2 - e, u / 2 - e];
    g0 = [grown(grow, "-x"), grown(grow, "-y"), grown(grow, "-z")];
    g1 = [grown(grow, "+x"), grown(grow, "+y"), grown(grow, "+z")];
    translate([0, 0, dz]) difference() {
        translate(p0 - g0) cube(p1 - p0 + g0 + g1);
        for (s = skip) translate(cc(s) - [u / 2 + e, u / 2 + e, u / 2 + e]) cube([u + 2 * e, u + 2 * e, u + 2 * e]);
        for (i = [lo[0] : hi[0]], j = [lo[1] : hi[1]], k = [lo[2] : hi[2]]) let(c = [i, j, k], p = cc(c), f = claim(edges, c, lo, hi, t)) {
            if (has(skip, c)) ;
            else if (has(screws, c)) screw_cut(p, p[2] - u / 2 + e, p[2] + u / 2 - e);
            else if (has(heads, c)) translate(p - [0, 0, u / 2 - e]) {
                pd_pin_hole(u - 2 * e, ext = 2);
                translate([0, 0, -1]) cylinder(d = head_recess_d, h = head_recess_h + 1);
            }
            else if (f != "") let(a = fax(f), q = [for (n = [0 : 2]) n == a ? (f[0] == "-" ? p0[a] : p1[a]) : p[n]])
                translate(q) into(f) pd_blind_pin_hole(u, taper = false, ext = 2);
            else let(q = [for (n = [0 : 2]) n == t ? p0[t] : p[n]]) translate(q) into(low(t)) pd_pin_hole(u - 2 * e, ext = 2);
        }
    }
}

// ---------- the pieces (left side; the right ones are mirrors) ----------

module nose() gplate([-2, 10, 0], [2, 11, 0], [["+y", "all"]], screws = [[-1, 10, 0], [1, 10, 0]]);
// headlight windows: the cells in front of the lights (x = +-32), bottom two rows
module fwall() gplate([-8, 12, 0], [8, 12, 4], [["+z", "alt", 1], ["-x", "alt", 0], ["+x", "alt", 0]],
                      skip = [[-4, 12, 0], [-4, 12, 1], [4, 12, 0], [4, 12, 1]]);
module fside_l() gplate([-8, 6, 0], [-8, 11, 4], [["+z", "alt", 1], ["-z", "alt", 1], ["-y", "alt", 1], ["+y", "alt", 1]]);
module fdeck() gplate([-8, 6, 5], [8, 12, 5], [["-y", "alt", 0], ["+y", "alt", 0], ["-x", "alt", 0], ["+x", "alt", 0]],
                      skip = [for (i = [-3 : 3], j = [6 : 7]) [i, j, 5]]);
// the inner column only at the boss: the micro:bit connector's end stands ~10 tall at x = -28.5 ... -26, y = 48 ... 56
module lobe_l() gplate([-6, 6, 0], [-4, 8, 0], [["-y", "all"], ["-x", "alt", 1], ["+y", "alt", 1]],
                       screws = [[-4, 8, 0]], skip = [[-4, 6, 0], [-4, 7, 0]]);
module rail_l() gplate([-3, -3, 2], [-2, 3, 2], [["-x", "alt", 0]], screws = [[-2, -1, 2], [-2, 1, 2]],
                       heads = [[-2, -3, 2], [-2, 3, 2]], dz = rail_dz);
module wall_l() gplate([-3, -3, 3], [-3, 3, 4], [["+z", "alt", 1], ["-z", "alt", 1]]);
module front_l() gplate([-8, 5, 0], [-4, 5, 4], [["+z", "alt", 1], ["-x", "alt", 0], ["+x", "alt", 0]]);
module skirt_l() gplate([-8, -4, 1], [-8, 4, 4], [["+z", "alt", 1], ["-z", "alt", 1], ["-y", "alt", 1], ["+y", "alt", 1]]);
module deck_l() gplate([-8, -5, 5], [-3, 5, 5], [["-y", "alt", 0], ["+y", "alt", 0], ["-x", "alt", 0], ["+x", "alt", 0]]);
module rear() gplate([-8, -5, 1], [8, -5, 4], [["+z", "alt", 1], ["-z", "alt", 1], ["-x", "alt", 0], ["+x", "alt", 0]]);

pieces = ["nose", "lobe_l", "lobe_r", "rail_l", "rail_r", "wall_l", "wall_r", "front_l", "front_r",
          "skirt_l", "skirt_r", "deck_l", "deck_r", "rear", "fwall", "fside_l", "fside_r", "fdeck"];
colors = [["nose", "#e67e22"], ["lobe", "#3cb371"], ["rail", "#4169e1"], ["wall", "#5dade2"], ["front", "#c0392b"],
          ["skirt", "#d35400"], ["deck", "#8e44ad"], ["rear", "#c0392b"], ["fwall", "#a93226"], ["fside", "#d35400"],
          ["fdeck", "#7d3c98"]];
function base(p) = let(n = len(p)) n > 2 && p[n - 2] == "_" ? [for (k = [0 : n - 3]) p[k]] : p;
function str_of(l, k = 0) = k >= len(l) ? "" : str(l[k], str_of(l, k + 1));
function bname(p) = let(b = base(p)) is_string(b) ? b : str_of(b);
function col(p) = [for (c = colors) if (c[0] == bname(p)) c[1]][0];

module left(b) {
    if (b == "nose") nose();
    if (b == "lobe") lobe_l();
    if (b == "rail") rail_l();
    if (b == "wall") wall_l();
    if (b == "front") front_l();
    if (b == "skirt") skirt_l();
    if (b == "deck") deck_l();
    if (b == "rear") rear();
    if (b == "fwall") fwall();
    if (b == "fside") fside_l();
    if (b == "fdeck") fdeck();
}
module piece(p) {
    b = bname(p);
    if (len(p) > 2 && p[len(p) - 1] == "r" && p[len(p) - 2] == "_") mirror([1, 0, 0]) left(b); else left(b);
}
// on the bed: the left piece's low face along its thin axis down (where the
// holes' tapers are); a right piece is its mirror image on the bed
module print_left(b) {
    if (b == "wall") translate([0, 0, 3 * u + u / 2 - e]) rotate([0, -90, 0]) wall_l();
    else if (b == "skirt") translate([0, 0, 8 * u + u / 2 - e]) rotate([0, -90, 0]) skirt_l();
    else if (b == "front") translate([0, 0, -(5 * u - u / 2 + e)]) rotate([90, 0, 0]) front_l();
    else if (b == "rear") translate([0, 0, -(-5 * u - u / 2 + e)]) rotate([90, 0, 0]) rear();
    else if (b == "fwall") translate([0, 0, -(12 * u - u / 2 + e)]) rotate([90, 0, 0]) fwall();
    else if (b == "fside") translate([0, 0, 8 * u + u / 2 - e]) rotate([0, -90, 0]) fside_l();
    else if (b == "fdeck") translate([0, 0, -(cc([0, 0, 5])[2] - u / 2 + e)]) fdeck();
    else if (b == "rail") translate([0, 0, -(cc([0, 0, 2])[2] + rail_dz - u / 2 + e)]) rail_l();
    else if (b == "deck") translate([0, 0, -(cc([0, 0, 5])[2] - u / 2 + e)]) deck_l();
    else translate([0, 0, -(z_k0 - u / 2 + e)]) left(b);
}

// ---------- the robot (a stand-in from the scan) ----------

module robot() {
    color("#e8e8e8") translate([0, 0, deck_lo - 1.5]) linear_extrude(1.5) polygon(cutebot_lower_deck);
    color("#e8e8e8") translate([-25, -33, deck_hi - 1.5]) cube([50, 66, 1.5]);   // upper deck: the scan photo's outline, roughly
    color("#f0c040", 0.8) translate([battery[0][0], battery[1][0], deck_hi]) cube([battery[0][1] - battery[0][0], battery[1][1] - battery[1][0], battery[2] - deck_hi]);
    color("#333") for (s = [-1, 1]) translate([s < 0 ? -55.26 : 36.74, 0, axle_z]) rotate([0, 90, 0]) cylinder(r = wheel_r, h = s < 0 ? 16.45 : 17.23, $fn = 64);
    color("#2e7d32") translate([-26.91, 50.62, 26]) cube([51.6, 1.6, 42]);         // micro:bit
    color("#222") for (x = [-28.5, 26]) translate([x, 48, deck_lo]) cube([2.5, 8, 10.5]);   // the edge connector's ends (scan, ~30.7 high)
    color("#222") translate([-5.1, 69.3, deck_lo]) cube([10.2, 2.5, 8.5]);           // sonar socket (guessed size)
    color("#ffd400") for (p = lights_xy) translate([p[0] - 3, p[1] - 2, deck_lo]) cube([6, 4, 1]);
    color("goldenrod") {
        for (p = [[-32, 64], [-8, 80], [8, 80], [32, 64]]) translate([p[0], p[1], deck_lo - 0.01]) cylinder(d = 6.5, h = 1.5);
        for (x = [-16, 16], y = [-8, 8]) translate([x, y, deck_hi - 0.01]) cylinder(d = 6.5, h = 1);
    }
    color("#555") for (x = [-16, 16], y = [-24, 24]) translate([x, y, deck_hi - 0.01]) cylinder(d = 6, h = 2.5);
}

module caster_placed() translate([0, nose_face, caster_top]) caster();

// ---------- the joints' 2L pins and the screws (for the views) ----------

// a pin centred on the boundary between two cells: at p, along axis a
module pin_at(p, a) translate(p) rotate(a == 0 ? [0, 0, 90] : a == 2 ? [90, 0, 0] : [0, 0, 0]) pin_2l();
function between(c, a, s) = cc(c) + [for (n = [0 : 2]) n == a ? s * u / 2 : 0];   // c's face toward +-a
module pins_l() {
    for (j = [-2, 0, 2]) pin_at([-16, u * j, deck_hi], 2);                          // rail into the deck's pin holes
    for (j = [-3, -1, 1, 3]) {
        pin_at(between([-3, j, 2], 2, 1), 2);                                       // rail - wall
        pin_at(between([-3, j, 4], 2, 1), 2);                                       // wall - deck
        pin_at(between([-8, j, 4], 2, 1), 2);                                       // skirt - deck
    }
    for (i = [-7, -5]) pin_at(between([i, 5, 4], 2, 1), 2);                         // front bulkhead - deck
    for (i = [-7, -5, -3]) pin_at(between([i, -5, 4], 2, 1), 2);                    // rear bulkhead - deck
    for (k = [1, 3]) { pin_at(between([-8, 4, k], 1, 1), 1); pin_at(between([-8, -4, k], 1, -1), 1); }   // skirt - bulkheads
    for (i = [-6, -5]) pin_at(between([i, 6, 0], 1, -1), 1);                        // lobe - front bulkhead
    for (i = [-2, -1]) pin_at(between([i, 11, 0], 1, 1), 1);                        // nose - front wall
    for (k = [1, 3]) { pin_at(between([-8, 6, k], 1, -1), 1); pin_at(between([-8, 11, k], 1, 1), 1); }   // front side - bulkhead, front wall
    for (j = [7, 9, 11]) pin_at(between([-8, j, 4], 2, 1), 2);                      // front side - front deck
    for (i = [-7, -5, -3, -1]) pin_at(between([i, 12, 4], 2, 1), 2);                // front wall - front deck
    for (i = [-8, -6, -4]) pin_at(between([i, 5, 5], 1, 1), 1);                     // deck - front deck
}
module pins() { pins_l(); mirror([1, 0, 0]) pins_l(); pin_at(between([0, 11, 0], 1, 1), 1); }
module screw_at(p, zb) translate([p[0], p[1], zb]) color("#9aa") {
    translate([0, 0, screw_floor]) cylinder(d = 5.5, h = 3);
    translate([0, 0, screw_floor - 6]) cylinder(d = 3, h = 6);
}
module screws() {
    for (p = [[-8, 80], [8, 80], [-32, 64], [32, 64]]) screw_at(p, deck_lo);
    for (x = [-16, 16], y = [-8, 8]) screw_at([x, y], deck_hi);
}

// ---------- output ----------

if (part == "all") {
    for (p = pieces) color(col(p)) piece(p);
    robot();
    caster_placed();
    color("#222") pins();
    screws();
}
else if (part == "robot") robot();
else if (part == "caster") caster_placed();
else if (part == "pins") pins();
else if (part == "screws") screws();
else if (part == "clash") intersection() {
    union() { for (p = pieces) piece(p); caster_placed(); }
    robot();
}
else if (len(part) > 6 && [for (k = [0 : 5]) part[k]] == ["p", "r", "i", "n", "t", "_"]) let(p = str_of([for (k = [6 : len(part) - 1]) part[k]]))
    if (len(p) > 2 && p[len(p) - 1] == "r" && p[len(p) - 2] == "_") mirror([1, 0, 0]) print_left(bname(p)); else print_left(bname(p));
else piece(part);
