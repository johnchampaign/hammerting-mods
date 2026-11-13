"""Read Hammerting .wkz archives (format WKZ10, uncompressed, memory-mapped by the game).

Header (0x30 bytes):
  0x00 magic b'WKZ10\\0\\0\\0'
  0x08 u64 unknown (0x0079_0072_0040_0000)
  0x10 u64 archive size
  0x18 u64 offset of hash index
  0x20 u64 offset of trailing table
  0x28 u64 unknown
Then file entries of 0x38 bytes each from 0x30:
  name_off, unk, name_hash, flags, content_hash, size, data_off  (all u64)
Names are NUL-terminated strings in a table at the first entry's name_off.
"""
import mmap
import os
import struct
import sys

ENTRY = struct.Struct('<7Q')


def open_archive(path):
    f = open(path, 'rb')
    m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    assert m[:5] == b'WKZ10', 'not a WKZ10 archive'
    return m


def entries(m):
    first_name = struct.unpack_from('<Q', m, 0x30)[0]
    off = 0x30
    while off + ENTRY.size <= first_name:
        name_off, unk, name_hash, flags, chash, size, data_off = ENTRY.unpack_from(m, off)
        if not (first_name <= name_off < len(m)):
            break
        end = m.find(b'\0', name_off)
        yield dict(name=m[name_off:end].decode('utf-8', 'replace'), unk=unk, name_hash=name_hash,
                   flags=flags, content_hash=chash, offset=data_off, size=size, entry_off=off)
        off += ENTRY.size


def find_game_dir():
    """The Hammerting install folder: $HAMMERTING_DIR if set, else the first Steam library
    (from each Steam root's steamapps/libraryfolders.vdf) holding steamapps/common/Hammerting."""
    if os.environ.get('HAMMERTING_DIR'):
        return os.environ['HAMMERTING_DIR']
    roots = [os.path.expanduser(p) for p in (
        '~/.local/share/Steam', '~/.steam/steam', '~/.var/app/com.valvesoftware.Steam/.local/share/Steam')]
    roots += [r'C:\Program Files (x86)\Steam', r'C:\Program Files\Steam']
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            roots.insert(0, winreg.QueryValueEx(k, 'SteamPath')[0])
    except (ImportError, OSError):
        pass
    libraries = []
    for root in roots:
        libraries.append(root)
        try:
            with open(os.path.join(root, 'steamapps', 'libraryfolders.vdf'), encoding='utf-8') as f:
                for line in f:
                    parts = line.split('"')
                    if len(parts) >= 4 and parts[1] == 'path':
                        libraries.append(parts[3].replace('\\\\', '\\'))
        except OSError:
            pass
    for lib in libraries:
        d = os.path.join(lib, 'steamapps', 'common', 'Hammerting')
        if os.path.exists(os.path.join(d, 'game.wkz')):
            return d
    return os.path.join(roots[0], 'steamapps', 'common', 'Hammerting')


GAME_WKZ = os.path.join(find_game_dir(), 'game.wkz')
_type_by_suffix = None


def type_for(name):
    """File type code, taken from how game.wkz types files with the same suffix."""
    global _type_by_suffix
    if _type_by_suffix is None:
        _type_by_suffix = {}
        for e in entries(open_archive(GAME_WKZ)):
            base = e['name'].rsplit('/', 1)[-1]
            parts = base.split('.')
            for i in range(1, len(parts)):
                _type_by_suffix.setdefault('.' + '.'.join(parts[i:]), e['flags'])
    base = name.rsplit('/', 1)[-1]
    parts = base.split('.')
    for i in range(1, len(parts)):
        t = _type_by_suffix.get('.' + '.'.join(parts[i:]))
        if t is not None:
            return t
    return 2


def _hashmap(pairs, capacity):
    """Bucketed hash map: 4 slots per bucket, bucket = hash % (capacity/4), home slot hash & 3."""
    buckets = capacity // 4
    slots = [(0, 0)] * capacity
    for h, v in pairs:
        b = (h % buckets) * 4
        for p in [h & 3] + [i for i in range(4) if i != h & 3]:
            if slots[b + p] == (0, 0):
                slots[b + p] = (h, v)
                break
        else:
            raise ValueError('bucket full; raise capacity')
    return struct.pack('<2Q', len(pairs), capacity) + b''.join(struct.pack('<2Q', *s) for s in slots)


