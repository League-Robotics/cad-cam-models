#!/usr/bin/env python3
"""Live OpenSCAD viewer: re-export STLs on save and show them in the browser.

Starts tools/buzzkill/serve.py on view/ and watches scad/ (and its models/).
Whenever a .scad file or view/targets.txt changes, every target is exported
again with OpenSCAD; the page reloads the newest STL on its own.

view/targets.txt has one target per line, `name: file.scad var=value ...`:

    left_arm: scad/gripper.scad part="left"
    nezha_frame: scad/nezha_gripper.scad part="frame"

Each var=value becomes a -D override and the STL lands in view/<name>.stl.

    scad_view.py [--port 8766]
"""
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEW = ROOT / "view"
TARGETS = VIEW / "targets.txt"
WATCH = [ROOT / "scad"]
DEFAULT_TARGETS = 'left_arm: scad/gripper.scad part="left"\n'

args = sys.argv[1:]
port = "8766"
if "--port" in args:
    port = args[args.index("--port") + 1]


def read_targets():
    targets = []
    for line in TARGETS.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        name, _, rest = line.partition(":")
        scad, *defs = shlex.split(rest, posix=False)
        targets.append((name.strip(), ROOT / scad, defs))
    return targets


def snapshot():
    files = [TARGETS]
    for d in WATCH:
        files += [p for p in d.rglob("*") if p.suffix.lower() in (".scad", ".stl")]
    return {p: p.stat().st_mtime for p in files if p.is_file()}


def export(name, scad, defs):
    out = VIEW / f"{name}.stl"
    tmp = VIEW / f".{name}.tmp.stl"
    cmd = ["openscad", "--backend=manifold", "-o", str(tmp)]
    for d in defs:
        cmd += ["-D", d]
    start = time.time()
    proc = subprocess.run(cmd + [str(scad)], cwd=scad.parent, capture_output=True, text=True)
    problems = [l for l in proc.stderr.splitlines() if l.startswith(("ERROR", "WARNING"))]
    if proc.returncode == 0 and tmp.exists() and tmp.stat().st_size > 84:
        tmp.replace(out)  # atomic, so the page never loads a half-written file
        print(f"{name}: {time.time() - start:.1f}s", flush=True)
    else:
        tmp.unlink(missing_ok=True)
        print(f"{name}: FAILED, keeping the last good STL", flush=True)
        problems = problems or proc.stderr.strip().splitlines()[-5:]
    for p in problems:
        print(f"  {p}", flush=True)


VIEW.mkdir(exist_ok=True)
if not TARGETS.exists():
    TARGETS.write_text(DEFAULT_TARGETS)
server = subprocess.Popen(
    [sys.executable, str(ROOT / "tools/buzzkill/serve.py"), str(VIEW), "--port", port]
)
try:
    seen = {}
    while True:
        now = snapshot()
        if now != seen:
            seen = now
            try:
                for target in read_targets():
                    export(*target)
            except Exception as e:  # a bad targets.txt line shouldn't stop the watcher
                print(f"targets.txt: {e}", flush=True)
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    server.terminate()
