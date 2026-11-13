"""Failed Equip Release: a dwarf whose automatic tool upgrade fails can be upgraded again, and the tool is freed.

Reported in Mar 2022 (S0/3187992458103779388, BUGS B5 and B12): "A third has one equipped and an
uncommon one 'to be equipped' but that is actually never happening", with reserved tools that
nobody can find or equip. When the equip sensor offers a dwarf an upgrade it claims the tool for him
(CLAIM_PERSONAL, auto-equip) and marks him busy. If the equip action ends with UT_FAILED,
sensor_equip_on_action_done only removes the action: the busy mark and the claim stay until the game
is reloaded, so that dwarf is never upgraded again and the tool is reserved for nobody. Seen in the
user's colony: an auto-equip claim on a tool lying on the floor held from the 16:29 autosave to
savegame30 at 17:00, with no load in between.

This clears the busy mark and releases the claim after a failed automatic equip. Equip orders given
by the player are unchanged. See re/notes/tool_upgrade.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'A failed automatic tool upgrade frees the tool and lets the dwarf be upgraded again (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x100
SITE = 0x1803ee4a8                      # sensor_equip_on_action_done: jne 0x1803ef366 (reason != 2)
SITE_OLD = bytes.fromhex('0f85b80e0000')
DONE = 0x1803ef366                      # utility_system_remove_action_instance, as before
RELEASE = 0x1801d3240                   # claim_system_release_claim_if_claimed


def apply(ctx):
    symbols = {'BASE': CAVE, 'DONE': DONE, 'RELEASE': RELEASE}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'failed_equip_release code cave')
    jne = b'\x0f\x85' + (CAVE + labels['failed_release'] - (SITE + 6)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jne, 'sensor_equip_on_action_done -> failed_release')
