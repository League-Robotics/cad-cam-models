#!/usr/bin/env python3
"""Independently parse the final NC and check tool sweeps against saved CAD."""
from pathlib import Path
import hashlib
import json
import math
import re
from collections import defaultdict
import pcbnew as p
from shapely import affinity
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

root = Path(__file__).resolve().parents[1]
cam = root / 'cam'
job = json.loads((cam / 'job.json').read_text())
nc = cam / job['program_file']
pos = {'X': None, 'Y': None, 'Z': None}
tool, operation, spindle, feed = None, None, False, None
tool_changes, segments = [], []
allowed = {'G0','G1','G4','G17','G21','G54','G90','M3','M5','M6','M9','M30','M331'}
time_minutes = 0
for line_no, raw in enumerate(nc.read_text().splitlines(), 1):
    if '(OPERATION ' in raw:
        operation = int(re.search(r'OPERATION (\d+)', raw)[1])
    s = re.sub(r'\([^)]*\)', '', raw).strip()
    if not s:
        continue
    words = re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)', s)
    assert words and words[0][0] in 'GM', (line_no,s)
    command = words[0][0]+words[0][1]
    assert command in allowed, (line_no,s)
    data = {k:float(v) for k,v in words[1:]}
    if command == 'M6':
        assert not spindle
        if tool is not None:
            assert pos['Z'] >= 5
        tool = int(data['T'])
        tool_changes.append(tool)
    elif command == 'M3':
        assert data['S'] == 12000 and tool in (2,3)
        spindle = True
    elif command == 'M5':
        spindle = False
    elif command == 'G4':
        time_minutes += data['P']/60
    if 'F' in data:
        feed = data['F']
        assert 0 < feed <= 300, (line_no,feed)
    if command not in ('G0','G1'):
        continue
    new = {k:data.get(k,pos[k]) for k in pos}
    if all(v is not None for v in new.values()):
        assert 0 <= new['X'] <= 150 and 0 <= new['Y'] <= 100
        assert -job['cutting']['depth_mm']-.00001 <= new['Z'] <= 10.00001
    if all(v is not None for v in (*pos.values(), *new.values())) and pos != new:
        a, b = tuple(pos.values()), tuple(new.values())
        if command == 'G0':
            assert (a[:2] == b[:2] and b[2] >= 5) or min(a[2],b[2]) >= 5, (line_no,s,a,b)
        if min(a[2],b[2]) < 0:
            assert command == 'G1' or (a[:2] == b[:2] and b[2] >= 5)
            assert spindle, (line_no,s)
        if command == 'G1':
            assert feed is not None
        segments.append((operation,tool,command,a,b,line_no))
        time_minutes += math.dist(a,b)/(feed if command == 'G1' else 2000)
    pos = new
assert tool_changes == [2,3]
assert not spindle and pos['Z'] == 10
assert nc.read_text().rstrip().endswith('M30')
assert not any(s in nc.read_text() for s in ['M370','G92','G10 ','G53','G43','G49'])

def clipped_xy(a,b,threshold):
    if min(a[2],b[2]) > threshold:
        return None
    lo, hi = 0., 1.
    if a[2] > threshold:
        lo = (threshold-a[2])/(b[2]-a[2])
    if b[2] > threshold:
        hi = (threshold-a[2])/(b[2]-a[2])
    aa = (a[0]+lo*(b[0]-a[0]),a[1]+lo*(b[1]-a[1]))
    bb = (a[0]+hi*(b[0]-a[0]),a[1]+hi*(b[1]-a[1]))
    return Point(aa) if aa == bb else LineString([aa,bb])

def sweep(op, threshold):
    paths=[]
    for operation,tool,command,a,b,_ in segments:
        if operation != op or command != 'G1':
            continue
        shape=clipped_xy(a,b,threshold)
        if shape is not None:
            radius=job['isolation']['effective_diameter_mm']/2 if tool==2 else .4
            paths.append(shape.buffer(radius,quad_segs=24))
    return unary_union(paths)

