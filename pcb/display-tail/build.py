#!/usr/bin/env python3
"""Generate the display-tail boards with KiCad 9's pcbnew (on Buzzkill): a 4P4C jack (the stocked Amphenol
73306-111LF, the same footprint as the rev B adapter) whose four lines go to four of the eleven pads on the back
of a Waveshare ESP32-S3-Touch-LCD-1.69: G, 3V3, 17 and 18. Since 2026-11-14 (evening) the link is a UART, not
I2C: the display firmware's RX is pad 17 and its TX pad 18 (3.3 V, 115200 8N1), so jack contact 4 (the robot's
TX) goes to 17 and contact 3 (the robot's RX) to 18. The copper is the same as for I2C; only the names changed.

Board frame (KiCad): x to the right, y DOWN the board, seen from the copper side, which is the side AWAY from the
display. The display's pad edge runs along the bottom (y = L); pad 18 is at the left, which is the display's
buttons side. The jack sits at the far (top) end with its mouth facing AWAY from the display, at the case's end
wall (Eric, 2026-11-14: the tail and jack are enclosed by the display's case). With the mouth up, the jack's pads
run left to right 1 GND, 2 3V3, 3 RX-of-robot, 4 TX-of-robot while the display pads run 18, 17 ... 3V3, G, so
GND and 3V3 go up round the right of the jack and 18/17 down round the left: no crossover, but the tail is
22.3 long to leave a two-track band between the jack's pads and the display pads. Copper is F.Cu only.

Two variants were drawn; Eric chose the BUTT one (2026-11-14, "B, butted edge-on"). The lap variant stays
here for the record (archive/lap-variant) and builds only when named on the command line.
  display-tail-lap   the tail laps LAP mm under the display's back; a 1.0 hole in a ring pad sits over each used
                     display pad and is soldered through from outside
  display-tail-butt  the tail butts against the display's pad edge, GAP mm off it, copper face level with the
                     display's back; a flat 0.64 pin lies along the tail pad and the display pad and is soldered to each

Display numbers (Waveshare's dimension drawing and wiki FAQ; nothing measured on the real board yet): 11 pads at
2.15 mm pitch, centres 1.84 mm in from the edge, pad 18's centre 4.16 mm from the PCB corner.
"""
from pathlib import Path
import json, sys, uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
JACK_LIB = ROOT.parent / 'design' / 'Adapter.pretty'     # the rev B adapter's footprints: Amphenol_73306-111LF
O = 50.
PITCH, INSET = 2.15, 1.84          # display pad pitch and inset from its edge (Waveshare)
PADS = ['18', '17', '3', '2', 'SCL', 'SDA', 'TX', 'RX', '3V3', 'G', '5V']   # from the buttons-side corner
USED = {'18': 'DISP_TX', '17': 'DISP_RX', '3V3': '+3V3', 'G': 'GND'}   # DISP_TX = pad 18 = the robot's RX; DISP_RX = pad 17 = the robot's TX
X18 = 1.5                          # pad 18 on the tail
W, L = 23.4, 22.3
JACK_MOUTH, JACK_CX = 1.0, W / 2    # mouth face 1.0 inside the top edge (as the adapter); centred across the tail
BAND = (17.7, 18.5)                 # the two tracks between the jack's pads (end 17.1) and the display pads (from 19.1)
TRACK = .4
NS = uuid.UUID('9c2f1b7e-6d7a-4b1e-9a0b-3f5e2d8c1a44')
IO = p.PCB_IO_KICAD_SEXPR()

VARIANTS = {
    'display-tail-lap': dict(title='Display tail: 4P4C jack to the Waveshare 1.69 LCD, lapped', mount='lap', lap=3.0, ring=(1.7, 1.9), hole=1.0),
    'display-tail-butt': dict(title='Display tail: 4P4C jack to the Waveshare 1.69 LCD, butted, UART', mount='butt', gap=1.2, pad=(1.7, 3.0)),
}
JACK_PADS = {'1': 'GND', '2': '+3V3', '3': 'DISP_TX', '4': 'DISP_RX'}   # the adapter's numbering: 4 3 2 1 left to right into the latch-up mouth


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


def text(owner, s, x, y, size=.8, layer=p.F_Fab, just=p.GR_TEXT_H_ALIGN_CENTER):
    t = p.PCB_TEXT(owner); t.SetText(s); t.SetPosition(v(x, y)); t.SetTextSize(v(size, size)); t.SetTextThickness(p.FromMM(size / 8))
    t.SetLayer(layer); t.SetHorizJustify(just); owner.Add(t)


