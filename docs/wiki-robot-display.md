---
title: "Robot Display (ESP32-S3 touch LCD)"
date: 2026-11-14
---

**Repository:** local only, `/Volumes/Proj/proj/robot-projects/watch-display`
(not on GitHub yet; started 2026-11-14).

A Waveshare ESP32-S3-Touch-LCD-1.69 (1.69 in, 240 x 280 touch LCD) made into
a display for the robots. The board runs our firmware as an **I2C slave**
(address 0x42, SDA on GPIO17, SCL on GPIO18): the robot's controller writes
ASCII commands (`T 0 Hello`, `G 0 80 Battery`, `I smile`, `K` to beep) and
reads back 10 bytes of touch, button and battery status. A printed case holds
it: a shell with a lip over the glass, and a lid with a 5 x 4 grid of Technic
pin holes to pin it onto a robot. Part of
[CAD Design Projects](/cad-design-projects).

- **Firmware:** `firmware/` (PlatformIO, Arduino core). The command set is in
  `firmware/src/main.cpp` and the README. `firmware/tools/display.py` drives
  it over USB for testing. The stock Waveshare flash is backed up in
  `backup/`.
- **Case:** `case/robot_display_case.scad`; `bash tools/build.sh` makes the
  STLs, the fit check, `case/views.png` and the sections; `bash tools/serve.sh`
  serves them on http://127.0.0.1:8771/. Every size is from Waveshare's STEP
  model; nothing measured on the real board yet, and nothing printed yet.
- **Wiring:** Nezha I2C cable black/red/yellow/green to the pads G/3V3/17/18,
  via the [Nezha 4P4C adapter or wire hub](/cad-design-projects/milled-pcbs).

Status 2026-11-14: firmware flashed and working over USB (console, drawing,
beep, touch chip found, I2C slave up); not yet driven from a micro:bit. Case
modelled and fit-checked against the STEP model, not printed.

Row for `cad-design-projects.md`:

| [Robot Display](/cad-design-projects/robot-display) | A Waveshare 1.69 in ESP32-S3 touch LCD as an I2C display for the robots: firmware and a printed LEGO-mountable case | `robot-projects/watch-display` (local only) |
