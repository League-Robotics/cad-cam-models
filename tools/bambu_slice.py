#!/usr/bin/env python3
"""Slice an STL for a garage Bambu printer with the Bambu Studio CLI.

    python3 tools/bambu_slice.py part.stl out_dir [--plate "Textured PEI Plate"] [--brim 5]

The CLI does not resolve a system profile's `inherits` chain or its `include`
templates when it is handed the JSON files directly: on 2026-11-02 that sent
an A1 job with a two-line stand-in start G-code (no bed levelling, no wipe, no
purge) and filament density 0, and the print never stuck. So this flattens
the machine, process and filament profiles first, checks the result, then
slices. Writes out_dir/<stem>.gcode.3mf (upload it, start plate 1).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

APP = Path("/Applications/BambuStudio.app/Contents")
BBL = APP / "Resources" / "profiles" / "BBL"
MACHINE = "Bambu Lab A1 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL A1"
FILAMENT = "Generic PLA @BBL A1"


def flatten(kind, name):
    """The profile `name` merged over its parents and its include templates."""
    d = json.loads((BBL / kind / f"{name}.json").read_text())
    out = flatten(kind, d["inherits"]) if d.get("inherits") else {}
    for inc in d.get("include", []):
        out.update(flatten(kind, inc))
    out.update({k: v for k, v in d.items() if k not in ("inherits", "include")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--plate", default="Textured PEI Plate")
    ap.add_argument("--brim", type=float, default=0, help="outer brim width, mm (0: none)")
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)

    machine, process, filament = flatten("machine", MACHINE), flatten("process", PROCESS), flatten("filament", FILAMENT)
    process["curr_bed_type"] = a.plate        # the CLI otherwise slices for the Cool Plate
    if a.brim:
        process.update(brim_type="outer_only", brim_width=str(a.brim))
    assert "G29" in machine["machine_start_gcode"], "start G-code lacks bed levelling"
    assert float(filament["filament_density"][0]) > 0, "filament density not resolved"

    paths = []
    for tag, p in (("machine", machine), ("process", process), ("filament", filament)):
        f = a.out_dir / f"{tag}.json"
        f.write_text(json.dumps(p, indent=1))
        paths.append(f)
    out = f"{a.stl.stem}.gcode.3mf"
    subprocess.run([str(APP / "MacOS" / "BambuStudio"), "--debug", "1", "--arrange", "1", "--orient", "0",
                    "--slice", "0", "--outputdir", str(a.out_dir), "--export-3mf", out,
                    "--load-settings", f"{paths[0]};{paths[1]}", "--load-filaments", str(paths[2]), str(a.stl)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    gcode = (a.out_dir / "plate_1.gcode").read_text()
    body = gcode.split("; EXECUTABLE_BLOCK_START", 1)[1]
    assert "G29" in body, "sliced G-code has no bed levelling"
    for line in gcode.splitlines():
        if line.startswith(("; model printing time", "; total filament weight", "; curr_bed_type")):
            print(line)
    print(f"wrote {a.out_dir / out}")


if __name__ == "__main__":
    sys.exit(main())
