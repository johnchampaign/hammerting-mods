"""Pier Keeps Catch: the fishing pier stores its catch instead of throwing it on the floor.

In default_production_complete_cbck a recipe whose output is LOOT_FISHING_DYNAMIC (the pier's only recipe) sets a
flag that makes the caught fish pop out onto the floor with a random velocity, where Mountainhome Maintain can't
count them and they rot in a few hours (BUGS B10). With the flag left clear, the fish take the same path as other
loot: they go into the producer's inventory, here the pier's own 60 slots, from where haulers and kitchens take
them. The fish supply bookkeeping that the same branch sets up (its second flag) is untouched.
See re/notes/clutter.md.
"""
DESCRIPTION = 'The fishing pier keeps its catch in its own inventory instead of dropping it (DLL patch)'

SITE = 0x1802dab81
OLD = bytes.fromhex('c68580d9000001')     # mov byte [rbp+0xd980], 1: pop the loot out
NEW = bytes.fromhex('c68580d9000000')     # leave it 0: add it to the producer's inventory


def apply(ctx):
    ctx.patch_dll(SITE, OLD, NEW, 'fishing loot goes into the pier')