print('Checking final NC tool sweeps...', flush=True)
top = unary_union([sweep(i,-.001) for i in [1,2,3]])
hole_bottom = sweep(2,-1.4)
outline_bottom = sweep(3,-1.4)
for center in [(19,36),(55,18)]:
    expected = Point(center).buffer(1.495,quad_segs=64)
    assert expected.difference(hole_bottom).area < 1e-6, 'Hole contains an uncut core'
    assert hole_bottom.intersection(Point(center).buffer(1.51)).area < math.pi*1.51**2
# The nominal outline is tool-center compensated outward by 0.4 mm.
tabs=[]
for edge in [LineString([(14.6,15),(14.6,39)]),LineString([(15,39.4),(59,39.4)]),
             LineString([(59.4,39),(59.4,15)]),LineString([(59,14.6),(15,14.6)])]:
    # Measure the tab's narrowest neck at the middle of the 0.8 mm kerf.
    # Roots at the board edge are wider because the cutter ends are rounded.
    left=edge.difference(outline_bottom.buffer(.002))
    assert abs(left.length-2.5) < .02, ('tab width',left.length)
    tabs.append(round(left.length,3))
for point in [(15,27),(37,39),(59,27),(37,15)]:
    assert not outline_bottom.intersects(Point(point).buffer(.1))
assert abs(job['stock_mm'][2]+job['tabs']['z_mm']-.5)<1e-9

# Extract the actual stored CAD copper independently of the CAM generator.
board=p.LoadBoard(str(root/'design/nezha-qwiic.kicad_pcb'))
assert abs(p.ToMM(board.GetDesignSettings().GetBoardThickness())-1.4)<1e-9
def xy(v):return (p.ToMM(v.x)-50+15,39-(p.ToMM(v.y)-50))
net_shapes=defaultdict(list)
terminals=[]
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:
            continue
        w,h=p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y)
        shape=box(-w/2,-h/2,w/2,h/2)
        if pad.GetShape()==p.PAD_SHAPE_ROUNDRECT:
            r=p.ToMM(pad.GetRoundRectCornerRadius())
            shape=box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=24)
        else:
            assert pad.GetShape()==p.PAD_SHAPE_RECT
        shape=affinity.rotate(shape,pad.GetOrientationDegrees(),origin=(0,0))
        center=xy(pad.GetPosition())
        shape=affinity.translate(shape,*center)
        net=pad.GetNetname() or f'{fp.GetReference()}_MP_{len(net_shapes)}'
        net_shapes[net].append(shape)
        if pad.GetNumber():
            terminals.append((fp.GetReference(),pad.GetNumber(),net,Point(center)))
for track in board.GetTracks():
    assert not isinstance(track,p.PCB_VIA)
    net_shapes[track.GetNetname()].append(LineString([xy(track.GetStart()),xy(track.GetEnd())]).buffer(p.ToMM(track.GetWidth())/2,quad_segs=24))
nets={n:unary_union(shapes) for n,shapes in net_shapes.items()}
copper=unary_union(list(nets.values()))
assert copper.buffer(-.01).intersection(top).area < 1e-6, 'Tool removes intended copper beyond 10 um tolerance'
residual=box(15,15,59,39).difference(top)
islands=list(residual.geoms) if hasattr(residual,'geoms') else [residual]
assignment={}
for ref,num,net,center in terminals:
    matches=[i for i,shape in enumerate(islands) if shape.covers(center)]
    assert len(matches)==1,(ref,num,'missing terminal')
    index=matches[0]
    if net in assignment:
        assert assignment[net]==index,(ref,num,'open circuit')
    assignment[net]=index
assert len(set(assignment.values()))==len(assignment),'Signals shorted after nominal isolation'
for net,index in assignment.items():
    assert islands[index].area < nets[net].area*1.15+.1,(net,'connected to background copper')

actual_depths={op:min(min(a[2],b[2]) for operation,tool,command,a,b,_ in segments if operation==op) for op in [1,2,3]}
assert abs(actual_depths[1]+job['isolation']['depth_mm'])<1e-5
for op in [2,3]:
    assert abs(actual_depths[op]+job['cutting']['depth_mm'])<1e-5
