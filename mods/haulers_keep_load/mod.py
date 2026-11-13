"""Haulers Keep Load: a hauler whose trip is cut short keeps what he carries instead of throwing it down.

Reported in Mar 2022 (S1/3187992943272016665, "Picking up stuff and throwing them everywhere!"):
dwarves and carts drop rings, ingots, gems and ore along the way, and merchants drop their goods
at the exit and go back for more. When the AI switches a dwarf away from BT_HAUL, bt_haul_exit
releases the trip's claims and drops every item he holds on the floor (try_drop_item_on_ground,
0x1804ee360). On a copy of KrazJomsglind savegame30 that happened 12 times in about 4 game minutes,
with up to 12 items at once, when a loaded hauler went to eat, sleep, pick something up or another
job. Loose items are only taken by production buildings and by storages that take from the ground,
and otherwise rot in about 2.8 game hours.

Here the exit no longer drops them: the items stay in the dwarf's inventory, unclaimed, and the
game's own BT_CLEAN_INVENTORY carries them to storage later. bt_haul_enter still drops a held item
that something else has claimed. See re/notes/hauling.md.
"""

DESCRIPTION = 'Haulers keep their load when a trip is interrupted instead of dropping it on the floor (DLL patch)'

SITE = 0x1804eec4f                          # bt_haul_exit: call try_drop_item_on_ground, per held item
SITE_OLD = bytes.fromhex('e80cf7ffff')


def apply(ctx):
    ctx.patch_dll(SITE, SITE_OLD, bytes.fromhex('0f1f440000'), 'bt_haul_exit keeps held items')
