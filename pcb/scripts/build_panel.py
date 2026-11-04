#!/usr/bin/env python3
"""Repeat the audited Rev B toolpaths, grouping isolation/holes/outlines.

No CNC connection. Coordinates stay relative to the original stock origin.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CAM = ROOT / 'cam'
OUT = CAM / 'panel'
OUT.mkdir(exist_ok=True)
job = json.loads((OUT / 'layout.json').read_text())
source = CAM / job['source_program']
assert hashlib.sha256(source.read_bytes()).hexdigest() == job['source_sha256']
ops = {1: [], 2: [], 3: []}
op, started = None, False
for line in source.read_text().splitlines():
    match = re.search(r'\(OPERATION (\d+):', line)
    if match:
        op, started = int(match[1]), False
        continue
    if op is None:
        continue
    if not started:
        if not line.startswith('G0 X'):
            continue
        started = True
    if line == 'M5':
        break
    if line.startswith('('):
        continue
    assert re.match(r'^G[014]\b', line), line
    ops[op].append(line)
assert all(ops.values())
lines = []
def emit(line):
    lines.append(line)
def comment(line):
    assert not any(c in line for c in '()')
    emit('(' + line + ')')
def tool(slot):
    for line in ['M5', 'G4 P3', f'M6 T{slot}', 'G0 Z5.00000',
                 'M3 S12000', 'G4 P3']:
        emit(line)
comment(f"NEZHA QWIIC REV B - {len(job['boards'])} NEW BOARDS - ORIGINAL CARVERA ATC")
comment('STOCK 150 X 100 X 1.4 mm - COPPER UP - SEE READ-ME-FIRST.txt')
comment('G54 XY0 MUST BE ORIGINAL STOCK LOWER LEFT - REMOVE THE 60 mm SHIFT')
comment('ENTIRE BOTTOM ROW X0..150 Y0..40 EXCLUDED FROM CUTTING AND LEVELING')
comment('CONFIRM ALL UPPER MACHINING AREA IS INTACT STOCK BEFORE RUNNING')
comment('T2 30 DEG V BIT 0.2 mm TIP; T3 0.8 mm CORN BIT')
comment('NEW BOARDS ALL ABOVE Y44; PROBE THIS PROGRAM AREA ONLY')
comment(f"AUTO Z PROBE WORK X{job['auto_z_probe_work_xy_mm'][0]} Y{job['auto_z_probe_work_xy_mm'][1]}; LEVEL {job['probe_grid'][0]} X {job['probe_grid'][1]} POINTS; 2 mm LIFT")
comment('Z0 TOP COPPER - ISOLATION Z-0.08 - FINAL CUT Z-1.45')
comment('FOUR 2.5 mm WIDE TABS PER BOARD - 0.5 mm REMAINS')
for line in ['G21', 'G90', 'G17', 'G54', 'M331']:
    emit(line)
for op in (1, 2, 3):
    comment(f'OPERATION {op}: ' + {1:'ALL TRACE ISOLATION',2:'ALL MOUNTING HOLES',3:'ALL OUTLINES WITH TABS'}[op])
    if op < 3:
        tool(op + 1)
    for board in job['boards']:
        x,y = board['lower_left_mm']
        comment(f"BOARD {board['id']}: lower left X{x} Y{y}")
        emit('G0 Z5.00000')
        for line in ops[op]:
            for axis, offset in [('X', x - 15), ('Y', y - 15)]:
                line = re.sub(axis + r'(-?[0-9.]+)',
                              lambda m: axis + f'{float(m[1]) + offset:.5f}', line)
            emit(line)
for line in ['G0 Z10.00000', 'M5', 'G4 P3', 'M9', 'M30']:
    emit(line)
target = OUT / job['program_file']
target.write_text('\n'.join(lines) + '\n')
print(f'{target.name}: {len(lines)} lines')
