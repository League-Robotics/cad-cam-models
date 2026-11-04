#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""Sections through a 4P4C plug's cable cavity with a plug-tail board in it (pcb/plug-tail).

    uv run tools/plug_tail_pics.py [STOCK_MM]

Writes view/plug_tail_section.png:
    left   looking into the cavity from the cable end: four 0.64 pins at 1.02 pitch, the board under them
    right  cut along one pin: channel wall, how far the pin sticks out, the tongue and its pad

The cavity (5.5 x 3.15) is the user's measurement. Where the channels sit in its height is NOT measured:
PIN_Z puts the pin centres at mid-height, where a flat cable's conductors would be. Change it once measured.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parents[1] / 'view' / 'plug_tail_section.png'

CAV_W, CAV_H = 5.5, 3.15     # cable cavity at the plug's back face (measured)
PIN, PITCH = 0.64, 1.02      # square header pin; 4P4C contact pitch
PIN_Z = CAV_H / 2            # pin centre above the cavity floor (assumed: mid-height)
STICK = 3.0                  # pin length out of the channel wall into the cavity (measured, about)
DEPTH = 6.0                  # channel wall to back face (rev A's tongue length; not measured)
TONGUE_W = 5.30              # tongue width (rev A and B)
PAD = (0.25, 10.25)          # rev B pad span from the tongue tip
STOCK = float(sys.argv[1]) if len(sys.argv) > 1 else 1.4   # board thickness (rev A: 1.4)

COPPER, BOARD, PINC, PLUG = '#c87533', '#e8dcbc', '#9aa4ab', '#d8d8de'
under = PIN_Z - PIN / 2      # floor to pin underside
over = STOCK - under         # how much the board pushes the pins up (>0) or hangs clear (<0)


def dim(ax, a, b, text, off=0.0, horiz=True, color='k'):
    """Dimension line from a to b, label in the middle."""
    (x0, y0), (x1, y1) = a, b
    ax.annotate('', (x0, y0), (x1, y1), arrowprops=dict(arrowstyle='<->', color=color, lw=.8))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(mx + (0 if horiz else off), my + (off if horiz else 0), text, ha='center' if horiz else 'left',
            va='center', fontsize=8, color=color, bbox=dict(fc='white', ec='none', pad=.5))


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw=dict(width_ratios=[1, 1.35]))
fig.suptitle(f'Plug tail in the 4P4C cable cavity: {STOCK:g} mm board under the pins  (pins assumed at mid-height)',
             fontsize=12)

# ---- left: looking into the cavity from the cable end ----------------------------------------
a1.add_patch(Rectangle((-CAV_W / 2 - 1.2, -1.0), CAV_W + 2.4, CAV_H + 2.0, fc=PLUG, ec='none'))
a1.add_patch(Rectangle((-CAV_W / 2, 0), CAV_W, CAV_H, fc='white', ec='k', lw=1))
a1.add_patch(Rectangle((-TONGUE_W / 2, 0 if over >= 0 else under - STOCK), TONGUE_W, STOCK,
                       fc=BOARD, ec='k', lw=.8, zorder=2))
top = max(STOCK, under)      # pins rest on the board if it is thicker than the space under them
for i in range(4):
    x = (i - 1.5) * PITCH
    a1.add_patch(Rectangle((x - PIN / 2, under), PIN, PIN, fc='none', ec='#555', ls=':', lw=.8, zorder=3))
    a1.add_patch(Rectangle((x - 0.31, top - 0.05), 0.62, 0.05, fc=COPPER, ec='none', zorder=3))
    a1.add_patch(Rectangle((x - PIN / 2, top), PIN, PIN, fc=PINC, ec='k', lw=.6, zorder=4))
    a1.text(x, top + PIN + .12, str(i + 1), ha='center', fontsize=8)
if over > 0:
    a1.add_patch(Rectangle((-TONGUE_W / 2, under), TONGUE_W, over, fc='#e05050', alpha=.45, ec='none', zorder=5))
    a1.text(TONGUE_W / 2 + .1, under + over / 2, f'{over:.2f} too thick:\npins bent up', fontsize=8,
            color='#b02020', va='center')
