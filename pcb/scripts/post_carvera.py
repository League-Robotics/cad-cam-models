#!/usr/bin/env python3
"""Post pcb2gcode isolation/outline paths for the ORIGINAL six-slot Carvera.

Keeps Carvera Controller's G54/probe/leveling state. No machine connection.
Holes are fully pocketed with the corn bit to avoid loose central slugs.
"""
from pathlib import Path
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
CAM = ROOT / 'cam'
job = json.loads((CAM / 'job.json').read_text())
dx, dy = job['gerber_translation_mm']
output = []

def emit(s):
    output.append(s)

def comment(s):
    assert '(' not in s and ')' not in s
    emit('(' + s + ')')

def tool(slot, description):
    comment(description)
    emit('M5')
    emit('G4 P3')
    emit(f'M6 T{slot}')
    emit('G0 Z5.00000')
    emit('M3 S12000')
    emit('G4 P3')

def translated_body(name):
    """Retain only explicit moves/feed/dwell after the first XY rapid.

    Fail closed on unfamiliar output; do not carry generic M0/T1/M2 commands
    from pcb2gcode into the Carvera program. Every cut coordinate is explicit.
    """
    started = False
    for raw in (CAM / 'raw' / name).read_text().splitlines():
        s = re.sub(r'\([^)]*\)', '', raw).strip()
        if not s:
            continue
        if not started:
            if re.match(r'G0?0\s+X', s):
                started = True
            else:
                continue
        if s.startswith('M5'):
            break
        assert re.match(r'^G0?[014]\b', s), (name, s)
        s = re.sub(r'^G0([014])\b', r'G\1', s)
        assert not re.search(r'[IJKR]', s), s
        for axis, offset in [('X', dx), ('Y', dy)]:
            s = re.sub(axis + r'(-?[0-9.]+)',
                       lambda m: axis + f'{float(m[1]) + offset:.5f}', s)
        # pcb2gcode uses a Z-only rapid to raise over each retaining tab.
        # Feed this short below-surface lift so all below-surface moves are G1.
        if s.startswith('G0 Z-'):
            s = 'G1' + s[2:] + ' F100.00000'
            emit(s)
            emit('G1 F300.00000')
        else:
            emit(s)
    assert started, name

def pocket_holes():
    drill = (ROOT / 'exports/milling/nezha-qwiic-NPTH.drl').read_text()
    assert 'T1C3.000' in drill
    holes = [(float(x) + dx, float(y) + dy)
             for x, y in re.findall(r'^X(-?[0-9.]+)Y(-?[0-9.]+)$', drill, re.M)]
    assert len(holes) == 2
    depth = job['cutting']['depth_mm']
    levels = [-min(depth, i * job['cutting']['max_stepdown_mm'])
              for i in range(1, math.ceil(depth / job['cutting']['max_stepdown_mm']) + 1)]
    for index, (x, y) in enumerate(holes, 1):
        comment(f'HOLE {index}: fully pocket 3.00 mm diameter')
        emit('G0 Z5.00000')
        emit(f'G0 X{x + .35:.5f} Y{y:.5f}')
        emit('G1 Z0.00000 F100.00000')
        emit('G1 F300.00000')
        previous_z = 0
        for z in levels:
            # The 0.35 mm center radius is smaller than the tool radius, so
            # the helical lap removes the center. A second, level lap clears
            # the entire floor before the outer laps finish the pocket.
            for lap, radius in enumerate([.35, .35, .70, 1.10]):
                emit(f'G1 X{x + radius:.5f} Y{y:.5f}')
                for i in range(1, 121):
                    angle = -2 * math.pi * i / 120
                    zi = previous_z + (z - previous_z) * i / 120 if lap == 0 else z
                    emit(f'G1 X{x + radius * math.cos(angle):.5f} '
                         f'Y{y + radius * math.sin(angle):.5f} Z{zi:.5f}')
            emit(f'G1 X{x + .35:.5f} Y{y:.5f}')
            previous_z = z
        emit('G0 Z5.00000')

comment('NEZHA-QWIIC REV B - ONE BOARD - ORIGINAL CARVERA ATC')
if job.get('trial_scope'):
    comment(job['trial_scope'])
comment('J1 = AMPHENOL 73306-111LF; LATCH UP; HEADER GND AT BOTTOM')
comment('BARE COPPER PCB STOCK: X150 Y100 THICKNESS1.40 mm')
comment('G54 XY0 = STOCK LOWER-LEFT; Z0 = COPPER TOP')
comment('Board lower-left X15 Y15; finished size 44 x 24 mm')
comment('T2 = 30 DEG V-BIT, 0.2 mm TIP; T3 = 0.8 mm CORN BIT')
comment('Set Auto Z Probe and Auto Leveling in Carvera Controller BEFORE RUN')
comment('6 x 4 probe grid, 2 mm lift; preserve active height compensation')
comment(f"THROUGH CUT: final Z-{job['cutting']['depth_mm']:.2f}; {job['workholding']['through_cut_allowance_mm']:.2f} mm below PCB")
comment('Tape thickness is NOT added to cutting depth; Z0 is top copper')
comment('Clamp outside the cutting and dust-shoe travel envelope')
emit('G21')
emit('G90')
emit('G17')
emit('G54')
emit('M331')
comment(f"OPERATION 1: TRACE ISOLATION, Z-{job['isolation']['depth_mm']:.2f}")
tool(2, 'ATC SLOT 2 - PCB ENGRAVING BIT')
translated_body('front.ngc')
comment('OPERATION 2: TWO 3.00 mm MOUNTING HOLES')
tool(3, 'ATC SLOT 3 - 0.8 mm CORN BIT')
pocket_holes()
comment('OPERATION 3: OUTLINE, FOUR 2.5 mm TABS, 0.5 mm THICK')
translated_body('outline.ngc')
emit('G0 Z10.00000')
emit('M5')
emit('G4 P3')
emit('M9')
emit('M30')
target = CAM / job['program_file']
target.write_text('\n'.join(output) + '\n')
print(f'{target.name}: {len(output)} lines')
