#!/usr/bin/env python3
"""The two ways the display tail can join the Waveshare ESP32-S3-Touch-LCD-1.69, drawn to scale
for Eric to choose (2026-11-14).   uv run --with matplotlib scripts/options_pic.py OUT.png

Frame: the tail's board frame, X right, Y down the board (plotted with the display at the bottom),
viewed from the tail's COPPER side = the display's BACK (component side).
Numbers: PCB 29.85 x 37.14 x 1.0, glass 41.13 x 33.13, LCD module 38.0 x 30.07, the parts on the back
and the flex are from Waveshare's STEP model (sliced with trimesh, scripts/stl_probe.py); the pad row
(11 pads, 2.15 pitch, first centre 4.16 from the corner, centres 1.84 in from the edge) from Waveshare's
dimension drawing and FAQ. Pad size 1.0 x 1.9 is a GUESS from the photo. The STEP has no pads, so the
parts are placed assuming the pad row is centred on the PCB (+-0.3).
"""
import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Polygon

PITCH, INSET = 2.15, 1.84
PCB_W, PCB_L = 29.85, 37.14
PADS = ['18', '17', '3', '2', 'SCL', 'SDA', 'TX', 'RX', '3V3', 'G', '5V']
USED = {'18': 'SCL', '17': 'SDA', '3V3': '3V3', 'G': 'GND'}
W, L = 23.4, 17.7                       # tail
X18 = 1.5                                # pad 18 on the tail's X
DX = X18 - 4.16                          # display left edge (buttons side) in tail X
def xs(x): return 12.25 - x              # STEP x -> tail X (pad 18 at STEP x = +10.75)
# parts on the display's back near the pad edge, from the STEP: tail X range, inboard start, depth below the back
OBST = [(xs(-8), xs(-12), 2.21, 4.4, 'RTC socket'), (xs(6), xs(-7), 2.58, 2.1, 'buzzer etc'), (xs(10), xs(8), 3.78, 0.3, 'flex lip')]
FLEX = (xs(12.37), xs(-12.6), 0.92)      # flex wraps the edge: 0.92 beyond it at PCB level
FLEX_FOLD = (xs(-4.2), xs(-8.3), 2.1)    # the fold's tail lying on the back, 0.3 thick
JACK = dict(mouth=W - 1.0, c=7.0, body=(11.18, 12.7), pads_y=14.4, pitch=1.27, hold=(5.65, 5.2, 5.5, 2.35))


def display(ax, y_edge):
    ax.add_patch(Rectangle((DX, y_edge), PCB_W, PCB_L, fc='#dbe9f6', ec='k', lw=1.2, zorder=1))
    ax.add_patch(Rectangle((DX + (PCB_W - 33.13) / 2 - 0.33, y_edge - 3.0), 33.13, 41.13, fill=False, ec='#444', ls='--', lw=.8))
    ax.add_patch(Rectangle((DX + (PCB_W - 30.07) / 2 + 0.1, y_edge - 1.71), 30.07, 38.0, fill=False, ec='#888', ls=':', lw=.8))
    for x0, x1, d, depth, lab in OBST:
        ax.add_patch(Rectangle((x0, y_edge + d), x1 - x0, 1.6, fc='#f3c6c6', ec='#a33', lw=.8, zorder=2))
    ax.add_patch(Rectangle((FLEX[0], y_edge - FLEX[2]), FLEX[1] - FLEX[0], FLEX[2], fc='#f7d9a0', ec='#b80', lw=.6, zorder=2))
    ax.add_patch(Rectangle((FLEX_FOLD[0], y_edge), FLEX_FOLD[1] - FLEX_FOLD[0], FLEX_FOLD[2], fc='none', ec='#b80', hatch='///', lw=.6, zorder=2))
    for i, name in enumerate(PADS):
        x = X18 + i * PITCH; used = name in USED
        ax.add_patch(Ellipse((x, y_edge + INSET), 1.0, 1.9, fc='#ffd34d' if used else '#ddd', ec='#555', lw=.7, zorder=4))
        ax.text(x, y_edge + 5.6, name, ha='center', va='top', fontsize=6.5, zorder=5, color='k' if used else '#666', fontweight='bold' if used else 'normal')
    ax.annotate('', (X18, y_edge + 5.0), (X18 + 10 * PITCH, y_edge + 5.0), arrowprops=dict(arrowstyle='<->', lw=.7))
    ax.text(X18 + 5 * PITCH, y_edge + 4.8, f'11 pads x {PITCH} = {10 * PITCH:.1f}', ha='center', va='bottom', fontsize=6.5)
    ax.text(DX + PCB_W / 2, y_edge + 8.5,
            'display PCB, back (component) side: 29.85 x 37.14 x 1.0\n'
            f'pad centres {INSET} in from the edge, pad 18 is 4.16 from the corner (Waveshare drawing)\n'
            'pink: parts on the back near the edge (STEP): RTC socket from 2.2 in (photo says ~3.5), 4.4 deep;\n'
            'buzzer and others from 2.6 in, 2.1 deep; flex lip from 3.8 in\n'
            'amber: the LCD flex wraps this edge, 0.9 past it; hatched: its fold lying on the back\n'
            'dashed: glass 41.13 x 33.13, 3.0 past this edge; dotted: LCD module, 1.7 past it',
            ha='center', va='top', fontsize=7, color='#224')


