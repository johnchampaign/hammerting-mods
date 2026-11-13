"""Equip Missing Tools: a dwarf takes a tool for a profession nobody has a tool for.

Auto-upgrade only offers a belt slot the professions its current tool already has, so a first
Cook's Ladle sat unused until the player equipped it by hand, and the cook house could not cook.
Now, when no belt has a tool for a profession and a free tool for it exists, a dwarf allowed that
profession takes it: one with an unused slot if there is one, then the most skilled. It replaces
the slot whose tool is used least, and only a tool whose
professions are all on another belt too, so the dwarves can't trade it back and forth. A dwarf's
weapon slot is never replaced, and slots set to custom or off in the toolbelt panel are left alone.
This also applies to spare tools already in storage, such as a lantern when nobody has one
(re/notes/tool_upgrade.md).

DLL patch: two call sites in sensor_equip_try_equip_upgrade, code in the .hmod section.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = "A dwarf takes a tool for a profession nobody has a tool for (DLL patch)"

CAVE = dllpatch.CAVE_VA + 0x800
SYMBOLS = {
    'BASE': CAVE,
    'KV_GET_PTR': 0x180599398,          # as called by refresh_autoupgrade 0x1801d0870
    'MOD_GET_PTR': 0x1805995a0,         # as called at 0x1803effcf
}
SITE = 0x1803efe80                      # cmp r9d, ebx; jle +0x42
SITE_OLD = bytes.fromhex('443bcb7e42')
ENTRY_SITE = 0x1803efff3                # mov eax, [rsp+0x48]; mov [rbp-0x76], bx
ENTRY_OLD = bytes.fromhex('8b44244866895d8a')
NOP3 = bytes.fromhex('0f1f00')


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x280, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'equip_missing_tools code cave')
    ctx.patch_dll(SITE, SITE_OLD, cave.call(SITE, CAVE + labels['score_slot']),
                  'tool upgrade score -> cave score_slot')
    ctx.patch_dll(ENTRY_SITE, ENTRY_OLD, cave.call(ENTRY_SITE, CAVE + labels['unused_slot_first']) + NOP3,
                  'equip entry value -> cave unused_slot_first')
