#!/usr/bin/env python3
"""Labelled pictures of the block gripper on the two-plate robot.

    uv run --with pillow tools/robot_pics.py [stances] [pieces]

Renders scad/block_gripper.scad with OpenSCAD's orthographic camera at a
known scale (half the image height = dist * tan(11.25 deg) model units) and
draws the labels, leaders and dimensions over the renders with Pillow
(cutebot_pics.py borrows these):

    view/block_gripper_stances.png   the three stances (level, low, front): side
                                     section and front view of each, labelled with
                                     which wall rows take the pins, plus the level
                                     assembly from the front-left
    view/block_gripper_pieces.png    the prints on the bed: frame, block, the three posts
"""
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "scad" / "block_gripper.scad"
OUT = ROOT / "view"
TAN = math.tan(math.radians(11.25))
ROT = {"right": (90, 0, 90), "top": (0, 0, 180), "front": (90, 0, 0), "iso": (62, 0, 30)}
GRIPPER = ["frame", "block", "post", "pins", "servo", "spline_arm", "idler_arm", "left_ext", "right_ext", "axle", "caster"]
SENSOR = ["pcb", "brackets", "back_parts", "sensors"]
BG = (255, 255, 229)


def font(size):
    for f in ["/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


F = font(17)
FB = font(20)


def scad_list(xs):
    return "[" + ", ".join(f'"{x}"' for x in xs) + "]"


class View:
    """An orthographic render: kind right (screen x = Y, up = Z), top
    (rotated 180: x = -X, down = +Y, so the robot's front is at the top),
    front (x = X, up = Z) or iso (no label mapping)."""

    def __init__(self, kind, centre, size, px_per_mm):
        self.kind, self.c, self.size, self.s = kind, centre, size, px_per_mm
        self.dist = size[1] / (2 * px_per_mm * TAN)

    def render(self, path, defs):
        cam = (*self.c, *ROT[self.kind], round(self.dist, 3))
        cmd = ["openscad", "-o", str(path), "--projection=o", "--camera=" + ",".join(str(v) for v in cam),
               f"--imgsize={self.size[0]},{self.size[1]}", "--colorscheme=Cornfield"]
        cmd += [f"-D{d}" for d in defs] + [str(SCAD)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        for line in r.stderr.splitlines():
            if "ERROR" in line or "WARNING" in line:
                print(line)
        return Image.open(path).convert("RGB")

    def p(self, a, b):
        cx, cy = self.size[0] / 2, self.size[1] / 2
        if self.kind == "right":
            return (cx + (a - self.c[1]) * self.s, cy - (b - self.c[2]) * self.s)
        if self.kind == "top":
            return (cx - (a - self.c[0]) * self.s, cy + (b - self.c[1]) * self.s)
        return (cx + (a - self.c[0]) * self.s, cy - (b - self.c[2]) * self.s)


class Sheet:
    def __init__(self, view, image, title):
        self.v, self.im = view, image
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.text((12, 10), title, FB)

    def text(self, xy, s, f=F, fill=(20, 24, 28)):
        x, y = xy
        w, h = self.d.textbbox((0, 0), s, font=f)[2:]
        self.d.rectangle([x - 4, y - 2, x + w + 4, y + h + 2], fill=(255, 255, 255, 215))
        self.d.text((x, y), s, font=f, fill=fill)
        return (x, y, x + w, y + h)

    def label(self, s, at, to, colour=(200, 30, 30), anchor="l"):
        """Text with its box's edge at `at` (model coords), a leader to `to`."""
        x, y = self.v.p(*at)
        w, h = self.d.textbbox((0, 0), s, font=F)[2:]
        if anchor == "r":
            x -= w
        elif anchor == "c":
            x -= w / 2
        box = self.text((x, y - h / 2), s)
        if to is None:
            return
        tx, ty = self.v.p(*to)
        sx = min(max(tx, box[0]), box[2])
        sy = min(max(ty, box[1] - 2), box[3] + 2)
        self.d.line([(sx, sy), (tx, ty)], fill=colour, width=2)
        self.d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=colour)

    def dim(self, a, b, s, offset, colour=(30, 60, 200)):
        ax, ay = self.v.p(*a)
        bx, by = self.v.p(*b)
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        px, py = -dy / n * offset * self.v.s, dx / n * offset * self.v.s
        a2, b2 = (ax + px, ay + py), (bx + px, by + py)
        self.d.line([(ax, ay), a2], fill=colour, width=1)
        self.d.line([(bx, by), b2], fill=colour, width=1)
        self.d.line([a2, b2], fill=colour, width=2)
        for q in (a2, b2):
            self.d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=colour)
        w, h = self.d.textbbox((0, 0), s, font=F)[2:]
        self.text(((a2[0] + b2[0]) / 2 - w / 2, (a2[1] + b2[1]) / 2 - h / 2), s, fill=colour)

    def hline(self, z, s, colour=(90, 90, 90)):
        y = self.v.p(0, z)[1]
        self.d.line([(0, y), (self.im.width, y)], fill=colour, width=2)
        w = self.d.textbbox((0, 0), s, font=F)[2]
        self.text((self.im.width - w - 20, y + 6), s, fill=colour)