def jack(ax, mouth, c):
    bw, bd = JACK['body']; ax.add_patch(Rectangle((mouth - bd, c - bw / 2), bd, bw, fc='#e8e8e8', ec='#333', lw=1, zorder=3))
    ax.text(mouth - bd / 2 + 1.5, c, 'J1 4P4C jack\n73306-111LF\nmouth ->\n14 tall, latch out', ha='center', va='center', fontsize=7, zorder=5)
    py = mouth - JACK['pads_y']; p = {}
    for n, net in zip(range(1, 5), ['GND', '3V3', 'SCL', 'SDA']):
        y = c - (n - 2.5) * JACK['pitch']; ax.add_patch(Rectangle((py - 1.7, y - .38), 3.4, .76, fc='#f0b040', ec='#630', lw=.5, zorder=4)); p[net] = (py, y)
        ax.text(py - 2.0, y, f'{n} {net}', ha='right', va='center', fontsize=6, zorder=5)
    hx, hy, hl, hw = JACK['hold']
    for s in (-1, 1): ax.add_patch(Rectangle((mouth - hx - hl / 2, c + s * hy - hw / 2), hl, hw, fc='#f0b040', ec='#630', lw=.5, zorder=4))
    return p


def tail(ax, opt, y_edge):
    ax.add_patch(Rectangle((0, 0), W, L, fc='#d9f0d0', ec='#063', lw=1.4, zorder=2, alpha=.9))
    p = jack(ax, JACK['mouth'], JACK['c']); tp = {}
    for i, name in enumerate(PADS):
        if name not in USED: continue
        x = X18 + i * PITCH
        if opt == 'A':
            ax.add_patch(Rectangle((x - .85, L - 2.4), 1.7, 2.2, fc='#f0b040', ec='#630', lw=.5, zorder=4)); tp[USED[name]] = (x, L - 2.4)
        else:
            ax.add_patch(Rectangle((x - .85, L - 3.2), 1.7, 3.0, fc='#f0b040', ec='#630', lw=.5, zorder=4)); tp[USED[name]] = (x, L - 3.2)
            ax.add_patch(Rectangle((x - .32, L - 2.9), .64, 2.9 + (y_edge - L) + INSET + .9, fc='#999', ec='#333', lw=.5, zorder=6))
    routes = {'SCL': [tp['SCL'], (tp['SCL'][0], p['SCL'][1]), (p['SCL'][0] - 1.7, p['SCL'][1])],
              'SDA': [tp['SDA'], (tp['SDA'][0], p['SDA'][1]), (p['SDA'][0] - 1.7, p['SDA'][1])],
              '3V3': [tp['3V3'], (tp['3V3'][0], 14.2), (13.3, 14.2), (13.3, p['3V3'][1]), (p['3V3'][0] + 1.7, p['3V3'][1])],
              'GND': [tp['GND'], (tp['GND'][0], p['GND'][1]), (p['GND'][0] + 1.7, p['GND'][1])]}
    for net, pts in routes.items():
        ax.plot([q[0] for q in pts], [q[1] for q in pts], color='#b5651d', lw=2.2, solid_capstyle='round', zorder=3)
    ax.text(0.4, 11.0, f'tail {W} x {L} x 1.4\ncopper up (this side)\nno mask, spare\ncopper cleared', fontsize=6.5, color='#063', va='top')


