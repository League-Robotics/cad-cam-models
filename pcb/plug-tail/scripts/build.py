#!/usr/bin/env python3
"""Generate the plug-tail boards (KiCad 9 on Buzzkill): a tongue that slides into the cable
cavity of a 4P4C plug, four square pins soldered flat on its pads, and an output tail.

Local coordinates: x across the board, 0 on the tongue's centreline; y from the tongue tip
(the plug's nose side) toward the tail. Copper is F.Cu only and faces the plug's contacts.
"""
from pathlib import Path
import json, sys, uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
O = 50.
PIN_PITCH = 1.02           # 4P4C contact spacing, 0.040 in
TONGUE_W, TONGUE_L = 5.30, 10.0   # rev B: 10 long (the user, 2026-11-04); rev A was 6.0
PLUG_PAD = (0.62, 0.25, 10.25) # width, start and end y of the pin pads: 10 long (rev A: 0.25-3.60)
# Rev B moved everything behind the tongue 4.8 back (4 for the tongue + 0.8 so every bend stays 0.75
# past the longer pads, as in rev A; a plain 4 puts the SIG/SCL diagonals 0.27 from pad 4).
TRACK = .4
NS = uuid.UUID('5f1d7c2e-3b0a-4f43-9d55-7a0a3c1c8e21')
IO = p.PCB_IO_KICAD_SEXPR()
KLIB = '/usr/share/kicad/footprints'

VARIANTS = {
    # rev C (the user, 2026-11-04): all four lines out on four 2.54 pins, in contact order; a servo plug goes on
    # G V S1, a J-port device uses all four. 10 wide: four 1.0 pads at 2.54 pitch plus edge clearance.
    'header-tail': dict(
        title='Nezha 4P4C plug to four header pins', width=10.0, length=19.0,
        plug=['GND', 'VCC', 'S1', 'S2'],
        parts={'J2': ('FlatPins_1x04_P2.54_SMD', 'HEADER G V S1 S2', (0, 16.2), 0, ['GND', 'VCC', 'S1', 'S2'])},
        tracks=[('GND', [(-1.53, 6.725), (-1.53, 11), (-3.81, 13.28), (-3.81, 16.2)]),
                ('VCC', [(-.51, 6.725), (-.51, 11), (-1.27, 11.76), (-1.27, 16.2)]),
                ('S1', [(.51, 6.725), (.51, 11), (1.27, 11.76), (1.27, 16.2)]),
                ('S2', [(1.53, 6.725), (1.53, 11), (3.81, 13.28), (3.81, 16.2)])]),
    'qwiic-tail': dict(
        title='Nezha 4P4C plug to Qwiic', width=9.0, length=24.0,
        plug=['GND', '+3V3', 'SCL', 'SDA'],
        parts={'J2': ('JST_SH_SM04B-SRSS-TB_Horizontal', 'SM04B-SRSS-TB', (0, 20.875), 0, ['GND', '+3V3', 'SDA', 'SCL_QWIIC']),
               'R1': ('R_1206_3216Metric', '0R 1206', (2.0, 15.2), 270, ['SCL', 'SCL_QWIIC'])},
        tracks=[('GND', [(-1.53, 6.725), (-1.53, 8.8), (-1.5, 18.875)]),
                ('+3V3', [(-.51, 6.725), (-.51, 8.8), (-.5, 18.875)]),
                ('SDA', [(1.53, 6.725), (1.53, 11), (3.4, 12.87), (3.4, 15.2), (.5, 15.2), (.5, 18.875)]),
                ('SCL', [(.51, 6.725), (.51, 11), (2.0, 12.49), (2.0, 13.7375)]),
                ('SCL_QWIIC', [(2.0, 16.6625), (2.0, 17.6), (1.5, 18.1), (1.5, 18.875)])]),
}


def uid(s): return str(uuid.uuid5(NS, s))
def v(x, y): return p.VECTOR2I(p.FromMM(x), p.FromMM(y))
def q(s): return json.dumps(str(s))


def layers(*ls):
    s = p.LSET()
    for l in ls: s.AddLayer(l)
    return s


def segment(owner, a, b, layer, width=.1):
    s = p.PCB_SHAPE(owner); s.SetShape(p.SHAPE_T_SEGMENT); s.SetStart(v(*a)); s.SetEnd(v(*b))
    s.SetLayer(layer); s.SetWidth(p.FromMM(width)); owner.Add(s)


def smd_row(name, n, pitch, w, h, y0, desc):
    fp = p.FOOTPRINT(None); fp.SetFPID(p.LIB_ID('PlugTail', name)); fp.SetReference('REF**'); fp.SetValue(name)
    fp.SetAttributes(p.FP_SMD); fp.SetLibDescription(desc)
    for i in range(n):
        a = p.PAD(fp); a.SetNumber(str(i + 1)); a.SetAttribute(p.PAD_ATTRIB_SMD); a.SetShape(p.PAD_SHAPE_RECT)
        a.SetPosition(v((i - (n - 1) / 2) * pitch, y0)); a.SetSize(v(w, h)); a.SetLayerSet(layers(p.F_Cu, p.F_Mask)); fp.Add(a)
    return fp