def stack(images, width):
    """Rows of images: each row (a list) scaled to `width`, stacked."""
    rows = []
    for row in images:
        rh = max(im.height for im in row)
        r = Image.new("RGB", (sum(im.width for im in row), rh), BG)
        x = 0
        for im in row:
            r.paste(im, (x, 0))
            x += im.width
        rows.append(r.resize((width, int(r.height * width / r.width))))
    sheet = Image.new("RGB", (width, sum(r.height for r in rows)), BG)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    return sheet


def echo_values(defs):
    """The scad's echo() as a dict (numbers and lists)."""
    import json, re
    f = Path(tempfile.mkdtemp()) / "values.echo"
    subprocess.run(["openscad", "-o", str(f)] + [f"-D{d}" for d in defs] + [str(SCAD)], capture_output=True, text=True)
    vals = {}
    for line in f.read_text().splitlines():
        if line.startswith("ECHO: "):
            for k, v in re.findall(r"(\w+) = (\[[^\]]*\]|[^,]+)", line[6:]):
                try:
                    vals[k] = json.loads(v)
                except ValueError:
                    vals[k] = v
    return vals


NOTES = {
    "level": ("1. level: the frame's 2nd and 3rd wall rows pinned to the block, its top row into the top plate's edge holes",
              ["floor 0.9 below flush with the bottom plate; cube paddles 16.4 off the ground",
               "the can arms close clear of the caster (post 16.8 deep)"]),
    "low": ("2. low: 8 lower, the frame's top two wall rows on the block, its bottom row into the bottom plate's edge holes",
            ["paddles 8.4 off the ground; the can arms close clear (post 17 deep: the beam is in the arm layer)"]),
    "front": ("3. front: 16 lower, the top wall row on the block's lower row, the 3rd row into the bottom plate's edge holes",
              ["paddles 0.4 off the ground (the user wants them barely clear); post 17.55 deep (the housing)",
               "cube paddles only: the arm layer is under the caster's beam, where the housing flares\n5.65 ahead of and behind it, and the can ring's rear ends hit it wherever the caster sits"]),
}


