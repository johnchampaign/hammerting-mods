"""_test_equip_fail (TEST ONLY): make the first automatic tool upgrades fail, and log equips.

Used to test failed_equip_release (BUGS B5, B12). The first HMOD_EQUIP_FAILS (default 2) automatic
equips that would end with UT_SUCCEEDED end with UT_FAILED instead, the same end a real failure gets;
the dwarf has already picked the tool up by then. The cave keeps two u32 counters after its code,
`left` and `failed`, readable from game memory. It also turns on the inventory/toolbelt (+9) and
equip sensor (+12) log groups, which log "Entity %hu equipping tool %hu in slot %lu" and "Removing
equip def ...". Uses .hmod 0x1e00 like the other test-only mods (install only one), no data area.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: the first automatic tool upgrades fail; equips are logged (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x1e00
LOG_SITE = 0x1802aecb0                      # gamestate::gamestate
LOG_OLD = bytes.fromhex('488905398b2f00')   # mov [rip+0x2f8b39], rax (0x1805a77f0)
RESUME = 0x1802aecb7
SETTINGS_PTR = 0x1805a77f0
FAIL_SITE = 0x1803b0dc0                     # equip_action_end
FAIL_OLD = bytes.fromhex('418bf1480faf7a18')  # mov esi, r9d; imul rdi, [rdx+0x18]
FAIL_RESUME = 0x1803b0dc8


def apply(ctx):
    fails = int(os.environ.get('HMOD_EQUIP_FAILS', '2'))
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'SETTINGS_PTR': SETTINGS_PTR, 'FAIL_RESUME': FAIL_RESUME,
               'FAILS': fails}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, '_test_equip_fail code cave')
    jmp = b'\xe9' + (CAVE + labels['equip_log_on'] - (LOG_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(LOG_SITE, LOG_OLD, jmp + b'\x90' * (len(LOG_OLD) - 5), 'gamestate::gamestate -> equip_log_on')
    jmp = b'\xe9' + (CAVE + labels['force_fail'] - (FAIL_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(FAIL_SITE, FAIL_OLD, jmp + b'\x90' * 3, 'equip_action_end -> force_fail')
    print(f'  _test_equip_fail: first {fails} automatic equips fail; counters at .hmod '
          f'{0x1e00 + labels["left"]:#x}')