allowance=job['workholding']['through_cut_allowance_mm']
assert allowance > 0 and abs(job['cutting']['depth_mm']-job['stock_mm'][2]-allowance)<1e-9
cutting=[s for s in segments if min(s[3][2],s[4][2])<0]
bounds=[min(min(s[3][i],s[4][i]) for s in cutting) for i in range(3)]+[max(max(s[3][i],s[4][i]) for s in cutting) for i in range(3)]
report={'status':'PASS','revision':job['revision'],'jack':job['jack'],'program_sha256':hashlib.sha256(nc.read_bytes()).hexdigest(),'cam_version':'pcb2gcode 3.0.4 a5604c4',
        'operation_min_z_mm':actual_depths,'through_cut_allowance_mm':allowance,'tool_changes':tool_changes,'stock_mm':job['stock_mm'],'board_lower_left_mm':[15,15],
        'motion_bounds_xyz_minmax_mm':[round(v,5) for v in bounds],
        'tab_widths_mm':tabs,'tab_remaining_thickness_mm':.5,'holes_mm':[[19,36,3],[55,18,3]],
        'isolated_cad_nets':sorted(assignment),'motion_estimate_minutes_excluding_probe_and_atc':round(time_minutes,1),
        'checks':['Supported command whitelist','Only slots 2 and 3; stopped spindle before ATC',
                  'No XY rapids below clearance','Cut-depth and stock bounds','Copper preservation with 10 um geometry tolerance',
                  'Nominal post-milling copper has no open or shorted CAD nets','Holes fully pocketed; no loose cores',
                  'Four 2.5 mm retaining tabs at through-cut depth','Controller origin and native leveling preserved'],
        'limits':'Offline nominal geometry only; machine, tool identity/runout, clamping, copper thickness, probing and actual cuts not physically verified.'}
(cam/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

# Review drawing: actual final NC center paths, stock placement and saved copper.
fig,(ax,detail)=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1.1,1]})
colors={1:'#087f8c',2:'#bd5d10',3:'#8b3fb0'}
for axis in [ax,detail]:
    for geometry in nets.values():
        for poly in geometry.geoms if hasattr(geometry,'geoms') else [geometry]:
            x,y=poly.exterior.xy
            axis.fill(x,y,color='#be4242',alpha=.55,zorder=1)
    for op in [1,2,3]:
        lines=[(a[:2],b[:2]) for operation,tool,command,a,b,_ in segments
               if operation==op and command=='G1' and min(a[2],b[2])<0 and a[:2]!=b[:2]]
        axis.add_collection(LineCollection(lines,colors=colors[op],linewidths=.35,alpha=.65,zorder=2))
    axis.plot([15,59,59,15,15],[15,15,39,39,15],color='#222',linewidth=.7)
    for x,y in [(15,27),(37,39),(59,27),(37,15)]:
        axis.plot(x,y,'s',color='#e6a400',markersize=5,zorder=5)
    axis.set_aspect('equal');axis.set_xlabel('X (mm)');axis.set_ylabel('Y (mm)')
    axis.grid(alpha=.15)
ax.plot([0,150,150,0,0],[0,0,100,100,0],color='#333')
ax.plot(0,0,'o',color='#111');ax.annotate('G54 origin',(0,0),(4,4),fontsize=8)
ax.annotate('One 44 x 24 mm board',(37,40),(35,62),arrowprops={'arrowstyle':'->'},ha='center',fontsize=9)
ax.text(90,50,'Unused stock',ha='center',color='#777')
ax.set_xlim(-4,154);ax.set_ylim(-4,104);ax.set_title('150 x 100 x 1.4 mm stock - copper side up')
detail.set_xlim(12,62);detail.set_ylim(12,42);detail.set_title('Final G-code paths and tab locations')
fig.suptitle('Nezha / Qwiic - REV B Amphenol - single-board Carvera job',fontsize=16)
fig.text(.5,.04,'T2 teal: trace isolation   |   T3 orange: 3 mm holes   |   T3 purple: outline   |   Yellow: retaining tabs',ha='center',fontsize=9)
fig.text(.5,.01,f"Z0 = copper top. Maximum cut Z = -{job['cutting']['depth_mm']:.2f} mm. Probe/level before cutting. Drawing is a review, not a print template.",ha='center',fontsize=8)
fig.tight_layout(rect=[0,.07,1,.94])
for ext in ['svg','pdf','png']:
    fig.savefig(cam/f'setup-preview.{ext}',dpi=150)
