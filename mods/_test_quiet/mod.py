"""Test only, never for play: no invaders, and an autosave every 30 game seconds.

Attack alerts pause the game and move the camera, which gets in the way of tests that need to
click on the map. This stops overworld attacks and generic waves (invader_cap's gates with a cap
of 0) and lair spawning. Replaces invader_cap and autosave_interval in the install list.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: no invaders, 30 second autosaves (DLL patch)'
AUTOSAVE_SECONDS = 30.0

CAVE = dllpatch.CAVE_VA + 0x540
ATTACK_SITE = 0x180452002
ATTACK_OLD = bytes.fromhex('488383a002000003')
ATTACK_RESUME = 0x18045200a
WAVE_SITE = 0x180459e4b
SPAWN_WAVE = 0x180454e50
SPAWNERS_SITE = 0x1804592af
SPAWNERS_OLD = bytes.fromhex('e89cecffff')
AUTOSAVE_RESET = 0x1802af379
AUTOSAVE_GATE = 0x1802af393


def apply(ctx):
    src = os.path.join(os.path.dirname(HERE), 'invader_cap', 'cave.s')
    symbols = {'BASE': CAVE, 'CAP': 0, 'ATTACK_RESUME': ATTACK_RESUME, 'SPAWN_WAVE': SPAWN_WAVE}
    code, labels = cave.assemble(src, symbols)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'no invaders: gates')
    jmp = b'\xe9' + (CAVE + labels['attack_gate'] - (ATTACK_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(ATTACK_SITE, ATTACK_OLD, jmp + b'\x90' * 3, 'overworld attack -> gate')
    old = b'\xe8' + (SPAWN_WAVE - (WAVE_SITE + 5)).to_bytes(4, 'little', signed=True)
    new = b'\xe8' + (CAVE + labels['wave_gate'] - (WAVE_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(WAVE_SITE, old, new, 'generic wave -> gate')
    ctx.patch_dll(SPAWNERS_SITE, SPAWNERS_OLD, b'\x90' * 5, 'no lair spawning')
    ctx.patch_dll(AUTOSAVE_RESET, struct.pack('<d', 300.0), struct.pack('<d', AUTOSAVE_SECONDS), 'autosave every 30 seconds')
    ctx.patch_dll(AUTOSAVE_GATE, bytes.fromhex('7430'), bytes.fromhex('eb30'), 'skip debug menu interval')
