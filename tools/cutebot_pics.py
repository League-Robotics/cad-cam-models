#!/usr/bin/env python3
"""Labelled pictures of the Cutebot gripper (scad/cutebot_gripper.scad).

    uv run --with pillow tools/cutebot_pics.py

Uses robot_pics.py's orthographic renders and label helpers:

    view/cutebot_gripper_side.png   section seen from the right, labelled
    view/cutebot_gripper_iso.png    the assembly from the front quarter
    view/cutebot_gripper_parts.png  the three prints on the bed
    view/cutebot_gripper.png        all three on one sheet
    view/cutebot_can_arms.png       the can arms closed: top view with what they
                                    hit in red (nothing), section through a ring end
    view/cutebot_can_ring.png       the ring closing: open, the tips meeting (theta
                                    6.8), concentric (5), fully lapped (4.3)
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import robot_pics as rp
from PIL import Image

SCAD = rp.ROOT / "scad" / "cutebot_gripper.scad"
rp.SCAD = SCAD


def echo_values():
    """The scad's echo() as a dict (numbers and lists)."""
    f = Path(tempfile.mkdtemp()) / "values.echo"
    subprocess.run(["openscad", "-o", str(f), str(SCAD)], capture_output=True, text=True)
    vals = {}
    for line in f.read_text().splitlines():
        if line.startswith("ECHO: "):
            for k, v in re.findall(r"(\w+) = (\[[^\]]*\]|[^,]+)", line[6:]):
                try:
                    vals[k] = json.loads(v)
                except ValueError:
                    vals[k] = v
    return vals


def main():
    out = rp.OUT
    v = echo_values()
    tmp = Path(tempfile.mkdtemp())
    # side: section at x = 0 seen from +x, the front (-y) at the left
    side = rp.View("right", (0, -16, 26), (1300, 720), 8)
    im = side.render(tmp / "side.png", ['part="section"', "section_x=0"])
    s = rp.Sheet(side, im, "Cutebot gripper, three prints pinned together: section at x = 0 from the right (front at the left)")
    boss_z, tab_z, floor_z, arm_z, rows = v["boss_z"], v["tab_z"], v["floor_z"], v["arm_z"], v["wall_rows_z"]
    post_y = v["post_y"]
    s.hline(0, "ground")
    s.hline(v["wall_top_z"], f"frame top {v['wall_top_z']:.1f}")
    s.dim((v["tab_y1"] + 6, 0), (v["tab_y1"] + 6, 18.6), "18.6 chassis underside (measured)", 0)
    s.label(f"PCB {boss_z - 18.6:g} thick, bosses 1.5 proud in the tab's holes", (v["tab_y1"] + 34, 12), (v["tab_y1"] + 4, boss_z - 0.7), anchor="r")
    s.label(f"tab on the bosses (M3 at x = +-8), 5 pins into wall row {v['tab_zc']:g}", (30, 46), (12, tab_z[1]), anchor="c")
    for z in rows:
        s.label(f"{z:g}", (v["back_y"] + 2, z), None, anchor="l")
    s.label("back wall: 4 rows x 6 columns of pin holes", (6, v["wall_top_z"] + 1), (v["back_y"] - 7, rows[1]), anchor="l")
    s.label("servo", (v["servo_back_y"] + 2, v["wall_top_z"] + 6), (v["servo_back_y"] + 1, v["wall_top_z"] - 3))
    s.label("floor (3 rows of pin holes)", (v["floor_y0"] + 30, floor_z[0] - 8), (v["floor_y0"] + 12, floor_z[0] + 2), anchor="l")
    s.label("arm layer (the gears)", (v["floor_y0"] + 4, arm_z[1] + 11), (v["floor_y0"] + 8, (arm_z[0] + arm_z[1]) / 2), anchor="l")
    s.label("2 pins out of the floor's front face (x = +-8)", (post_y[1] - 6, -7), (post_y[1] - 1, (floor_z[0] + floor_z[1]) / 2), anchor="l")
    s.label("caster post: back face at the gear teeth", (post_y[0] - 4, 40), (post_y[0] + 4, 26), anchor="r")
    s.label("EV3 ball caster", (post_y[0] - 14, 20), (post_y[0] - 10, 14), anchor="r")
    s.dim((post_y[0] - 24, 0), (post_y[0] - 24, v["paddle_z0"]), f"paddles {v['paddle_z0']:g} off the ground", 0)
    im.save(out / "cutebot_gripper_side.png")
    # iso
    iso = rp.View("iso", (0, -12, 22), (1300, 900), 7)
    im2 = iso.render(tmp / "iso.png", ['part="assembly"'])
    rp.Sheet(iso, im2, "Cutebot gripper on the nose (stand-in): frame (grey), tab (tan), caster post (green), pins")
    im2.save(out / "cutebot_gripper_iso.png")
    # the three prints
    prints = []
    for name, part, c, size, title in [
        ("frame", "print_frame", (4, 18, 14), (520, 520), "frame: on its back wall"),
        ("tab", "print_tab", (0, 9, 4), (390, 520), "tab: flat, screw heads up"),
        ("post", "print_post", (0, 2, 9), (390, 520), "post: on its back face"),
    ]:
        pv = rp.View("iso", c, size, 7)
        pim = pv.render(tmp / f"{name}.png", [f'part="{part}"'])
        rp.Sheet(pv, pim, title)
        prints.append(pim)
    row = Image.new("RGB", (sum(p.width for p in prints), 520), rp.BG)
    x = 0
    for p in prints:
        row.paste(p, (x, 0))
        x += p.width
    row.save(out / "cutebot_gripper_parts.png")
    rp.stack([[im], [im2], [row]], 1300).save(out / "cutebot_gripper.png")
    print(out / "cutebot_gripper.png")
    can_arms(v, tmp, out)


