#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];CAM=ROOT/'cam';OUT=ROOT/'exports'
report=json.loads((CAM/'validation.json').read_text());job=json.loads((CAM/'job.json').read_text())
assert report['status']=='PASS'
for kind,name in job['programs'].items():assert hashlib.sha256((CAM/name).read_bytes()).hexdigest()==report['program_sha256'][kind]
(CAM/'tools.csv').write_text('slot,description,spindle_rpm,xy_feed_mm_min,notes\n2,"30 degree V-bit; 0.2 mm tip; 3.175 mm shank",12000,300,Isolation depth 0.12 mm\n3,"0.8 mm corn bit; 3.175 mm shank",12000,300,Helical holes at 100 mm/min; through depth 1.55 mm\n')
files=[CAM/name for name in job['programs'].values()]+[CAM/name for name in ['READ-ME-FIRST.txt','job.json','validation.json','tools.csv','panel-layout.pdf','panel-layout.png']]+[ROOT/'parts.csv',ROOT/'README.txt',OUT/'assembly-preview.pdf']
mapping={f.name:f for f in files};assert len(mapping)==len(files)
manifest=''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {name}\n' for name,f in sorted(mapping.items()))
(CAM/'SHA256SUMS.txt').write_text(manifest)
mapping['SHA256SUMS.txt']=CAM/'SHA256SUMS.txt'
def pack(path,entries):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,f in entries.items():z.write(f,name)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    print(f'{path.name}: {path.stat().st_size} bytes, {len(entries)} files')
pack(OUT/'nezha-wire-hub-A-carvera.zip',mapping)
pack(OUT/'nezha-wire-hub-A-fabrication.zip',{f.name:f for f in (OUT/'fabrication').iterdir() if f.is_file() and f.suffix!='.gbrjob'})
project={}
for folder in ['design','references','scripts']:
    for f in (ROOT/folder).rglob('*'):
        if f.is_file() and '__pycache__' not in str(f) and f.suffix not in ['.pyc','.kicad_prl']:project[str(f.relative_to(ROOT))]=f
for folder,patterns in [('checks',['*.json','netlist.xml']),('exports',['*.pdf','*.svg']),('exports/fabrication',['*']),('exports/milling',['*.gtl','*.gm1','*.drl','*.kicad_pcb']),('cam',['*.nc','*.json','*.txt','*.csv','*.pdf','*.svg','millproject'])]:
    for pattern in patterns:
        for f in (ROOT/folder).glob(pattern):
            if f.is_file() and f.suffix!='.gbrjob':project[str(f.relative_to(ROOT))]=f
project['README.txt']=ROOT/'README.txt';project['parts.csv']=ROOT/'parts.csv'
pack(OUT/'nezha-wire-hub-A-project.zip',project)
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n' for f in sorted(OUT.glob('*.zip'))))
