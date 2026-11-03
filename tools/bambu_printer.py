#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt"]
# ///
"""Drive a garage Bambu printer over LAN MQTT and FTPS (LAN Only + Developer Mode).

    uv run tools/bambu_printer.py NAME status
    uv run tools/bambu_printer.py NAME start FILE.gcode.3mf   upload (FTPS) and start plate 1, external spool
    uv run tools/bambu_printer.py NAME stop
    uv run tools/bambu_printer.py NAME wipe     A1, idle: home, wipe the nozzle as the start G-code does, cool down
    uv run tools/bambu_printer.py NAME clear    clear the reported print error (does not clear HMS notices)

NAME is verlet, slerp, catmull or nurbs. The access code comes from the
busboom-home-network .env (<NAME>_ACCESS_CODE) and is never printed. Printer
list and setup: busboom-home-network docs/3d-printers.md. Slice with
tools/bambu_slice.py.

wipe is for HMS 0300_1A00_0002_0001 ("the nozzle is covered with filament, or
the build plate is crooked"): the user says it just needs the nozzle wiped
(2026-11-02). The routine is the "wipe nozzle" block of the A1's start G-code
(Bambu Studio's BBL profile), at 170 (PLA's first layer less 50). Sent in one
gcode_line message it was acknowledged and silently not run (2026-11-02), so
it goes in chunks of CHUNK lines, which the printer queues; each chunk ends by
setting the bed target to a marker (30, 31, ...), and wipe watches the markers
until the last one. Takes about 2 minutes. The HMS notice itself stays listed
afterwards (and through a good print): neither wipe nor clean_print_error
removes it over MQTT; it does not block printing.
"""
import json
import os
import re
import ssl
import subprocess
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

from bambu_slice import MACHINE, flatten

NETWORK = Path("/Volumes/Proj/proj/home-projects/busboom-home-network")
PRINTERS = {   # name: (ip, serial, model)
    "verlet": ("192.168.6.33", "03900D5C2511669", "A1"),
    "slerp": ("192.168.6.89", "03919D581609403", "A1"),
    "catmull": ("192.168.6.34", "03900D5C2506993", "A1"),
    "nurbs": ("192.168.6.35", "01S00D570700417", "P1P"),
}
WIPE_TEMP = 170
CHUNK = 18                     # wipe G-code lines per gcode_line message


