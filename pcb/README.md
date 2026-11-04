# Carvera PCB projects

This folder holds the PCBs milled on the Carvera; each board has its own folder and README. It is `pcb/` in the gears CAD/CAM repo since 2026-11-03; the earlier history is in the old standalone repo, `/Volumes/Proj/proj/CAM/nezha-qwiic`. Buzzkill's working copy (`~/projects/nezha-qwiic`) is still where KiCad and pcb2gcode run.

- This top level: the Nezha 4P4C jack to Qwiic adapter, revision B (below).
- [wire-hub/](wire-hub/README.txt): Nezha cable wires to 2.54 mm, JST PH and Qwiic connectors.
- [plug-tail/](plug-tail/README.txt): boards that slide into the back of a 4P4C plug, for servos and Qwiic.

# Nezha 4P4C to Qwiic adapter — revision B

A 44 × 24 mm passive adapter with a 4P4C receptacle, a four-position 0.1-inch male header in the middle, and a top-entry Qwiic receptacle. All components are surface mounted; all routing is on the front copper. Two 3.00 mm non-plated holes accept heat-staked enclosure posts. Designed 2026-10-05.

**Status:** prototype CAD and manufacturing exports complete. KiCad reports zero electrical-rule violations, board-rule violations, unconnected items, and schematic/layout mismatches. The saved CAD and exported schematic netlist also match the independent pin table. The one-board Carvera NC passes offline motion, copper-isolation, hole, and tab checks. No physical prototype or on-machine cutting trial has been tested. This is a standalone electronics/CAM project at `/Volumes/Proj/proj/CAM/nezha-qwiic`.

**Revision B:** J1 is now the stocked Amphenol 73306-111LF latch-up jack. Its footprint comes from the retrieved manufacturer drawing. J2 and J3 are turned 180 degrees to retain a single copper layer and one crossover resistor. With J1 on the left in the component-side drawing, J2 runs top-to-bottom **SCL, SDA, 3V3, GND**; pin 1 / GND is at the bottom. The 44 × 24 mm outline, mounting-hole centers, stock placement, tools, tabs, and 1.45 mm through-cut depth remain the same. Use the revision B files; revision A files fit the old Kycon jack.

## Files

- [Editable KiCad project](design/nezha-qwiic.kicad_pro), [schematic](design/nezha-qwiic.kicad_sch), and [PCB](design/nezha-qwiic.kicad_pcb)
- [Schematic PDF](exports/schematic.pdf) and [board drawing PDF](exports/board.pdf), viewed from the component side
- [Scalable board preview](exports/board-review.svg)
- [Fabrication ZIP](exports/nezha-qwiic-revB-fabrication.zip) and [Carvera milling-input ZIP](exports/nezha-qwiic-revB-milling-inputs.zip)
- [One-board Carvera G-code](cam/nezha-qwiic-revB-one-board-carvera-cut145.nc), [setup instructions](cam/READ-ME-FIRST.txt), [stock layout PDF](cam/setup-preview.pdf), and [complete CAM package](exports/nezha-qwiic-revB-carvera-one-board.zip)
- [Parts list](parts.csv), [supplier and price review](suppliers.csv), [wiring table](wiring.csv), and [validation results](checks/validation.json)

The ZIP packages and raster previews are generated files excluded from Git; their unpacked source files are retained. A working copy and the installed EDA tools are on Buzzkill at `/home/ros/projects/nezha-qwiic`.

## Wiring and assembly

| Signal | Nezha cable color | J1 contact | J2 male header | J3 Qwiic contact | Qwiic wire |
| --- | --- | --- | --- | --- | --- |
| GND | Black | 1 | 1 | 1 | Black |
| 3.3 V | Red | 2 | 2 | 2 | Red |
| SDA | Yellow | 4 | 3 | 3 | Blue |
| SCL | Green | 3 | 4 | 4 | Yellow |

The user confirmed 3.3 V sensor power and clarified the plug colors: latch-side left-to-right yellow–green–red–black; contact-side black–red–green–yellow. The drawing convention is plug nose away and cable toward the viewer. The Amphenol jack has its latch above the contacts. The manufacturer drawing does not assign contact numbers: this project's J1 numbering is explicitly 4–3–2–1 left-to-right when looking into that latch-up mouth, corresponding to yellow/SDA, green/SCL, red/3V3, and black/GND. On the actual board, J1's solder pads run top-to-bottom SDA, SCL, 3V3, GND. This physical mapping is recorded in the schematic and drawing-source record.

J2 has one straight row of four male pins at 2.54 mm pitch. Its SMT solder tails alternate sides; this is not a two-row header. With J1 on the left in the board preview, J2 runs from SCL at the top through SDA and 3V3 to GND at the bottom. Pin numbers and their nets remain 1=GND, 2=3V3, 3=SDA, 4=SCL; the physical orientation changes from revision A. The header is a tap into the four lines and needs no removable shunts.

