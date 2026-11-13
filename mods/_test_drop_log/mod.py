"""_test_drop_log (TEST ONLY): turn on the GAMESTATE-HAUL log lines.

node_haul.cpp and the haul claim code log pickups, stolen hauls and items dropped on the
ground ("Hauler [%hu] is dropping item [%hu] on the ground"), but only when byte +8 of the
gamestate debug settings (g_debuginator_gamestate_settings) is set, which it never is in
release. This sets it, and the movement (+10), equip (+12) and talk (+14) groups, when the gamestate
is created, so the lines reach the session log. Used to
look into BUGS B5. It also copies the stack at each drop into a ring in the .hmod data area (DATA
below), to name the code that ends a haul with items in hand. Uses .hmod 0x1e00 like _test_pier_diag
and _test_talk_leave (install only one) and data after the code part (CAVE_SIZE) like stranded_rescue (leave it out). The
GAMESTATE-BT line for every behaviour switch is turned on too.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: log hauling, including items dropped by haulers (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x1e00
SITE = 0x1802aecb0
SITE_OLD = bytes.fromhex('488905398b2f00')   # mov [rip+0x2f8b39], rax (0x1805a77f0)
RESUME = 0x1802aecb7
SETTINGS_PTR = 0x1805a77f0
DROP_SITE = 0x1804ee360                     # try_drop_item_on_ground
DROP_OLD = bytes.fromhex('66894c2408')       # mov word ptr [rsp+8], cx
DROP_RESUME = 0x1804ee365
DATA = dllpatch.CAVE_VA + dllpatch.CAVE_SIZE
# ai_behavior_system_update: cmp byte ptr [r13+0xda], 0; je (no "Entity %hu switching from %s to %s" line)
SWITCH_LOG_JE = 0x180359048


def apply(ctx):
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'SETTINGS_PTR': SETTINGS_PTR, 'DROP_RESUME': DROP_RESUME,
               'DATA': DATA}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, '_test_drop_log code cave')
    jmp = b'\xe9' + (CAVE + labels['haul_log_on'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'gamestate::gamestate -> haul_log_on')
    jmp = b'\xe9' + (CAVE + labels['drop_stack'] - (DROP_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(DROP_SITE, DROP_OLD, jmp, 'try_drop_item_on_ground -> drop_stack')
    ctx.patch_dll(SWITCH_LOG_JE, bytes.fromhex('0f8429010000'), b'\x90' * 6, 'log every behaviour switch')
