# Case for the robot display

`robot_display_case.scad`: a **shell** the display drops into from the back
(a 1.2 mm lip holds the glass from the front) and a **lid** that plugs into
the back. The LEGO lid is a 9 mm plate with a 5 x 4 grid of Technic pin holes
(Part Designer fits, through `gears/scad/lego.scad`), so the display pins onto
a beam or plate with two or more half-pins. The flat lid is a 2.5 mm plate for
gluing or velcro.

Outside 44.7 x 36.7 mm; 23.2 tall with the LEGO lid, 16.7 with the flat one.
`views.png` is the standard four-view picture; `bash ../tools/build.sh` makes
it, the STLs, the fit check and the labelled sections (`out/case_section.png`).

## Where the numbers come from

Everything under `[Measured]` in the .scad is from Waveshare's STEP model
(`ref/waveshare/ESP32-S3-Touch-LCD-1_69.stp`), sliced in FreeCAD on
2026-11-14. **Nothing has been measured on the real board.** The first thing
to do with the printed shell is drop the board in and check:

- the glass sits in its pocket (41.13 x 33.13, 0.2 clearance a side) with its
  chamfered edge just under the lip, and the face about 1 mm behind the lip;
- the USB-C plug reaches the socket through the 13 x 7.5 cutout;
- the three side buttons can be pressed through their 7 x 4 slots;
- the lid's plug is a push fit (0.15 clearance a side).

Frame: the STEP model's. X along the short axis (buttons at +x, USB at -x),
Y along the long axis (header pads and flex at -y), Z out of the screen. The
glass centre is at y = -1.275 and the case is centred on it.

Key model facts: glass 41.13 x 33.13, corner R 5.4, 1.75 thick, with a 2 mm
chamfer round its top edge; LCD module under it 38.0 x 30.07 (centre
y = -1.52); PCB 37.14 x 29.85 x 1.0; deepest component on the back 4.4 below
the PCB. The PCB's four corner mounting holes are not in the model; from
Waveshare's dimension drawing they are about 3 mm in from the corners, so a
later lid could carry locating pins.

## Our picks (2026-11-14)

- Walls 1.6, lip 1.2, lip overlaps the glass by 1.5 (on its chamfer).
- Under the glass a 0.6 flat ledge, then a 45° chamfer down to the cavity, so
  the shell prints face down with no overhang.
- Cavity 0.3 a side round the module; 0.5 between the deepest part and the lid.
- Header slot 28 x 4 in the -y wall, under the PCB, for a right-angle header
  or wires soldered to the pads.
- Lid held by friction; glue if loose. No screws: the walls are too thin and
  the PCB holes sit under the glass.
- No battery pocket: the robot powers it.

## Printing

`out/shell_print.stl` (face down, pocket up) and `out/lid_print.stl` (LEGO
face down, plug up), PLA, 0.4 nozzle. No supports. Not printed yet.

## History

- 2026-11-14: designed from the STEP model; fit check against a box envelope
  of the model passes with zero overlap. Not yet printed or checked on the
  real board.

- 2026-11-14: `case/joint_pic.py` draws how the lid joins the shell (`out/case_joint.png`,
  with the exploded view from `case/exploded.scad`). Eric asked how the parts connect:
  today it is a plain 2 mm push-fit plug, no snaps.
