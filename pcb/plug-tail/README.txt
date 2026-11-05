NEZHA 4P4C PLUG TAILS - REVISION C - 2026-11-04

REV C (the user, 2026-11-04): the servo tail is now the HEADER TAIL
(design/header-tail), 10.0 x 19.0, with all FOUR lines out on four flat 2.54
pins in plug-contact order: GND, VCC, S1, S2 (cable black, red, green,
yellow). A servo plug goes on G V S1; a J-port device uses all four. Program
cam/plug-tails-C-4up-iso120-cut155.nc, area 53 x 30. Rev B is in
archive/rev-B; the 3-pin servo tail's files were moved out of the live tree.

REV B (the user, 2026-11-04): the narrow tongue is 10 mm long, not 6, and the
pin pads run 10 mm along it (0.25-10.25 from the tip), so the wires/pins from
the plug have more length on the board. Everything behind the tongue moved
4.8 mm back (4 for the tongue + 0.8 so each trace bend stays 0.75 past the
pads, as in rev A). Servo tail 8.0 x 19.0, Qwiic tail 9.0 x 24.0. Program
cam/plug-tails-B-4up-iso120-cut155.nc, area 49 x 30. Rev A is in archive/rev-A.
The rest of this file was written for rev A; its sizes are rev A's.


A sliver of board that slides into the cable cavity at the back of a 4P4C
plug. Four square header pins (0.64 mm, double length) lie in the plug's wire
channels where the cable conductors would be, and are soldered flat onto the
board's pads. The board then carries the signals out to a different
connector. Two tails share the same plug end:

 servo-tail  8.0 x 14.2 mm  three flat 2.54 mm pins for a servo plug (G V S)
 qwiic-tail  9.0 x 19.2 mm  side-entry JST SH (Qwiic) socket, 0R crossover

Everything is surface-mount on ONE copper layer, the top. No holes, no vias.

PLUG END (both boards)
Tongue 5.30 mm wide x 6.0 mm long, for a cavity measured at about 5.5 x 3.15.
Pin pads: 4 at 1.02 mm pitch (the standard 0.040 in modular-plug spacing),
0.62 mm wide, 0.40 mm gaps, running 0.25-3.60 mm from the tongue tip.
The tongue tip goes in first and stops against the wall where the wire
channels start; the tongue is longer than the cavity is deep, so the step
where the board widens may stand a little proud of the plug's back face.
The 0.8 mm cutter leaves a 0.4 mm radius in the two inside corners at the
root of the tongue. No retaining tab is placed on the tongue.

Pad order, copper face toward the plug's CONTACTS, plug nose pointing away,
left to right: contact 1, 2, 3, 4.
 I2C port (from the first adapter): GND, 3V3, SCL, SDA.
 Servo port: ASSUMED GND, V, SIG, unused. NOT VERIFIED - see below.

ASSUMPTIONS TO CHECK BEFORE CUTTING
1. Servo port pinout and voltage. The servo tail routes contact 1 -> G,
   contact 2 -> V, contact 3 -> S and leaves contact 4 unconnected. Meter a
   servo port (or its cable) and say which contact is which, and what voltage
   is on V. If V is not between G and S in contact order, the single copper
   layer needs a crossover like the Qwiic tail's.
2. Pin pitch. 1.02 mm centre to centre, so pins 1 and 4 are 3.06 mm apart
   centre to centre, 3.70 mm across their outside edges. A 4.0 mm reading
   would mean 1.12 mm pitch; that is one constant in scripts/build.py.
3. Board thickness. Copper-up board under the pins: the board's top must sit
   at the underside of the pins. With 1.4 mm stock the pins ride 1.4 mm
   above the cavity floor and the stack (board + pin) is 2.04 of the 3.15 mm.
   Measure cavity floor to pin underside; thinner stock may be needed.
4. Cavity depth (back face to channel wall). The tongue is 6.0 mm long and
   the pads cover the first 3.6 mm; the pins need to lie on that stretch.
5. Which side of the pins the board sits. Board UNDER the pins with copper
   facing the contacts is assumed. If it has to go above them, copper facing
   the latch, the pad order reverses: mirror the layout.

ASSEMBLY (suggested order)
a. Solder the four pins flat on the tongue pads first, outside the plug,
   with the pins overhanging the tongue tip by the channel length.
b. Feed the pins into the plug's wire channels and slide the tongue into
   the cavity until the tip stops.
c. Crimp. The contact blades bite the pins and the strain-relief bar clamps
   the board. Check that all four contacts are pressed flush; a blade that
   stops on a solid pin and stands proud can jam the jack.
   (Crimping first and then sliding the board in also fits the geometry,
   but the joints are then soldered inside the cavity mouth.)
d. Servo tail: lay three 0.64 mm square pins on the 1.0 x 5.0 mm pads, with
   about 6 mm overhanging the end for the servo socket, and solder them.
   Standard pins pulled from a header are long enough; trim double-length
   ones to about 11 mm. Servo plug: brown/black on G, red on V, orange on S.
   Qwiic tail: fit R1 (insulated-body 0R 1206) and the SM04B socket,
   including both anchor tabs. R1 carries SCL over the SDA track.
e. Milled boards have no solder mask and the copper around the tracks is
   left in place (floating). Keep solder off it; check every pair of
   signals for shorts and each signal for continuity before power.

PARTS (per board) - see parts.csv
 Both:  one 4P4C plug; four 0.64 mm square double-length header pins.
 Servo: three more 0.64 mm square pins.
 Qwiic: JST SM04B-SRSS-TB(LF)(SN) side-entry socket; YAGEO RC1206JR-070RL.
 The Qwiic socket here is the HORIZONTAL SM04B, not the BM04B top-entry
 part used on the first adapter.

MACHINING - see cam/READ-ME-FIRST.txt
 cam/plug-tails-A-4up-iso120-cut155.nc: 2 servo + 2 Qwiic tails in a
 49 x 25 mm free area, copper up, G54 at that area's lower-left corner.
 Offline checks: cam/validation.json. Not test-cut.

FILES
 design/servo-tail, design/qwiic-tail  KiCad 9 projects
 exports/assembly-preview.pdf           both boards with pins and labels
 exports/<board>/schematic.pdf          schematics
 exports/<board>/fabrication/           Gerbers for a board house (F.Cu)
 exports/<board>/milling/               simplified Gerbers used for CAM
 checks/                                geometry, ERC, DRC, netlists

REGENERATION ON BUZZKILL (ros@buzzkill.local:~/projects/nezha-qwiic/plug-tail)
 python3 scripts/build.py          CAD, from the constants at its top
 python3 scripts/export.py         ERC/DRC (fails on any violation), Gerbers
 python3 scripts/make_cam.py       pcb2gcode isolation + generated outlines
 python3 scripts/check_and_draw.py independent checks, drawings
KiCad 9.0.8, pcb2gcode 3.0.4, Shapely 2.1.2. build.py overwrites the CAD.
