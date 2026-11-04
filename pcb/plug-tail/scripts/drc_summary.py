#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
bad = 0
for n in sys.argv[1:]:
    e = json.loads((ROOT / f'checks/{n}-erc.json').read_text()); d = json.loads((ROOT / f'checks/{n}-drc.json').read_text())
    items = [('erc', v['type'], v['description'], [i['description'] for i in v['items']]) for s in e['sheets'] for v in s['violations']]
    items += [(key, v['type'], v['description'], [i['description'] for i in v['items']]) for key in ['violations', 'unconnected_items', 'schematic_parity'] for v in d[key]]
    print(n, 'clean' if not items else '')
    for it in items: print('  ', *it)
    bad += len(items)
sys.exit(1 if bad else 0)
