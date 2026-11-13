"""Reachable Affluence: the Righteous Affluence victory asks for a sensible hoard.

How the vanilla check works (vault_system_add_coin, 0x18026b130): coin fills the vaults one at
a time in build order, and after each deposit the mission gets that vault's own fullness in
whole percent plus its capacity. A leftover developer HACK in MISSION_GEN_ACQUIRE_VAULT_FULLNESS
ignores vaults holding 1,000 gold or less, so only a Large Vault counts. The goal is therefore:
fill every vault built before the first Large Vault, then fill that Large Vault to the target.
Vanilla asks for 100% of a 50,000-gold Large Vault, far beyond what a fortress earns (a colony
on its first Large Vault banked about 15-30 gold per real hour after wages).

This mod makes a Large Vault hold LARGE_VAULT_GOLD and asks for TARGET_PERCENT of it. The
capacity is saved on each built vault, so a vault built before this mod keeps 50,000 gold:
`tools/save.py vaultcap` rewrites it. The build part says two Large Vaults, but one completed it in the user's game
(savegame72: completed-part count 1, no second vault).
"""
import struct

DESCRIPTION = 'Affluence victory needs a Large Vault 10% full, and a Large Vault holds 2,000 gold, not 50,000'

TARGET_PERCENT = 10
LARGE_VAULT_GOLD = 2_000        # vanilla 50,000; must stay above 1,000 (the HACK's 10,000,000 copper)
COPPER_PER_GOLD = 10_000

RECORDS = 'database/smart_event/cave_mission_records_cdb.bin'
LARGE_VAULT = 'entity/building/vault_large.entity'


def set_capacity(ctx, copper):
    """KV_GOLD_MAX in the entity: key[56], u64 hash, u64 type 0x10003 (u64), u64 value."""
    d = bytearray(ctx.read(LARGE_VAULT))
    o = d.index(b'KV_GOLD_MAX\0') + 56
    _, kind, old = struct.unpack_from('<QQQ', d, o)
    assert kind == 0x10003 and old == 500_000_000, (hex(kind), old)
    struct.pack_into('<Q', d, o + 16, copper)
    ctx.write(LARGE_VAULT, bytes(d))


def apply(ctx):
    t = TARGET_PERCENT
    assert LARGE_VAULT_GOLD > 1_000
    set_capacity(ctx, LARGE_VAULT_GOLD * COPPER_PER_GOLD)
    ctx.replace_cstr(RECORDS,
                     "MISSION_GEN_ACQUIRE_VAULT_FULLNESS('DUMMY', '100', '100')",
                     f"MISSION_GEN_ACQUIRE_VAULT_FULLNESS('DUMMY', '{t}', '{t}')")
    gold = LARGE_VAULT_GOLD * t // 100
    cave = ctx.loc('cave')
    desc = cave.key('MISSION_AFFLUENCE_DESC')
    assert 'fill them to the brim!' in desc.text
    desc.text = desc.text.replace('fill them to the brim!',
                                  f'fill the first one to {t}% of its capacity!')
    cave.key('MISSION_AFFLUENCE_AMASS_DESC').text = (
        f'Coin fills our vaults in the order they were built. Once the vaults built before '
        f'our first Large Vault are full, that Large Vault must reach {t}% ({gold:,} gold).')
