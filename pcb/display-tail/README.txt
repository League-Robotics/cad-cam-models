DISPLAY TAIL - REVISION A - 2026-11-14 (designed and checked; NOT cut)

A 23.4 x 22.3 x 1.4 mm single-sided milled board that joins a robot's 4P4C
cable to the Waveshare ESP32-S3-Touch-LCD-1.69 ("robot display",
/Volumes/Proj/proj/robot-projects/watch-display). One 4P4C jack, the stocked
Amphenol 73306-111LF (latch up, the rev B adapter's footprint), and four pads
that solder to four of the eleven pads on the BACK of the display's PCB.
Copper on ONE side, the side away from the display. No mask, no silk, all
spare copper cleared. Project: /Volumes/Proj/proj/CAD/gears/pcb/display-tail/

2026-11-14, evening (Eric, via the watch-display session): the link is a UART,
not I2C (display RX = pad 17, TX = pad 18, 3.3 V, 115200 8N1; the copper is
the same, only the names changed), and the tail and jack are enclosed by the
display's case, so the jack moved to the far end with its mouth facing away
from the display, where the case's end wall is. Later that evening Eric picked
the robot end: Nezha port J2, on which the micro:bit's TX is P12 and RX is
P2 (source: ELECFREAKS pxt-PlanetX wifi.ts initWIFI(): J1 P8/P1, J2 P12/P2,
J3 P14/P13, J4 P16/P15 as TX/RX). The nets are unchanged by that. Which
4P4C CONTACT carries each of GND, 3V3, TX and RX on the Nezha J2 jack is
still UNVERIFIED (see WIRING and ASSUMPTIONS 4). Do not cut anything yet.

Two ways of joining were drawn (gears/view/display_tail_options.png) and
Eric chose the BUTT one on 2026-11-14 ("B, butted edge-on"):
 display-tail-butt  the tail lies in the display's plane, butted 1.2 mm off
                    the pad edge (room for the LCD flex), copper face level
                    with the display's back; a flat 0.64 mm square pin lies
                    along each 1.7 x 3.0 tail pad and the display pad and is
                    soldered to both. This is the live design.
 display-tail-lap   (archive/lap-variant, not chosen) the tail lapping 3.0 mm
                    under the display's back, soldered through 1.0 mm holes
                    in ring pads; it needed 3.3 mm of free board behind the
                    pad edge, which the STEP model does not promise.
The case (robot-projects/watch-display, case/) extends past the pad edge
and encloses the whole tail and jack (66.8 mm end to end): a 24.4-wide slot
in the pad-edge wall from 1.7 above to 1.5 below the PCB's back face, a
pocket 0.5 round the jack body, and a plug opening in its end wall of
11.8 x 15.3 (0.3 beyond the jack each side, from 0.3 above the copper face
to 1.0 beyond the jack's top, so the latch is clear), centred on the jack. The case was built from this
tail's numbers on 2026-11-14; if the tail changes, tell that project.

WIRING (netlist checked by scripts/check_and_draw.py against this table)
 Net       J1 jack contact  Display pad (J2 pin)  Display function (UART)      Robot side (Nezha J2)
 GND       1                G                     ground                       GND
 +3V3      2                3V3                   3.3 V regulator output       3V3
 DISP_TX   3                18                    GPIO18, the display's TX     robot RX = micro:bit P2
 DISP_RX   4                17                    GPIO17, the display's RX     robot TX = micro:bit P12
The other seven display pads (3, 2, SCL, SDA, TX, RX, 5V) are left alone;
SCL/SDA and TX/RX there are the display's INTERNAL bus and USB console.
J1 contact numbering is the rev B adapter's: 4 3 2 1 left to right looking
into the latch-up mouth (pcb/README.md, "Wiring and assembly"). WHERE THE
CONTACT ASSIGNMENT CAME FROM: it is NOT from a Nezha J2 pinout; none was
found in Eric's repos. It is carried over from the rev B adapter's Nezha
I2C-port cable, whose colours Eric confirmed: black GND contact 1, red 3V3
contact 2, green SCL contact 3, yellow SDA contact 4. The GUESS is that the
J2 port's cable has the same colour-to-contact order and that the micro:bit
TX (P12) sits where SDA/yellow was (contact 4) and RX (P2) where SCL/green
was (contact 3). If a J2 cable proves otherwise, the fix is to swap the two
signal nets on J1 in build.py (JACK_PADS) and rebuild; the copper routing
stays the same. Whatever the cable, the robot's TX must land on pad 17 and
its RX on pad 18. On this board, mouth up (away from the display), J1's pads run
left to right 1 GND, 2 3V3, 3 DISP_TX, 4 DISP_RX. GND and 3V3 go up and
round the right of the jack, 18/17 down and round the left through a
two-track band between the jack's pads and the display pads: no crossover.

ORIENTATION
Board frame: x across, y DOWN the board, seen from the copper side, which is
the display's back (component) side. The display's pad edge runs along the
bottom edge of the tail; pad 18 is at the LEFT, the display's buttons
(RST/BOOT/PWR) side, G and 5V toward the right, the USB-C side. The jack is
centred across the tail at its far end, its mouth face 1.0 mm inside the
tail's far edge, facing AWAY from the display; its body stands on the copper
side (the lid side of the case), 14 mm tall with the latch away from the
board. The glass overhangs the pad edge by 3.0 mm on the other side of the
display; the tail never reaches it.

DISPLAY NUMBERS (Waveshare's dimension drawing, wiki FAQ and STEP model;
NOTHING MEASURED ON THE REAL BOARD YET)
 PCB 29.85 x 37.14 x 1.0. The 11 pads run along a SHORT edge, 2.15 mm pitch
 (FAQ: "spacing between the 11 tp points on the back ... 2.15mm"; the
 drawing's 4.16 from the corner + 10 x 2.15 + 4.16 = 29.82 agrees), centres
 1.84 mm in from the edge, order 18 17 3 2 SCL SDA TX RX 3V3 G 5V from the
 buttons-side corner. They are oval back-side pads, about 1.0 x 1.9 (a guess
 from the photo), NOT castellations. The LCD flex wraps that edge (0.9 mm
 past it at PCB level). Parts on the back near the edge, from the STEP: RTC
 socket from 2.2 mm in beside G/5V (the photo suggests ~3.5), buzzer and the
 flex connector from 2.6 in, deeper parts 4.4 below the back.
 Tail pad 18 is at x = 1.5, so the tail's left edge is 2.66 inside the
 display's buttons-side edge and its right edge 3.8 inside the USB-side edge.

ASSUMPTIONS TO CHECK BEFORE CUTTING
1. Pad pitch and inset: measure pad 18 centre to pad G centre (should be
   9 x 2.15 = 19.35) and the edge to a pad centre (1.84). PITCH, INSET and
   X18 are constants at the top of scripts/build.py.
2. Where the LCD flex lies at the pad edge: the tail sits 1.2 mm off the
   edge (GAP in build.py) to clear it, and the pins pass over it to the
   pads; make sure a pin or the iron cannot touch the flex.
3. The display pads' length: the pin must reach from the tail pad (its
   far end 4.4 mm from the display edge) onto the display pad (0.8 to
   2.9 mm in): 7 mm pins laid from the tail pad's FAR end, 3.8 mm
   overhanging the tail, 2.6 mm onto the display pad. Confirm the pad
   ends on the board. Do NOT use longer pins or let a pin's far end pass
   the tail pad: under pads 18 and 17 the two band tracks run only 0.6 and
   1.4 mm beyond the pad end (an 8 mm pin with 3.5 mm overhang, as this
   README said until 2026-11-14 evening, would have shorted pad 18 to the
   DISP_RX band track).
4. The jack contact order on the Nezha J2 port: GUESSED from the I2C-port
   cable (see WIRING), not read from a Nezha pinout or measured. Before
   cutting, check on a Nezha J2 jack (or its cable, with the Nezha powered
   off) which contact is GND, 3V3, P12 and P2; before power, plug in the
   unpowered cable and check continuity from each plug contact to the
   display pad (P12 to 17, P2 to 18, GND to G, 3V3 to 3V3), and for shorts
   between the four nets.
5. The tail is 1.4 thick, the display 1.0; the copper faces are set level,
   so the tail's top stands 0.4 above the display's PCB top, 1.6 below the
   LCD module's underside (the case slot allows 1.7).

PARTS (per board) - see parts.csv
 J1  Amphenol 73306-111LF 4P4C jack (stock; Mouser 649-73306-111LF,
     DigiKey 609-4469-1-ND; manufacturer drawing 73306 rev M, kept at
     pcb/references/Amphenol-73306-revM.pdf). Dimensions below.
 P1  four 0.64 mm square header pins, 7 mm long (cut from a header strip).
No resistors or other parts.

JACK DIMENSIONS (Amphenol 73306-111LF, drawing 73306 rev M, sheet 1; mm)
 Housing 11.18 wide at the mouth, 12.7 deep (mouth face to rear, at the
 top), 14.0 +-0.1 tall above the hold-down bearing plane (= the copper
 face). The rear view is drawn 11.68 wide and the base 11.68 deep (the
 rear is undercut 1.02 at the bottom); the housing underside stands
 0.35 +-0.05 above the board on two standoffs. The four solder tails
 leave the rear at the base and reach 4.31 past it (15.99 from the mouth
 face; the lands run 12.7 to 16.1), with a 1.8 flat foot, 0.4 wide, 0.2
 thick, 1.27 pitch. Hold-down tabs on 2.35 x 5.5 lands at +-5.2, 2.8 to
 8.3 from the mouth face. Read off the mouth view at 22 px/mm (+-0.2):
 plug opening 7.9 wide, floor 3.3 above the board, 7.1 tall (to 10.4),
 then a 5.75-wide step 1.9 tall (latch lever room, to 12.3) and a
 2.6-wide keyway 0.9 tall (to 13.2) under the 0.8 roof. Guessed, not on
 the drawing: cavity depth 10, undercut height 2, how far forward the
 11.68-wide rear runs (2), tab leg height 4.5, the springs' shape.
 On this board (case frame): housing x -5.0..+6.2 (-5.3..+6.4 at the
 rear), y 9.8..22.5 (mouth face at 22.5, 1.0 inside the tail's far edge),
 z 0.35..14.0; tails to y 6.5; plug opening x -3.4..+4.5, z 3.3..13.2.

HOLES
 None. The display pads are 2.15 mm apart, so the guideline's 1.8 mm wire
 holes in 1/8 in square pads do not fit; the pins are soldered flat on
 1.7 x 3.0 pads instead (0.45 mm between adjacent pads 18/17 and 3V3/G).
 The pads sit 0.2 mm from the tail's display edge (x 1.5, 3.65, 18.7, 20.85;
 y 19.1 to 22.1 from the top edge). The jack's own pads end at y 17.1 and
 the two tracks to 18 and 17 run at y 17.7 and 18.5 between them.

MACHINING - cam/
 display-tail-butt-A-2up-clear-cut155.nc: two boards side by side in a
 55.8 x 28.3 mm free area, copper up, nothing mirrored, G54 at the area's
 lower-left, display edges at the bottom, jack mouths at the top. Tools
 are the standard buildout: T4 30-degree V-bit (Z-0.12, two passes round the
 copper, then the narrow gaps), T3 1.0 mm flat end mill (Z-0.10, clears the
 rest, 0.3 from copper), T5 0.8 mm corn cutter (holes, then outlines to
 Z-1.55 in 0.25 steps, climb). Three 1.5 mm tabs a board leaving 0.5 mm, on
 the left, right and jack edges, none on the display edge (that edge must be
 clean to butt against the display: file the other stubs flush). 12,000 RPM,
 300 mm/min, plunges 100. The vacuum is switched by the program (M851 S100
 after every M3, M852 after every M5). About 19.6 minutes of motion plus
 probing and two tool changes. Offline checks:
 cam/validation.json. NOT test-cut; nothing moves without Eric's go-ahead.

ASSEMBLY
 Fit the jack first (SMT, on the copper side, hold-down tabs too; the four
 traces run under its body, which is plastic). Tack the
 four pins flat on the tail pads, each starting at the pad's FAR end (the
 jack side) and overhanging the display edge by 3.8 mm (7 mm pins), lay
 the tail copper-side-level with the display's back, 1.2 mm off its edge
 (a 1.2 mm shim between them helps; the case slot locates it later), and
 solder each pin to its display pad: 18, 17, 3V3, G.
 Keep solder off the bare tracks (no mask), check continuity and the
 six pairs for shorts before power. 3.3 V into the 3V3 pad back-feeds the
 display's regulator (see the watch-display README); the robot port must be
 3.3 V.

FILES
 design/display-tail-butt                            KiCad 9 project
 exports/display-tail-butt/schematic.pdf             schematic
 exports/display-tail-butt/fabrication/              Gerbers for a board house
 exports/display-tail-butt/milling/                  simplified Gerbers
 exports/display-tail-butt-review.{png,svg,pdf}      labelled board picture (also gears/view/)
 archive/lap-variant/                                the lap variant, complete, not chosen
 exports/layers.json                                 copper and outlines as polygons (CAM input)
 cam/                                                NC programs, job.json, strip layouts, validation.json
 checks/                                             geometry, ERC, DRC, netlists
 scripts/options_pic.py                              the two-option picture (gears/view/display_tail_options.png)
 scripts/display_back_profile.py                     the STEP/STL slicing that gave the back-side numbers
 scripts/make_viewer_stls.py                         the viewer pieces below (runs on the Mac with uv)
 exports/viewer/                                     one binary STL per material in the CASE frame (pad edge
                                                     y=0 away from the display, x=0 display centre +buttons,
                                                     z=0 copper face +lid): tail_fr4, tail_copper, tail_pads,
                                                     tail_pins, jack_body, jack_metal; manifest.json (bounds,
                                                     frame, jack numbers); display-tail-viewer-pieces.png

REGENERATION ON BUZZKILL (eric@buzzkill:~/projects/gears-pcb/display-tail,
with ../design/Adapter.pretty for the jack footprint; rsync from this folder)
 python3 scripts/build.py          CAD, from the constants at its top (add display-tail-lap to build that too)
 python3 scripts/export.py         ERC/DRC (fails on any violation), netlists, PDFs, Gerbers
 python3 scripts/dump_layers.py    exports/layers.json
 python3 scripts/make_cam.py       the NC programs (shapely only; also runs on the Mac with uv)
 python3 scripts/check_and_draw.py independent checks, review pictures, validation.json
KiCad 9.0.8, pcbnew Python, Shapely 2.1.2, matplotlib. build.py overwrites
the CAD; preserve manual edits before running it again.

REFERENCES
 Waveshare wiki: https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-1.69
 (dimension drawing ESP32-S3-Touch-LCD-1.69_Dim.jpg, pinout details-5.jpg,
 schematic V2.1, 3D model zip); local copies in
 /Volumes/Proj/proj/robot-projects/watch-display/ref/waveshare/
 Amphenol 73306: ../references/Amphenol-73306-revM.pdf (the adapter's copy)
 Guidelines: http://robot-garage.home/cad-design-projects/guidelines
