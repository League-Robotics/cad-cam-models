#!/usr/bin/env python3
"""Package only the final Carvera NC and its matching operator documents."""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
cam=root/'cam'
job=json.loads((cam/'job.json').read_text())
nc=cam/job['program_file']
report=json.loads((cam/'validation.json').read_text())
assert report['status']=='PASS'
assert report['program_sha256']==hashlib.sha256(nc.read_bytes()).hexdigest()
names=[nc.name,'READ-ME-FIRST.txt','tools.csv','job.json','validation.json',
       'setup-preview.pdf','setup-preview.svg']
(cam/'SHA256SUMS.txt').write_text(''.join(
    f'{hashlib.sha256((cam/n).read_bytes()).hexdigest()}  {n}\n' for n in names))
names.append('SHA256SUMS.txt')
target=root/'exports/nezha-qwiic-revB-carvera-one-board.zip'
with ZipFile(target,'w',ZIP_DEFLATED) as z:
    for name in names:
        z.write(cam/name,name)
print(f'{target.name}: {len(names)} files')
