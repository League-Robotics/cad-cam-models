#!/usr/bin/env python3
"""Single-board and 25-board Carvera files. No machine connection."""
from pathlib import Path
import json, math, re, subprocess
ROOT=Path(__file__).resolve().parents[1];CAM=ROOT/'cam';CAM.mkdir(exist_ok=True)
(CAM/'raw').mkdir(exist_ok=True)
diam=.2+2*.12*math.tan(math.radians(15))
config=f'''# Inputs already mirror B.Cu exactly once. Do not use back-side mirroring.
metric=true
metricoutput=true
front=../exports/milling/machining-view-F_Cu.gtl
outline=../exports/milling/machining-view-Edge_Cuts.gm1
output-dir=raw
zero-start=false
x-offset=0
y-offset=0
zsafe=5
zchange=10
mill-diameters={diam:.6f}
isolation-width=0.35
milling-overlap=50%
zwork=-0.12
mill-feed=300
mill-vertfeed=100
mill-speed=12000
cutter-diameter=0.8
cut-side=front
zcut=-1.55
cut-feed=300
cut-vertfeed=100
cut-speed=12000
cut-infeed=0.25
bridges=2.0
bridgesnum=4
zbridges=-0.9
nog64=true
nog91-1=true
nom6=true
spinup-time=3
spindown-time=3
tolerance=0.002
optimise=0.001
sanity-checks=true
'''
(CAM/'millproject').write_text(config)
with (CAM/'raw/generation.log').open('w') as log:
    subprocess.run(['/home/ros/.local/bin/pcb2gcode'],cwd=CAM,stdout=log,stderr=log,check=True)
holes=json.loads((ROOT/'checks/holes.json').read_text())
placements=[{'id':1+r*5+c,'x':6+c*28,'y':6+r*18} for r in range(5) for c in range(5)]
job={'name':'nezha-wire-hub','revision':'A','stock_mm':[150,100,1.4],'board_mm':[26,16],
     'placements':placements,'gap_mm':2,'edge_margin_mm':6,'isolation':{'depth_mm':.12,'effective_diameter_mm':diam,'tip_mm':.2,'angle_deg':30},
     'through_depth_mm':1.55,'through_allowance_mm':.15,'stepdown_mm':.25,'tabs':{'per_board':4,'width_mm':2.,'remaining_mm':.5,'z_mm':-.9},
     'transform_from_top_view':'machineX=placementX+26-topX; machineY=placementY+16-topY',
     'probe_grid':[16,11],'probe_lift_mm':2,'auto_z_stock_point_mm':[16,8],
     'tools':[{'slot':2,'tool':'30 degree V-bit, 0.2 mm tip','rpm':12000,'feed_mm_min':300}, {'slot':3,'tool':'0.8 mm corn bit','rpm':12000,'feed_mm_min':300,'hole_helix_feed_mm_min':100}],
     'programs':{'panel':'nezha-wire-hub-A-25up-iso120-cut155.nc','single':'nezha-wire-hub-A-one-iso120-cut155.nc'}}
(CAM/'job.json').write_text(json.dumps(job,indent=2)+'\n')
def rawbody(name,dx,dy):
    started=False;out=[]
    for raw in (CAM/'raw'/name).read_text().splitlines():
        s=re.sub(r'\([^)]*\)','',raw).strip()
        if not s:continue
        if not started:
            if re.match(r'G0?0\s+X',s):started=True
            else:continue
        if s.startswith('M5'):break
        assert re.match(r'^G0?[014]\b',s),s
        s=re.sub(r'^G0([014])\b',r'G\1',s)
        assert not re.search(r'[IJKR]',s),s
        for axis,d in [('X',dx),('Y',dy)]:s=re.sub(axis+r'(-?[0-9.]+)',lambda m:axis+f'{float(m[1])+d:.5f}',s)
        if s.startswith('G0 Z-'):out.extend(['G1'+s[2:]+' F100','G1 F300'])
        else:out.append(s)
    assert started
    return out
def holepaths(dx,dy):
    out=[]
    for h in sorted(holes,key=lambda h:(h['x'],h['y'])):
        x,y=dx+26-h['x'],dy+16-h['y'];radius=(h['diameter']-.8)/2
        assert 0<radius<.4
        out += [f"(HOLE {h['reference']}.{h['pin']} diameter {h['diameter']:.2f})",'G0 Z5',f'G0 X{x+radius:.5f} Y{y:.5f}','G1 Z0 F100']
        prev=0
        for k in range(1,8):
            z=-min(1.55,k*.25)
            out.append('G1 F100')
            for i in range(1,49):
                a=-2*math.pi*i/48
                out.append(f'G1 X{x+radius*math.cos(a):.5f} Y{y+radius*math.sin(a):.5f} Z{prev+(z-prev)*i/48:.5f}')
            prev=z
        out.append('G1 F300')
        for i in range(1,49):
            a=-2*math.pi*i/48;out.append(f'G1 X{x+radius*math.cos(a):.5f} Y{y+radius*math.sin(a):.5f} Z-1.55000')
        out.append('G0 Z5')
    return out
def tool(n):return ['M5','G4 P3',f'M6 T{n}','G0 Z5','M3 S12000','G4 P3']
def program(ps,kind):
    out=[f'(NEZHA WIRE HUB REV A - {len(ps)} BOARDS - ORIGINAL CARVERA)',
         '(FRESH STOCK X150 Y100 THICKNESS 1.40 - BOTTOM COPPER FACING UP)',
         '(CAM IS ALREADY MIRRORED - DO NOT MIRROR AGAIN)',
         '(G54 XY0 STOCK LOWER LEFT - Z0 COPPER SURFACE)',
         '(T2 30 DEG V BIT 0.2 TIP - T3 0.8 MM CORN BIT)',
         '(ISOLATION Z-0.12 - THROUGH Z-1.55 - TABS RETAIN 0.50 MM)',
         '(TAPE THICKNESS IS NOT ADDED TO DEPTH)',
         '(AUTO Z AND FULL JOB AUTO LEVELING REQUIRED BEFORE RUN)',
         '(16 BY 11 LEVEL GRID FOR PANEL - 6 BY 4 FOR SINGLE - LIFT 2 MM)',
         'G21','G90','G17','G54','M331','(OPERATION 1 TRACE ISOLATION)']+tool(2)
    for b in ps:
        out.append(f"(BOARD {b['id']})");out+=rawbody('front.ngc',b['x'],b['y']+16)
    out+=['(OPERATION 2 THROUGH HOLES)']+tool(3)
    for b in ps:
        out.append(f"(BOARD {b['id']})");out+=holepaths(b['x'],b['y'])
    out+=['(OPERATION 3 TABBED OUTLINES)']
    for b in ps:
        out.append(f"(BOARD {b['id']})");out+=rawbody('outline.ngc',b['x'],b['y']+16)
    out+=['G0 Z10','M5','G4 P3','M9','M30']
    f=CAM/job['programs'][kind];f.write_text('\n'.join(out)+'\n');print(f'{f.name}: {len(out)} lines')
program(placements[:1],'single');program(placements,'panel')
