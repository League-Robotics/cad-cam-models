#!/usr/bin/env bash
# Run on Buzzkill after build_adapter.py. No machine motion or G-code output.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p checks exports/fabrication exports/milling
pcb=design/nezha-qwiic.kicad_pcb
sch=design/nezha-qwiic.kicad_sch
kicad-cli sch erc --exit-code-violations --format json -o checks/erc.json "$sch"
kicad-cli pcb drc --schematic-parity --exit-code-violations --format json -o checks/drc.json "$pcb"
kicad-cli sch export netlist --format kicadxml -o checks/netlist.xml "$sch"
kicad-cli sch export pdf -o exports/schematic.pdf "$sch"
kicad-cli pcb export svg --layers F.Cu,F.Silkscreen,F.Fab,Edge.Cuts --mode-single --page-size-mode 2 -o exports/board.svg "$pcb"
python3 - <<'PY'
from pathlib import Path
p=Path('exports/board.svg')
# Presentation colors only. Manufacturing artwork and all geometry unchanged.
s=p.read_text().replace('#F2EDA1','#202830').replace('#AFAFAF','#66727D').replace('#D0D2CD','#66727D')
Path('exports/board-review.svg').write_text(s)
PY
rsvg-convert -w 1760 -b white -o exports/board.png exports/board-review.svg
rsvg-convert -f pdf -o exports/board.pdf exports/board-review.svg
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,Edge.Cuts --use-drill-file-origin -o exports/fabrication/ "$pcb"
kicad-cli pcb export drill --excellon-units mm --drill-origin plot --excellon-separate-th --generate-map --generate-report -o exports/fabrication/ "$pcb"
kicad-cli pcb export gerbers --layers F.Cu,Edge.Cuts --no-x2 --no-netlist --disable-aperture-macros --use-drill-file-origin -o exports/milling/ "$pcb"
kicad-cli pcb export drill --excellon-units mm --drill-origin plot --excellon-separate-th --generate-map --generate-report -o exports/milling/ "$pcb"
xvfb-run -a gerbv -x png -D 900 -o exports/milling/copper-preview.png exports/milling/nezha-qwiic-F_Cu.gtl exports/milling/nezha-qwiic-Edge_Cuts.gm1 2> checks/gerbv.log
test ! -s checks/gerbv.log
python3 scripts/verify_adapter.py
