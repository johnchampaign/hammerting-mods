"""Overworld Goods First: haulers fetch goods waiting in a settlement before loose items.

A hauler takes the nearest item its destination accepts. A storage that takes from the ground and
the overworld (`ground_pickup`'s default) nearly always has a loose item closer than a settlement,
so goods you paid for wait there indefinitely: 10 gauze sat in Suthnock for about 27 real minutes.
Items in a settlement now count as nearest, and the choice among settlements still goes by distance.
See re/notes/market_buying.md.

The scaled distance also reached the test that lets a hauler take over another's claim when he is 10
tiles nearer, while the claimant's own distance there is unscaled. So every hauler beat every
claimant, and several dwarves took one settlement item from each other every tick without moving
(seen 2026-11-10, four dwarves standing still on "haul"). A claim on a settlement item is now never
taken over.

DLL patch: one call site in bt_haul_update and one in should_haul_item, code in the .hmod section
(0xa80 and 0x2580).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Haulers fetch goods waiting in a settlement before loose items (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0xa80
STEAL_CAVE = dllpatch.CAVE_VA + 0x2580
SYMBOLS = {
    'BASE': CAVE,
    'IN_OVERWORLD': 0x18053a218,        # "CURRENTLY_IN_OVERWORLD", as read at 0x1801dc1d1
    'HAS_TAG_PTR': 0x1805991b8,         # called at 0x1801dc1ee in add_haulable_items
}
SITE = 0x1804f8b65                      # mov r13, [rbp+0xa0]
SITE_OLD = bytes.fromhex('4c8bada0000000')
NOP2 = bytes.fromhex('6690')
STEAL_SITE = 0x1804ee326                # mov rcx, [rdi]; add rcx, 0xa0000 (should_haul_item)
STEAL_OLD = bytes.fromhex('488b0f4881c100000a00')
NOP5 = bytes.fromhex('0f1f440000')


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'overworld_goods_first code cave')
    ctx.patch_dll(SITE, SITE_OLD, cave.call(SITE, CAVE + labels['goods_first']) + NOP2,
                  'haul item distance -> cave goods_first')
    code, labels = cave.assemble(os.path.join(HERE, 'no_steal.s'), dict(SYMBOLS, BASE=STEAL_CAVE))
    assert len(code) <= 0x80, 'no_steal outgrew its share of .hmod'
    ctx.patch_dll(STEAL_CAVE, bytes(len(code)), code, 'overworld_goods_first no_steal cave')
    ctx.patch_dll(STEAL_SITE, STEAL_OLD, cave.call(STEAL_SITE, STEAL_CAVE + labels['no_steal']) + NOP5,
                  'haul steal distance -> cave no_steal')
