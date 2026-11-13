"""Natural Healing: dwarves slowly regain health on their own.

Vanilla dwarves have no health gain: CLS_DWARF (record 0 of
database/modifier/modifier/dwarf_modifiers_cdb.bin) sets STATUSBAR_HEALTH_MAX but no
STATUSBAR_HEALTH_GAIN, so health returns only through items (gauze, slimebalm, ...). Without
medicine a wounded dwarf stays below the 25% combat threshold for good, which drives the
"panic spiral" (BUGS A6, re/notes/panic_spiral.md). This mod adds STATUSBAR_HEALTH_GAIN to
CLS_DWARF's first free value slot. statusbar_system_update adds the gain every tick (10 per game
second) and clamps to max, as it does for energy, morale, greed and hunger, whose base rates are
about -0.05 per tick.

Value slots are 0x48 bytes from record offset 0x490: tag (char[56] + u64 wc_hash), i32 16.16
value, u32 is_percent.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import wchash  # noqa: E402

REGEN_PER_TICK = 0.05   # health per tick: 0.5 per game second, about 150 per 5 game minutes
DESCRIPTION = f'Dwarves regain {REGEN_PER_TICK * 10:g} health per second on their own'

RECORDS = 'database/modifier/modifier/dwarf_modifiers_cdb.bin'
SLOTS = 0x490
SLOT_SIZE = 0x48
SLOT_COUNT = 20          # used slots 0-17 in vanilla; stop well short of the next field


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    rec = 16                                    # record 0, after u64 count and u64 bytes
    assert d[rec:rec + 0x40].split(b'\0')[0] == b'CLS_DWARF'
    tags = []
    for i in range(SLOT_COUNT):
        o = rec + SLOTS + SLOT_SIZE * i
        tags.append(bytes(d[o:o + 0x38]).split(b'\0')[0])
    assert b'STATUSBAR_HEALTH_GAIN' not in tags, 'CLS_DWARF already has a health gain'
    free = tags.index(b'')
    o = rec + SLOTS + SLOT_SIZE * free
    assert not any(d[o:o + SLOT_SIZE]), f'slot {free} is not empty'
    name = b'STATUSBAR_HEALTH_GAIN'
    d[o:o + 0x38] = name.ljust(0x38, b'\0')
    struct.pack_into('<QiI', d, o + 0x38, wchash.metrohash64(name), round(REGEN_PER_TICK * 65536), 0)
    ctx.write(RECORDS, bytes(d))
