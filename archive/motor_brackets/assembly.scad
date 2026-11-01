// Shows a Part Designer bracket mounted on the motor envelope, both in the motor's frame.
// openscad -D 'part="cradle"' -D 'ox=-16' -D 'oy=-24' -D 'oz=-8' assembly.scad
part = "side_plate";
ox = 0; oy = 0; oz = 0;
show_motor = true;
if (show_motor) color("SteelBlue", 0.9) import("motor.stl");
color("Orange") translate([ox, oy, oz]) import(str("stl/", part, ".stl"));
