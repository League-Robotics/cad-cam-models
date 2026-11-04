#!/usr/bin/env python3
"""Audit final panel motions against validated single-board CAD and CAM."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import math
import re
import runpy
from shapely import affinity
from shapely.geometry import box, Point
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'cam/panel'
job = json.loads((OUT / 'layout.json').read_text())
# Re-run the source's independent CAD / residual-copper / hole / tab checks.
base = runpy.run_path(str(ROOT / 'scripts/check_carvera.py'))
source = ROOT / 'cam' / job['source_program']
assert hashlib.sha256(source.read_bytes()).hexdigest() == job['source_sha256']
nc = OUT / job['program_file']
positions = {b['id']: b['lower_left_mm'] for b in job['boards']}
segments = defaultdict(list)
feeds = defaultdict(list)
pos = {'X':None,'Y':None,'Z':None}
op, board, tool, feed, spindle = None, None, None, None, False
changes, block_order, minutes = [], [], 0
allowed = {'G0','G1','G4','G17','G21','G54','G90','M3','M5','M6','M9','M30','M331'}
for line_no, raw in enumerate(nc.read_text().splitlines(),1):
    if '(OPERATION ' in raw:
        op = int(re.search(r'OPERATION (\d+)',raw)[1])
    if '(BOARD ' in raw:
        board = re.search(r'BOARD (B\d+):',raw)[1]
        block_order.append([op,board])
    s = re.sub(r'\([^)]*\)','',raw).strip()
    if not s:
        continue
    words = re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)',s)
    assert re.sub(r'\s+','',s) == ''.join(k+v for k,v in words), (line_no,s)
    cmd=words[0][0]+words[0][1]
    assert cmd in allowed,(line_no,s)
    data={k:float(v) for k,v in words[1:]}
    if cmd=='M6':
        assert not spindle and (tool is None or pos['Z']>=5)
        tool=int(data['T']); changes.append(tool)
    elif cmd=='M3':
        assert data['S']==12000 and tool in (2,3)
        spindle=True
    elif cmd=='M5':
        spindle=False
    elif cmd=='G4':
        assert data['P'] in (0,3)
        minutes+=data['P']/60
    if 'F' in data:
        feed=data['F']; assert feed in (100,300)
    if cmd not in ('G0','G1'):
        continue
    new={k:data.get(k,pos[k]) for k in pos}
    assert new['Z'] is None or -1.450001<=new['Z']<=10.000001
    if all(v is not None for v in new.values()):
        assert 0<=new['X']<=150 and 0<=new['Y']<=100
    if all(v is not None for v in (*pos.values(),*new.values())) and pos!=new:
        a,b=tuple(pos.values()),tuple(new.values())
        if cmd=='G0':
            assert (a[:2]==b[:2] and b[2]>=5) or min(a[2],b[2])>=5,(line_no,s)
        if min(a[2],b[2])<0:
            assert spindle and tool=={1:2,2:3,3:3}[op]
        if cmd=='G1':
            assert spindle and feed is not None
            segments[(op,board)].append((a,b))
            feeds[(op,board)].append(feed)
        minutes+=math.dist(a,b)/(feed if cmd=='G1' else 2000)
    pos=new
assert changes==[2,3] and not spindle and pos['Z']==10
assert nc.read_text().rstrip().endswith('M30')
assert block_order==[[o,b['id']] for o in (1,2,3) for b in job['boards']]
assert not any(x in nc.read_text() for x in ['G92','G10 ','G53','G43','G49','M370'])

# Compare EVERY feed segment, including plunges/retractions/tab lifts, to
# the original source in order. Translation cannot change electrical topology.
source_segments={o:[(a,b) for oo,t,c,a,b,n in base['segments'] if oo==o and c=='G1'] for o in (1,2,3)}
for (op,bid),actual in segments.items():
    expected=source_segments[op]
    assert len(actual)==len(expected),(op,bid,len(actual),len(expected))
    dx,dy=positions[bid][0]-15,positions[bid][1]-15
    for (a,b),(sa,sb) in zip(actual,expected):
        for point,original in [(a,sa),(b,sb)]:
            assert max(abs(point[i]-original[i]-[dx,dy,0][i]) for i in range(3))<.000011,(op,bid,point,original)
    # Planar cuts use 300 mm/min; every Z-only plunge/lift uses 100.
    for (a,b),f in zip(actual,feeds[(op,bid)]):
        assert f==(100 if a[:2]==b[:2] else 300),(op,bid,a,b,f)

occupied=unary_union([box(*r['bounds_xyxy_mm']) for r in job['excluded_regions']])
stock=box(0,0,150,100)
all_sweeps={}
for bid,(x,y) in positions.items():
    shape=affinity.translate(base['top'],xoff=x-15,yoff=y-15)
    assert stock.covers(shape),'Tool sweep leaves stock'
    assert shape.distance(occupied)>=job['minimum_clearance_from_excluded_regions_mm']
    all_sweeps[bid]=shape
for i,a in enumerate(positions):
    for b in list(positions)[i+1:]:
        assert all_sweeps[a].distance(all_sweeps[b])>=.39,'Overlapping adjacent kerfs'
# The controller probes the NC machining rectangle before any new cuts.
bounds=unary_union(list(all_sweeps.values())).bounds
tool_centers=[]
for ss in segments.values():
    for a,b in ss:
        if min(a[2],b[2])<0:
            tool_centers.extend([a[:2],b[:2]])
center_bounds=[min(a[0] for a in tool_centers),min(a[1] for a in tool_centers),max(a[0] for a in tool_centers),max(a[1] for a in tool_centers)]
probe_box=box(*center_bounds)
assert stock.covers(probe_box) and probe_box.distance(occupied)>=3
nx,ny=job['probe_grid']
px=[center_bounds[0]+i*(center_bounds[2]-center_bounds[0])/(nx-1) for i in range(nx)]
py=[center_bounds[1]+i*(center_bounds[3]-center_bounds[1])/(ny-1) for i in range(ny)]
assert max(px[1]-px[0],py[1]-py[0])<=10
zpoint=Point(job['auto_z_probe_work_xy_mm'])
assert probe_box.covers(zpoint) and zpoint.distance(occupied)>3
report={
    'status':'PASS',
    'exclusion_basis':job['exclusion_basis'],
    'excluded_regions':job['excluded_regions'],
    'program_sha256':hashlib.sha256(nc.read_bytes()).hexdigest(),
    'source_program_sha256':job['source_sha256'],
    'new_boards':len(positions),'planned_usable_total_if_test_passes':job['assembly_part_sets_for_sheet'],
    'board_lower_lefts_mm':positions,'tool_changes':changes,
    'cut_depth_mm':1.45,'through_cut_allowance_mm':.05,
    'tabs_per_board':4,'tab_widths_mm':base['tabs'],'tab_remaining_thickness_mm':.5,
    'holes_count':2*len(positions),'holes_diameter_mm':3,
    'cutter_sweep_bounds_xyxy_mm':[round(v,5) for v in bounds],
    'tool_center_and_expected_leveling_bounds_xyxy_mm':[round(v,5) for v in center_bounds],
    'minimum_tool_sweep_clearance_from_excluded_regions_mm':round(min(s.distance(occupied) for s in all_sweeps.values()),3),
    'probe_grid':job['probe_grid'],'maximum_probe_spacing_mm':round(max(px[1]-px[0],py[1]-py[0]),3),
    'motion_estimate_minutes_excluding_probe_and_atc':round(minutes,1),
    'checks':['Independent single-board CAD/copper connectivity, pockets and tabs check rerun',
              'Every panel feed segment equals translated audited source segment',
              'Feeds, spindle, supported commands and clearance moves verified',
              'Only one T2 selection and one T3 selection',
              'Every tool sweep inside stock; entire bottom row excluded',
              'Adjacent cutter sweeps do not overlap',
              'Entire leveling rectangle on stock and above the excluded bottom row',
              'All isolation then all holes then all outlines'],
    'limits':'Offline nominal geometry. Requires intact stock above the excluded Y0..40 strip. Machine, tools, workholding and physical probing not verified.'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

fig,ax=plt.subplots(figsize=(12,9))
ax.add_patch(Rectangle((0,0),150,100,facecolor='#faf5e9',edgecolor='#303840',lw=1.8))
for old in job['excluded_regions']:
    x1,y1,x2,y2=old['bounds_xyxy_mm']
    ax.add_patch(Rectangle((x1,y1),x2-x1,y2-y1,facecolor='#d9d9d9',edgecolor='#a43c3c',hatch='///',lw=1))
    ax.text((x1+x2)/2,(y1+y2)/2,old['id']+'\nNO CUTTING OR PROBING BELOW Y40',ha='center',va='center',color='#803030',fontsize=10)
for bid,(x,y) in positions.items():
    ax.add_patch(Rectangle((x,y),44,24,fill=False,edgecolor='#213a50',lw=1))
    for op in (1,2,3):
        paths=[(a[:2],b[:2]) for a,b in segments[(op,bid)] if min(a[2],b[2])<0 and a[:2]!=b[:2]]
        ax.add_collection(LineCollection(paths,colors={1:'#16818d',2:'#bd6516',3:'#7c49a0'}[op],linewidths=.3))
    for tx,ty in [(x,y+12),(x+22,y+24),(x+44,y+12),(x+22,y)]:
        ax.plot(tx,ty,'s',color='#d99a00',markersize=4,zorder=5)
    ax.text(x+22,y+24.8,f'{bid}  ({x:g}, {y:g})',ha='center',fontsize=9,fontweight='bold')
for x in px:
    for y in py:
        ax.plot(x,y,'.',color='#326b36',markersize=3,alpha=.55)
ax.plot(*job['auto_z_probe_work_xy_mm'],'+',color='#12351c',ms=12,mew=2)
ax.annotate('G54 = original stock corner\nUndo the 60 mm shift',(0,0),(9,5),fontsize=10,arrowprops={'arrowstyle':'->'})
ax.text(75,105,f"{len(positions)} new adapters · bottom row excluded",ha='center',fontsize=19,fontweight='bold')
ax.text(75,101.5,'150 × 100 × 1.4 mm stock · copper side up · all dimensions in mm',ha='center',fontsize=11)
ax.set_xlim(-3,153);ax.set_ylim(-2,108);ax.set_aspect('equal')
ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)');ax.grid(alpha=.12)
fig.text(.5,.055,'Teal: isolation  |  Orange: holes  |  Purple: outline  |  Gold: tabs  |  Green dots: leveling grid',ha='center',fontsize=9)
fig.text(.5,.032,'Whole bottom row reserved; probe only the intact upper stock. T2: 30° / 0.2 mm V-bit. T3: 0.8 mm corn bit.',ha='center',fontsize=9)
fig.text(.5,.012,'Z0 = top copper. Final cut −1.45 mm. 4 tabs per board, 2.5 mm wide × 0.5 mm thick. Review drawing, not a scale template.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.07,1,.99])
for ext in ('pdf','svg','png'):
    fig.savefig(OUT/f'panel-layout.{ext}',dpi=150)
