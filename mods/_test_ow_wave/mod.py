"""Test only, never for play: fire BURST overworld attacks whenever the lair wave timer is due.

Edited wars revert to peace before an army forms, so this calls the attack function directly, to
exercise the overworld spawn path and the invader_cap gates (BUGS A8,
re/notes/overworld_invaders.md). Also autosaves every 6 game seconds, so leave autosave_interval
out of the install when using this.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = "TEST ONLY: attack bursts on the lair timer, 6 second autosaves (DLL patch)"

CAVE = dllpatch.CAVE_VA + 0x600
SITE = 0x1804592af
SITE_OLD = bytes.fromhex('e89cecffff')
UPDATE_SPAWNERS = 0x180457f50
SYMBOLS = {
    'BASE': CAVE,
    'BURST': int(os.environ.get('HMOD_TEST_BURST', '14')),
    'LAUNCH': 0x180451ff0,
    'UPDATE_SPAWNERS': UPDATE_SPAWNERS,
}
AUTOSAVE_RESET = 0x1802af379
AUTOSAVE_GATE = 0x1802af393


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'test wave cave')
    call = b'\xe8' + (CAVE + labels['test_wave'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, call, 'wave timer -> test wave')
    ctx.patch_dll(AUTOSAVE_RESET, struct.pack('<d', 300.0), struct.pack('<d', 6.0), 'autosave every 6 seconds')
    ctx.patch_dll(AUTOSAVE_GATE, bytes.fromhex('7430'), bytes.fromhex('eb30'), 'skip debug menu interval')
