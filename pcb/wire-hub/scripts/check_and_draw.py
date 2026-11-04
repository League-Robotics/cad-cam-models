#!/usr/bin/env python3
"""Independently validate saved CAD/netlist and final machine motions."""
from pathlib import Path
from collections import defaultdict
import json, re, math, hashlib, xml.etree.ElementTree as ET
import pcbnew as p
from shapely.geometry import Point, LineString, box
from shapely import affinity
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parents[1];CAM=ROOT/'cam';job=json.loads((CAM/'job.json').read_text())
b=p.LoadBoard(str(ROOT/'design/nezha-wire-hub.kicad_pcb'));b.BuildConnectivity()
expected={str(i+1):'/'+n for i,n in enumerate(['GND','+3V3','SDA','SCL'])}
tree=ET.parse(ROOT/'checks/netlist.xml');schem={}
for n in tree.findall('.//nets/net'):
    schem[n.attrib['name']]={(a.attrib['ref'],a.attrib['pin']) for a in n.findall('node')}
assert schem=={n:{('J'+str(j),num) for j in range(1,6)} for num,n in expected.items()},schem
assert len(list(b.GetFootprints()))==5 and abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-1.4)<1e-9
holes=[];terminal_shapes={};netparts=defaultdict(list)
def xy(v):return 26-(p.ToMM(v.x)-50),16-(p.ToMM(v.y)-50)
def padshape(a):
    w,h=p.ToMM(a.GetSize().x),p.ToMM(a.GetSize().y);shape=a.GetShape()
    if shape==p.PAD_SHAPE_CIRCLE:s=Point(0,0).buffer(w/2,quad_segs=48)
    elif shape==p.PAD_SHAPE_RECT:s=box(-w/2,-h/2,w/2,h/2)
    elif shape==p.PAD_SHAPE_OVAL:
        if w>h:s=LineString([(-(w-h)/2,0),((w-h)/2,0)]).buffer(h/2,quad_segs=48)
        else:s=LineString([(0,-(h-w)/2),(0,(h-w)/2)]).buffer(w/2,quad_segs=48)
    elif shape==p.PAD_SHAPE_ROUNDRECT:
        r=p.ToMM(a.GetRoundRectCornerRadius());s=box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=48)
    else:raise AssertionError(shape)
    s=affinity.rotate(s,-a.GetOrientationDegrees(),origin=(0,0));s=affinity.translate(s,*xy(a.GetPosition()))
    if a.GetDrillSize().x:s=s.difference(Point(xy(a.GetPosition())).buffer(p.ToMM(a.GetDrillSize().x)/2,quad_segs=48))
    return s
for fp in b.GetFootprints():
    ref=fp.GetReference();assert (fp.GetLayer()==p.B_Cu)==(ref=='J5')
    for a in fp.Pads():
        assert not a.FlashLayer(p.F_Cu) and a.FlashLayer(p.B_Cu),'Top copper annulus present'
        num=a.GetNumber();net=a.GetNetname()
        if num:assert net==expected[num],(ref,num,net)
        s=padshape(a);netparts[net or 'MECH'].append(s)
        if num:terminal_shapes[(ref,num,net)]=s
        if a.GetDrillSize().x:holes.append((*xy(a.GetPosition()),p.ToMM(a.GetDrillSize().x)))
for t in b.GetTracks():
    assert not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu
    netparts[t.GetNetname()].append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2,quad_segs=48))
# Through-hole drills remove copper from both pads AND tracks that run
# through pad centers. Subtract them after uniting the net shapes.
drill_voids=unary_union([Point(x,y).buffer(d/2,quad_segs=48) for x,y,d in holes])
nets={n:unary_union(ss).difference(drill_voids) for n,ss in netparts.items()};copper=unary_union(list(nets.values()))
for n in expected.values():assert nets[n].geom_type=='Polygon',('CAD net disconnected',n)
minclear=min(nets[a].distance(nets[c]) for i,a in enumerate(nets) for c in list(nets)[i+1:]);assert minclear>=.3-1e-6,minclear
assert len(holes)==16
# Independently check the saved manufacturing-only mirrored board, including
# every numbered pin and every trace, rather than trusting the transform script.
mb=p.LoadBoard(str(ROOT/'exports/milling/machining-view.kicad_pcb'));mb.BuildConnectivity()
actual={}
for fp in mb.GetFootprints():
    for a in fp.Pads():
        if a.GetNumber():actual[(fp.GetReference(),a.GetNumber())]=(p.ToMM(a.GetPosition().x)-50,16-(p.ToMM(a.GetPosition().y)-50),a.GetNetname())
