#!/usr/bin/env python3
"""ERC, DRC with schematic parity, schematic PDFs, fabrication and milling Gerbers."""
from pathlib import Path
import subprocess as sp

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['header-tail', 'qwiic-tail']


def run(*args): sp.run(args, cwd=ROOT, check=True, stdout=sp.DEVNULL)


for n in NAMES:
    pcb, sch = f'design/{n}/{n}.kicad_pcb', f'design/{n}/{n}.kicad_sch'
    for d in [f'exports/{n}/fabrication', f'exports/{n}/milling', 'checks']: (ROOT / d).mkdir(parents=True, exist_ok=True)
    run('kicad-cli', 'sch', 'erc', '--exit-code-violations', '--format', 'json', '-o', f'checks/{n}-erc.json', sch)
    run('kicad-cli', 'pcb', 'drc', '--schematic-parity', '--exit-code-violations', '--format', 'json', '-o', f'checks/{n}-drc.json', pcb)
    run('kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', f'checks/{n}-netlist.xml', sch)
    run('kicad-cli', 'sch', 'export', 'pdf', '-o', f'exports/{n}/schematic.pdf', sch)
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,F.Mask,F.Paste,F.Fab,Edge.Cuts', '--use-drill-file-origin',
        '-o', f'exports/{n}/fabrication/', pcb)
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,Edge.Cuts', '--no-x2', '--no-netlist', '--disable-aperture-macros',
        '--use-drill-file-origin', '-o', f'exports/{n}/milling/', pcb)
    (ROOT / f'exports/{n}/fabrication/ORDER-NOTES.txt').write_text(
        'Single copper layer on TOP (F.Cu), no holes, no vias. Nominal thickness 1.4 mm; the tongue must fit the plug cavity, '
        'so confirm thickness against the measured cavity before ordering. Do not mirror.\n')
    print(n, 'ERC/DRC clean; exported')
