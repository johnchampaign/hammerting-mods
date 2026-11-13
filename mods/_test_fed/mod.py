"""Test only, never for play: dwarves never need food, sleep, morale or pay.

The colony copies used for tests run short of food, and the dwarves then crowd the cook house and
ignore other work, which hides the behaviour under test. This sets CLS_DWARF's bar rates to refill
quickly, so test jobs get done at once.
"""
import struct

DESCRIPTION = 'TEST ONLY: dwarf needs bars refill by themselves'
RECORDS = 'database/modifier/modifier/dwarf_modifiers_cdb.bin'
SLOTS = 0x490
SLOT_SIZE = 0x48
SLOT_COUNT = 20
RATE = 1.0     # per tick
NAMES = (b'STATUSBAR_HUNGER_GAIN', b'STATUSBAR_ENERGY_GAIN', b'STATUSBAR_MORALE_GAIN', b'STATUSBAR_GREED_GAIN')


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    rec = 16
    assert d[rec:rec + 0x40].split(b'\0')[0] == b'CLS_DWARF'
    done = 0
    for i in range(SLOT_COUNT):
        o = rec + SLOTS + SLOT_SIZE * i
        if bytes(d[o:o + 0x38]).split(b'\0')[0] in NAMES:
            struct.pack_into('<i', d, o + 0x40, round(RATE * 65536))
            done += 1
    assert done == len(NAMES), done
    ctx.write(RECORDS, bytes(d))
