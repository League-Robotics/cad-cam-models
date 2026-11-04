#!/usr/bin/env python3
"""Build the adapter with KiCad 9's pcbnew, on Buzzkill. Dimensions are mm."""
from pathlib import Path
import json
import uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design'
LIB = OUT / 'Adapter.pretty'
OUT.mkdir(exist_ok=True)
LIB.mkdir(exist_ok=True)
# Remove the superseded generated footprint from the active project library.
(LIB/'Kycon_GMX-SMT4-N-44.kicad_mod').unlink(missing_ok=True)
NAME = 'nezha-qwiic'
IO = p.PCB_IO_KICAD_SEXPR()
NS = uuid.UUID('24850d9f-d02c-4720-860e-a2e4a20a8d15')
def uid(s): return str(uuid.uuid5(NS, s))
def v(x, y): return p.VECTOR2I(p.FromMM(x), p.FromMM(y))
def q(s): return json.dumps(str(s))

def pad(fp, number, x, y, sx, sy, hole=None):
    a = p.PAD(fp)
    a.SetNumber(str(number))
    a.SetPosition(v(x,y))
    a.SetSize(v(sx,sy))
    a.SetShape(p.PAD_SHAPE_RECT if hole is None else p.PAD_SHAPE_CIRCLE)
    a.SetAttribute(p.PAD_ATTRIB_SMD if hole is None else p.PAD_ATTRIB_NPTH)
    layers=p.LSET()
    for layer in [p.F_Cu,p.F_Paste,p.F_Mask] if hole is None else [p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask]:layers.AddLayer(layer)
    a.SetLayerSet(layers)
    if hole: a.SetDrillSize(v(hole,hole))
    fp.Add(a)
    return a

def line(owner, a, b, layer, width=0.12):
    s = p.PCB_SHAPE(owner)
    s.SetShape(p.SHAPE_T_SEGMENT)
    s.SetStart(v(*a)); s.SetEnd(v(*b)); s.SetLayer(layer); s.SetWidth(p.FromMM(width))
    owner.Add(s)