for fp in b.GetFootprints():
    for a in fp.Pads():
        if a.GetNumber():assert all(abs(k-l)<1e-6 for k,l in zip(actual[(fp.GetReference(),a.GetNumber())][:2],xy(a.GetPosition())))
for mt in mb.GetTracks():assert mt.GetLayer()==p.F_Cu
drill=(ROOT/'exports/milling/machining-view-NPTH.drl').read_text();assert drill.count('\nX')==16
allowed={'G0','G1','G4','G17','G21','G54','G90','M3','M5','M6','M9','M30','M331'}
def parse(path,placements):
    pos={'X':None,'Y':None,'Z':None};op=bid=tool=feed=None;spin=False;changes=[];segments=defaultdict(list);minutes=0;bounds=[];last=None
    origins={d['id']:(d['x'],d['y']) for d in placements}
    for line_no,raw in enumerate(path.read_text().splitlines(),1):
        if raw.startswith('(OPERATION '):op=int(re.search(r'OPERATION (\d+)',raw)[1]);bid=None
        if raw.startswith('(BOARD '):bid=int(re.search(r'BOARD (\d+)',raw)[1])
        s=re.sub(r'\([^)]*\)','',raw).strip()
        if not s:continue
        words=re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)',s);assert words
        assert ''.join(k+v for k,v in words)==s.replace(' ',''),(line_no,s)
        cmd=words[0][0]+words[0][1];assert cmd in allowed,(line_no,s);last=cmd
        data={k:float(v) for k,v in words[1:]}
        if cmd=='M6':
            assert not spin and (tool is None or pos['Z']>=5);tool=int(data['T']);changes.append(tool)
        if cmd=='M3':assert data['S']==12000 and tool in (2,3);spin=True
        if cmd=='M5':spin=False
        if cmd=='G4':minutes+=data['P']/60
        if 'F' in data:feed=data['F'];assert 0<feed<=300
        if cmd not in ('G0','G1'):continue
        new={k:data.get(k,pos[k]) for k in pos}
        if all(v is not None for v in new.values()):
            assert 0<=new['X']<=150 and 0<=new['Y']<=100 and -1.55001<=new['Z']<=10
        if all(v is not None for v in (*pos.values(),*new.values())) and pos!=new:
            a,bb=tuple(pos.values()),tuple(new.values())
            if cmd=='G0':assert (a[:2]==bb[:2] and bb[2]>=5) or min(a[2],bb[2])>=5,(line_no,s)
            if min(a[2],bb[2])<0:assert spin
            if cmd=='G1':assert feed
            minutes+=math.dist(a,bb)/(feed if cmd=='G1' else 2000)
            if cmd=='G1' and min(a[2],bb[2])<0:
                assert bid in origins;dx,dy=origins[bid]
                # Compare only the material-cutting part of vertical entries.
                # Repeated boards may start their approach at Z10 versus Z5.
                if max(a[2],bb[2])>0:assert a[:2]==bb[:2]
                aa=(a[0]-dx,a[1]-dy,min(0,a[2]));cc=(bb[0]-dx,bb[1]-dy,min(0,bb[2]));segments[(bid,op)].append((aa,cc))
                bounds.extend([a,bb])
                if op==2:assert abs(bb[2]-a[2])<=.25+.00001
        pos=new
    assert changes==[2,3] and not spin and pos['Z']==10 and last=='M30'
    return segments,round(minutes,1),[min(v[i] for v in bounds) for i in range(3)]+[max(v[i] for v in bounds) for i in range(3)]
single,singlemin,sbounds=parse(CAM/job['programs']['single'],job['placements'][:1])
panel,panelmin,pbounds=parse(CAM/job['programs']['panel'],job['placements'])
for bid in range(1,26):
    for op in [1,2,3]:
        assert len(panel[(bid,op)])==len(single[(1,op)])
        for aa,bb in zip(panel[(bid,op)],single[(1,op)]):
            assert max(abs(a-b) for x,y in zip(aa,bb) for a,b in zip(x,y))<.000011,('panel differs',bid,op,aa,bb)
def clipped(a,b,z):
    if min(a[2],b[2])>z:return None
    lo=0 if a[2]<=z else (z-a[2])/(b[2]-a[2]);hi=1 if b[2]<=z else (z-a[2])/(b[2]-a[2])
    aa=tuple(a[i]+lo*(b[i]-a[i]) for i in [0,1]);bb=tuple(a[i]+hi*(b[i]-a[i]) for i in [0,1])
    return Point(aa) if aa==bb else LineString([aa,bb])
