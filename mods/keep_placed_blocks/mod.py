"""Keep Placed Blocks: a block placed above a walkway is no longer deleted when something nearby is built or removed.

Reported in Jul 2021 (S1/4241812037687177600, three players confirming): bricks placed in the two tiles above
scaffolding, or above a walk bridge, turn back into background "after a random delay". Reservoir walls vanishing
(R/u9emye) and bricks vanishing in "invisible no-build zones" (R/urpwzr) fit the same cause.

A room's pattern turns a blank cell one or two rows above a 'W' walkway cell into 'C', headroom. C cells set no
layer bit, so Place Block accepts them. When any room or infrastructure piece is destroyed (a ghost cancelled or
finished, a teardown), room_system_remove_destroyed_entities re-applies every finished room within 128 tiles that
shares its rows or columns, in mode 1 (room_system_write_pattern 0x180167560), and mode 1 clears the solid bit and
material of C cells. The block vanishes with no dig order and its materials are lost.

Here that re-apply leaves a solid C tile alone. A room's own creation still carves its headroom, so cave rooms
from map generation are unchanged, and so is a ghost's dig order on solid headroom. See re/notes/tile_placement.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Blocks placed above walkways survive nearby building and teardown (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x6c0
SITE = 0x180167958
SITE_OLD = bytes.fromhex('83fe010f859a040000')   # cmp esi, 1; jne 0x180167dfb
MODE1 = 0x180167961
MODE_OTHER = 0x180167dfb
SKIP = 0x180167f89                              # next layer or cell, after reloading r9
REFRESH_RET = 0x18016950c                       # return address of the re-apply call in remove_destroyed_entities


def apply(ctx):
    symbols = {'BASE': CAVE, 'MODE1': MODE1, 'MODE_OTHER': MODE_OTHER, 'SKIP': SKIP,
               'REFRESH_RET': REFRESH_RET}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x40
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'keep_placed_blocks code cave')
    jmp = b'\xe9' + (CAVE + labels['keep_check'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'write_pattern mode 1 -> keep_check')
