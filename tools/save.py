#!/usr/bin/env python3
"""Read and patch Hammerting saves.

A save (<Documents>/My Games/Warpzone Studios/tdtd/save/<name>.2.save) is a WKZ10 archive
with one file per game system. Most files are
  u32 unknown (0x400000, 0x1800000, ...), u8 1, u64 uncompressed size, LZ4 block
and are kept as-is unless patched; patched files are re-packed as a literal-only LZ4 block.

usage:
  save.py list <save>
  save.py affluence <save> <out-name> [percent]   copy the save with the Affluence fullness
                                                 target set to percent (default 10)
  save.py ground <save> <out-name>                 copy the save with every general storage
                                                 set to take items from the ground
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lz4block  # noqa: E402
import wkz  # noqa: E402
from wchash import wc_hash_string  # noqa: E402

SAVE_DIR = os.path.expanduser('~/.local/share/Steam/steamapps/compatdata/760650/pfx/drive_c/users/'
                              'steamuser/Documents/My Games/Warpzone Studios/tdtd/save')


def lz4_literals(data):
    """An LZ4 block holding data as one literal run (valid as a final sequence)."""
    n = len(data)
    if n < 15:
        return bytes([n << 4]) + data
    out = bytearray([0xf0])
    rest = n - 15
    while rest >= 255:
        out.append(255)
        rest -= 255
    out.append(rest)
    return bytes(out) + data


class Save:
    def __init__(self, path):
        m = wkz.open_archive(path)
        self.entries = [e for e in wkz.entries(m) if e['name'] != 'all.fileinfo']
        self.raw = {e['name']: bytes(m[e['offset']:e['offset'] + e['size']]) for e in self.entries}
        self.types = {e['name']: e['flags'] for e in self.entries}

    def unpack(self, name):
        r = self.raw[name]
        head, flag, size = struct.unpack_from('<IBQ', r, 0)
        assert flag == 1, f'{name}: unexpected flag {flag}'
        data = lz4block.decompress(r, 13)
        assert len(data) == size
        return head, data

    def repack(self, name, data):
        head, _ = self.unpack(name)
        self.raw[name] = struct.pack('<IBQ', head, 1, len(data)) + lz4_literals(data)

    def write(self, path):
        wkz.write(path, sorted(self.raw.items()), types=self.types)


def set_affluence_target(save, percent):
    """The Affluence mission's fullness part is stored as TYPE=DUMMY, AMOUNT_WANTED=<n>,
    AMOUNT_DONE=<n> right after the MISSION_AFFLUENCE record name."""
    name = 'smart_event_system/data.bin'
    _, d = save.unpack(name)
    d = bytearray(d)
    start = d.index(b'MISSION_AFFLUENCE\0')
    end = d.index(b'MISSION_', start + 20)
    dummy = d.index(b'DUMMY\0', start, end)
    key = d.index(b'AMOUNT_WANTED\0', dummy, end)
    # After the 56-byte key buffer: u64 key hash, u64 type (0x10004: i64, count 1), i64 value.
    hash_off = key + 56
    assert struct.unpack_from('<Q', d, hash_off)[0] == wc_hash_string('AMOUNT_WANTED')
    assert struct.unpack_from('<Q', d, hash_off + 8)[0] == 0x10004
    val_off = hash_off + 16
    old, = struct.unpack_from('<q', d, val_off)
    assert old in (100, percent), f'unexpected AMOUNT_WANTED {old} at {val_off}'
    struct.pack_into('<q', d, val_off, percent)
    save.repack(name, bytes(d))
    return old


def set_vault_capacity(save, prefix, copper):
    """Set KV_GOLD_MAX of every built vault whose debug name starts with prefix (e.g.
    'building/vault_large['), and move the vault system's total capacity with it.
    key_value_system/key_value.bin holds four arrays, each u64 count, u64 bytes, data: entities
    (u16), keys per entity (u64), key hashes (u64), values {u64 type, u64 value}.
    vault_system/data.bin: u64 n, u64 bytes, n u16 vault ids, 8 bytes, u64 coin, u64 capacity."""
    _, names = save.unpack('debug_name_system/data.bin')
    n = struct.unpack_from('<Q', names, 0)[0]
    names = [x.decode() for x in names[16:16 + n].split(b'\0')]
    name = 'key_value_system/key_value.bin'
    _, d = save.unpack(name)
    d = bytearray(d)
    arrays, off = [], 0
    for _ in range(4):
        count, size = struct.unpack_from('<QQ', d, off)
        arrays.append((count, off + 16))
        off += 16 + size
    (ne, oe), (nk, ok), (_, oh), (_, ov) = arrays
    ents = struct.unpack_from(f'<{ne}H', d, oe)
    per = struct.unpack_from(f'<{nk}Q', d, ok)
    key = wc_hash_string('KV_GOLD_MAX')
    changed, delta, i = [], 0, 0
    for e, c in zip(ents, per):
        if names[e].startswith(prefix):
            for j in range(i, i + c):
                if struct.unpack_from('<Q', d, oh + 8 * j)[0] == key:
                    kind, old = struct.unpack_from('<QQ', d, ov + 16 * j)
                    assert kind == 0x10003, hex(kind)
                    struct.pack_into('<Q', d, ov + 16 * j + 8, copper)
                    changed.append((e, old))
                    delta += copper - old
        i += c
    save.repack(name, bytes(d))
    name = 'vault_system/data.bin'
    _, v = save.unpack(name)
    v = bytearray(v)
    cap_off = 16 + struct.unpack_from('<Q', v, 8)[0] + 16
    coin, cap = struct.unpack_from('<QQ', v, cap_off - 8)
    assert cap + delta > coin, 'coin would exceed the new capacity'
    struct.pack_into('<Q', v, cap_off, cap + delta)
    save.repack(name, bytes(v))
    return changed, cap, cap + delta


HAUL_SOURCE_TAKE_FROM_GROUND = 1
HAUL_DESTINATION_STORAGE = 2


def enable_ground_pickup(save):
    """Turn on "take from ground" for every storage. haul_system/data.bin starts with
    u64 6, u64 n, n bytes, u64 count, then count 22-byte destination records:
    u16 entity, u8 destination type mask, ..., u8 haul source mask at +13 (new general
    storages get 0x04, take from overworld only; see haul_system_create_components)."""
    name = 'haul_system/data.bin'
    _, data = save.unpack(name)
    d = bytearray(data)
    n = struct.unpack_from('<Q', d, 8)[0]
    o = 16 + n
    count = struct.unpack_from('<Q', d, o)[0]
    o += 8
    changed = []
    for i in range(count):
        r = o + 22 * i
        ent, kind = struct.unpack_from('<HB', d, r)
        if kind & HAUL_DESTINATION_STORAGE and not d[r + 13] & HAUL_SOURCE_TAKE_FROM_GROUND:
            assert d[r + 13] != 0xff, f'entity {ent}: unexpected source mask'
            d[r + 13] |= HAUL_SOURCE_TAKE_FROM_GROUND
            changed.append(ent)
    save.repack(name, bytes(d))
    return changed


def main(argv):
    cmd, path = argv[0], argv[1]
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(SAVE_DIR, path if path.endswith('.save') else path + '.2.save')
    save = Save(path)
    if cmd == 'list':
        for e in save.entries:
            print(f"{e['size']:>9} {e['flags']:>3} {e['name']}")
    elif cmd == 'affluence':
        out = argv[2]
        percent = int(argv[3]) if len(argv) > 3 else 10
        out_path = os.path.join(SAVE_DIR, out + '.2.save')
        assert not os.path.exists(out_path), f'{out_path} exists'
        old = set_affluence_target(save, percent)
        save.write(out_path)
        print(f'Affluence target {old}% -> {percent}%; wrote {out_path}')
    elif cmd == 'ground':
        out_path = os.path.join(SAVE_DIR, argv[2] + '.2.save')
        assert not os.path.exists(out_path), f'{out_path} exists'
        changed = enable_ground_pickup(save)
        save.write(out_path)
        print(f'take-from-ground enabled on {len(changed)} storages {changed}; wrote {out_path}')
    elif cmd == 'vaultcap':
        out_path = os.path.join(SAVE_DIR, argv[2] + '.2.save')
        assert not os.path.exists(out_path), f'{out_path} exists'
        gold = int(argv[3]) if len(argv) > 3 else 2000
        changed, old, new = set_vault_capacity(save, 'building/vault_large[', gold * 10_000)
        save.write(out_path)
        print(f'Large Vaults {changed} -> {gold} gold; total capacity {old} -> {new} copper; wrote {out_path}')


if __name__ == '__main__':
    main(sys.argv[1:])
