NEZHA WIRE HUB - REVISION A - 2026-10-29

A 26 x 16 mm passive 3.3 V I2C adapter, separate from the earlier 4P4C-jack
adapter. Project: /Volumes/Proj/proj/CAM/nezha-qwiic/wire-hub/

CONNECTIONS
J1: four stripped cable wires; insert from top and solder underneath.
J2: four-position 2.54 mm FEMALE through-hole header, on top.
J3: four-position 2.54 mm MALE through-hole header, on top.
J4: four-position 2.00 mm JST PH through-hole socket/header, on top.
J5: four-position 1.00 mm JST SH/Qwiic surface-mount socket, underneath.
The four wire holes and all four connectors are electrically in parallel.
All solder joints and all manufactured copper are on the BOTTOM.

Every connector uses pin 1=GND, 2=3V3, 3=SDA, 4=SCL.
Viewed from TOP with wire holes on the LEFT, wire holes run top-to-bottom:
BLACK (GND), RED (3V3), YELLOW (SDA), GREEN (SCL).
Spread the two loose signal wires into their labeled holes; do not copy the
black/red/green/yellow physical order of the telephone plug contacts.
This removes the need for a crossover resistor. No active parts or pull-ups.
J4 PH uses this board's stated pinout; PH itself does not define a signal order.
Use 3.3 V I2C ports. This is not a motor-power or 5 V level-conversion adapter.

PARTS
One each per board; 25 each for a completely populated sheet:
J2 Harwin M20-7820442 (female, 2.54 mm, 8.5 mm body height).
J3 Harwin M20-9990446 (male, 2.54 mm, vertical).
J4 JST B4B-PH-K-S(LF)(SN) (PH, 2 mm, vertical through-hole).
J5 JST BM04B-SRSS-TB(LF)(SN) (SH, 1 mm, top-entry SMT).
J5 is the same selected part as the older adapter. The standard JST SH/Qwiic
PCB sockets are SMT; no through-hole substitute is used.
See parts.csv for supplier links. No purchasing/cart changes were made.
Optional PH mating cable: PHR-4 housing with compatible JST PH contacts or a
preassembled PH cable; verify its pin order before using it.

HOLES AND FOOTPRINTS
16 unplated solder holes per board. No vias or plated barrels are required.
Wire holes: 1.10 mm diameter, 2.10 mm lands, 2.54 mm pitch.
Male/female header holes: 1.05 mm diameter, 2.00 mm lands, 2.54 mm pitch.
The Harwin female drawing calls for 1.02 +/- 0.05 mm finished holes.
PH holes: 0.90 mm diameter, enlarged 1.60 x 2.00 mm oval/rectangular lands,
2.00 mm pitch. The PH hole is intentionally larger than the standard KiCad
0.75 mm hole to allow milling with the existing 0.8 mm corn bit. Check the
first connector's fit before populating the sheet. Minimum PH annulus 0.35 mm.
The Qwiic land pattern retains KiCad/JST dimensions, including both anchor tabs.
Main tracks 0.60 mm wide; Qwiic fanout tracks 0.40 mm. No copper pours.

KiCad represents the solder holes using through-hole electrical pads with
unused layers removed and Keep Top/Bottom disabled. All top annuli are
suppressed, confirmed by the validation script. The fabrication drill file
explicitly marks all holes NON_PLATED. The pads remain connected on B.Cu.

FABRICATION / CAM ORIENTATION
The editable design and fabrication Gerbers use normal TOP-view coordinates.
Fabrication: one bottom copper layer; 26 x 16 x 1.4 mm; all holes unplated.
Ask a fabricator to quote this single-sided specification; it is not a
conventional two-layer plated-hole ordering preset.

The separate machining-only artwork is mirrored ONCE to show bottom copper
face-up. The machine transform from top-view board coordinates is:
X = board-placement-X + 26 - top-X
Y = board-placement-Y + 16 - top-Y
Do not mirror the CAM Gerbers or finished G-code again.

PANEL
25 boards, 5 columns by 5 rows, in fresh 150 mm X by 100 mm Y stock.
Board width 26; height 16; gutters 2; nominal border 6 mm on every side.
Lower-left origins X = 6,34,62,90,118; Y = 6,24,42,60,78 mm.
Each board has four 2 mm-wide tabs retaining 0.5 mm thickness.
The board outlines occupy X6..144 / Y6..94; cutter sweeps extend to
approximately X5.2..144.8 / Y5.2..94.8. Clamp and dust-shoe clearance must
extend beyond that envelope. Full-area flat tape support is preferred.
See cam/READ-ME-FIRST.txt before using either machining file.

ASSEMBLY
Use exports/assembly-preview.pdf for top/bottom orientation.
Deburr the holes and edges, remove isolation debris and clean the copper.
Fit the bottom SMT Qwiic socket first, including both mechanical anchors.
Insert top headers and PH connector, then solder their pins on the bottom.
Keep solder fillets clear of adjacent exposed tracks; milled boards have no
solder mask. Insert/tin/trim the four wires and solder them in the labeled order.
Secure the cable jacket to the board/enclosure so pulls do not load the joints.
Check all five connectors for continuity on each signal, and check all six
signal pairs for shorts before connecting power. Verify the actual Nezha
cable with a meter; the photographs do not establish electrical continuity.

FILES
 design/nezha-wire-hub.kicad_pro - editable KiCad project
 design/nezha-wire-hub.kicad_sch - schematic
 design/nezha-wire-hub.kicad_pcb - individual board
 exports/schematic.pdf - schematic drawing
 exports/assembly-preview.pdf - annotated top and bottom views
 exports/fabrication/ - single-board Gerbers and unplated drill file
 exports/milling/ - mirrored-once machining input files
 cam/panel-layout.pdf - full-stock layout
 cam/validation.json - offline checks and final NC hashes
 parts.csv - board BOM with 1-board and 25-board quantities
 references/ - manufacturer drawings and source URLs

REGENERATION ON BUZZKILL
Working copy: /home/ros/projects/nezha-qwiic/wire-hub/
 python3 scripts/build_wire_hub.py
 python3 scripts/export_wire_hub.py
 python3 scripts/make_cam.py
 python3 scripts/check_and_draw.py
 python3 scripts/package.py
Build regenerates CAD; preserve manual edits before running it again.
KiCad 9.0.8, footprint library 9.0.7, pcb2gcode 3.0.4 and Shapely 2.1.2.

REFERENCES
JST SH: https://www.jst-mfg.com/product/pdf/eng/eSH.pdf
JST PH: https://www.jst-mfg.com/product/pdf/eng/ePH.pdf
Qwiic pinout: https://www.sparkfun.com/qwiic
Harwin: https://www.harwin.com/products/M20-7820442
Harwin: https://www.harwin.com/products/M20-9990446
Makera: https://wiki.makera.com/en/carvera/manual/software
KiCad library-derived JST geometry retains its upstream license; see
 design/KICAD-LIBRARY-COPYRIGHT.txt.
