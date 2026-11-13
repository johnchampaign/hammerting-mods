"""Greed Purse Guard: a dwarf whose purse is over-full no longer counts a wage trip as useful.

The wage desire (desire_util::evaluate_refill_statusbar_desire_filler, gold branch) scores a
trip to the starting chest from coins = min(hoard, purse capacity - carried coin) and
greed = min(missing greed, 10 * coins). Both mins compare unsigned, so a dwarf carrying more
than its capacity (10 + 50 x level) gets a negative free space that wraps to a huge number:
the trip scores as worthwhile, the take node moves nothing and reports success, and the trip
can repeat with nothing paid (BUGS A7). Signed compares make that score negative, and the
desire sensor only acts on scores above 0.01 (signed, 0x1803cd87b). For carried <= capacity
and greed below max both operands are non-negative, so nothing else changes.
Not reproduced in testing: with work available the empty trip lost to work. See
re/notes/greed_loop.md.
"""
DESCRIPTION = "Dwarves carrying more coin than their purse holds don't make empty wage trips (DLL patch)"


def apply(ctx):
    ctx.patch_dll(0x1802de54e, bytes.fromhex('480f42c1'), bytes.fromhex('480f4cc1'),
                  'wage desire: coins = min_signed(hoard, purse space)')
    ctx.patch_dll(0x1802de561, bytes.fromhex('4c0f42c9'), bytes.fromhex('4c0f4cc9'),
                  'wage desire: greed = min_signed(missing, 10 * coins)')