def can_arms(v, tmp, out):
    """The can arms closed on the caster: the ring's rear ends are trimmed and
    the caster sits as far back as its housing lets the post's pins go."""
    post_y, beam_y1 = v["post_y"], v["post_y"][0] - 7.8
    can = ['ext="can"', "theta=0", 'hide=["cutebot","floor","servo"]']
    top = rp.View("top", (0, -52, 22), (900, 640), 9)
    im = top.render(tmp / "can_top.png", ['part="clash_view"'] + can)
    s = rp.Sheet(top, im, "Can arms closed (theta 0) from above: what they hit would be red; the arms and caster see-through")
    s.label(f"caster moved back 1.3: post {post_y[1] - post_y[0]:.1f} deep (was 18.3)", (14, post_y[0] - 3), (10, post_y[0] - 4), anchor="l")
    s.label("ring ends cut flat: 3.1 off, 0.5 clear of the caster", (4, beam_y1 - 9), (4, beam_y1 - 1.5), anchor="l")
    s.label("the housing's top", (-14, beam_y1 - 3), (-9, beam_y1 - 5), anchor="r")
    im.save(out / "cutebot_can_arms_top.png")
    side = rp.View("right", (0, -50, 20), (900, 560), 9)
    im2 = side.render(tmp / "can_side.png", ['part="section"', "section_x=6"] + can)
    s = rp.Sheet(side, im2, "Section at x = 6 (through a ring end and a mating pin) from the right, front at the left")
    s.label("ring end (arm layer)", (beam_y1 - 4, 36), (beam_y1 - 2.5, 23), anchor="r")
    s.label("caster beam", (post_y[0] - 2, 41), (post_y[0] - 4, 25), anchor="l")
    s.label("post", (post_y[1] - 2, 41), (post_y[1] - 6, 26), anchor="l")
    s.label("housing pocket, 0.4 clear", (post_y[0] + 2, 4), (post_y[0] + 6, 13), anchor="l")
    s.label("mating pin: 0.8 wall to the pocket", (post_y[1] + 6, 6), (post_y[1] - 7.5, 15), anchor="l")
    s.dim((post_y[0], 31), (post_y[1], 31), f"{post_y[1] - post_y[0]:.1f}", 0)
    s.dim((beam_y1 - 0.5, 29.5), (beam_y1, 29.5), "0.5", 0)
    im2.save(out / "cutebot_can_arms_side.png")
    rp.stack([[im], [im2]], 900).save(out / "cutebot_can_arms.png")
    print(out / "cutebot_can_arms.png")
    # the ring closing (the ring turned 15 on the arm and 5 about the axle): the tips meet at theta 6.8, the halves are
    # concentric at 5, the tips lap fully at 4.3 (the limit: beyond it they jam)
    poses = [(90, "open (theta 90)"), (6.8, "theta 6.8: the tips meet, the circle forms"),
             (5, "theta 5: concentric 65 ring, tips lapped 7"), (4.3, "theta 4.3: closed, the 10 mm tips fully lapped (they jam past this)")]
    row = []
    for t, title in poses:
        pv = rp.View("top", (0, -75, 22), (620, 900), 6)
        pim = pv.render(tmp / f"ring_{t}.png", ['part="ring_view"', 'ext="can"', f"theta={t}", 'hide=["cutebot","floor","servo"]'])
        rp.Sheet(pv, pim, title)
        row.append(pim)
    sheet = Image.new("RGB", (sum(p.width for p in row), 900), rp.BG)
    x = 0
    for p_ in row:
        sheet.paste(p_, (x, 0)); x += p_.width
    sheet.save(out / "cutebot_can_ring.png")
    print(out / "cutebot_can_ring.png")


if __name__ == "__main__":
    main()