def _capacity(n):
    return max(40, (n * 16 + 3) // 4 * 4)


def write(path, files, filetime=0, types=None):
    """files: list of (archive_name, bytes). Writes a WKZ10 archive with an all.fileinfo.
    types: optional {name: type}; other files are typed by suffix as in game.wkz."""
    from wchash import metrohash64
    files = sorted(files)
    info = sorted((metrohash64(n.encode()), filetime, metrohash64(d)) for n, d in files)
    files.append(('all.fileinfo', b''.join(struct.pack('<3Q', *i) for i in info)))
    given = types or {}
    types = [given.get(n, type_for(n)) if n != 'all.fileinfo' else 2 for n, _ in files]
    ntypes = max(types) + 1
    data_off = 0x30 + ENTRY.size * len(files)
    offsets, blob = [], b''
    for _, d in files:
        offsets.append(data_off + len(blob))
        blob += d
    names_off = data_off + len(blob)
    name_offsets, names = [], b''
    for n, _ in files:
        name_offsets.append(names_off + len(names))
        names += n.encode() + b'\0'
    filemap_off = names_off + len(names)
    entry_off = [0x30 + ENTRY.size * i for i in range(len(files))]
    hashes = [metrohash64(n.encode()) for n, _ in files]
    filemap = _hashmap(list(zip(hashes, entry_off)), _capacity(len(files)))
    # Directory tables: every directory lists all files beneath it, grouped by type,
    # each group sorted by name hash.
    dirs = {}
    for i, (n, _) in enumerate(files):
        parts = n.split('/')[:-1]
        for k in range(len(parts) + 1):
            dirs.setdefault('/'.join(parts[:k]) + ('/' if k else ''), []).append(i)
    pos = filemap_off + len(filemap)
    dir_tables, dir_pairs = b'', []
    for d in sorted(dirs, key=lambda s: (s.count('/'), s)):
        table_off = pos + len(dir_tables)
        dir_pairs.append((metrohash64(d.encode()), table_off))
        lists, slots = b'', []
        list_base = table_off + 16 * ntypes
        for t in range(ntypes):
            members = sorted((hashes[i], entry_off[i]) for i in dirs[d] if types[i] == t)
            if members:
                slots.append(struct.pack('<2Q', len(members), list_base + len(lists)))
                lists += b''.join(struct.pack('<2Q', *m) for m in members)
            else:
                slots.append(struct.pack('<2Q', 0, (1 << 64) - 1))
        dir_tables += b''.join(slots) + lists
    dirmap_off = pos + len(dir_tables)
    dirmap = _hashmap(dir_pairs, _capacity(len(dir_pairs)))
    size = dirmap_off + len(dirmap)
    out = b'WKZ10\0\0\0' + struct.pack('<5Q', 0x400000, size, filemap_off, dirmap_off, ntypes)
    for i, (n, d) in enumerate(files):
        out += ENTRY.pack(name_offsets[i], 0, hashes[i], types[i], metrohash64(d), len(d), offsets[i])
    out += blob + names + filemap + dir_tables + dirmap
    assert len(out) == size
    with open(path, 'wb') as f:
        f.write(out)


def main():
    m = open_archive(sys.argv[1])
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'list'
    if cmd == 'list':
        for e in entries(m):
            print(f"{e['offset']:>12} {e['size']:>10} {e['flags']:>3} {e['unk']:>4} {e['name']}")
    elif cmd == 'cat':
        for e in entries(m):
            if e['name'] == sys.argv[3]:
                sys.stdout.buffer.write(m[e['offset']:e['offset'] + e['size']])
                return
        sys.exit('not found')
    elif cmd == 'extract':
        import os
        out = sys.argv[3]
        pattern = sys.argv[4] if len(sys.argv) > 4 else ''
        for e in entries(m):
            if pattern not in e['name']:
                continue
            dst = os.path.join(out, e['name'])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as o:
                o.write(m[e['offset']:e['offset'] + e['size']])


if __name__ == '__main__':
    main()