def display_pads(spec):
    """The four used display pads as one footprint; pad numbers are the display's pad names. Origin at pad 18."""
    fp = p.FOOTPRINT(None); fp.SetFPID(p.LIB_ID('DisplayTail', 'DisplayPads_4of11')); fp.SetReference('REF**'); fp.SetValue('DisplayPads_4of11')
    fp.SetAttributes(p.FP_SMD if spec['mount'] == 'butt' else p.FP_THROUGH_HOLE)
    fp.SetLibDescription('Waveshare ESP32-S3-Touch-LCD-1.69 back pads 18, 17, 3V3, G at 2.15 mm pitch; pad 18 at the origin')
    for i, name in enumerate(PADS):
        if name not in USED: continue
        a = p.PAD(fp); a.SetNumber(name); a.SetShape(p.PAD_SHAPE_RECT); a.SetPosition(v(i * PITCH, 0))
        if spec['mount'] == 'lap':      # ring with an unplated 1.0 hole; copper on the front only (as the wire hub)
            a.SetAttribute(p.PAD_ATTRIB_PTH); a.SetSize(v(*spec['ring'])); a.SetDrillSize(v(spec['hole'], spec['hole']))
            a.SetLayerSet(layers(p.F_Cu, p.B_Cu, p.F_Mask, p.B_Mask)); a.SetRemoveUnconnected(True); a.SetKeepTopBottom(False)
        else:
            a.SetAttribute(p.PAD_ATTRIB_SMD); a.SetSize(v(*spec['pad'])); a.SetLayerSet(layers(p.F_Cu, p.F_Mask))
        fp.Add(a)
    return fp


def libraries(lib, spec):
    lib.mkdir(parents=True, exist_ok=True)
    jack = p.FootprintLoad(str(JACK_LIB), 'Amphenol_73306-111LF'); jack.SetFPID(p.LIB_ID('DisplayTail', 'Amphenol_73306-111LF'))
    IO.FootprintSave(str(lib), jack)
    IO.FootprintSave(str(lib), display_pads(spec))