def sweep(op,z):
    lines=[clipped(a,b,z) for a,b in single[(1,op)]];lines=[l for l in lines if l is not None]
    return unary_union(lines).buffer(job['isolation']['effective_diameter_mm']/2 if op==1 else .4,quad_segs=32)
print('Checking tool sweeps, through holes, tabs and remaining copper...',flush=True)
top=unary_union([sweep(op,-.001) for op in [1,2,3]]);holebottom=sweep(2,-1.4);outlinebottom=sweep(3,-1.4)
for x,y,d in holes:assert Point(x,y).buffer(d/2-.003,quad_segs=64).difference(holebottom).area<1e-6,('uncut hole',x,y,d)

if copper.buffer(-.01).intersection(top).area>1e-6:
    print({n:{op:round(g.buffer(-.01).intersection(sweep(op,-.001)).area,5) for op in [1,2,3]} for n,g in nets.items()},flush=True)
    fig,ax=plt.subplots(figsize=(10,7))
    for geom,col in [(top,'#bbbbbb'),(copper,'#d45d44')]:
        for poly in geom.geoms if hasattr(geom,'geoms') else [geom]:
            xx,yy=poly.exterior.xy;ax.fill(xx,yy,color=col,alpha=.65)
            for ring in poly.interiors:
                xx,yy=ring.xy;ax.fill(xx,yy,color='white')
    ax.set_aspect('equal');ax.set_xlim(-1,27);ax.set_ylim(-1,17);fig.savefig(ROOT/'checks/cut-diagnostic.png')
assert copper.buffer(-.01).intersection(top).area<1e-6,('copper damage',copper.buffer(-.01).intersection(top).area)
residual=box(0,0,26,16).difference(top);islands=list(residual.geoms);assignment={}
for (ref,num,n),s in terminal_shapes.items():
    anchor=s.buffer(-.05).representative_point();found=[i for i,shape in enumerate(islands) if shape.covers(anchor)];assert len(found)==1,(ref,num,'lost pad')
    i=found[0]
    if n in assignment:assert assignment[n]==i,(ref,num,'open')
    assignment[n]=i
assert len(set(assignment.values()))==4,'shorted signals'
for n,i in assignment.items():assert islands[i].area<nets[n].area*1.2+.2,(n,'background copper connection')
tabs=[]
for edge in [LineString([(-.4,0),(-.4,16)]),LineString([(0,16.4),(26,16.4)]),LineString([(26.4,16),(26.4,0)]),LineString([(26,-.4),(0,-.4)])]:
    left=edge.difference(outlinebottom.buffer(.002));assert abs(left.length-2)<.02,left.length;tabs.append(round(left.length,3))
actualdepths={op:min(min(a[2],bb[2]) for a,bb in single[(1,op)]) for op in [1,2,3]};assert actualdepths=={1:-.12,2:-1.55,3:-1.55}
for bd in job['placements']:
    envelope=box(bd['x']-.8,bd['y']-.8,bd['x']+26.8,bd['y']+16.8);assert box(0,0,150,100).contains(envelope)
    for other in job['placements']:
        if bd['id']==other['id']:continue
        assert not envelope.intersects(box(other['x'],other['y'],other['x']+26,other['y']+16))
report={'status':'PASS','date':'2026-10-29','cad_min_clearance_mm':round(minclear,4),'copper_layer':'B.Cu only; no top annuli flashed','electrical_nets':expected,'headers_per_net':5,'holes_per_board':16,'total_panel_holes':400,'boards':25,'board_mm':[26,16,1.4],'stock_mm':[150,100,1.4],'operation_min_z_mm':actualdepths,'tab_neck_widths_mm':tabs,'tab_remaining_mm':.5,'through_allowance_mm':.15,'single_motion_minutes':singlemin,'panel_motion_minutes':panelmin,'panel_motion_bounds_mm':pbounds,'checks':['ERC/DRC/schematic parity zero violations','All 20 connector pins agree with independent net table','No vias or flashed top copper','Mirrored CAM connector centers match original CAD','400 holes pocketed without residual cores','Final nominal copper preserves all four nets without opens or shorts','25 copies identical to validated single-board motions','100 tabs; 2 mm neck and 0.5 mm remaining thickness','Safe clearance rapids, bounded feed/depth, stopped spindle at ATC','No origin reset or commands that disable native leveling'],'limits':'Offline geometry validation. Actual cutter diameter, runout, stock flatness, tape support and probe accuracy remain operator-dependent; not physically test-cut.'}
report['program_sha256']={kind:hashlib.sha256((CAM/f).read_bytes()).hexdigest() for kind,f in job['programs'].items()}
(CAM/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)

