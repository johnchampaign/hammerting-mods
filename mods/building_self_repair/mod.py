"""Building Self Repair: quarries slowly regain Building Health on their own.

At 0 Building Health a building is "killed" (death_system) and stays disabled until repaired, and the
only repair item is a Block of Granite (STATUSBAR_BUILDING_HEALTH_INSTANT on CLS_BLOCK_GRANITE in
item_modifiers_cdb.bin), which only a quarry can make. Wandering slimes, a Slime King and rats wear
every building down, so once the quarry itself reaches 0 nothing can make blocks and the colony is
soft-locked: in run 4 (savegame57 continued, Nov 2026) the quarry, foundry, smithy and Cook House all
sat at 0, every queue stalled and all four dwarves stood idle.

This mod adds STATUSBAR_HEALTH_GAIN to the first free value slot of the BUILDING_QUARRY* records in
room_modifiers_cdb.bin, the same gain tag natural_healing gives dwarves: the Building Health bar's
record in statusbar/statusbar.bin names STATUSBAR_HEALTH_GAIN as its gain (STATUSBAR_BUILDING_HEALTH_GAIN
does nothing; tried first). Blocks still repair at once; this only guarantees a broken quarry comes back.
Value slots are 0x48 bytes from record offset 0x490: tag (char[56] + u64 wc_hash), i32 16.16 value,
u32 is_percent.

Only quarries: a building with the gain never reaches the death step. The first version gave every
BUILDING_* and MECH_* record the gain, and from then on no building was "killed" in any session (they
were killed often before). Buildings still stopped working at 0, but the death effect
(death_util::init_death_effects, lambda at 0x1803ffad0) is also what destroys an entity with KV_IS_DOOR,
so a door at 0 stayed shut and invaders kept hitting it (user report, Nov 12 2026, door 3677 at 40.05
in savegame66). A quarry that never dies is the one exception worth having.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import wchash  # noqa: E402

REGEN_PER_TICK = 0.05   # 0.5 Building Health per game second: a Small Quarry (2500) refills in about 83 game minutes
DESCRIPTION = f'Quarries regain {REGEN_PER_TICK * 10:g} Building Health per second on their own, so a broken quarry recovers'

RECORDS = 'database/modifier/modifier/room_modifiers_cdb.bin'
SLOTS = 0x490
SLOT_SIZE = 0x48
SLOT_COUNT = 20
GAIN = b'STATUSBAR_HEALTH_GAIN'


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, size = struct.unpack_from('<QQ', d, 0)
    rs = size // count
    done = []
    for i in range(count):
        rec = 16 + i * rs
        name = bytes(d[rec:rec + 0x40]).split(b'\0')[0]
        if not name.startswith(b'BUILDING_QUARRY'):
            continue
        tags = [bytes(d[rec + SLOTS + SLOT_SIZE * k:rec + SLOTS + SLOT_SIZE * k + 0x38]).split(b'\0')[0]
                for k in range(SLOT_COUNT)]
        if b'STATUSBAR_BUILDING_HEALTH_MAX' not in tags:
            continue
        assert GAIN not in tags, name
        free = tags.index(b'')
        o = rec + SLOTS + SLOT_SIZE * free
        assert not any(d[o:o + SLOT_SIZE]), (name, free)
        d[o:o + 0x38] = GAIN.ljust(0x38, b'\0')
        struct.pack_into('<QiI', d, o + 0x38, wchash.metrohash64(GAIN), round(REGEN_PER_TICK * 65536), 0)
        done.append(name)
    assert b'BUILDING_QUARRY_SMALL' in done, done
    ctx.write(RECORDS, bytes(d))