def build(name, spec):
    out = ROOT / 'design' / name; lib = out / 'DisplayTail.pretty'; libraries(lib, spec)
    def k(x, y): return v(O + x, O + y)
    board = p.BOARD(); ds = board.GetDesignSettings(); ds.SetBoardThickness(p.FromMM(1.4)); ds.SetAuxOrigin(v(O, O))
    tb = board.GetTitleBlock(); tb.SetTitle(spec['title']); tb.SetRevision('A'); tb.SetDate('2026-11-14')
    nets = {}
    for n in ['GND', '+3V3', 'DISP_RX', 'DISP_TX']:
        net = p.NETINFO_ITEM(board, '/' + n); board.Add(net); nets[n] = net
    # the display pad row: ring centres over the display pads (lap) or pads up to 0.2 from the tail's edge (butt)
    row_y = L - spec['lap'] + INSET if spec['mount'] == 'lap' else L - 0.2 - spec['pad'][1] / 2
    parts = {'J1': ('Amphenol_73306-111LF', '73306-111LF', (JACK_CX, JACK_MOUTH), 0, JACK_PADS),
             'J2': ('DisplayPads_4of11', 'DISPLAY PADS 18 17 3V3 G', (X18, row_y), 0, {n: USED[n] for n in USED})}
    pads = {}
    for ref, (fn, value, (x, y), angle, pinnets) in parts.items():
        fp = IO.FootprintLoad(str(lib), fn); fp.SetReference(ref); fp.SetValue(value)
        fp.SetPath(p.KIID_PATH('/' + uid(name + 'sheet') + '/' + uid(name + ref))); fp.SetFPID(p.LIB_ID('DisplayTail', fn))
        board.Add(fp); fp.SetOrientationDegrees(angle); fp.SetPosition(k(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        for a in fp.Pads():
            num = a.GetNumber()
            if not num: continue
            a.SetNet(nets[pinnets[num]])
            pads[(ref, num)] = (round(p.ToMM(a.GetPosition().x) - O, 4), round(p.ToMM(a.GetPosition().y) - O, 4))
    # the jack unrotated: mouth at the top, pads 14.4 below it running left to right 1 GND, 2 3V3, 3, 4
    assert pads[('J1', '1')] == (round(JACK_CX - 1.905, 4), JACK_MOUTH + 14.4) and pads[('J1', '4')] == (round(JACK_CX + 1.905, 4), JACK_MOUTH + 14.4), pads
    assert pads[('J2', '18')][0] == X18 and pads[('J2', 'G')][0] == round(X18 + 9 * PITCH, 4), pads
    top = row_y - (spec['ring'][1] if spec['mount'] == 'lap' else spec['pad'][1]) / 2   # top of the display-pad row
    P = lambda ref, n: pads[(ref, n)]
    j = {n: P('J1', str(i)) for i, n in enumerate(['GND', '+3V3', 'DISP_TX', 'DISP_RX'], 1)}
    pt, pb = JACK_MOUTH + 14.4 - 1.5, JACK_MOUTH + 14.4 + 1.5      # inside the top and bottom ends of the jack's 3.4 long pads
    up1, up2 = JACK_MOUTH + 9.0, JACK_MOUTH + 10.4                  # the band under the jack between its hold-downs (end 9.4) and its pads (from 13.7)
    tracks = [('GND', [(j['GND'][0], pt), (j['GND'][0], up1), (P('J2', 'G')[0], up1), P('J2', 'G')]),
              ('+3V3', [(j['+3V3'][0], pt), (j['+3V3'][0], up2), (P('J2', '3V3')[0], up2), P('J2', '3V3')]),
              ('DISP_TX', [(j['DISP_TX'][0], pb), (j['DISP_TX'][0], BAND[0]), (X18, BAND[0]), P('J2', '18')]),
              ('DISP_RX', [(j['DISP_RX'][0], pb), (j['DISP_RX'][0], BAND[1]), (P('J2', '17')[0], BAND[1]), P('J2', '17')])]
    for n, pts in tracks:
        for a, b in zip(pts, pts[1:]):
            t = p.PCB_TRACK(board); t.SetStart(k(*a)); t.SetEnd(k(*b)); t.SetLayer(p.F_Cu); t.SetWidth(p.FromMM(TRACK)); t.SetNet(nets[n]); board.Add(t)
    outline = [(0, 0), (W, 0), (W, L), (0, L)]
    for a, b in zip(outline, outline[1:] + outline[:1]): segment(board, (O + a[0], O + a[1]), (O + b[0], O + b[1]), p.Edge_Cuts, .05)
    # where the display sits, on the fab layer
    edge_y = L - spec['lap'] if spec['mount'] == 'lap' else L + spec['gap']
    segment(board, (O - 1, O + edge_y), (O + W + 1, O + edge_y), p.F_Fab, .1)
    text(board, 'DISPLAY EDGE' if spec['mount'] == 'lap' else 'DISPLAY EDGE %.1f BELOW' % spec['gap'], O + W / 2, O + edge_y - 0.6, .6)
    for i, nm in enumerate(PADS):
        text(board, nm, O + X18 + i * PITCH, O + top - 0.6, .5)
    text(board, 'MOUTH ^', O + JACK_CX, O + JACK_MOUTH + 1.2, .7)
    board.BuildConnectivity(); p.SaveBoard(str(out / f'{name}.kicad_pcb'), board)
    schematic(name, spec, parts, out)
    rules = '(version 1)\n(rule "No back copper" (constraint disallow track via) (layer "B.Cu"))\n(rule "No vias" (constraint disallow via))\n' \
            '(rule "Milling clearance" (constraint clearance (min 0.3mm)))\n(rule "Milling track width" (constraint track_width (min 0.35mm)))\n' \
            '(rule "Edge clearance" (constraint edge_clearance (min 0.2mm)))\n'
    (out / f'{name}.kicad_dru').write_text(rules)
    project = {'meta': {'filename': f'{name}.kicad_pro', 'version': 1},
               'board': {'design_settings': {'rules': {'min_clearance': .3, 'min_track_width': .35, 'min_copper_edge_clearance': .2,
                                                       'min_silk_clearance': .15, 'min_text_height': .5, 'min_text_thickness': .06},
                                             'defaults': {'board_outline_line_width': .05}}},
               'net_settings': {'classes': [{'name': 'Default', 'clearance': .3, 'track_width': TRACK}], 'meta': {'version': 4}}}
    (out / f'{name}.kicad_pro').write_text(json.dumps(project, indent=2) + '\n')
    (out / 'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "DisplayTail") (type "KiCad") (uri "${KIPRJMOD}/DisplayTail.pretty") (options "") (descr "Display-tail footprints")))\n')
    (out / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "DisplayTail") (type "KiCad") (uri "${KIPRJMOD}/DisplayTail.kicad_sym") (options "") (descr "Display-tail symbols")))\n')
    holes = [{'pad': n, 'x': P('J2', n)[0], 'y': P('J2', n)[1], 'd': spec['hole']} for n in USED] if spec['mount'] == 'lap' else []
    return {'board_mm': [W, L, 1.4], 'mount': spec['mount'], 'lap_mm': spec.get('lap'), 'gap_mm': spec.get('gap'), 'display_edge_y': edge_y,
            'outline': outline, 'pads': {f'{r}.{n}': xy for (r, n), xy in pads.items()}, 'holes': holes,
            'display_pads': {nm: [round(X18 + i * PITCH, 4), round(edge_y + INSET, 4)] for i, nm in enumerate(PADS)},
            'nets': sorted(nets), 'jack': {'mouth_y': JACK_MOUTH, 'centre_x': JACK_CX, 'rotation': 0, 'body_mm': [11.18, 12.7, 14.0]}}


