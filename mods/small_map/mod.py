"""Small Map: new random maps are 768 x 768 tiles instead of 1024 x 1024.

The colony starts near the top of the map and the Underworld (the only source of Sulphur
Sprouts, needed for Dwarf Licorice) lies along the bottom, so in a 1024 x 1024 map the player
digs 750-900 tiles down through repeats of the same three biomes to reach it. The map size
comes from the `random` scenario record: the new-game menu leaves scenario_settings
_map_width/_map_height at 0, so scenario_setup_for_map_generation (0x1804819c0) uses the
record's _width/_height (plus 4 blocks of border, so 1024 becomes 1088).

scenario_record (scenario.h): _tag at +0, u16 _width +0x40, u16 _height +0x42,
_map_generator[64] +0x68, u16 _start_position[2] +0xa8. The start keeps its distance from the
top of the map (128 tiles) and stays centred. Only new games change; a saved map keeps its size.

The map must stay square: the generator keeps one size value (0x1805b2d94, the width) and uses it
for both axes, so a 1024 x 512 map crashed in stamp_vein (0x180313f7e checks a vein tile's y
against the width) while placing ore near the top edge.

The biome bands don't scale with the map. Dawnlit Caverns around the start and the Underworld
along the bottom keep roughly the same thickness, and the other three biomes fill what is left.
At 512 x 512 there was no room left: one test map had only Dawnlit and Underworld, which loses
their ores and the Geological Explorations mission. At 768 x 768 one test map had all five biomes
and every ore, the start area looked normal, and the Underworld began about 520 tiles below the
start, against about 750 on a 1024 map. Only one map of each size was generated.
"""
import struct

DESCRIPTION = 'New random maps are 768 x 768 instead of 1024 x 1024, so the Underworld is about 30% closer'

SIZE = 768                      # vanilla 1024; square only, and 512 squeezed out three biomes
RECORDS = 'database/scenario/scenario_random.bin'
WIDTH_OFF = 0x40
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
        struct.pack_into('<HH', d, rec + WIDTH_OFF, SIZE, SIZE)
        struct.pack_into('<HH', d, rec + START_OFF, SIZE // 2, SIZE - (h - sy))
        ctx.write(RECORDS, bytes(d))
        return
    raise AssertionError('no random scenario record')
