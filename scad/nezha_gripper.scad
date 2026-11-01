// Gripper on the Nezha motor: gear nubs (swap_gripper.scad) on the motor axle
// and the idler axle, in gripper.scad's 1U frame, taking the swappable can,
// cube and ball arms.
// part: "assembly", "motor_nub", "idler_nub", "frame" (printable, as placed
// in the assembly) or "clash" (what the arms hit in the frame and motor at
// theta; empty = clear).
// show: in the assembly, "all" or one component in place (for viewers that
// colour each STL): "motor_nub", "idler_nub", "left_ext", "right_ext",
// "frame", "motor".

use <gripper.scad>
use <swap_gripper.scad>

theta = 0;
ext = "can";        // swappable arm shown: "can", "cube", "cube_low", "ball"
part = "assembly";
show = "all";
motor_axis = [54.3, 19.7];
idler_axis = [78.3, 19.7];
gear_y = 21.0;
$fn = 48;

module at(p) translate([p[0], gear_y, p[1]]) rotate([90, 0, 0]) children();

// gripper.scad's frame with the right end-wall notch taken down to the bottom
// plate: past ~48 deg the idler nub's stub swings below the old notch.
module nezha_frame() difference() {
  frame();
  translate([89, 13.0, 7.6]) cube([10, 21.4 - 13.0, 3]);
}

function shown(c) = show == "all" || show == c;

module arms(t) {
  at(motor_axis) rotate(t) {
    if (shown("motor_nub")) color("orange") nub_arm(-1);
    if (shown("left_ext")) color("mediumseagreen") arm_part(ext);
  }
  at(idler_axis) rotate(-t) {
    if (shown("idler_nub")) color("royalblue") nub_arm(1);
    if (shown("right_ext")) color("mediumseagreen") handed(1) arm_part(ext, 1);
  }
}

if (part == "motor_nub") nub_arm(-1);
else if (part == "idler_nub") nub_arm(1);
else if (part == "frame") nezha_frame();
else if (part == "clash") intersection() {
  arms(theta);
  union() { nezha_frame(); import("models/nezha_motor.stl"); }
}
else {
  arms(theta);
  if (shown("motor")) color("hotpink") import("models/nezha_motor.stl");
  if (shown("frame")) color("lightgray") nezha_frame();
}