def libraries(lib):
    lib.mkdir(parents=True, exist_ok=True)
    w, y1, y2 = PLUG_PAD
    IO.FootprintSave(str(lib), smd_row('PlugPins_1x04_P1.02_SMD', 4, PIN_PITCH, w, y2 - y1, (y1 + y2) / 2,
                                       'Four 0.64 mm square pins lying flat, as they leave a 4P4C plug; origin at the tongue tip'))
    IO.FootprintSave(str(lib), smd_row('FlatPins_1x04_P2.54_SMD', 4, 2.54, 1.0, 5.0, 0,
                                       'Four 0.64 mm square pins lying flat, overhanging the board end for a header plug'))
    sh = p.FootprintLoad(f'{KLIB}/Connector_JST.pretty', 'JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal')
    sh.SetFPID(p.LIB_ID('PlugTail', 'JST_SH_SM04B-SRSS-TB_Horizontal'))
    for a in sh.Pads():
        if a.GetNumber() == 'MP': a.SetNumber('')
    IO.FootprintSave(str(lib), sh)
    r = p.FootprintLoad(f'{KLIB}/Resistor_SMD.pretty', 'R_1206_3216Metric'); r.SetFPID(p.LIB_ID('PlugTail', 'R_1206_3216Metric'))
    IO.FootprintSave(str(lib), r)


def build(name, spec):
    out = ROOT / 'design' / name; lib = out / 'PlugTail.pretty'; libraries(lib)
    W, L = spec['width'], spec['length']; X0 = O + W / 2
    def k(x, y): return v(X0 + x, O + y)
    board = p.BOARD(); ds = board.GetDesignSettings(); ds.SetBoardThickness(p.FromMM(1.4)); ds.SetAuxOrigin(v(O, O))
    tb = board.GetTitleBlock(); tb.SetTitle(spec['title']); tb.SetRevision('C'); tb.SetDate('2026-11-04')
    names = sorted({n for n in spec['plug'] if n} | {n for *_, ns in spec['parts'].values() for n in ns})
    nets = {}
    for n in names:
        net = p.NETINFO_ITEM(board, '/' + n); board.Add(net); nets[n] = net
    nc = p.NETINFO_ITEM(board, 'unconnected-(J1-Pad4)')
    parts = {'J1': ('PlugPins_1x04_P1.02_SMD', '4P4C PLUG PINS', (0, 0), 0, spec['plug']), **spec['parts']}
    pads = {}
    for ref, (fn, value, (x, y), angle, pinnets) in parts.items():
        fp = IO.FootprintLoad(str(lib), fn); fp.SetReference(ref); fp.SetValue(value)
        fp.SetPath(p.KIID_PATH('/' + uid(name + 'sheet') + '/' + uid(name + ref))); fp.SetFPID(p.LIB_ID('PlugTail', fn))
        board.Add(fp); fp.SetOrientationDegrees(angle); fp.SetPosition(k(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        for a in fp.Pads():
            num = a.GetNumber()
            if not num: continue
            n = pinnets[int(num) - 1]
            if n: a.SetNet(nets[n])
            elif n is None and ref == 'J1': board.Add(nc); a.SetNet(nc)
            pads[(ref, num)] = (round(p.ToMM(a.GetPosition().x) - X0, 4), round(p.ToMM(a.GetPosition().y) - O, 4))
    assert [pads[('J1', str(i))][0] for i in range(1, 5)] == [-1.53, -.51, .51, 1.53], pads
    if 'R1' in parts: assert pads[('R1', '1')][1] < pads[('R1', '2')][1], ('R1 pad 1 must face the plug', pads)
    for n, pts in spec['tracks']:
        for a, b in zip(pts, pts[1:]):
            t = p.PCB_TRACK(board); t.SetStart(k(*a)); t.SetEnd(k(*b)); t.SetLayer(p.F_Cu)
            t.SetWidth(p.FromMM(TRACK)); t.SetNet(nets[n]); board.Add(t)
    tw = TONGUE_W / 2
    outline = [(-tw, 0), (tw, 0), (tw, TONGUE_L), (W / 2, TONGUE_L), (W / 2, L), (-W / 2, L), (-W / 2, TONGUE_L), (-tw, TONGUE_L)]
    for a, b in zip(outline, outline[1:] + outline[:1]): segment(board, (X0 + a[0], O + a[1]), (X0 + b[0], O + b[1]), p.Edge_Cuts, .05)
    segment(board, (X0 - W / 2 - 1, O + TONGUE_L), (X0 - tw - .3, O + TONGUE_L), p.F_Fab, .1)
    t = p.PCB_TEXT(board); t.SetText('PLUG BACK FACE'); t.SetPosition(k(-W / 2 - 1, TONGUE_L - .6)); t.SetTextSize(v(.6, .6))
    t.SetTextThickness(p.FromMM(.08)); t.SetLayer(p.F_Fab); t.SetHorizJustify(p.GR_TEXT_H_ALIGN_RIGHT); board.Add(t)
    board.BuildConnectivity(); p.SaveBoard(str(out / f'{name}.kicad_pcb'), board)
    schematic(name, spec, parts, out)
    rules = '(version 1)\n(rule "No back copper" (constraint disallow track via) (layer "B.Cu"))\n(rule "No vias" (constraint disallow via))\n' \
            '(rule "Milling clearance" (constraint clearance (min 0.3mm)))\n(rule "Milling track width" (constraint track_width (min 0.35mm)))\n' \
            '(rule "Edge clearance" (constraint edge_clearance (min 0.2mm)))\n'
    (out / f'{name}.kicad_dru').write_text(rules)
    project = {'meta': {'filename': f'{name}.kicad_pro', 'version': 1},
               'board': {'design_settings': {'rules': {'min_clearance': .3, 'min_track_width': .35, 'min_copper_edge_clearance': .2,
                                                       'min_silk_clearance': .15, 'min_text_height': .6, 'min_text_thickness': .08},
                                             'defaults': {'board_outline_line_width': .05}}},
               'net_settings': {'classes': [{'name': 'Default', 'clearance': .3, 'track_width': TRACK}], 'meta': {'version': 4}}}
    (out / f'{name}.kicad_pro').write_text(json.dumps(project, indent=2) + '\n')
    (out / 'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "PlugTail") (type "KiCad") (uri "${KIPRJMOD}/PlugTail.pretty") (options "") (descr "Plug-tail footprints")))\n')
    (out / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "PlugTail") (type "KiCad") (uri "${KIPRJMOD}/PlugTail.kicad_sym") (options "") (descr "Plug-tail symbols")))\n')
    return {'board_mm': [W, L, 1.4], 'tongue_mm': [TONGUE_W, TONGUE_L], 'outline': outline, 'pads': {f'{r}.{n}': xy for (r, n), xy in pads.items()},
            'plug_pads_left_to_right': spec['plug'], 'nets': names}


