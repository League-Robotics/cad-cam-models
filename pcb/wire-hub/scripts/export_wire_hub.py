#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp, json
import pcbnew as p
root=Path(__file__).resolve().parents[1];name='nezha-wire-hub'
def run(*args):sp.run(args,cwd=root,check=True)
for d in ['exports/fabrication','exports/milling','checks','cam/raw']:(root/d).mkdir(parents=True,exist_ok=True)
pcb=f'design/{name}.kicad_pcb';sch=f'design/{name}.kicad_sch'
run('kicad-cli','sch','erc','--exit-code-violations','--format','json','-o','checks/erc.json',sch)
run('kicad-cli','pcb','drc','--schematic-parity','--exit-code-violations','--format','json','-o','checks/drc.json',pcb)
run('kicad-cli','sch','export','netlist','--format','kicadxml','-o','checks/netlist.xml',sch)
run('kicad-cli','sch','export','pdf','-o','exports/schematic.pdf',sch)
run('kicad-cli','pcb','export','gerbers','--layers','B.Cu,B.Mask,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts','--use-drill-file-origin','-o','exports/fabrication/',pcb)
b=p.LoadBoard(str(root/pcb));holes=[]
for f in b.GetFootprints():
    for a in f.Pads():
        if a.GetDrillSize().x:
            holes.append({'reference':f.GetReference(),'pin':a.GetNumber(),'x':p.ToMM(a.GetPosition().x)-50,'y':p.ToMM(a.GetPosition().y)-50,'diameter':p.ToMM(a.GetDrillSize().x)})
assert len(holes)==16
(root/'checks/holes.json').write_text(json.dumps(holes,indent=2)+'\n')
def drill(path,mirror=False):
    sizes=sorted({h['diameter'] for h in holes});lines=['M48',';TYPE=NON_PLATED','METRIC,TZ','FMAT,2']+[f'T{i+1}C{d:.3f}' for i,d in enumerate(sizes)]+['%','G90','G05']
    for i,d in enumerate(sizes):
        lines.append(f'T{i+1}')
        for h in holes:
            if h['diameter']==d:lines.append(f"X{(26-h['x'] if mirror else h['x']):.5f}Y{-h['y']:.5f}")
    lines+=['M30'];path.write_text('\n'.join(lines)+'\n')
drill(root/f'exports/fabrication/{name}-NPTH.drl')
# Build a manufacturing-only, already-mirrored copper view. This lets every
# machining operation use one explicit transform: X=26-topX; Y=16-topY.
# The editable electrical design remains unmirrored and uses B.Cu only.
center=p.VECTOR2I(p.FromMM(63),p.FromMM(58))
for fp in b.GetFootprints():fp.Flip(center,p.FLIP_DIRECTION_LEFT_RIGHT)
for t in b.GetTracks():t.Flip(center,p.FLIP_DIRECTION_LEFT_RIGHT)
for d in b.GetDrawings():d.Flip(center,p.FLIP_DIRECTION_LEFT_RIGHT)
p.SaveBoard(str(root/'exports/milling/machining-view.kicad_pcb'),b)
run('kicad-cli','pcb','export','gerbers','--layers','F.Cu,Edge.Cuts','--no-x2','--no-netlist','--disable-aperture-macros','--use-drill-file-origin','-o','exports/milling/','exports/milling/machining-view.kicad_pcb')
drill(root/'exports/milling/machining-view-NPTH.drl',True)
(root/'exports/fabrication/ORDER-NOTES.txt').write_text('Single copper layer on BOTTOM, 26 x 16 mm, nominal thickness 1.4 mm. All 16 solder holes are NON-PLATED; copper annuli on bottom only. Quote single-sided manufacture from B_Cu and NPTH drill. Do not mirror these fabrication Gerbers. Top and bottom legend and bottom mask/paste are supplied. A conventional two-layer plated-hole variant has NOT been generated.\n')
print('Exported original fabrication artwork and mirrored-once CAM artwork.')