**Fit R1, an insulated-body 1206 zero-ohm resistor.** It carries SCL over the SDA trace to make the crossing possible with one copper layer. Do not replace it with a solder blob or a bare conductor touching the board. The board adds no pull-ups, regulator, or level conversion.

Before first power, plug in the actual unpowered cable and check continuity from each cable color to the labeled J2 pin, including the wiring of both cable ends. Check for shorts between adjacent signals and between 3V3 and GND. This confirms the physical plug orientation and assembly against the CAD assumptions.

## Selected parts and footprint sources

| Ref | Part | Notes and source |
| --- | --- | --- |
| J1 | Amphenol 73306-111LF | Right-angle, latch-up 4P4C SMT jack. Custom footprint from [manufacturer drawing 73306](references/Amphenol-73306-revM.pdf), released revision M, sheet 3 revision B; [source and interpretation](references/footprint-source.json). Body height 14.0 mm. |
| J2 | Samtec TSM-104-01-L-SV | Four-position vertical male SMT header, no alignment-pin or locking-clip options. Custom footprint from [Samtec recommended land pattern](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xx-sv-xx-xxx-xx-footprint.pdf), revision D. |
| J3 | JST BM04B-SRSS-TB(LF)(SN) | Top-entry, 1 mm SH connector. Use **BM04B**, not the horizontal SM04B version. [JST SH drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf). |
| R1 | YAGEO RC1206JR-070RL | 1206 zero-ohm resistor; insulated ceramic body required for the trace crossing. |
| H1, H2 | Board features | 3.00 mm NPTH; no purchased metal fastener required. |

