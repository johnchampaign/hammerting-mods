#!/usr/bin/env python3
"""Show computed modifier values per entity from the running game's memory. Read-only.

modifier_system_get_by_hash (entity DLL 0x180046720) reads: system = [ecs+0x40]; entries [system+0x20], 0x68 bytes
each, pointer to the entry record at +0 (record = modifier_entry, wc_tag name at +0, hash +0x38); per-entity lists
[system+0x70], 16 bytes each {items ptr, u32 count, u32 capacity}; items 8 bytes {u16 entry index, u16, i32 value
16.16}. An index with bit 15 set is skipped by dependency lookups. There are two modifier systems (two gamestates);
this takes the first one it can verify.

usage: modvals.py [--funcs] NAME_PREFIX...    e.g. modvals.py PROF_MINER_ PROF_ALL_
  Prints, per entity that has any matching entry, the matching values. --funcs also prints each matching entry's
  funcs (source, compute, dependencies and weights).
"""
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wchash import wc_hash_string  # noqa: E402

pid = int(subprocess.check_output("ps -eo pid,comm | awk '$2 == \"boot.exe\" {print $1; exit}'", shell=True))
mem = open(f'/proc/{pid}/mem', 'rb', buffering=0)
regions = []
for line in open(f'/proc/{pid}/maps'):
    m = re.match(r'([0-9a-f]+)-([0-9a-f]+) (r.-.)', line)
    if m and 'w' in m.group(3):
        s, e = int(m.group(1), 16), int(m.group(2), 16)
        if 4096 <= e - s < 1 << 31:
            regions.append((s, e))


def rd(a, n):
    if not 0 < a < 1 << 47:
        raise OSError(a)
    mem.seek(a)
    return mem.read(n)


def q(a):
    return struct.unpack('<Q', rd(a, 8))[0]


def find(pat, limit=50):
    hits = []
    for s, e in regions:
        try:
            d = rd(s, e - s)
        except OSError:
            continue
        i = d.find(pat)
        while i >= 0 and len(hits) < limit:
            hits.append(s + i)
            i = d.find(pat, i + 1)
    return hits


def tag(name):
    return name.encode().ljust(0x38, b'\0') + struct.pack('<Q', wc_hash_string(name))


def name_at(p):
    try:
        n = rd(q(p), 0x38).split(b'\0')[0]
    except (OSError, struct.error, ValueError):
        return None
    return n.decode() if n and n.replace(b'_', b'').isalnum() else None


def locate():
    """(entries table, per-entity lists) of a modifier system, found from a generated entry's record."""
    for r in find(tag('PROF_MINER_SPEED')):
        for h in find(struct.pack('<Q', r)):
            if not (name_at(h - 0x68) and name_at(h + 0x68)):
                continue
            p = h
            while name_at(p - 0x68):
                p -= 0x68
            for x in find(struct.pack('<Q', p)):
                try:
                    lists = q(x - 0x20 + 0x70)
                    rows = [struct.unpack('<QII', rd(lists + 16 * k, 16)) for k in range(1, 33)]
                except (OSError, struct.error):
                    continue
                if all(n <= cap < 5000 and (ptr == 0) == (cap == 0) for ptr, n, cap in rows) and \
                        any(n for _, n, _ in rows) and abs(lists - p) > 0x100000:
                    return p, lists
    raise SystemExit('modifier system not found')


def funcs_of(table, i):
    rec = q(table + i * 0x68)
    out = []
    for j in range(4):
        f = rec + 0xc8 + j * 0x8c0
        if not q(f + 0x78):
            break
        deps = []
        for k in range(16):
            n = rd(f + 0x80 + k * 0x40, 0x38).split(b'\0')[0].decode()
            if not n:
                break
            deps.append((n, struct.unpack('<i', rd(f + 0x880 + 4 * k, 4))[0] / 65536))
        out.append((rd(f, 0x38).split(b'\0')[0].decode(), rd(f + 0x40, 0x38).split(b'\0')[0].decode(), deps))
    return out


def main(args):
    show_funcs = '--funcs' in args
    prefixes = tuple(a for a in args if a != '--funcs') or ('PROF_ALL_',)
    table, lists = locate()
    names = {}
    while name_at(table + len(names) * 0x68):
        names[len(names)] = name_at(table + len(names) * 0x68)
    wanted = {i for i, n in names.items() if n.startswith(prefixes)}
    if show_funcs:
        for i in sorted(wanted):
            print(names[i], funcs_of(table, i))
    for c in range(1, 20000):
        try:
            ptr, cnt = struct.unpack('<QI', rd(lists + c * 16, 12))
            items = rd(ptr, 8 * cnt) if ptr and 0 < cnt < 5000 else b''
        except OSError:
            break
        vals = {}
        for k in range(len(items) // 8):
            e, _, v = struct.unpack_from('<HHi', items, 8 * k)
            if not e & 0x8000 and e in wanted:
                vals.setdefault(names[e], v / 65536)
        if vals:
            print(f'list {c}:', '  '.join(f'{n}={v:.3f}' for n, v in sorted(vals.items())))


if __name__ == '__main__':
    main(sys.argv[1:])