EFFECTS = '(effects (font (size 1.27 1.27)))'


def symbol(key, names, prefix=''):
    n = len(names)
    pins = ''.join(f'(pin passive line (at -7.62 {-i * 2.54} 0) (length 2.54) (name "{nm}" {EFFECTS}) (number "{nm}" {EFFECTS}))' for i, nm in enumerate(names))
    return f'''(symbol "{prefix}{key}" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
 (property "Reference" "J" (at 0 5.08 0) {EFFECTS})
 (property "Value" "{key}" (at 0 2.54 0) {EFFECTS})
 (symbol "{key}_0_1" (rectangle (start -5.08 1.27) (end 5.08 {-(n - 1) * 2.54 - 1.27}) (stroke (width .254) (type default)) (fill (type background))))
 (symbol "{key}_1_1" {pins}))'''


def schematic(name, spec, parts, out):
    syms = {ref: ('Jack4', list(pinnets)) if ref == 'J1' else ('DisplayPads4', list(pinnets)) for ref, (*_, pinnets) in parts.items()}
    (out / 'DisplayTail.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n' + '\n'.join(symbol(k, nm) for k, nm in syms.values()) + '\n)')
    sheet = uid(name + 'sheet')
    s = [f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid {sheet}) (paper "A4")
 (title_block (title {q(spec["title"])}) (date "2026-11-14") (rev "A") (comment 1 "Front copper only. J1 pads 4 3 2 1 left to right into the latch-up mouth (as the rev B adapter). J2 pins are the display's pad names. UART: DISP_RX = pad 17 (robot TX), DISP_TX = pad 18 (robot RX)."))
 (lib_symbols {" ".join(symbol(k, nm, "DisplayTail:") for k, nm in syms.values())})''']
    for col, (ref, (fn, value, _, _, pinnets)) in enumerate(parts.items()):
        key, names = syms[ref]; x, y = 63.5 + col * 76.2, 63.5
        s.append(f'''(symbol (lib_id "DisplayTail:{key}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(name + ref)})
      (property "Reference" "{ref}" (at {x} {y - 7.62} 0) {EFFECTS})
      (property "Value" {q(value)} (at {x} {y - 5.08} 0) {EFFECTS})
      (property "Footprint" "DisplayTail:{fn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
      (instances (project "{name}" (path "/{sheet}" (reference "{ref}") (unit 1)))))''')
        for i, nm in enumerate(names):
            py = y + i * 2.54; n = pinnets[nm]
            s.append(f'(wire (pts (xy {x - 7.62} {py}) (xy {x - 20.32} {py})) (stroke (width 0) (type default)) (uuid {uid(name + ref + "w" + nm)}))')
            s.append(f'(label {q(n)} (at {x - 20.32} {py} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid(name + ref + "l" + nm)}))')
    s.append(')'); (out / f'{name}.kicad_sch').write_text('\n'.join(s) + '\n')


if __name__ == '__main__':
    which = sys.argv[1:] or ['display-tail-butt']
    (ROOT / 'checks').mkdir(exist_ok=True)
    geo = {n: build(n, VARIANTS[n]) for n in which}
    (ROOT / 'checks/geometry.json').write_text(json.dumps(geo, indent=1) + '\n'); print(json.dumps(geo, indent=1))