The JST and resistor footprints derive from KiCad library version 9.0.7, under the [KiCad library license](https://www.kicad.org/libraries/license/); the installed package's [attribution and license text](design/KICAD-LIBRARY-COPYRIGHT.txt) are retained. The JST mechanical mounting pads have been given blank pad numbers; their geometry is retained. Custom symbols and footprints are included with the project. Qwiic's power, signal order, and cable colors follow [SparkFun's Qwiic specification](https://www.sparkfun.com/qwiic).

## Small-quantity suppliers

Checked 2026-10-05. Prices are listed USD component prices, before shipping, tax, and any tariffs; availability can change. Each board needs one of each of the following four components. No purchase has been made. Amazon searches did not produce listings with verified matching manufacturer part numbers and footprints.

| Ref | Exact part and supplier | Listed price | Ordering notes |
| --- | --- | --- | --- |
| J1 | [Amphenol 73306-111LF at Mouser](https://www.mouser.com/en/ProductDetail/Amphenol-FCI/73306-111LF?qs=yJYkLTYh576cZAwwAWqqNg%3D%3D), 649-73306-111LF | $2.43 each | 845 listed in stock; minimum 1; choose cut tape. Matches revision B. |
| J2 | [Samtec TSM-104-01-L-SV at DigiKey](https://www.digikey.com/en/products/detail/samtec-inc/TSM-104-01-L-SV/6679016), SAM10279-ND | $0.64 each | In stock; minimum 1. Four male pins at 2.54 mm pitch, SMT solder tails. |
| J3 | [JST BM04B-SRSS-TB at DigiKey](https://www.digikey.com/en/products/detail/jst-sales-america-inc/BM04B-SRSS-TB/926696), 455-BM04B-SRSS-TBCT-ND | $0.53 each | In stock; minimum 1. Choose cut tape and the vertical BM04B version. |
| R1 | [YAGEO RC1206JR-070RL at DigiKey](https://www.digikey.com/en/products/detail/yageo/RC1206JR-070RL/729184), 311-0.0ERCT-ND | $0.10 for 1; $0.30 for 10 | In stock; required insulated-body crossover. Choose cut tape. |

J1 also has a [DigiKey listing](https://www.digikey.com/en/products/detail/amphenol-cs-fci/73306-111LF/1525840), 609-4469-1-ND, showing $2.30 each and 2 in stock in the retrieved page. Mouser's retrieved page was newer and showed substantially more stock. All listed active parts match revision B. The original Kycon jack is not an alternative for this layout.

Do not substitute a generic RJ11 6P4C jack, a through-hole header, or a horizontal JST SM04B connector in this layout. The two 3 mm mounting holes are board features and add no purchased components.

## Mechanical dimensions

- Finished board: 44.00 × 24.00 mm rectangle, thickness 1.40 mm for the user's stock.
- Hole diameter: 3.00 mm, non-plated. Centers are (4.00, 3.00) and (40.00, 21.00) mm, measured from the upper-left board corner with X right and Y down in the component-side drawing.
- A nominal 5 mm diameter head area is kept clear around each hole; match the enclosure's post length and melted head to the actual board thickness.
- J1 opening faces left, 1.0 mm inside the board edge; body width 11.18 mm, depth 12.7 mm, and height 14.0 ± 0.1 mm. Its centerline is Y = 12.50 mm. Allow enclosure clearance for the latch on top. J2's pin row is at X = 29.50 mm, with pins 1–4 at Y = 15.81, 13.27, 10.73, 8.19 mm respectively. J3 is top entry; allow clearance for its cable above the board.

The rendered PDF is a review drawing. Use CAD or Gerber geometry for machining and check print scaling before using a paper template.

## Outsourced fabrication

The fabrication ZIP includes front and blank back copper, masks, top silkscreen, paste, outline, non-plated drill file, and order notes. A conventional two-layer order works, with all routing on the front and no back copper. Suggested prototype specification: FR-4, 1.4 mm, 1 oz copper, two 3.00 mm NPTH, top solder mask and silkscreen. A fabricator can alternatively quote a single-copper-layer board from the same geometry. No fabrication order has been placed.

## Carvera milling

The milling ZIP contains front copper and board outline as RS-274X Gerbers, the NPTH Excellon file, and CAM notes. The milling Gerbers omit X2 and netlist attributes and aperture macros, and rendered successfully in gerbv with no diagnostics.

Use copper-up stock. All files share the upper-left board origin: exported X = 0…44 mm and Y = 0…−24 mm. Do not mirror this component-side artwork or independently reposition the drill and outline files. The outline is the finished perimeter, not a cutter-center path.

Tracks are 0.40 mm wide; the design-rule minimum copper clearance is 0.30 mm. The Qwiic pads have 0.40 mm gaps. Choose an isolation tool with effective cutting width comfortably below the smallest gap; the selected 30° / 0.2 mm-tip bit has a nominal 0.243 mm effective width at 0.08 mm depth. Actual cutter shape, runout, cutting depth, and stock flatness determine what the machine can achieve. Review the toolpath and cut a coupon before the first board.

The user supplied 100 × 150 × 1.4 mm stock and requested **one board first**. [pcb2gcode 3.0.4](https://github.com/pcb2gcode/pcb2gcode/releases/tag/v3.0.4) is installed on Buzzkill and generates the isolation and tabbed-outline paths. A Carvera postprocessor assigns the original machine's ATC slots, preserves the controller's native leveling, and pockets both mounting holes completely. [CAM setup instructions](cam/READ-ME-FIRST.txt) specify stock orientation, origin, tools, probing, fixturing, and the bare-copper assumption.

The NC uses a different origin from the raw Gerbers: G54 XY zero is the **lower-left of the stock**, with 150 mm along X and 100 mm along Y. The board's lower-left is (15, 15) mm. This is a translation of (+15, +39) mm from the Gerbers, without mirroring. The NC already includes this placement; do not add another 15 mm controller offset.

Slot 2 holds the standard 30° V-bit with a 0.2 mm tip; slot 3 holds the 0.8 mm corn bit. Both run at 12,000 RPM and 300 mm/min; isolation is 0.08 mm deep. Through-cuts reach 1.45 mm in passes no deeper than 0.25 mm. Four tabs have 2.5 mm minimum neck width and retain 0.5 mm of material. Hole and outline paths are cut after the traces. The `cut145` update reduces the extra depth to 0.05 mm below the 1.4 mm PCB. The user has a sacrificial backer and about 1 mm of double-sided tape; tape thickness is not added to the cutting depth. Auto-leveling follows the copper surface but does not measure board thickness or tape compression. These are conservative choices relative to [Makera's PCB cutting table](https://wiki.makera.com/en/speeds-and-feeds).

The independent [NC validation](cam/validation.json) reconstructs the final tool sweeps, confirms that all CAD signal nets remain connected and separated, checks that the holes have no uncut cores, measures the four retaining tabs, and checks command syntax, depth, stock bounds, clearance moves, and tool changes. Its motion estimate excludes probing, ATC, acceleration, and controller processing delays. Actual bit geometry, copper thickness, probing accuracy, clamping, and machine behavior still require operator verification. More copies can be panelized after this single-board test.

## Buzzkill tools and regeneration

Passwordless SSH and sudo were verified at `ros@buzzkill.local` (Ubuntu 26.04 LTS). Installed from the host's Ubuntu repositories: KiCad 9.0.8; symbols, footprints, and 3D libraries 9.0.7; ngspice 45.2; gerbv 2.10.0; Xvfb; and librsvg rendering tools. Added pcb2gcode 3.0.4 (upstream release commit `a5604c4`, with bundled gerbv 2.13.0), its Ubuntu runtime libraries, and Shapely 2.1.2 for CAM checks. The executable launcher is `/home/ros/.local/bin/pcb2gcode`. A passive adapter needs connectivity and clearance checks; no circuit simulation is needed for this design.

From `/home/ros/projects/nezha-qwiic`:

```sh
python3 scripts/build_adapter.py > checks/geometry.json
bash scripts/export_adapter.sh
python3 scripts/package_adapter.py

# Regenerate one-board Carvera NC after the exports exist:
bash scripts/run_cam.sh
```

The build script overwrites the generated schematic, PCB, project settings, and local libraries. After manual CAD edits, run only export and packaging to preserve those edits. Export runs KiCad ERC and DRC with schematic parity, then independently checks pad nets, the schematic netlist, the header pitch, front-only tracks, and the actual exported drill locations. Packaging records checksums in `exports/SHA256SUMS.txt`.
