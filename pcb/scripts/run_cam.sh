#!/usr/bin/env bash
# Run on Buzzkill after export_adapter.sh. Produces files only; no CNC connection.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p cam/raw
cam_executable="${PCB2GCODE_BIN:-/home/ros/.local/bin/pcb2gcode}"
(cd cam && "$cam_executable" > raw/generation.log 2>&1)
python3 scripts/post_carvera.py
python3 scripts/check_carvera.py
python3 scripts/package_carvera.py
