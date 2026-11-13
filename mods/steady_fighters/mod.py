"""Steady Fighters: a wounded dwarf obeys the player's attack order.

Health ratio r = STATUSBAR_HEALTH current / max (16.16). Below r 0.25 the player's attack
order (ACTION_MOVE_TO_ATTACK, rank 6) scores 0, so a wounded militia dwarf ignores it (BUGS A6).
This mod removes that gate, so an explicit order is followed at any health.

Left as in vanilla on purpose: below 0.25 dwarves don't approach enemies on their own and
armed ones retreat, and below about 0.40 a dwarf with medicine reachable leaves the fight to
heal (rank 7). A first version also lowered those to 10% and ranked healing below combat; in a
test on the user's save (all dwarves at 20% health, the rat raid) a level-9 dwarf then fought
on and died, while unpatched she held back and lived. See re/notes/panic_spiral.md.
"""
DESCRIPTION = "Wounded dwarves obey attack orders instead of ignoring them below 25% health (DLL patch)"

PATCHES = [
    (0x1803b6dbd, '3d00400000', '3d00000000',
     'attack order (move_to_attack): no health gate'),
]


def apply(ctx):
    for va, old, new, note in PATCHES:
        ctx.patch_dll(va, bytes.fromhex(old), bytes.fromhex(new), note)