def section(ax, opt):
    """Side view through a used pad, looking along the pad row. Display at the right, up = toward the glass."""
    ax.add_patch(Rectangle((0, -2.5), 12, 1.0, fc='#dbe9f6', ec='k', lw=1)); ax.text(7, -2.0, 'display PCB 1.0', ha='center', va='center', fontsize=6.5)
    ax.add_patch(Rectangle((-1.71, 0.5), 13.7, 1.0, fc='#bbb', ec='#666', lw=.6)); ax.text(7, 1.0, 'LCD module', ha='center', va='center', fontsize=6.5)
    ax.add_patch(Rectangle((-3.0, 2.05), 15, 1.75, fc='#333', ec='k', lw=.6)); ax.text(7, 2.9, 'glass', ha='center', va='center', fontsize=6.5, color='w')
    ax.add_patch(Rectangle((INSET - .95, -2.62), 1.9, .12, fc='#ffd34d', ec='#630', lw=.4)); ax.text(INSET + 1.1, -2.9, 'display pad', fontsize=6, va='top')
    ax.plot([-0.92, -0.92, 0, 0], [0.5, -2.4, -2.4, -1.5], color='#b80', lw=1.5); ax.text(-1.1, -0.5, 'flex', fontsize=6, ha='right', color='#850')
    if opt == 'A':
        ax.add_patch(Rectangle((2.1 - L, -4.0), L, 1.4, fc='#d9f0d0', ec='#063', lw=1)); ax.text(2.1 - L / 2, -3.3, 'tail 1.4, copper DOWN (outside)', ha='center', va='center', fontsize=6.5)
        ax.add_patch(Rectangle((2.1 - 2.4, -4.12), 2.2, .12, fc='#f0b040', ec='#630', lw=.4))
        ax.add_patch(Polygon([(2.1, -4.12), (2.1, -2.62), (2.75, -2.62), (3.0, -4.12)], closed=True, fc='#aaa', ec='#333', lw=.5))
        ax.text(3.3, -3.7, 'solder: tail edge pad, down the 1.4 edge,\nonto the 0.8 of display pad left showing', fontsize=6.5, va='center')
        ax.add_patch(Rectangle((2.1 - 12.7 - 1.0, -4.0 - 5), 12.7, 5, fc='#e8e8e8', ec='#333', lw=.8)); ax.text(2.1 - 7.3, -6.5, 'jack (14 tall, cut off)', ha='center', fontsize=6.5)
        ax.annotate('', (2.1, -4.6), (0, -4.6), arrowprops=dict(arrowstyle='<->', lw=.6)); ax.text(1.05, -5.3, 'laps 2.1', ha='center', fontsize=6)
        ax.plot([2.21, 2.21], [-2.5, -6.9], color='#a33', lw=1.2); ax.text(2.4, -6.8, 'RTC socket 2.2 in (STEP)', fontsize=6, color='#700', va='top')
        ax.plot([2.58, 2.58], [-2.5, -4.6], color='#a33', lw=1.2); ax.text(2.8, -5.0, 'buzzer 2.6 in', fontsize=6, color='#700', va='top')
    else:
        g = 1.2
        ax.add_patch(Rectangle((-g - L, -2.5), L, 1.4, fc='#d9f0d0', ec='#063', lw=1)); ax.text(-g - L / 2, -1.8, 'tail 1.4, copper DOWN, its copper face level with the display back', ha='center', va='center', fontsize=6.5)
        ax.add_patch(Rectangle((-g - 3.2, -2.62), 3.0, .12, fc='#f0b040', ec='#630', lw=.4))
        ax.add_patch(Rectangle((-g - 2.9, -3.26), 2.9 + g + INSET + .9, .64, fc='#999', ec='#333', lw=.5)); ax.text(-g - 3.0, -3.5, '0.64 square pin along both pads, soldered to each', fontsize=6.5, va='top', ha='left')
        ax.add_patch(Rectangle((-g - 12.7 - 1.0, -2.5 - 5), 12.7, 5, fc='#e8e8e8', ec='#333', lw=.8)); ax.text(-g - 7.3, -5.5, 'jack (14 tall, cut off)', ha='center', fontsize=6.5)
        ax.annotate('', (-g, -0.6), (0, -0.6), arrowprops=dict(arrowstyle='<->', lw=.6)); ax.text(-g / 2, -0.1, f'gap {g} for the flex', ha='center', fontsize=6)
    ax.set_xlim(-19, 13); ax.set_ylim(-9.5, 4.5); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('section through a used pad, same scale (jack cut off)', fontsize=8)


fig = plt.figure(figsize=(17, 10.5))
for col, (opt, title) in enumerate([('A', 'OPTION A: tail FLAT ON THE BACK, lapping 2.1 mm over the pad edge; soldered from outside over the tail edge'),
                                    ('B', 'OPTION B: tail BUTTED against the pad edge, same plane; four flat 0.64 pins bridge pad to pad')]):
    ax = fig.add_subplot(2, 2, col + 1)
    y_edge = L - 2.1 if opt == 'A' else L + 1.2
    display(ax, y_edge); tail(ax, opt, y_edge)
    ax.set_xlim(-6, 30); ax.set_ylim(y_edge + 17, -1.5); ax.set_aspect('equal')
    ax.set_title(title, fontsize=8.5, fontweight='bold', loc='left'); ax.set_xticks(range(-5, 31, 5)); ax.set_yticks(range(0, int(y_edge + 17), 5)); ax.grid(True, lw=.3)
    ax.set_xlabel('tail X mm. View from the display back: pad 18 at the left (buttons side), jack mouth toward the USB side', fontsize=7)
    section(fig.add_subplot(2, 2, col + 3), opt)
fig.text(.5, .985, 'Display tail: two ways to join the Waveshare ESP32-S3-Touch-LCD-1.69, seen from its back. Yellow = the four display pads used, orange = tail copper. '
         'Sizes from the STEP model and Waveshare drawing; pad size a guess.', ha='center', va='top', fontsize=8.5)
plt.tight_layout(rect=(0, 0, 1, .97)); plt.savefig(sys.argv[1], dpi=120); print('wrote', sys.argv[1])
