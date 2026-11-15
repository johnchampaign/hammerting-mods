"""Stairs Timeout: a dwarf stalled on a step gives up the step and re-plans instead of standing there for good.

Every one-tile step in dug terrain (a stepped slope or a diagonal shaft) runs the walk_stairs behaviour. It plays one
step animation, and only that animation's done event (event_callback_stairs_anim_done 0x1804dc980) moves the dwarf to
the step's end and starts the next step or finishes. bt_walk_stairs_update (0x1804dda70) just waits for that event and
has no timeout, so a dwarf whose event never arrives stands still with his job running: no idle alert, no stranded
alert, and the job broker keeps him. The user's Torner (GreatHvitforge savegame79, 2026-11-15) stood like that at
546.5, 692, exactly on a step point of the one walk edge through a two-wide diagonal shaft, while "hauling a good"
for at least three real minutes. A reload freed him. Why the event was lost was not found.

This watches each dwarf's position while the behaviour runs. When it has not changed for LIMIT_SECONDS game seconds
(default 10, `HMOD_STAIRS_TIMEOUT`; a step takes well under 2), the update returns BT_FAILURE instead. The behaviour's
own exit then stops the animation lock and movement lock, and his job plans again from where he stands. Positions live
in a 128-slot table by entity id in the .hmod section (not saved); two dwarves sharing a slot only reset each other.
See re/notes/stuck_dwarves.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

LIMIT_SECONDS = float(os.environ.get('HMOD_STAIRS_TIMEOUT', '10'))

DESCRIPTION = 'A dwarf stuck on a step for 10 game seconds gives it up and re-plans, instead of standing there (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2680
TABLE = dllpatch.CAVE_VA + 0x2780       # SLOTS * 16 bytes, to 0x2f80
SLOTS = 128
COUNT = TABLE + SLOTS * 16              # u32 timeouts, u32 last entity, i32 x, y (read from memory in tests)
SITE = 0x1804dda70                      # bt_walk_stairs_update
SITE_OLD = bytes.fromhex('4c8bdc' '49895b08')  # mov r11,rsp; mov [r11+8],rbx
SYMBOLS = {
    'BASE': CAVE,
    'TABLE': TABLE,
    'SLOTS': SLOTS,
    'COUNT': COUNT,
    'LIMIT': round(LIMIT_SECONDS * 0x10000),
    'RESUME': 0x1804dda77,
    'WORLD_POSITIONS': 0x1800e9720,     # fixed_transform_system_get_world_positions(ecs)
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= TABLE - CAVE, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'stairs_timeout code cave')
    jmp = b'\xe9' + (CAVE + labels['watch'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'walk_stairs update -> stall timeout')
