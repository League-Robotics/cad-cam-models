#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial"]
# ///
"""Talk to the robot display over its USB serial console.

    uv run firmware/tools/display.py [--port /dev/cu.usbmodemXXXX] "T 0 Hello" "G 0 75 Speed" ...
    uv run firmware/tools/display.py --demo        # a short tour of every command
    uv run firmware/tools/display.py --watch       # print the status line once a second

Each argument is one command, exactly as a robot would send it over I2C (see
firmware/src/main.cpp for the list). With no commands it reads a line at a
time from stdin.
"""
import argparse, glob, sys, time
import serial

DEMO = [
    "C", "F white black", "Z 3", "U 0 ROBOT", "Z 2", "T 2 line two, size 2", "T 3 line three",
    "F yellow", "T 4 yellow text", "F white", "G 0 80 Battery", "G 1 35 Speed", "K 1500 80", "sleep 2",
    "C", "N 42", "sleep 1.5",
    "C", "I smile", "sleep 1", "I heart", "sleep 1", "I check", "sleep 1", "I cross", "sleep 1", "I up", "sleep 1", "I stop", "sleep 1",
    "C", "R 10 10 60 40 red", "Q 150 60 30 cyan", "L 0 0 279 239 green", "T 10 shapes", "sleep 2",
    "C", "U 0 touch me", "watch 8",
]

def find_port():
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if not ports:
        sys.exit("no /dev/cu.usbmodem* port; is the display plugged in?")
    return ports[0]

def send(ser, cmd, quiet=False):
    ser.reset_input_buffer()
    ser.write((cmd + "\n").encode())
    time.sleep(0.05)
    out = ser.read_all().decode(errors="replace").strip()
    if not quiet:
        print(f"> {cmd}\n{out}")
    return out

def watch(ser, seconds):
    end = time.time() + seconds
    while time.time() < end:
        print(send(ser, "?", quiet=True).splitlines()[-1])
        time.sleep(1)

def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--port")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--watch", action="store_true")
    p.add_argument("commands", nargs="*")
    a = p.parse_args()
    ser = serial.Serial(a.port or find_port(), 115200, timeout=0.2)
    time.sleep(0.2)
    cmds = DEMO if a.demo else a.commands
    if a.watch:
        watch(ser, 10 ** 9)
    if not cmds:
        for line in sys.stdin:
            send(ser, line.rstrip("\n"))
        return
    for c in cmds:
        if c.startswith("sleep "):
            time.sleep(float(c.split()[1]))
        elif c.startswith("watch "):
            watch(ser, float(c.split()[1]))
        else:
            send(ser, c)

if __name__ == "__main__":
    main()
