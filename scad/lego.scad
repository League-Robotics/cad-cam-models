// LEGO Technic features for our parts, all from Technic.scad (lib/Technic.scad,
// github.com/cfinke/Technic.scad). Include this file, not the library, so
// every part shares one copy and one set of overrides:
//
//     include <lego.scad>
//
// Then the library's modules (technic_beam, technic_pin, technic_axle, ...)
// and dimensions (technic_hole_diameter, technic_height_in_mm, ...) are all
// in scope. Don't hand-roll Technic geometry; add helpers here that take
// their shape from the library.

include <lib/Technic.scad/Technic.scad>

// The library sets $fa = 1, $fs = 0.05 (very fine meshes); parts set their own
// $fn, which takes precedence.

// A pin hole to subtract: the inside of the library's pin connector (bore
// technic_hole_diameter, counterbore at each face), `length` units long with
// its bottom face at z = 0. `ext` carries the counterbore out past both faces
// so the cut is clean.
module technic_pin_hole(length = 1, ext = 1) {
    cb_r = technic_pin_connector_outer_diameter / 2 - technic_pin_connector_shoulder_wall_thickness;
    h = technic_height_in_mm * length;
    difference() {
        cylinder(r = cb_r, h = h);
        technic_pin_connector(length = length);
    }
    translate([0, 0, -ext]) cylinder(r = cb_r, h = ext + 0.01);
    translate([0, 0, h - 0.01]) cylinder(r = cb_r, h = ext + 0.01);
}

// ---- Holes for parts we 3D print ----------------------------------------
// From Part Designer, the League's fork (lego3d.jointheleague.org,
// github.com/league-infrastructure/partdesigner, src/measurements.ts and
// config.ts, default settings). Its holes are tuned for printing; Technic.scad
// above is exact LEGO and is not. In Part Designer every outside face sits
// pd_edge in from the 8 mm cell, so one cell is pd_unit - 2 * pd_edge thick.
pd_unit = 8;
pd_edge = 0.2;            // edgeMargin
pd_cb_r = 3.2;            // interiorRadius: counterbore
pd_cb_depth = 0.89;       // pinHoleOffset: counterbore depth from the face
pd_pin_r = 2.475;         // pinHoleRadius: bore
pd_taper = 1.0;           // basePinTaper: cone from counterbore to bore on the bed face (35.94 deg)
pd_axle_half = 0.5 * 2.02; // axleHoleSize: half the width of the cross's arms
pd_fn = 32;               // subdivisionsPerQuarter 8, vertex at 0 deg
pd_cell = pd_unit - 2 * pd_edge;

// Printed pin hole to subtract, through a wall of thickness h with its bed
// (bottom) face at z = 0. taper: the cone on the bed face so the step prints
// without support (off: a flat step, as upstream Part Designer). ext carries
// the counterbore out past both faces for a clean cut.
module pd_pin_hole(h = pd_cell, taper = true, ext = 1) {
    t = taper ? pd_taper : 0;
    rotate_extrude($fn = pd_fn) polygon([
        [0, -ext], [pd_cb_r, -ext], [pd_cb_r, pd_cb_depth], [pd_pin_r, pd_cb_depth + t],
        [pd_pin_r, h - pd_cb_depth], [pd_cb_r, h - pd_cb_depth], [pd_cb_r, h + ext], [0, h + ext]]);
}

// Printed axle hole to subtract: the cross clipped by the bore circle, straight
// through (no counterbore or taper), bed face at z = 0.
module pd_axle_hole(h = pd_cell, ext = 1) {
    translate([0, 0, -ext]) linear_extrude(h + 2 * ext) intersection() {
        circle(r = pd_pin_r, $fn = pd_fn);
        union() {
            square([2 * pd_axle_half, 2 * pd_pin_r + 1], center = true);
            square([2 * pd_pin_r + 1, 2 * pd_axle_half], center = true);
        }
    }
}

// Exact LEGO pin hole as a plain profile (no connector geometry): the
// library's bore with its shoulder counterbore at both faces, `length` units
// long, bottom face at z = 0. The same hole as technic_pin_hole(), but one
// rotate_extrude, for models with hundreds of holes (robot_plate.scad).
module technic_pin_hole_fast(length = 1, ext = 1) {
    cb_r = technic_pin_connector_outer_diameter / 2 - technic_pin_connector_shoulder_wall_thickness;
    r = technic_hole_diameter / 2;
    d = technic_pin_connector_shoulder_depth;
    h = technic_height_in_mm * length;
    rotate_extrude() polygon([[0, -ext], [cb_r, -ext], [cb_r, d], [r, d], [r, h - d], [cb_r, h - d], [cb_r, h + ext], [0, h + ext]]);
}

// Exact LEGO pin hole going in from a face, blind: the bore `depth` deep
// (one cell, 8, takes half a 2L pin) with the shoulder counterbore at the
// face only. Face at z = 0, hole along +z.
module technic_blind_pin_hole(depth = technic_beam_hole_spacing, ext = 1) {
    cb_r = technic_pin_connector_outer_diameter / 2 - technic_pin_connector_shoulder_wall_thickness;
    r = technic_hole_diameter / 2;
    d = technic_pin_connector_shoulder_depth;
    rotate_extrude() polygon([[0, -ext], [cb_r, -ext], [cb_r, d], [r, d], [r, depth], [0, depth]]);
}

// Printed pin hole going in from a face, blind: counterbore and taper at the
// face (z = 0), bore to `depth` along +z, no counterbore at the far end (so it
// can stop short of a crossing hole). 8 deep takes half a 2L pin.
module pd_blind_pin_hole(depth = pd_unit, taper = true, ext = 1) {
    t = taper ? pd_taper : 0;
    rotate_extrude($fn = pd_fn) polygon([
        [0, -ext], [pd_cb_r, -ext], [pd_cb_r, pd_cb_depth], [pd_pin_r, pd_cb_depth + t], [pd_pin_r, depth], [0, depth]]);
}
