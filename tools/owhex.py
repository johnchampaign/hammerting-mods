#!/usr/bin/env python3
"""Read overworld hexes from a save. Read-only.

overworld_map_system/data.bin holds u64 count, u64 bytes, then a record per hex: u16 entity, i32 x, y, ...,
biome tag at +0x56, faction and location tags, u64 6, u64 6, then 6 road edge flags (directions in D), a road
byte and the explored byte. The next record follows, so don't read the fields after the flags as this hex's.
Roads are entity +0xf0..+0xf6 and explored +0xf7 in the game's own 0x158-byte records.

usage: owhex.py <save>   prints what is revealed, then every location
"""
import re
import struct
import sys

import save as sv

D = [(0, -1), (1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0)]


def hexes(path):
    _, o = sv.Save(path).unpack('overworld_map_system/data.bin')
    out = []
    for m in re.finditer(rb'OWBIOME_[A-Z_]+\x00', o):
        p = m.start()
        ent, = struct.unpack_from('<H', o, p - 0x56)
        x, y = struct.unpack_from('<ii', o, p - 0x54)
        q = o.find(b'\x06\0\0\0\0\0\0\0\x06\0\0\0\0\0\0\0', p + 56)
        fac = re.search(rb'FACTION_[A-Z]+', o[p:q])
        loc = re.search(rb'OWLOC_[A-Z_]+', o[p:q])
        flags = o[q + 16:q + 24]
        out.append({'ent': ent, 'x': x, 'y': y, 'fac': fac and fac.group().decode()[8:],
                    'loc': loc and loc.group().decode()[6:], 'roads': flags[:6], 'road': flags[6],
                    'explored': flags[7]})
    return out


if __name__ == '__main__':
    h = hexes(sys.argv[1])
    print('explored', sum(r['explored'] for r in h), 'of', len(h))
    for r in h:
        if r['loc']:
            print(r['ent'], r['loc'], r['fac'] or '-', (r['x'], r['y']), 'seen' if r['explored'] else 'fog')
