#!/usr/bin/env python3
"""ERC, DRC with schematic parity, netlists, schematic PDFs, fabrication and milling Gerbers (kicad-cli 9, Buzzkill)."""
from pathlib import Path
import json, subprocess as sp, sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = sys.argv[1:] or list(json.loads((ROOT / 'checks/geometry.json').read_text()))


def run(*args): sp.run(args, cwd=ROOT, check=True, stdout=sp.DEVNULL)


for n in NAMES:
    pcb, sch = f'design/{n}/{n}.kicad_pcb', f'design/{n}/{n}.kicad_sch'
    for d in [f'exports/{n}/fabrication', f'exports/{n}/milling', 'checks']: (ROOT / d).mkdir(parents=True, exist_ok=True)
    run('kicad-cli', 'sch', 'erc', '--exit-code-violations', '--format', 'json', '-o', f'checks/{n}-erc.json', sch)
    run('kicad-cli', 'pcb', 'drc', '--schematic-parity', '--exit-code-violations', '--format', 'json', '-o', f'checks/{n}-drc.json', pcb)
    run('kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', f'checks/{n}-netlist.xml', sch)
    run('kicad-cli', 'sch', 'export', 'pdf', '-o', f'exports/{n}/schematic.pdf', sch)
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,F.Mask,F.Paste,F.Fab,Edge.Cuts', '--use-drill-file-origin', '-o', f'exports/{n}/fabrication/', pcb)
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,Edge.Cuts', '--no-x2', '--no-netlist', '--disable-aperture-macros', '--use-drill-file-origin', '-o', f'exports/{n}/milling/', pcb)
    holes = json.loads((ROOT / 'checks/geometry.json').read_text())[n]['holes']
    note = 'Single copper layer on TOP (F.Cu), no vias. Nominal thickness 1.4 mm. Do not mirror.\n'
    if holes:
        run('kicad-cli', 'pcb', 'export', 'drill', '--excellon-units', 'mm', '--drill-origin', 'plot', '-o', f'exports/{n}/fabrication/', pcb)
        note += f'{len(holes)} solder-through holes of {holes[0]["d"]} mm are NON-PLATED with a copper ring on the top only; the drill file lists them as PTH because KiCad draws the ring as a through-hole pad.\n'
    (ROOT / f'exports/{n}/fabrication/ORDER-NOTES.txt').write_text(note)
    print(n, 'ERC/DRC clean; exported')
