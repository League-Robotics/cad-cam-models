// Swappable arms (swap_gripper.scad) on the standard servo gripper
// (servo_gripper.scad): spline nub with the servo hub, idler nub on the LEGO
// axle, same frame. part = "clash" leaves only what the jaws hit in the frame
// and servo at theta (empty = clear).

use <servo_gripper.scad>
use <swap_gripper.scad>

theta = 0;
arm = "cube";       // "can", "cube", "ball"
part = "assembly";  // "assembly", "clash", "spline_nub" or "idler_nub"
show_servo = true;
spline_axis = -10;  // servo_gripper.scad, standard servo
idler_axis = 14;

module jaws(t) {
  on_axis(spline_axis) rotate(t) {
    color("orange") spline_hub() nub_body(-1);
    color(arm_color(arm)) arm_part(arm);
  }
  on_axis(idler_axis) rotate(-t) {
    color("royalblue") nub_arm(1);
    color(arm_color(arm)) handed(1) arm_part(arm);
  }
}
function arm_color(a) = a == "can" ? "tomato" : a == "ball" ? "mediumpurple" : "mediumseagreen";

if (part == "spline_nub") spline_hub() nub_body(-1);   // z = 0 on the bed, boss up
else if (part == "idler_nub") nub_arm(1);
else rotate([90, 0, 0])
  if (part == "clash") intersection() {
    jaws(theta);
    difference() {   // the spline itself sits in the socket by design
      union() { frame(); servo_model(); }
      translate([0, 0, spline_axis]) rotate([-90, 0, 0]) cylinder(r = 3.2, h = 100);
    }
  }
  else {
    jaws(theta);
    color("lightgray") frame();
    if (show_servo) color("dimgray") servo_model();
  }
