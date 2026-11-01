// Swappable arms (swap_gripper.scad) on the Nezha motor gripper (gripper.scad).
// part = "clash" leaves only what the jaws hit in the frame and motor at theta.

use <gripper.scad>
use <swap_gripper.scad>

theta = 0;
arm = "cube";       // "can", "cube", "ball"
part = "assembly";  // "assembly", "clash" or "frame"
motor_axis = [54.3, 19.7];
idler_axis = [78.3, 19.7];
gear_y = 21.0;

module at(p) translate([p[0], gear_y, p[1]]) rotate([90, 0, 0]) children();
function arm_color(a) = a == "can" ? "tomato" : a == "ball" ? "mediumpurple" : "mediumseagreen";

// gripper.scad's frame with the right end-wall notch taken down to the bottom
// plate: past ~48 deg the idler nub's stub swings below the old notch.
module swap_frame() difference() {
  frame();
  translate([89, 13.0, 7.6]) cube([10, 21.4 - 13.0, 3]);
}

module jaws(t) {
  at(motor_axis) rotate(t) { color("orange") nub_arm(-1); color(arm_color(arm)) arm_part(arm); }
  at(idler_axis) rotate(-t) { color("royalblue") nub_arm(1); color(arm_color(arm)) handed(1) arm_part(arm); }
}

if (part == "frame") swap_frame();
else if (part == "clash") intersection() {
  jaws(theta);
  union() { swap_frame(); import("nezha_motor.stl"); }
}
else {
  jaws(theta);
  color("hotpink") import("nezha_motor.stl");
  color("lightgray") swap_frame();
}
