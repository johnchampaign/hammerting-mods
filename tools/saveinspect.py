#!/usr/bin/env python3
"""Read entity-level facts out of a save: names, loose vs held, claims and decay.

Formats (all little-endian, 65536 entity slots):
- debug_name_system/data.bin: u64 size, u64 size, then one NUL-terminated name per entity
  slot, e.g. "crafting_material/egg_chicken[1745]" (the number is the entity id). Only
  some entities (items, buildings, dwarves) are named.
- family_component_system: u64 0xffff, u64, then 10 bytes per entity; the first u16 is the
  parent. Items lying loose on the floor have parent 0.
- claim_system/claims.bin: u64 count, then 13-byte records (u16 entity, u16 claimer,
  u64, u8 type). Type 9 by an ow_hex_* entity is an overworld market's stock; type 4 by a
  building is a production-queue reservation.
- decay_system/data.bin: u64 count, u64 byte size, u16 entity ids, u64 count, then
  (i32 accum, i32 rate) in 16.16 fixed point. Items are destroyed at accum 10000.

usage: saveinspect.py <save> [items|food|loose]
"""
import collections
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from save import Save  # noqa: E402

SAVE_DIR = os.path.expanduser('~/.local/share/Steam/steamapps/compatdata/760650/pfx/drive_c/users/'
                              'steamuser/Documents/My Games/Warpzone Studios/tdtd/save')
FOOD = re.compile(r'food|meat|egg|lichen|berry|ration|haunch|bacon|honey|beet|cabbage|hops|fish|'
                  r'cheese|root_killer|flower_killer|bread|stew|soup|algae|barley|wheat|shroom_toncap')


class Entities:
    def __init__(self, path):
        if not os.path.exists(path):
            path = os.path.join(SAVE_DIR, path if path.endswith('.save') else path + '.2.save')
        s = Save(path)
        _, d = s.unpack('debug_name_system/data.bin')
        n = struct.unpack_from('<Q', d, 0)[0]
        self.names = [x.decode() for x in d[16:16 + n].split(b'\0')]
        _, self._fam = s.unpack('family_component_system/family_component_system.bin')
        _, d = s.unpack('claim_system/claims.bin')
        self.claims = {}
        for i in range(struct.unpack_from('<Q', d, 0)[0]):
            ent, claimer, _, kind = struct.unpack_from('<HHQB', d, 8 + 13 * i)
            self.claims[ent] = (kind, claimer)
        _, d = s.unpack('decay_system/data.bin')
        n, nb = struct.unpack_from('<QQ', d, 0)
        ids = struct.unpack_from(f'<{n}H', d, 16)
        self.decay = {ids[i]: struct.unpack_from('<i', d, 24 + nb + 8 * i)[0] / 65536 for i in range(n)}

    def kind(self, e):
        return re.sub(r'\[\d+\]$', '', self.names[e]) if self.names[e] else f'#{e}'

    def parent(self, e):
        return struct.unpack_from('<H', self._fam, 16 + 10 * e)[0]

    def where(self, e):
        """'loose', 'market' (overworld stock), or 'held' (in some inventory, which can be a
        settlement's: bought goods waiting to be fetched have no claim and count as held).
        Live creatures carry their drops in their own inventories (a rat holds its haunch, hide and
        bone, spawned with ids right after it), and those count as held and unclaimed too, though no
        dwarf can take them. In inventory_system/data.bin they are 16-byte records (8 zero bytes,
        u16 count 1-3, u16 ids), around 2.36 MB in savegame32; which entity owns a record is not decoded."""
        if self.parent(e) == 0:
            return 'loose'
        c = self.claims.get(e)
        if c and self.kind(c[1]).startswith('ow_'):
            return 'market'
        return 'held'

    def items(self):
        return [e for e in self.decay]


def main(argv):
    ents = Entities(argv[0])
    what = argv[1] if len(argv) > 1 else 'items'
    c = collections.Counter()
    for e in ents.items():
        k = ents.kind(e)
        if what == 'food' and not FOOD.search(k.split('/')[-1]):
            continue
        w = ents.where(e)
        if what == 'loose' and w != 'loose':
            continue
        cl = ents.claims.get(e)
        claim = ents.kind(cl[1]) if cl and w != 'market' else ''
        c[(w, k, claim)] += 1
    tot = collections.Counter()
    for (w, _, _), v in c.items():
        tot[w] += v
    print(dict(tot))
    for (w, k, claim), v in sorted(c.items(), key=lambda kv: (kv[0][0], -kv[1])):
        if w != 'market':
            print(f'{v:5}  {w:6}  {k}' + (f'  (claimed by {claim})' if claim else ''))


if __name__ == '__main__':
    main(sys.argv[1:])
