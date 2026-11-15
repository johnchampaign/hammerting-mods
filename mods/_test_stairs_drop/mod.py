"""Test only, never for play: one dwarf's walk_stairs walk stalls once, to test stairs_timeout.

event_callback_stairs_anim_done (0x1804dc980) ends each step of the walk_stairs behaviour. HMOD_DROP_KIND picks what
happens the first time it runs for dwarf HMOD_DROP_ENTITY (default 2139) after launch:
- `end` (default): at the walk's end the dwarf is put on the end tile and taken off animation driving, but the byte
  bt_walk_stairs_update waits for is not set. In a test (2026-11-15) the dwarf walked on anyway, so something else
  ends the behaviour then.
- `event`: the step animation's done event is dropped. The dwarf stopped mid-step and stayed animation driven with no
  animation; about a second later the game crashed in locomotion_system_update (0x180413b08).
Uses .hmod 0x1e00-0x1e80 (the shared test range) and a flag byte at 0x1e80.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: one dwarf\'s stairs walk stalls once (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x1e00
KIND = os.environ.get('HMOD_DROP_KIND', 'end')
SITES = {
    'end': (0x1804dd036, bytes.fromhex('41c60701' 'e9c7000000')),     # mov byte ptr [r15],1; jmp 0x1804dd106
    'event': (0x1804dc9de, bytes.fromhex('4d8b36' '488d8d90000000')),  # mov r14,[r14]; lea rcx,[rbp+0x90]
}
SYMBOLS = {
    'BASE': CAVE,
    'FLAG': dllpatch.CAVE_VA + 0x1e80,
    'TARGET': int(os.environ.get('HMOD_DROP_ENTITY', '2139')),
    'END_RETURN': 0x1804dd106,
    'EVENT_RETURN': 0x1804dd11e,
    'EVENT_RESUME': 0x1804dc9e8,
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, '_test_stairs_drop code cave')
    site, old = SITES[KIND]
    jmp = b'\xe9' + (CAVE + labels['drop_' + KIND] - (site + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(site, old, jmp + b'\x90' * (len(old) - 5), f'stairs anim done -> drop one ({KIND})')
