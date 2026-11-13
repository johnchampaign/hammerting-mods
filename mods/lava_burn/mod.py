"""Lava Burn: lava hurts a tenth as fast.

EFFECT_IN_LAVA (database/modifier/modifier/dwarf_modifiers_cdb.bin) is STATUSBAR_HEALTH_GAIN -10 per
tick, about 100 HP per game second, against 1300-2700 HP. A dwarf is unconscious in under half a minute,
faster than a player can react (BUGS B8, re/notes/lava.md). This sets -1. It applies to every creature
that takes this effect.

Value slots are 0x48 bytes from record offset 0x490: tag (char[56] + u64 wc_hash), i32 16.16 value,
u32 is_percent.
"""
import struct

DESCRIPTION = 'Lava burns a tenth as fast'

RECORDS = 'database/modifier/modifier/dwarf_modifiers_cdb.bin'
RECORD_SIZE = 0xdc90
SLOTS = 0x490
SLOT_SIZE = 0x48
SLOT_COUNT = 20
TAG = b'EFFECT_IN_LAVA'
GAIN = b'STATUSBAR_HEALTH_GAIN'
OLD_VALUE = -10 << 16
NEW_VALUE = -1 << 16


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, = struct.unpack_from('<Q', d, 0)
    for i in range(count):
        rec = 16 + RECORD_SIZE * i
        if d[rec:rec + 0x40].split(b'\0')[0] == TAG:
            break
    else:
        raise AssertionError('no EFFECT_IN_LAVA record')
    for s in range(SLOT_COUNT):
        o = rec + SLOTS + SLOT_SIZE * s
        if d[o:o + 0x38].split(b'\0')[0] == GAIN:
            assert struct.unpack_from('<i', d, o + 0x40)[0] == OLD_VALUE
            struct.pack_into('<i', d, o + 0x40, NEW_VALUE)
            ctx.write(RECORDS, bytes(d))
            return
    raise AssertionError('EFFECT_IN_LAVA has no health value')