def access_code(name):
    for line in (NETWORK / ".env").read_text().splitlines():
        if line.startswith(f"{name.upper()}_ACCESS_CODE="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {name.upper()}_ACCESS_CODE in {NETWORK / '.env'}")


def a1_wipe_gcode():
    """Home, the start G-code's wipe block, then heaters and fan off and the head up, as a list of
    lines without comments, display-only M1002s or bed commands (the chunk markers use the bed)."""
    g = flatten("machine", MACHINE)["machine_start_gcode"]
    block = g[g.index(";===== wipe nozzle ====="):g.index(";===== wipe nozzle end")]
    block = re.sub(r"\{nozzle_temperature_initial_layer\[initial_extruder\]-50\}", str(WIPE_TEMP), block)
    assert "{" not in block and "[" not in block, "unresolved placeholder in the wipe block"
    lines = [re.sub(r"\s*;.*", "", l).strip() for l in ["G28"] + block.splitlines()]
    lines = [l for l in lines if l and not l.startswith(("M1002", "M140"))]
    return lines + ["M104 S0", "M106 S0", "G1 Z20 F1200", "M400"]


def wipe(name, timeout=420):
    """Send the wipe in marked chunks and wait until the last marker shows; heaters off after."""
    lines = a1_wipe_gcode()
    chunks = [lines[i:i + CHUNK] for i in range(0, len(lines), CHUNK)]
    last = 30 + len(chunks) - 1
    reqs = [{"print": {"sequence_id": str(100 + i), "command": "gcode_line",
                       "param": "\n".join(c + [f"M140 S{30 + i}"]) + "\n"}} for i, c in enumerate(chunks)]
    mqtt_session(name, reqs, wait=8)
    t0, seen = time.time(), []
    while time.time() - t0 < timeout:
        p = report(name)
        if p.get("bed_target_temper") not in seen:
            seen.append(p.get("bed_target_temper"))
        if p.get("bed_target_temper") == last:
            break
        time.sleep(6)
    command(name, {"print": {"sequence_id": "200", "command": "gcode_line", "param": "M140 S0\n"}})
    return {"done": seen[-1] == last, "markers_seen": seen, "seconds": round(time.time() - t0)}


def mqtt_session(name, requests, wait=10, until=None):
    """Publish each request after connecting; collect the reports for `wait` s (or until until(report))."""
    ip, serial, _ = PRINTERS[name]
    reports, done = [], [False]

    def on_connect(c, u, f, rc, p=None):
        c.subscribe(f"device/{serial}/report")
        for r in requests:
            c.publish(f"device/{serial}/request", json.dumps(r))

    def on_message(c, u, m):
        d = json.loads(m.payload)
        reports.append(d)
        if until and until(d):
            done[0] = True

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.username_pw_set("bblp", access_code(name))
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(ip, 8883, 30)
    c.loop_start()
    t0 = time.time()
    while time.time() - t0 < wait and not done[0]:
        time.sleep(0.2)
    c.loop_stop()
    return reports


def report(name):
    """The printer's full status report (pushall)."""
    reps = mqtt_session(name, [{"pushing": {"sequence_id": "1", "command": "pushall"}}],
                        until=lambda d: "vt_tray" in d.get("print", {}))
    return next((r["print"] for r in reps if "vt_tray" in r.get("print", {})), {})


def status(name):
    p = report(name)
    t = p.get("vt_tray", {})
    return {"state": p.get("gcode_state"), "job": p.get("subtask_name"), "percent": p.get("mc_percent"),
            "nozzle": p.get("nozzle_diameter"), "print_error": p.get("print_error"),
            "hms": ["%08X_%08X" % (h["attr"], h["code"]) for h in p.get("hms", [])],
            "spool": {k: t.get(k) for k in ("tray_type", "tray_color")}}


def command(name, req, wait=10):
    cmd = req["print"]["command"]
    reps = mqtt_session(name, [req], wait=wait,
                        until=lambda d: d.get("print", {}).get("command") == cmd and "result" in d["print"])
    return next(({k: r["print"].get(k) for k in ("command", "result", "reason")}
                 for r in reps if r.get("print", {}).get("command") == cmd and "result" in r["print"]), None)


def main():
    name, verb, *rest = sys.argv[1:]
    if name not in PRINTERS:
        sys.exit(f"unknown printer {name}: {', '.join(PRINTERS)}")
    if verb == "status":
        print(json.dumps(status(name), indent=1))
    elif verb == "start":
        f = Path(rest[0])
        ip = PRINTERS[name][0]
        subprocess.run(["curl", "-s", "-k", "--user", f"bblp:{access_code(name)}", "-T", str(f), f"ftps://{ip}:990/"],
                       check=True)
        print("uploaded", f.name)
        print(command(name, {"print": {
            "sequence_id": "2", "command": "project_file", "param": "Metadata/plate_1.gcode",
            "subtask_name": f.name.removesuffix(".gcode.3mf"), "url": f"file:///sdcard/{f.name}", "md5": "",
            "timelapse": False, "bed_leveling": True, "flow_cali": False, "vibration_cali": False,
            "layer_inspect": False, "use_ams": False, "ams_mapping": [], "profile_id": "0", "project_id": "0",
            "subtask_id": "0", "task_id": "0"}}))
    elif verb == "stop":
        print(command(name, {"print": {"sequence_id": "3", "command": "stop", "param": ""}}))
    elif verb == "wipe":
        if PRINTERS[name][2] != "A1":
            sys.exit("wipe is the A1 routine")
        s = status(name)
        if s["state"] in ("PREPARE", "RUNNING", "PAUSE"):
            sys.exit(f"{name} is {s['state']}: not wiping during a job")
        print(json.dumps(wipe(name)))
        print(json.dumps(status(name), indent=1))
    elif verb == "clear":
        print(command(name, {"print": {"sequence_id": "5", "command": "clean_print_error", "subtask_id": "",
                                       "print_error": status(name)["print_error"] or 0}}))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
