#!/usr/bin/env python3
"""Generate a single-bottom-copper wire hub using KiCad 9 on Buzzkill."""
from pathlib import Path
import json, uuid
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design'; LIB=OUT/'WireHub.pretty'
for d in [OUT,LIB,ROOT/'checks',ROOT/'exports']: d.mkdir(parents=True,exist_ok=True)
NAME='nezha-wire-hub'; W,H=26.,16.; O=50.
NS=uuid.UUID('c6863c8a-c159-4a44-bb3f-2d6546b097cc')
def uid(s):return str(uuid.uuid5(NS,s))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def q(s):return json.dumps(str(s))
IO=p.PCB_IO_KICAD_SEXPR()
def layers(*ls):
    s=p.LSET()
    for l in ls:s.AddLayer(l)
    return s
def line(owner,a,b,layer,width=.1):
    s=p.PCB_SHAPE(owner);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*b));s.SetLayer(layer);s.SetWidth(p.FromMM(width));owner.Add(s)
def rect(owner,x1,y1,x2,y2,layer,width=.1):
    pts=[(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
    for a,b in zip(pts,pts[1:]):line(owner,a,b,layer,width)
def header(name,body_width,body_length,drill,pad_dia):
    fp=p.FOOTPRINT(None);fp.SetFPID(p.LIB_ID('WireHub',name));fp.SetReference('REF**');fp.SetValue(name);fp.SetAttributes(p.FP_THROUGH_HOLE)
    fp.SetLibDescription('4 pins on 2.54 mm pitch; bottom copper only; locally milled holes are unplated')
    for i in range(4):
        a=p.PAD(fp);a.SetNumber(str(i+1));a.SetAttribute(p.PAD_ATTRIB_PTH);a.SetShape(p.PAD_SHAPE_RECT if i==0 else p.PAD_SHAPE_CIRCLE);a.SetPosition(v(0,i*2.54));a.SetSize(v(pad_dia,pad_dia));a.SetDrillSize(v(drill,drill));a.SetLayerSet(layers(p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask));a.SetRemoveUnconnected(True);a.SetKeepTopBottom(False);fp.Add(a)
    over=(body_length-7.62)/2
    rect(fp,-body_width/2,-over,body_width/2,7.62+over,p.F_Fab)
    rect(fp,-body_width/2-.3,-over-.3,body_width/2+.3,7.62+over+.3,p.F_CrtYd,.05)
    IO.FootprintSave(str(LIB),fp)
header('Wire_1x04_P2.54_D1.10',2.1,9.72,1.1,2.1)
header('Harwin_M20_7820442_Female',2.5,10.56,1.05,2.0)
header('Harwin_M20_9990446_Male',2.54,10.16,1.05,2.0)
ph=p.FootprintLoad('/usr/share/kicad/footprints/Connector_JST.pretty','JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical')
ph.SetFPID(p.LIB_ID('WireHub','JST_PH_B4B_4_BottomPads_D0.90'))
for a in ph.Pads():
    a.SetLayerSet(layers(p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask));a.SetDrillSize(v(.9,.9));a.SetSize(v(1.6,2.0));a.SetRemoveUnconnected(True);a.SetKeepTopBottom(False);a.SetShape(p.PAD_SHAPE_RECT if a.GetNumber()=='1' else p.PAD_SHAPE_OVAL)
IO.FootprintSave(str(LIB),ph)
sh=p.FootprintLoad('/usr/share/kicad/footprints/Connector_JST.pretty','JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical')
sh.SetFPID(p.LIB_ID('WireHub','JST_SH_BM04B_SRSS'))
for a in sh.Pads():
    if a.GetNumber()=='MP':a.SetNumber('')
IO.FootprintSave(str(LIB),sh)

board=p.BOARD();board.GetDesignSettings().SetBoardThickness(p.FromMM(1.4));board.GetDesignSettings().SetAuxOrigin(v(O,O))
tb=board.GetTitleBlock();tb.SetTitle('Nezha wire / header / PH / Qwiic hub');tb.SetRevision('A');tb.SetDate('2026-10-29')
nets={}
signals=['GND','+3V3','SDA','SCL']
for n in signals:
    net=p.NETINFO_ITEM(board,'/'+n);board.Add(net);nets[n]=net
specs={
 'J1':('Wire_1x04_P2.54_D1.10','WIRE BLACK RED YELLOW GREEN',3,4.19,0,False),
 'J2':('Harwin_M20_7820442_Female','M20-7820442 FEMALE',8,4.19,0,False),
 'J3':('Harwin_M20_9990446_Male','M20-9990446 MALE',13,4.19,0,False),
 'J4':('JST_PH_B4B_4_BottomPads_D0.90','B4B-PH-K-S',18,5,270,False),
 'J5':('JST_SH_BM04B_SRSS','BM04B-SRSS-TB',23,8,270,True)}
points={}
for ref,(fn,value,x,y,angle,bottom) in specs.items():
    fp=IO.FootprintLoad(str(LIB),fn);fp.SetReference(ref);fp.SetValue(value);fp.SetPath(p.KIID_PATH('/'+uid('sheet')+'/'+uid(ref)))
    fp.SetFPID(p.LIB_ID('WireHub',fn))
    board.Add(fp)
    if bottom:fp.Flip(v(0,0),p.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(angle);fp.SetPosition(v(O+x,O+y));fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
    for a in fp.Pads():
        num=a.GetNumber()
        if num:a.SetNet(nets[signals[int(num)-1]])
        points[(ref,num)]=(p.ToMM(a.GetPosition().x)-O,p.ToMM(a.GetPosition().y)-O)
def P(ref,i):return points[(ref,str(i))]
def track(n,pts,width=.6):
    for a,b in zip(pts,pts[1:]):
        if a==b:continue
        t=p.PCB_TRACK(board);t.SetStart(v(O+a[0],O+a[1]));t.SetEnd(v(O+b[0],O+b[1]));t.SetLayer(p.B_Cu);t.SetWidth(p.FromMM(width));t.SetNet(nets[n]);board.Add(t)
# All numbered rows ascend physically from top to bottom in the component view.
assert [round(P('J5',i)[1],3) for i in range(1,5)]==[6.5,7.5,8.5,9.5],points
assert P('J5',1)[0]>23,points
for i,n in enumerate(signals,1):
    y=P('J3',i)[1]; py=P('J4',i)[1]; qx,qy=P('J5',i)
    track(n,[P('J1',i),P('J2',i),P('J3',i),(14.8,y),(16.4,py),P('J4',i)])
    track(n,[P('J4',i),(19.2,py),(20.2,qy),(qx,qy)],.4)
rect(board,O,O,O+W,O+H,p.Edge_Cuts,.05)
def text(s,x,y,size=.8,layer=p.F_SilkS):
    t=p.PCB_TEXT(board);t.SetText(s);t.SetPosition(v(O+x,O+y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);board.Add(t)
for s,x in [('WIRE',3),('FEMALE',8),('MALE',13),('PH',18),('QWIIC',23)]:text(s,x,1.1,.8)
text('3V3 ONLY  /  WIRE HUB A',13,14.8,.8)
for i,s in enumerate(['G','V','D','C'],1):text(s,5.5,P('J1',i)[1],.8)
text('QWIIC',23,2.5,.8,p.B_SilkS)
board.BuildConnectivity();p.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)

effects='(effects (font (size 1.27 1.27)))'
pins=''.join(f'(pin passive line (at -7.62 {-i*2.54} 0) (length 2.54) (name "{i+1}" {effects}) (number "{i+1}" {effects}))' for i in range(4))
symbol=f'''(symbol "Conn4" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
 (property "Reference" "J" (at 0 5.08 0) {effects})
 (property "Value" "Conn4" (at 0 2.54 0) {effects})
 (symbol "Conn4_0_1" (rectangle (start -5.08 1.27) (end 5.08 -8.89) (stroke (width .254) (type default)) (fill (type background))))
 (symbol "Conn4_1_1" {pins}))'''
(OUT/'WireHub.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+symbol+'\n)')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "WireHub") (type "KiCad") (uri "${KIPRJMOD}/WireHub.kicad_sym") (options "") (descr "Wire hub symbols")))\n')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "WireHub") (type "KiCad") (uri "${KIPRJMOD}/WireHub.pretty") (options "") (descr "Bottom-copper wire hub footprints")))\n')
embedded=symbol.replace('(symbol "Conn4"','(symbol "WireHub:Conn4"',1)
sch=[f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid {uid('sheet')}) (paper "A4")
 (title_block (title "Nezha 3.3V wire / header / PH / Qwiic hub") (date "2026-10-29") (rev "A") (comment 1 "All connectors parallel. Bottom copper only. No crossover or active parts."))
 (lib_symbols {embedded})''']
for ref,x,y in [('J1',63.5,63.5),('J2',139.7,63.5),('J3',215.9,63.5),('J4',101.6,114.3),('J5',190.5,114.3)]:
    fn,value,*_=specs[ref]
    sch.append(f'''(symbol (lib_id "WireHub:Conn4") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})
      (property "Reference" "{ref}" (at {x} {y-7.62} 0) {effects})
      (property "Value" {q(value)} (at {x} {y-5.08} 0) {effects})
      (property "Footprint" "WireHub:{fn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
      (instances (project "{NAME}" (path "/{uid('sheet')}" (reference "{ref}") (unit 1)))))''')
    for i,n in enumerate(signals):
        py=y+i*2.54
        sch.append(f'(wire (pts (xy {x-7.62} {py}) (xy {x-22.86} {py})) (stroke (width 0) (type default)) (uuid {uid(ref+"w"+str(i))}))')
        sch.append(f'(label {q(n)} (at {x-22.86} {py} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid(ref+"l"+str(i))}))')
notes=[('J1: stripped cable wires enter from TOP; solder on BOTTOM.\n1 BLACK = GND; 2 RED = 3V3; 3 YELLOW = SDA; 4 GREEN = SCL.',30,30),('J2 female and J3 male: 2.54 mm pitch, four positions.\nJ4: JST PH, 2 mm pitch, through-hole, top entry.\nJ5: JST SH, 1 mm pitch, Qwiic, SMT on BOTTOM.',30,145),('All five pin-number mappings: 1=GND, 2=3V3, 3=SDA, 4=SCL.\nPH wiring is defined by this board; check the mating cable.\n3.3 V I2C only. No regulator, level shifter or added pull-ups.\nCheck cable continuity before power. Wire colors alone are not proof.',145,145),('26 x 16 mm. One copper layer: B.Cu. No vias or jumpers.\nLocal milling: 16 unplated solder holes, all solder joints on BOTTOM.\nCAM is mirrored once for machining BOTTOM copper face-up.',30,173)]
for s,x,y in notes:sch.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid {uid(s)}))')
sch.append(')');(OUT/(NAME+'.kicad_sch')).write_text('\n'.join(sch)+'\n')
project={'meta':{'filename':NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.3,'min_track_width':.35,'min_copper_edge_clearance':.5,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.1},'defaults':{'board_outline_line_width':.05}}},'net_settings':{'classes':[{'name':'Default','clearance':.3,'track_width':.4}],'meta':{'version':4}}}
(OUT/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
(OUT/(NAME+'.kicad_dru')).write_text('(version 1)\n(rule "No top copper routing" (constraint disallow track via) (layer "F.Cu"))\n(rule "No vias" (constraint disallow via))\n(rule "Milling clearance" (constraint clearance (min 0.3mm)))\n(rule "Milling track width" (constraint track_width (min 0.35mm)))\n(rule "Edge clearance" (constraint edge_clearance (min 0.5mm)))\n')
data={'name':NAME,'revision':'A','board_mm':[W,H,1.4],'copper_layer':'B.Cu','pads':{ref:{str(i):P(ref,i) for i in range(1,5)} for ref in specs},'pinout':{str(i+1):n for i,n in enumerate(signals)}}
(ROOT/'checks/geometry.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