dim(a1, (-CAV_W / 2, -.45), (CAV_W / 2, -.45), f'{CAV_W} cavity (measured)')
dim(a1, (-CAV_W / 2 - .45, 0), (-CAV_W / 2 - .45, CAV_H), f'{CAV_H}', off=-.75, horiz=False)
dim(a1, (-2.25, 0), (-2.25, under), f'h = {under:.2f}?', off=.08, horiz=False, color='#2050b0')
dim(a1, ((-1.5) * PITCH, CAV_H + .55), ((-.5) * PITCH, CAV_H + .55), f'{PITCH}')
a1.text(0, -1.35, 'dotted: where the channels hold the pins\n'
        'blue h: floor to pin underside = the board thickness that fits. MEASURE', ha='center', va='top',
        fontsize=8.5)
a1.set_title('Looking into the cavity from the cable end\n(contact side up, copper face up)', fontsize=10)
a1.set_xlim(-4.6, 5.4), a1.set_ylim(-2.4, 4.6), a1.set_aspect('equal'), a1.axis('off')

# ---- right: cut along one pin ------------------------------------------------------------------
# x: 0 at the channel wall, + toward the cable end
a2.add_patch(Rectangle((-5, -1.0), 5, CAV_H + 2.0, fc=PLUG, ec='none'))                 # plug body ahead of the wall
a2.add_patch(Rectangle((0, -1.0), DEPTH, 1.0, fc=PLUG, ec='none'))                       # floor
a2.add_patch(Rectangle((0, CAV_H), DEPTH, 1.0, fc=PLUG, ec='none'))                      # roof
a2.add_patch(Rectangle((-5, under), 5, PIN, fc='white', ec='none'))                      # channel
a2.add_patch(Rectangle((-5, top), 5 + STICK, PIN, fc=PINC, ec='k', lw=.6, zorder=4))     # pin
a2.add_patch(Rectangle((-3.4, CAV_H + .95), .35, -(CAV_H + .95 - top - PIN), fc=COPPER, ec='k', lw=.6))
a2.text(-3.22, CAV_H + 1.1, 'contact blade\n(crimp)', ha='center', fontsize=8)
y0 = top - STOCK
a2.add_patch(Rectangle((0, y0), 14.5, STOCK, fc=BOARD, ec='k', lw=.8, zorder=2))  # tongue + tail
a2.add_patch(Rectangle((PAD[0], top - .05), PAD[1] - PAD[0], .05, fc=COPPER, ec='none', zorder=3))
a2.plot([DEPTH, DEPTH], [-1.0, CAV_H + 1.0], color='#7040a0', ls='--', lw=1)
a2.text(DEPTH + .1, CAV_H + .8, 'plug back face\n(depth not measured)', color='#7040a0', fontsize=8)
dim(a2, (0, top + PIN + .35), (STICK, top + PIN + .35), f'pin sticks out ~{STICK:g}')
dim(a2, (PAD[0], y0 - .4), (PAD[1], y0 - .4), f'pad {PAD[0]}-{PAD[1]} from tongue tip')
dim(a2, (14.8, y0), (14.8, top), f'{STOCK:g}', off=.1, horiz=False)
a2.text(12.3, 2.2, 'tail out of the plug:\nservo pins / Qwiic', ha='center', fontsize=8.5)
a2.text(-2.5, -1.35, 'channel wall at 0; tongue tip butts against it,\nsolder joint is the pin lying on the pad',
        ha='center', va='top', fontsize=8.5)
a2.set_title('Cut along one pin (plug nose to the left)', fontsize=10)
a2.set_xlim(-5.2, 16.2), a2.set_ylim(-2.4, 5.0), a2.set_aspect('equal'), a2.axis('off')

OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, dpi=160, bbox_inches='tight')
print(f'{OUT}  h={under:.3f}  board {STOCK} -> {"interferes by" if over > 0 else "clears by"} {abs(over):.3f}')
