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
    uv run tools/bambu_printer.py NAME resume   resume a paused job
    uv run tools/bambu_printer.py NAME watch    follow a job to the end, resuming nozzle-clumping pauses

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
removes it over MQTT; it does not block printing, and it comes back at the
next homing. A wipe can stall (2026-11-03: markers stopped at 36 of 39); wipe
then exits non-zero.

watch is for the same notice in the middle of a job. The A1's nozzle
clumping check dips the nozzle just off the bed at about layer 2-3; a hit
pauses the job (verlet, 2026-11-02 23:14: tilt_table_v3 sat paused at layer
3 all night). The user clears it by rubbing the nozzle and resuming; forum
reports say plain resume mostly works too, and the check does not run again.
watch polls every minute; on a pause with print_error CLUMP_ERROR
(0300_8014), or with a clumping notice raised during this job, it saves a
camera frame and resumes, at most MAX_RESUMES times. The notice alone is not
enough: on catmull (2026-11-03) its timestamp was the job's start homing, not
the pause, and the notice stays listed after it is dealt with. Any
other pause, a repeat, FAILED, or no report for OFFLINE_S ends it non-zero
without touching the printer; FINISH ends it 0. A wipe while paused is not
done: the start G-code's wipe re-homes Z and turns bed levelling off, and
whether gcode_line runs during a pause (and resume returns the head) is
untested. Camera frames and the log go to LOG_DIR.
"""
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.request
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
PRINTERS_API = ("http://192.168.5.11", "printers.home")   # agony's Caddy (printers.home may not resolve)
CLUMP_HMS = "0300_1A00_0002_0001"
CLUMP_ERROR = 0x03008014       # print_error of a nozzle-clumping pause
MAX_RESUMES = 2                # clumping pauses resumed per job; one more ends the watch
STALE_S = 300                  # an HMS raised this long before the job was last seen running is old
OFFLINE_S = 900
START_S = 300                  # how long `watch` waits for a job it was started for to show as running
LOG_DIR = Path.home() / "Library" / "Logs" / "bambu_watch"


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


def hms_id(h):
    """An HMS entry as the printers page and Bambu's wiki write it, AAAA_BBBB_CCCC_DDDD."""
    return "%04X_%04X_%04X_%04X" % (h["attr"] >> 16, h["attr"] & 0xFFFF, h["code"] >> 16, h["code"] & 0xFFFF)


def status(name):
    p = report(name)
    t = p.get("vt_tray", {})
    return {"state": p.get("gcode_state"), "job": p.get("subtask_name"), "percent": p.get("mc_percent"),
            "layer": [p.get("layer_num"), p.get("total_layer_num")],
            "nozzle": p.get("nozzle_diameter"), "print_error": p.get("print_error"),
            "hms": [hms_id(h) for h in p.get("hms", [])],
            "spool": {k: t.get(k) for k in ("tray_type", "tray_color")}}


def camera(name, out):
    """Save a camera frame from the printers service; False if there is none."""
    base, host = PRINTERS_API
    try:
        req = urllib.request.Request(f"{base}/camera/{name}.jpg", headers={"Host": host})
        Path(out).write_bytes(urllib.request.urlopen(req, timeout=30).read())
        return True
    except OSError:
        return False


def watch(name, every=60):
    """Follow the job to its end (see the module notes). Returns the exit code."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = open(LOG_DIR / f"{name}.log", "a")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {name} {msg}"
        print(line, flush=True)
        log.write(line + "\n"), log.flush()

    def frame(tag):
        f = LOG_DIR / f"{name}_{time.strftime('%Y%m%d_%H%M%S')}_{tag}.jpg"
        say(f"camera {f}" if camera(name, f) else "camera: no frame")

    last_running, last_report, resumes, shown = time.time(), time.time(), 0, None
    t0, started = time.time(), False
    while True:
        p = report(name)
        if not p:
            if time.time() - last_report > OFFLINE_S:
                say(f"no report for {OFFLINE_S // 60} min: giving up")
                return 2
            time.sleep(every)
            continue
        last_report = time.time()
        st, job, layer = p.get("gcode_state"), p.get("subtask_name"), p.get("layer_num")
        hms = {hms_id(h): h.get("timestamp", 0) for h in p.get("hms", [])}
        now_shown = (st, job, (layer or 0) // 10)
        if now_shown != shown:
            say(f"{st} {job} layer {layer}/{p.get('total_layer_num')} {p.get('mc_percent')}% "
                f"{p.get('mc_remaining_time')} min left print_error {p.get('print_error')} hms {sorted(hms)}")
            shown = now_shown
        if st in ("RUNNING", "PREPARE", "SLICING"):
            last_running, started = time.time(), True
        elif not started and st in ("FINISH", "FAILED", "IDLE"):
            # just after `start` the printer still reports the last job's end for a few seconds
            if time.time() - t0 > START_S:
                say(f"job never started ({st} after {START_S // 60} min)")
                return 1
        elif st == "FINISH":
            frame("finish")
            return 0
        elif st in ("FAILED", "IDLE"):
            say(f"job ended {st}")
            frame(st.lower())
            return 1
        elif st == "PAUSE":
            clump = p.get("print_error") == CLUMP_ERROR or hms.get(CLUMP_HMS, 0) > last_running - STALE_S
            frame("pause")
            if not clump:
                say(f"paused, not for nozzle clumping (print_error {p.get('print_error')}): left alone")
                return 1
            if resumes >= MAX_RESUMES:
                say(f"nozzle clumping pause number {resumes + 1}: not resuming again, needs a look")
                return 1
            resumes += 1
            say(f"nozzle clumping pause (print_error {p.get('print_error')}): resume {resumes}: "
                f"{command(name, {'print': {'sequence_id': '6', 'command': 'resume', 'param': ''}})}")
            time.sleep(45)
            last_running = time.time()
            frame("resumed")
            continue
        time.sleep(every)


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
        w = wipe(name)
        print(json.dumps(w))
        print(json.dumps(status(name), indent=1))
        if not w["done"]:
            sys.exit("wipe did not finish (last marker not seen): check the printer before starting a job")
    elif verb == "resume":
        print(command(name, {"print": {"sequence_id": "6", "command": "resume", "param": ""}}))
    elif verb == "watch":
        sys.exit(watch(name))
    elif verb == "clear":
        print(command(name, {"print": {"sequence_id": "5", "command": "clean_print_error", "subtask_id": "",
                                       "print_error": status(name)["print_error"] or 0}}))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
