"""Half Height Map: new random maps are 1024 x 512 tiles instead of 1024 x 1024.

The colony starts near the top of the map and the Underworld (the only source of Sulphur
Sprouts, needed for Dwarf Licorice) lies along the bottom, so in a 1024 x 1024 map the player
digs 750-900 tiles down through repeats of the same three biomes to reach it. The map size
comes from the `random` scenario record: the new-game menu leaves scenario_settings
_map_width/_map_height at 0, so scenario_setup_for_map_generation (0x1804819c0) uses the
record's _width/_height (plus 4 blocks of border, so 1024 becomes 1088).

scenario_record (scenario.h): _tag at +0, u16 _width +0x40, u16 _height +0x42,
_map_generator[64] +0x68, u16 _start_position[2] +0xa8. The start keeps its distance from the
top of the map (128 tiles). Only new games change; a saved map keeps its size.
"""
import struct

DESCRIPTION = 'New random maps are half as tall (1024 x 512), so the Underworld is about half as deep'

HEIGHT = 512                    # vanilla 1024
RECORDS = 'database/scenario/scenario_random.bin'
WIDTH_OFF = 0x40
HEIGHT_OFF = 0x42
START_OFF = 0xa8


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, total = struct.unpack_from('<QQ', d, 0)
    size = total // count
    for i in range(count):
        rec = 16 + i * size
        if d[rec:rec + 0x38].split(b'\0')[0] != b'random':
            continue
        w, h = struct.unpack_from('<HH', d, rec + WIDTH_OFF)
        sx, sy = struct.unpack_from('<HH', d, rec + START_OFF)
        assert (w, h, sx, sy) == (1024, 1024, 512, 896), (w, h, sx, sy)
        struct.pack_into('<H', d, rec + HEIGHT_OFF, HEIGHT)
        struct.pack_into('<H', d, rec + START_OFF + 2, HEIGHT - (h - sy))
        ctx.write(RECORDS, bytes(d))
        return
    raise AssertionError('no random scenario record')
