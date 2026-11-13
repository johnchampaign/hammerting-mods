"""Lava Not Fuel: furnaces no longer burn lava.

CLS_FLUID_LAVA (database/modifier/modifier/item_modifiers_cdb.bin) carries STATUSBAR_FUEL_INSTANT
250, and any item with a positive value is a fuel candidate. Nearby lava can win over distant coal,
and the player has no setting to forbid it, which drains the lava needed for sulphur sprouts and
so the licorice and alliance chain (BUGS B8, re/notes/lava.md). This sets the value to 0. Coal and
charcoal are unaffected, and no recipe needs lava specifically as fuel.

Value slots are 0x48 bytes from record offset 0x490: tag (char[56] + u64 wc_hash), i32 16.16 value,
u32 is_percent.
"""
import struct

DESCRIPTION = 'Furnaces no longer burn lava as fuel'

RECORDS = 'database/modifier/modifier/item_modifiers_cdb.bin'
RECORD_SIZE = 0xdc90
SLOTS = 0x490
SLOT_SIZE = 0x48
SLOT_COUNT = 20
TAG = b'CLS_FLUID_LAVA'
FUEL = b'STATUSBAR_FUEL_INSTANT'
OLD_VALUE = 250 << 16


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, = struct.unpack_from('<Q', d, 0)
    for i in range(count):
        rec = 16 + RECORD_SIZE * i
        if d[rec:rec + 0x40].split(b'\0')[0] == TAG:
            break
    else:
        raise AssertionError('no CLS_FLUID_LAVA record')
    for s in range(SLOT_COUNT):
        o = rec + SLOTS + SLOT_SIZE * s
        if d[o:o + 0x38].split(b'\0')[0] == FUEL:
            assert struct.unpack_from('<i', d, o + 0x40)[0] == OLD_VALUE
            struct.pack_into('<i', d, o + 0x40, 0)
            ctx.write(RECORDS, bytes(d))
            return
    raise AssertionError('CLS_FLUID_LAVA has no fuel value')
