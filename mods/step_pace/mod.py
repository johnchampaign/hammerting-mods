"""Step Pace: dwarves take one-tile steps at their walking pace.

Reported as "stairs move dwarves at half speed" (S0/3112519747616498954, Feb 2021: a stairway "twice as long to go up
the same distance" as a scaffold). Every one-tile step in dug terrain runs the walk_stairs behaviour,
which plays the skip_up or skip_down animation once per step at a fixed playback multiplier of 1.0 and moves the
dwarf with the animation. Plain walking plays its animation at the dwarf's STAT_MOVE_SPEED (bt_walk_enter), and
climbing reads STAT_CLIMB_SPEED, but steps read nothing.

This plays each step at FACTOR * STAT_MOVE_SPEED (default 2.0, set HMOD_STEP_FACTOR when installing), clamped to
0.25..2.5, so steps keep pace with walking and follow the same speed traits, gear and statuses. Small Scaffold Stair
columns (about 6.7 tiles a second already), ladders, jumps and falls are unchanged.

Tested on a copy of KrazJomsglind savegame32 (3 game minutes each way, 13 dwarves, positions read from memory at
10 Hz): on stepped slopes dwarves moved at 4.1-5.0 tiles a second without the mod, against 4.6-7.6 on the flat,
and 5.8-7.8 with it. Without it a step took about 0.3 s for one tile across, where walking covers a tile in 0.14 s.
Whether Stone Stairways use the same behaviour was not seen: no dwarf crossed one in 11 minutes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves take one-tile steps at their walking pace instead of about half speed (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2000
ENTER_SITE = 0x1804dd655               # bt_walk_stairs_enter: first step's playback multiplier
ENTER_OLD = bytes.fromhex('48c785a0010000' '00000100')   # mov qword ptr [rbp+0x1a0], 0x10000
ENTER_RESUME = 0x1804dd660
NEXT_SITE = 0x1804dd041                 # event_callback_stairs_anim_done: each following step
NEXT_OLD = bytes.fromhex('48c78590010000' '00000100')    # mov qword ptr [rbp+0x190], 0x10000
NEXT_RESUME = 0x1804dd04c
GET_BY_NAME = 0x180599598               # modifier_system_get_by_name import slot


def apply(ctx):
    factor = round(float(os.environ.get('HMOD_STEP_FACTOR', '2.0')) * 0x10000)
    symbols = {'BASE': CAVE, 'ENTER_RESUME': ENTER_RESUME, 'NEXT_RESUME': NEXT_RESUME, 'GET_BY_NAME': GET_BY_NAME,
               'FACTOR': factor, 'MIN': 0x4000, 'MAX': 0x28000}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'step_pace code cave')
    for site, old, label in ((ENTER_SITE, ENTER_OLD, 'step_enter'), (NEXT_SITE, NEXT_OLD, 'step_next')):
        jmp = b'\xe9' + (CAVE + labels[label] - (site + 5)).to_bytes(4, 'little', signed=True)
        ctx.patch_dll(site, old, jmp + b'\x90' * (len(old) - 5), f'walk_stairs step playback -> {label}')