EFFECTS = '(effects (font (size 1.27 1.27)))'


def symbol(n, prefix=''):
    pins = ''.join(f'(pin passive line (at -7.62 {-i * 2.54} 0) (length 2.54) (name "{i + 1}" {EFFECTS}) (number "{i + 1}" {EFFECTS}))' for i in range(n))
    return f'''(symbol "{prefix}Conn{n}" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
 (property "Reference" "J" (at 0 5.08 0) {EFFECTS})
 (property "Value" "Conn{n}" (at 0 2.54 0) {EFFECTS})
 (symbol "Conn{n}_0_1" (rectangle (start -5.08 1.27) (end 5.08 {-(n - 1) * 2.54 - 1.27}) (stroke (width .254) (type default)) (fill (type background))))
 (symbol "Conn{n}_1_1" {pins}))'''


def schematic(name, spec, parts, out):
    sizes = sorted({len(ns) for *_, ns in parts.values()})
    (out / 'PlugTail.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n' + '\n'.join(symbol(n) for n in sizes) + '\n)')
    sheet = uid(name + 'sheet')
    s = [f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid {sheet}) (paper "A4")
 (title_block (title {q(spec["title"])}) (date "2026-11-04") (rev "C") (comment 1 "Front copper only. J1 pads are the plug contacts, left to right seen from the contact side, nose away."))
 (lib_symbols {" ".join(symbol(n, "PlugTail:") for n in sizes)})''']
    for col, (ref, (fn, value, _, _, pinnets)) in enumerate(parts.items()):
        x, y = 63.5 + col * 63.5, 63.5
        s.append(f'''(symbol (lib_id "PlugTail:Conn{len(pinnets)}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(name + ref)})
      (property "Reference" "{ref}" (at {x} {y - 7.62} 0) {EFFECTS})
      (property "Value" {q(value)} (at {x} {y - 5.08} 0) {EFFECTS})
      (property "Footprint" "PlugTail:{fn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
      (instances (project "{name}" (path "/{sheet}" (reference "{ref}") (unit 1)))))''')
        for i, n in enumerate(pinnets):
            py = y + i * 2.54
            if n is None:
                s.append(f'(no_connect (at {x - 7.62} {py}) (uuid {uid(name + ref + "nc" + str(i))}))'); continue
            s.append(f'(wire (pts (xy {x - 7.62} {py}) (xy {x - 20.32} {py})) (stroke (width 0) (type default)) (uuid {uid(name + ref + "w" + str(i))}))')
            s.append(f'(label {q(n)} (at {x - 20.32} {py} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid(name + ref + "l" + str(i))}))')
    s.append(')'); (out / f'{name}.kicad_sch').write_text('\n'.join(s) + '\n')


if __name__ == '__main__':
    which = sys.argv[1:] or list(VARIANTS)
    (ROOT / 'checks').mkdir(exist_ok=True)
    geo = {n: build(n, VARIANTS[n]) for n in which}
    (ROOT / 'checks/geometry.json').write_text(json.dumps(geo, indent=1) + '\n'); print(json.dumps(geo, indent=1))