def stances(tmp):
    """view/block_gripper_stances.png: the three stances side by side (sensor on top)."""
    rows = []
    for st in ("level", "low", "front"):
        base = ['sensor_mount="top"', 'ext="cube"', f'stance="{st}"']
        e = echo_values(base)
        v = View("right", (0, -5, 5), (1500, 760), 4.6)
        im = v.render(tmp / "s_side.png", base + ['part="section"', "section_x=0.01"])
        title, lines = NOTES[st]
        sh = Sheet(v, im, title + "  (side, cut at x = 0; front to the left)")
        for i, t in enumerate(lines):
            sh.label(t, (-155, 78 - 11 * i), None)
        sh.hline(e["ground_z"], "ground")
        sh.dim((70, e["ground_z"]), (70, 0.1), "deck 24.5", 0)
        W = e["wall_top_z"]
        sh.label(f"frame wall top {W:g}", (-14, W + 8), (-8, W), anchor="r")
        for z in e["block_rows"]:
            sh.label(f"5 pins: block row {z:g} = wall row", (30, z + 14 if z > 24 else z - 14), (0, z), anchor="l")
        for z in e["edge_rows"]:
            sh.label(f"3 pins (x 0, +-16): plate's edge holes, wall row {z:g}", (30, z + (14 if z > 20 else -22)), (0, z), anchor="l")
        bz = e["block_z"]
        sh.label("block 5 x 3 x 2 under the top plate, 10 pins up into it", (152, 60), (14, (bz[0] + bz[1]) / 2), anchor="r")
        fz = e["floor_z"]
        sh.label(f"floor {fz[0]:.1f}..{fz[1]:.1f}", (-60, fz[0] - 14), (-20, (fz[0] + fz[1]) / 2), anchor="r")
        pz = e["paddle_z0"]
        sh.dim((-90, e["ground_z"]), (-90, pz), f"{pz - e['ground_z']:.1f}", 0)
        py = e["post_y"]
        sh.dim((py[0], e["caster_top_z"] + 6), (py[1], e["caster_top_z"] + 6), f"post {e['post_d']:.2f}", 0)
        sh.label("caster post, pinned into the floor's front face (x +-8)", (-60, -30 if st != "front" else -40), (py[1] - 4, (fz[0] + fz[1]) / 2 - (0 if st != "level" else 6)), anchor="r")
        side = sh.im
        v = View("front", (0, 0, 8), (720, 760), 4.6)
        im = v.render(tmp / "s_front.png", base + ['part="assembly"', 'hide=["floor"]'])
        sh = Sheet(v, im, "front")
        sh.hline(e["ground_z"], "ground")
        rows.append([side, sh.im])
    v = View("iso", (0, 20, 0), (1100, 760), 4)
    im = v.render(tmp / "s_iso.png", ['sensor_mount="top"', 'ext="cube"', 'stance="level"', 'part="assembly"', 'hide=["floor"]'])
    Sheet(v, im, "1. level, from the front-left: frame (grey), block (tan, between the plates), post (green), pins")
    v2 = View("iso", (0, 20, 0), (1100, 760), 4)
    im2 = v2.render(tmp / "s_iso2.png", ['sensor_mount="top"', 'ext="cube"', 'stance="level"', 'part="assembly"', 'hide=["floor", "top_plate", "servo"]', "theta=66"])
    Sheet(v2, im2, "1. level, arms open 66, the top plate and servo hidden: the block's two rows of holes meet the wall")
    rows.append([im, im2])
    stack(rows, 2200).save(OUT / "block_gripper_stances.png")
    print("wrote", OUT / "block_gripper_stances.png")


def pieces(tmp):
    """view/block_gripper_pieces.png: the prints on the bed."""
    prints = [("frame", "print_frame", "level", (4, 18, 14), (520, 520), "frame: on its back wall (one for every robot)"),
              ("block", "print_block", "level", (0, 12, 8), (390, 520), "block: flat; 10 holes down, 2 x 5 in its front face"),
              ("post_level", "print_post", "level", (0, 2, 9), (390, 520), "post 'level': on its back face"),
              ("post_low", "print_post", "low", (0, 2, 9), (390, 520), "post 'low'"),
              ("post_front", "print_post", "front", (0, 2, 11), (390, 520), "post 'front'")]
    row = []
    for name, part, st, c, size, title in prints:
        pv = View("iso", c, size, 7)
        pim = pv.render(tmp / f"{name}.png", [f'part="{part}"', f'stance="{st}"'])
        Sheet(pv, pim, title)
        row.append(pim)
    stack([row], 2200).save(OUT / "block_gripper_pieces.png")
    print("wrote", OUT / "block_gripper_pieces.png")


def main():
    import sys
    OUT.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    what = sys.argv[1:] or ["stances", "pieces"]
    for w in what:
        if w == "stances":
            stances(tmp)
        elif w == "pieces":
            pieces(tmp)
        else:
            raise SystemExit(f"unknown picture {w}")


if __name__ == "__main__":
    main()