def rect(owner,x1,y1,x2,y2,layer,width=0.12):
    pts=[(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
    for a,b in zip(pts,pts[1:]):line(owner,a,b,layer,width)

def footprint(name, description):
    fp=p.FOOTPRINT(None);fp.SetFPID(p.LIB_ID('Adapter',name));fp.SetAttributes(p.FP_SMD)
    fp.SetLibDescription(description);fp.SetReference('REF**');fp.SetValue(name)
    fp.Reference().SetPosition(v(0,-2));fp.Value().SetVisible(False)
    return fp

# FCI / Amphenol drawing 73306, released revision M, sheet 3 revision B.
# Local front is y=0, body extends toward +y. Drawing sheet 3 shows the
# opposite orientation (mouth right, tails left); dimensions are transformed.
# The drawing does not label contacts. Project numbering is explicitly
# 4-3-2-1 left-to-right looking into the latch-UP mouth, so pad 1 is GND
# for the user's stated latch-side plug colors YELLOW GREEN RED BLACK.
jack=footprint('Amphenol_73306-111LF','Amphenol/FCI 73306 rev M; sheet 3 B land pattern; front y=0; latch up; project front-view numbering 4 3 2 1')
for n in range(1,5):pad(jack,n,(n-2.5)*1.27,14.4,.76,3.4)
for x in [-5.2,5.2]:pad(jack,'',x,5.65,2.35,5.5)
rect(jack,-5.59,0,5.59,12.7,p.F_Fab,.1)
# Silk leaves clearance around the two hold-down lands.
line(jack,(-5.79,0),(5.79,0),p.F_SilkS)
for x in [-5.79,5.79]:
    line(jack,(x,0),(x,2.6),p.F_SilkS)
    line(jack,(x,8.7),(x,12.9),p.F_SilkS)
rect(jack,-6.875,-.5,6.875,16.6,p.F_CrtYd,.05)
IO.FootprintSave(str(LIB),jack)

header=footprint('Samtec_TSM-104-01-L-SV','Samtec TSM single-row vertical recommended land pattern rev D; no alignment/locking option')
for n in range(1,5):pad(header,n,(2.5-n)*2.54,1.46 if n%2 else -1.46,1.27,3.43)
for n in range(1,5):
    x=(2.5-n)*2.54
    rect(header,x-.32,-.32,x+.32,.32,p.F_Fab,.1)
rect(header,-5.08,-1.27,5.08,1.27,p.F_Fab,.1)
rect(header,-5.58,-3.675,5.58,3.675,p.F_CrtYd,.05)
for x in [-5.3,5.3]:line(header,(x,-1.1),(x,1.1),p.F_SilkS)
IO.FootprintSave(str(LIB),header)

for lib,name in [('Connector_JST','JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical'),('Resistor_SMD','R_1206_3216Metric')]:
    fp=p.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',name)
    for a in fp.Pads():
        if a.GetNumber()=='MP':a.SetNumber('')
    fp.SetFPID(p.LIB_ID('Adapter',name))
    IO.FootprintSave(str(LIB),fp)

hole=footprint('HeatStake_3mm','3.00 mm non-plated heat-stake hole; 5 mm nominal head keepout')
hole.SetAttributes(p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
pad(hole,'',0,0,3,3,3)
circle=p.PCB_SHAPE(hole);circle.SetShape(p.SHAPE_T_CIRCLE);circle.SetCenter(v(0,0));circle.SetEnd(v(1.5,0));circle.SetWidth(p.FromMM(.1));circle.SetLayer(p.F_Fab);hole.Add(circle)
rect(hole,-2.5,-2.5,2.5,2.5,p.F_CrtYd,.05)
IO.FootprintSave(str(LIB),hole)

board=p.BOARD()
board.GetDesignSettings().SetBoardThickness(p.FromMM(1.4))
board.GetDesignSettings().SetAuxOrigin(v(50,50))
tb=board.GetTitleBlock();tb.SetTitle('Nezha 3.3 V / 4P4C to Qwiic');tb.SetRevision('B');tb.SetDate('2026-10-05')
nets={}
for name in ['GND','+3V3','SDA','SCL','SCL_JACK']:
    net=p.NETINFO_ITEM(board,'/'+name);board.Add(net);nets[name]=net

specs={
 'J1':('Amphenol_73306-111LF','73306-111LF',1,12.5,90,{'1':'GND','2':'+3V3','3':'SCL_JACK','4':'SDA'}),
 'J2':('Samtec_TSM-104-01-L-SV','TSM-104-01-L-SV',29.5,12,270,{'1':'GND','2':'+3V3','3':'SDA','4':'SCL'}),
 'J3':('JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical','BM04B-SRSS-TB',38.5,12,90,{'1':'GND','2':'+3V3','3':'SDA','4':'SCL'}),
 'R1':('R_1206_3216Metric','0',24,9.8,270,{'1':'SCL','2':'SCL_JACK'}),
 'H1':('HeatStake_3mm','3mm NPTH',4,3,0,{}),
 'H2':('HeatStake_3mm','3mm NPTH',40,21,0,{})}
fps={};points={}
for ref,(fn,value,x,y,angle,netmap) in specs.items():
    fp=IO.FootprintLoad(str(LIB),fn);fp.SetReference(ref);fp.SetValue(value)
    fp.SetFPID(p.LIB_ID('Adapter',fn))
    fp.SetPath(p.KIID_PATH('/'+uid('sheet')+'/'+uid(ref)))
    fp.SetOrientationDegrees(angle);fp.SetPosition(v(x+50,y+50))
    fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
    for a in fp.Pads():
        n=a.GetNumber()
        if n in netmap:a.SetNet(nets[netmap[n]])
        points[(ref,n)]=(p.ToMM(a.GetPosition().x)-50,p.ToMM(a.GetPosition().y)-50)
    board.Add(fp);fps[ref]=fp

def track(net, points, width=.4):
    for a,b in zip(points,points[1:]):
        if a==b:continue
        t=p.PCB_TRACK(board);t.SetStart(v(a[0]+50,a[1]+50));t.SetEnd(v(b[0]+50,b[1]+50));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(width));t.SetNet(nets[net]);board.Add(t)
P=lambda ref,n:points[(ref,str(n))]
track('GND',[P('J1',1),(22.5,13.905),(24.405,15.81),P('J2',1),(32.8,15.81),(35.11,13.5),P('J3',1)])
track('+3V3',[P('J1',2),(23,12.635),(23.635,13.27),P('J2',2),(33,13.27),(33.77,12.5),P('J3',2)])
track('SCL_JACK',[P('J1',3),P('R1',2)])
track('SDA',[P('J1',4),(22.5,10.095),(22.795,9.8),(26.3,9.8),(27.23,10.73),P('J2',3),(33,10.73),(33.77,11.5),P('J3',3)])
track('SCL',[P('R1',1),(26,8.3375),(26.1475,8.19),P('J2',4),(33.3,8.19),(35.61,10.5),P('J3',4)])
rect(board,50,50,94,74,p.Edge_Cuts,.05)

def text(s,x,y,size=1,layer=p.F_SilkS):
    t=p.PCB_TEXT(board);t.SetText(s);t.SetPosition(v(50+x,50+y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(size*.15));t.SetLayer(layer);board.Add(t)
text('NEZHA > QWIIC',26.5,2.2,1.25)
text('3V3 ONLY   REV B',25.5,21.5,1)
text('J1 4P4C',10,2,1)
text('J2',29.5,5.3,.85)
text('J3',38.5,7,.85)
text('R1 0R',23.3,6,.8)
text('1',17.9,15.5,.8)
for s,y in [('SCL',8.19),('SDA',10.73),('3V3',13.27),('GND',15.81)]:text(s,34.5,y-.8,.8)
board.BuildConnectivity()
p.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)

# Embedded symbols keep the schematic self-contained; the project library is
# also provided so symbol editing and library parity checks work normally.
effects='(effects (font (size 1.27 1.27)))'
def connector_symbol(name,count):
    pins=''.join(f'(pin passive line (at -7.62 {-i*2.54} 0) (length 2.54) (name "{i+1}" {effects}) (number "{i+1}" {effects}))' for i in range(count))
    return f'''(symbol "{name}" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
    (property "Reference" "J" (at 0 5.08 0) {effects})
    (property "Value" "{name}" (at 0 2.54 0) {effects})
    (symbol "{name}_0_1" (rectangle (start -5.08 1.27) (end 5.08 {-count*2.54+1.27}) (stroke (width .254) (type default)) (fill (type background))))
    (symbol "{name}_1_1" {pins}))'''
conn=connector_symbol('Conn4',4)
res='''(symbol "R" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
 (property "Reference" "R" (at 0 3.81 0) EFFECTS)
 (property "Value" "0" (at 0 -3.81 0) EFFECTS)
 (symbol "R_0_1" (rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .254) (type default)) (fill (type none))))
 (symbol "R_1_1" (pin passive line (at -5.08 0 0) (length 2.54) (name "~" EFFECTS) (number "1" EFFECTS)) (pin passive line (at 5.08 0 180) (length 2.54) (name "~" EFFECTS) (number "2" EFFECTS))))'''.replace('EFFECTS',effects)
mount='''(symbol "MountingHole" (in_bom no) (on_board yes)
 (property "Reference" "H" (at 0 3.81 0) EFFECTS)
 (property "Value" "3mm NPTH" (at 0 -3.81 0) EFFECTS)
 (symbol "MountingHole_0_1" (circle (center 0 0) (radius 1.524) (stroke (width .254) (type default)) (fill (type none)))))'''.replace('EFFECTS',effects)
library='(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+conn+res+mount+'\n)'
(OUT/'Adapter.kicad_sym').write_text(library)
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Adapter") (type "KiCad") (uri "${KIPRJMOD}/Adapter.kicad_sym") (options "") (descr "Adapter symbols")))\n')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Adapter") (type "KiCad") (uri "${KIPRJMOD}/Adapter.pretty") (options "") (descr "Verified adapter footprints")))\n')
embedded=''.join(s.replace('(symbol "'+n+'"','(symbol "Adapter:'+n+'"',1) for s,n in [(conn,'Conn4'),(res,'R'),(mount,'MountingHole')])
sch=[f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid {uid('sheet')}) (paper "A4")
 (title_block (title "Nezha 3.3 V / 4P4C to Qwiic") (date "2026-10-05") (rev "B") (comment 1 "Passive adapter. R1 is the single-sided crossover link."))
 (lib_symbols {embedded})''']
def note(s,x,y,size=1.27):sch.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid(s+str(x)+str(y))}))')
def instance(ref,symbol,x,y):
    fn,value,*_=specs[ref]
    sch.append(f'''(symbol (lib_id "Adapter:{symbol}") (at {x} {y} 0) (unit 1) (in_bom {'no' if ref[0]=='H' else 'yes'}) (on_board yes) (dnp no) (uuid {uid(ref)})
    (property "Reference" "{ref}" (at {x} {y-7.62} 0) {effects})
    (property "Value" {q(value)} (at {x} {y-5.08} 0) {effects})
    (property "Footprint" "Adapter:{fn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "{NAME}" (path "/{uid('sheet')}" (reference "{ref}") (unit 1)))))''')
def wire(a,b,key):sch.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid(key)}))')
def label(net,x,y,key):sch.append(f'(label {q(net)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid(key)}))')
for ref,x in [('J1',63.5),('J2',139.7),('J3',215.9)]:
    y=76.2;instance(ref,'Conn4',x,y)
    for i in range(4):
        net=specs[ref][-1][str(i+1)];py=y+i*2.54
        wire((x-7.62,py),(x-22.86,py),ref+'wire'+str(i))
        label(net,x-22.86,py,ref+'label'+str(i))
