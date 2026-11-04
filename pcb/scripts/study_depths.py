#!/usr/bin/env python3
"""Build isolated depth trials and audit their copper, pockets and tabs.

Nothing connects to the machine. Trial files remain studies; only an explicitly
selected trial should be copied into cam/depth-test for a fresh-stock test.
"""
from pathlib import Path
import contextlib
import io
import json
import math
import re
import runpy
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'studies/20261005-depth-trials'
OUT.mkdir(parents=True,exist_ok=True)
depths=[.08,.10,.12,.15,.20]
reports=[]
for depth in depths:
    tag=f'iso{round(depth*1000):03d}-cut155'
    trial=OUT/tag
    for sub in ('scripts','cam/raw','design','exports/milling'):
        (trial/sub).mkdir(parents=True,exist_ok=True)
    for name in ('post_carvera.py','check_carvera.py'):
        shutil.copy2(ROOT/'scripts'/name,trial/'scripts'/name)
    shutil.copy2(ROOT/'design/nezha-qwiic.kicad_pcb',trial/'design/nezha-qwiic.kicad_pcb')
    for f in (ROOT/'exports/milling').iterdir():
        if f.is_file(): shutil.copy2(f,trial/'exports/milling'/f.name)
    job=json.loads((ROOT/'cam/job.json').read_text())
    diameter=.2+2*depth*math.tan(math.radians(15))
    job['isolation']['depth_mm']=depth
    job['isolation']['effective_diameter_mm']=round(diameter,6)
    job['cutting']['depth_mm']=1.55
    job['workholding']['through_cut_allowance_mm']=.15
    job['program_file']=f'nezha-qwiic-revB-one-board-carvera-{tag}.nc'
    job['trial_scope']='Fresh stock only. Not a recovery program for repositioned boards.'
    (trial/'cam/job.json').write_text(json.dumps(job,indent=2)+'\n')
    config=(ROOT/'cam/millproject').read_text()
    for key,value in [('mill-diameters',f'{diameter:.6f}'),('zwork',f'{-depth:.5f}'),
                      ('zcut','-1.55'),('zmilldrill','-1.55'),('zdrill','-1.55')]:
        config=re.sub(r'^'+re.escape(key)+r'=.*$',key+'='+value,config,flags=re.M)
    (trial/'cam/millproject').write_text(config)
    print(f'Generating {tag}; V-bit diameter {diameter:.6f} mm',flush=True)
    with (trial/'cam/raw/generation.log').open('w') as log:
        result=subprocess.run(['/home/ros/.local/bin/pcb2gcode'],cwd=trial/'cam',stdout=log,stderr=subprocess.STDOUT)
    report={'isolation_depth_mm':depth,'effective_tool_diameter_mm':round(diameter,6),
            'cutout_depth_mm':1.55,'extra_below_nominal_stock_mm':.15,'trial':tag}
    if result.returncode:
        report.update(status='CAM_GENERATION_FAILED',returncode=result.returncode)
        reports.append(report)
        continue
    subprocess.run(['python3',str(trial/'scripts/post_carvera.py')],check=True)
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            checked=runpy.run_path(str(trial/'scripts/check_carvera.py'))
        nets=checked['nets']
        pairs=[]
        keys=list(nets)
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                pairs.append((nets[a].distance(nets[b]),a,b))
        gap,a,b=min(pairs)
        report.update(status='PASS',minimum_cad_copper_gap_mm=round(gap,6),
                      nearest_copper_nets=[a,b],
                      gap_minus_tool_diameter_mm=round(gap-diameter,6),
                      theoretical_depth_at_gap_width_mm=round((gap-.2)/(2*math.tan(math.radians(15))),6),
                      program_sha256=checked['report']['program_sha256'],
                      tab_widths_mm=checked['tabs'])
    except Exception as exc:
        report.update(status='VALIDATION_FAILED',reason=f'{type(exc).__name__}: {exc}')
    (trial/'validation-output.txt').write_text(output.getvalue())
    reports.append(report)
    print(json.dumps(report),flush=True)
(OUT/'depth-comparison.json').write_text(json.dumps({
    'tool':'30 degree included angle, 0.2 mm flat tip',
    'formula':'effective_diameter = 0.2 + 2 * depth * tan(15 degrees)',
    'original_isolation_depth_mm':.08,'original_cutout_depth_mm':1.45,
    'recommended_next_test_isolation_mm':.12,'recommended_next_test_cutout_mm':1.55,
    'limits':'Nominal geometry checks only. Not a measured machine/process depth limit. Extra depth does not compensate for moving stock or an invalid height map.',
    'trials':reports},indent=2)+'\n')
assert next(r for r in reports if r['isolation_depth_mm']==.12)['status']=='PASS'
print('Depth comparison saved; recommended 0.12 / 1.55 trial passed.',flush=True)
