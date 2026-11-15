// The assembly pulled apart for the picture of how the lid joins the shell.
// `use`, not `include`: the main file's part switch must not render.
use <robot_display_case.scad>
color("SteelBlue", 0.85) shell();
color("DarkOrange") translate([0, 0, -14]) lid_lego();
color("ForestGreen", 0.6) translate([0, 0, -4]) board_env();