instance('R1','R',101.6,114.3)
wire((96.52,114.3),(83.82,114.3),'R1left');label('SCL',83.82,114.3,'R1l')
wire((106.68,114.3),(127,114.3),'R1right');label('SCL_JACK',127,114.3,'R1r')
instance('H1','MountingHole',170,115);instance('H2','MountingHole',205,115)
note('J1 FRONT VIEW: latch UP; project contacts 4 3 2 1 left to right.\n1 BLACK/GND; 2 RED/3V3; 3 GREEN/SCL; 4 YELLOW/SDA.',35,40)
note('J2: 0.1 inch / 2.54 mm MALE\nJ3: JST-SH 1 mm TOP ENTRY (Qwiic)',140,40)
note('R1 = 0 ohm, 1206. Fit this link for SCL continuity.\nSDA passes under its insulated body on the front copper.',35,137)
note('J1: Amphenol 73306-111LF. Body height 14 mm.\nJ2 pin 1 / GND is at the BOTTOM in the board drawing.',35,151)
note('2 x 3.00 mm NON-PLATED holes.\nAll copper routing on F.Cu; no vias.\n3.3 V confirmed by user; no regulator or level conversion.',160,137)
note('Cable convention: plug nose away, cable toward viewer.\nLatch-side view YELLOW GREEN RED BLACK.\nContact-side view BLACK RED GREEN YELLOW.\nBefore powering the first assembled board, continuity-check\nactual cable colors against J2 labels, including both cable ends.',35,163)
sch.append(')');(OUT/(NAME+'.kicad_sch')).write_text('\n'.join(sch)+'\n')
project={
 'meta':{'filename':NAME+'.kicad_pro','version':1},
 'board':{'design_settings':{'rules':{'min_clearance':.3,'min_track_width':.35,'min_copper_edge_clearance':.5,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.1},'rule_severities':{'silk_over_copper':'warning'},'defaults':{'board_outline_line_width':.05}}},
 'net_settings':{'classes':[{'name':'Default','clearance':.3,'track_width':.4,'via_diameter':.6,'via_drill':.3}],'meta':{'version':4}}}
(OUT/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
(OUT/(NAME+'.kicad_dru')).write_text('''(version 1)
(rule "Front copper only" (constraint disallow track via) (layer "B.Cu"))
(rule "No vias on milled adapter" (constraint disallow via))
(rule "Milling copper clearance" (constraint clearance (min 0.3mm)))
(rule "Milling track width" (constraint track_width (min 0.35mm)))
(rule "Board edge clearance" (constraint edge_clearance (min 0.5mm)))
''')
print(json.dumps({'revision':'B','jack':'Amphenol 73306-111LF','board_mm':[44,24],'holes_mm':[[4,3,3],[40,21,3]],'pads':{ref:{str(n):P(ref,n) for n in range(1,5)} for ref in ['J1','J2','J3']}},indent=2))