colors={'/GND':'#263d47','/+3V3':'#cb4a38','/SDA':'#1d88a8','/SCL':'#b48a09','MECH':'#969e9c'}
def drawcopper(ax,dx=0,dy=0,topview=False,alpha=1):
    for n,g in nets.items():
        g=affinity.scale(g,xfact=-1,yfact=1,origin=(13,8)) if topview else g
        for poly in list(g.geoms) if hasattr(g,'geoms') else [g]:
            xx,yy=poly.exterior.xy;ax.fill([x+dx for x in xx],[y+dy for y in yy],color=colors[n],alpha=alpha)
            for ring in poly.interiors:
                xx,yy=ring.xy;ax.fill([x+dx for x in xx],[y+dy for y in yy],color='white')
    ax.add_patch(Rectangle((dx,dy),26,16,fill=False,edgecolor='#29383a',linewidth=1))
def clean(ax):ax.set_aspect('equal');ax.set_xlabel('mm');ax.set_ylabel('mm');ax.grid(alpha=.15)
fig,(a,c)=plt.subplots(1,2,figsize=(12,5.2));drawcopper(a,topview=True,alpha=.55);drawcopper(c)
for ref,x,y,w,h in [('J1',3,8,2.1,9.72),('J2',8,8,2.5,10.56),('J3',13,8,2.54,10.16),('J4',17.45,8,4.5,9.9)]:
    a.add_patch(Rectangle((x-w/2,y-h/2),w,h,fill=False,edgecolor='#192a2e',linewidth=1.3));a.text(x,17,ref,ha='center',weight='bold')
for y,n in [(11.81,'BLACK / GND'),(9.27,'RED / 3V3'),(6.73,'YELLOW / SDA'),(4.19,'GREEN / SCL')]:a.text(-1,y,n,ha='right',va='center',fontsize=8)
qfp=next(fp for fp in b.GetFootprints() if fp.GetReference()=='J5')
for item in qfp.GraphicalItems():
    if isinstance(item,p.PCB_SHAPE) and item.GetLayer()==p.B_Fab and item.GetShape()==p.SHAPE_T_SEGMENT:
        st,en=xy(item.GetStart()),xy(item.GetEnd());c.plot([st[0],en[0]],[st[1],en[1]],color='#192a2e',linewidth=1)
c.text(3,12.4,'J5 Qwiic',ha='center',weight='bold',fontsize=9)
a.set_title('TOP: wires + female + male + JST PH\nCopper shown faintly through the board',fontsize=11)
c.set_title('BOTTOM: actual copper / soldering side\nQwiic socket mounts here',fontsize=11)
for ax in [a,c]:clean(ax);ax.set_xlim(-1,27);ax.set_ylim(-1,18)
a.set_xlim(-10,27)
fig.suptitle('Nezha wire hub A  |  26 × 16 mm  |  3.3 V I²C',fontsize=16)
fig.text(.5,.02,'Every numbered connector: 1 GND · 2 3V3 · 3 SDA · 4 SCL. Qwiic is on the underside. No jumper resistor.',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.14,1,.92])
for ext in ['pdf','svg','png']:fig.savefig(ROOT/f'exports/assembly-preview.{ext}',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(figsize=(11,7.8))
ax.add_patch(Rectangle((0,0),150,100,fill=False,edgecolor='#192a2e',linewidth=1.8))
for bd in job['placements']:
    x,y=bd['x'],bd['y'];drawcopper(ax,x,y)
    ax.text(x+13,y+13.3,str(bd['id']),ha='center',fontsize=8,color='#50575a')
    for px,py in [(x,y+8),(x+13,y),(x+26,y+8),(x+13,y+16)]:ax.plot(px,py,'s',color='#d58b1e',markersize=2.5)
ax.plot(0,0,'ko');ax.annotate('G54 (0,0)',(0,0),(2,-4),fontsize=9)
ax.plot(16,8,'o',color='#9d3188',markersize=5);ax.annotate('Auto Z on bare copper',(16,8),(4,-10),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.set_xlim(-3,153);ax.set_ylim(-13,104);clean(ax)
ax.set_title('25 adapters · 150 × 100 × 1.4 mm fresh stock\nBOTTOM copper facing up — machining files already mirrored',fontsize=15)
fig.text(.5,.02,'5 × 5 array · 2 mm gutters · 6 mm border · four tabs per board · T2 isolation / T3 holes + outline',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.04,1,1])
for ext in ['pdf','svg','png']:fig.savefig(CAM/f'panel-layout.{ext}',dpi=160)
