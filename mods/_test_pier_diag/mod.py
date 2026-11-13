"""TEST ONLY: counts loot items that pass or fail the inventory item check in craft completion (B10)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: counts loot items in craft completion (DLL patch)'
CAVE = dllpatch.CAVE_VA + 0x1e00
SITE = 0x1802d95a1
SYMBOLS = {'BASE': CAVE, 'HAS_ITEM': 0x180115180, 'RESUME': 0x1802d95a6}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, '_test_pier_diag cave')
    old = b'\xe8' + (0x180115180 - (SITE + 5)).to_bytes(4, 'little', signed=True)
    jmp = b'\xe9' + (CAVE + labels['hook'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, old, jmp, 'loot item check -> counter')
