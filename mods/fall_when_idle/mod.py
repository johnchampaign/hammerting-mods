"""Fall When Idle: an idle dwarf with nothing under him falls, whatever his last movement.

fall_sensor_update (0x1803f4710) is the only code that recovers a dwarf left without
support: it starts BT_FALL, which lands him and snaps him to the nearest walkable edge. For
a dwarf with a valid graph position it checks the tile below only when his MOVEMENT_STATE
key is missing or STAND. Walking never writes that key, and the exits of vertical jumps
leave JUMP or CLIMB behind, so such a dwarf keeps a stale state and stands in mid-air when
the block under him is dug out (BUGS A10). In the user's save two of six dwarves had JUMP.
This mod runs the support check for every dwarf that has no movement behaviour running.
Dwarves on climb or jump-to-room edges are still skipped earlier, as before (miners hang on
climb edges). See re/notes/stuck_dwarves.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = "Idle dwarves with no ground under them fall instead of hovering (DLL patch)"

CAVE = dllpatch.CAVE_VA + 0x300         # 0x000-0x200 whole_batch_inputs, 0x200-0x300 reachable_diplomacy
SITE = 0x1803f4ef1
SITE_OLD = bytes.fromhex('0f57c0488d0de5e41500')   # xorps xmm0,xmm0; lea rcx,[rip+0x15e4e5]
SYMBOLS = {
    'BASE': CAVE,
    'IS_ACTIVE': 0x180401010,           # movement_system_is_active(ecs, entity)
    'SUPPORT': 0x1803f501e,             # fall sensor: check the tile below
    'RESUME': 0x1803f4efb,              # fall sensor: read MOVEMENT_STATE (after the lea)
    'STATE_KEY': 0x1805533e0,           # "MOVEMENT_STATE"
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x100, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'fall_when_idle code cave')
    jmp = b'\xe9' + (CAVE + labels['stand_gate'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * 5, 'fall sensor movement-state gate -> cave')
