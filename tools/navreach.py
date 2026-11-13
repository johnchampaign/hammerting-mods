#!/usr/bin/env python3
"""Show which map nodes each dwarf can reach, read from the running game's memory. Read-only.

Each dwarf has a navgraph query named "movement": record (0x318 bytes) with u64 entity at +0,
name at +8, wc_hash(name) at +0x40, query handle at +0x48. The handle holds the graph at +0, and at
+0x20 the result array (20 bytes per node id, u32 at +0xc non-zero = reached) with its size at +0x28.
The graph holds nodes at +0x60 (count +0x68) and edges at +0x70 (count +0x78). The tile_graph holds
the graph at +0 and node positions at +0x28 (i16 x, y per node id; 32767 for gamepath nodes).

A dwarf cut off from the rest reaches a small set that doesn't overlap the others'. A dwarf whose
query hasn't run yet (just loaded, paused) reads 0.

usage: navreach.py <dwarf entity id>...   ids from saveinspect or the session log
"""
import re
import struct
import subprocess
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wchash import wc_hash_string  # noqa: E402

pid = int(subprocess.check_output("ps -eo pid,comm --sort=-rss | awk '$2 ~ /boot/ {print $1; exit}'",
                                  shell=True).split()[0])
mem = open(f'/proc/{pid}/mem', 'rb', buffering=0)


def rd(addr, size):
    mem.seek(addr)
    return mem.read(size)


def u64(addr):
    return struct.unpack('<Q', rd(addr, 8))[0]


def u32(addr):
    return struct.unpack('<I', rd(addr, 4))[0]


def find(pattern, limit):
    hits = []
    for line in open(f'/proc/{pid}/maps'):
        m = re.match(r'([0-9a-f]+)-([0-9a-f]+) (r.-.)', line)
        if not m or 'w' not in m.group(3):
            continue
        start, end = int(m.group(1), 16), int(m.group(2), 16)
        if end - start < 4096 or end - start >= 1 << 31:
            continue
        try:
            data = rd(start, end - start)
        except OSError:
            continue
        i = data.find(pattern)
        while i >= 0 and len(hits) < limit:
            hits.append(start + i)
            i = data.find(pattern, i + 1)
    return hits


def find_tile_graph(graph):
    for p in find(struct.pack('<Q', graph), 400):
        try:
            _, m, _, _, n1, cap1, _, n2, cap2 = struct.unpack('<QQQQIIQII', rd(p, 0x38))
        except OSError:
            continue
        if n1 > 1000 and n2 > 1000 and n1 <= cap1 and n2 <= cap2 and m >> 32 == 0:
            return p
    raise SystemExit('tile graph not found')


def main(dwarves):
    handles = {}
    for h in find(struct.pack('<Q', wc_hash_string('movement')), 400):
        entity = u64(h - 0x40)
        if entity in dwarves:
            handles[entity] = u64(h + 8)
    if not handles:
        raise SystemExit('no movement query found for those dwarves')
    reached = {}
    for e, q in handles.items():
        n = u32(q + 0x28)
        res = rd(u64(q + 0x20), 20 * n)
        reached[e] = {i for i in range(n) if struct.unpack_from('<I', res, 20 * i + 12)[0]}
    graph = u64(next(iter(handles.values())))
    pos = rd(u64(find_tile_graph(graph) + 0x28), 4 * u32(graph + 0x68))
    largest = max(reached.values(), key=len)
    for e in dwarves:
        if e not in reached:
            print(e, 'no query')
            continue
        s = reached[e]
        print(e, 'reaches', len(s), 'nodes, shared with largest group:', len(s & largest))
        if s and not s & largest:
            tiles = sorted(t for t in (struct.unpack_from('<hh', pos, 4 * i) for i in s) if t[0] != 32767)
            print('   cut off, tiles:', tiles)


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]])
