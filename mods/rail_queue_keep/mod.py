"""Rail Queue Keep: a dwarf waiting for a Handcar keeps his place in its queue.

A dwarf waiting at a station re-enqueues every 256 ticks, and station_system_enqueue then picks a
vehicle again. For each passenger vehicle that reaches him it counts the dwarves ahead of him (his
place if he is queued on it, else its whole queue) and should take the smallest count, but whenever
a vehicle's count was not smaller it took it anyway if its cost (distance) was lower
(0x18035c21e..0x18035c22d). Switching dequeues him and appends him at the back of the new queue,
and a Handcar drives to the first entry of its queue, so with two Handcars waiting dwarves followed
whichever was nearest, lost their place each time, and turned both Handcars around. In the user's
colony (savegame68, two Handcars on a 480-tile shaft) dwarves piled up at the top station; the
session log showed riders switching Handcars back and forth every few hundred ticks, and waits
there of up to 110 game seconds, most ending when the dwarf gave up.

Now fewer dwarves ahead wins, a tie keeps the vehicle he is already queued on, and only then the
lower cost wins. A dwarf who isn't queued yet still gets the nearest of the emptiest queues.
See re/notes/carts_elevators.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves waiting for a Handcar keep their place instead of chasing the nearest one (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2600
SITE = 0x18035c21e
# cmp r8,r13; jae; mov r13,r8; jmp choose; cmp rcx,rbx; jge skip
SITE_OLD = bytes.fromhex('4d3bc573054d8be8eb05483bcb7d0a')
SYMBOLS = {
    'BASE': CAVE,
    'CHOOSE': 0x18035c22d,      # movzx r15d,r9b; best = this vehicle
    'SKIP': 0x18035c237,        # next vehicle
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x40, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'rail_queue_keep code cave')
    jmp = b'\xe9' + (CAVE + labels['pick'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\xcc' * (len(SITE_OLD) - 5), 'vehicle choice keeps a rider\'s place')
