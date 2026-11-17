"""Read and write compiled .loc localization tables.

File layout (integers u64 little-endian):
  0x00 section count (1, or 2 in dubious_entries, items and modifier)
  then per section, 0x28 bytes from 0x08:
    language, char[8] ("en-US"; a second section is "any", entries shown in every language)
    offset of key hashes      (keys are wc_hash of the key name: MetroHash64)
    offset of entry offsets   (absolute file offsets)
    offset of entry data
    entry count
  every section's hashes[count] (sorted ascending) and offsets[count], then every section's entries.
A table written with one section but a count of 2 makes the game read the hash array as a second
section header, whose "language" then shows up in the Options language list (and crashed it).

Entry layout:
  u8 0, u32 nargs, u16 blob_end[nargs], blobs, UTF-8 text, NUL
Each blob is a compiled eval chain that fills the next %Oproperty_comp in the text
(see tools/evalchain.py).

usage: loc.py <file.loc> [substring]   prints "hash<TAB>nargs<TAB>text"
"""
import struct
import sys


class Entry:
    def __init__(self, text, blobs=()):
        self.text = text
        self.blobs = list(blobs)

    @classmethod
    def parse(cls, d, x):
        nargs, = struct.unpack_from('<I', d, x + 1)
        ends = struct.unpack_from('<%dH' % nargs, d, x + 5) if nargs else ()
        b0 = x + 5 + 2 * nargs
        blobs = [d[b0 + (ends[i - 1] if i else 0):b0 + ends[i]] for i in range(nargs)]
        t0 = b0 + (ends[-1] if nargs else 0)
        return cls(d[t0:d.index(b'\0', t0)].decode('utf-8'), blobs)

    def pack(self):
        ends, total = [], 0
        for b in self.blobs:
            total += len(b)
            ends.append(total)
        return (b'\0' + struct.pack('<I', len(self.blobs)) + struct.pack('<%dH' % len(ends), *ends)
                + b''.join(self.blobs) + self.text.encode('utf-8') + b'\0')


class Section:
    def __init__(self, lang, entries, order):
        self.lang = lang
        self.entries = entries      # key hash -> Entry
        self.order = order          # hashes in the order their data is stored


class LocTable:
    """A table's first section is its language (lang, entries, key, set); any others are kept as
    they are in sections[1:]."""

    def __init__(self, data):
        n, = struct.unpack_from('<Q', data, 0)
        self.sections = []
        for i in range(n):
            lang = data[8 + 0x28 * i:16 + 0x28 * i].rstrip(b'\0').decode()
            hash_off, offs_off, _, count = struct.unpack_from('<4Q', data, 16 + 0x28 * i)
            hashes = struct.unpack_from('<%dQ' % count, data, hash_off)
            offs = struct.unpack_from('<%dQ' % count, data, offs_off)
            entries = {h: Entry.parse(data, o) for h, o in zip(hashes, offs)}
            self.sections.append(Section(lang, entries, [h for _, h in sorted(zip(offs, hashes))]))

    @property
    def lang(self):
        return self.sections[0].lang

    @property
    def entries(self):
        return self.sections[0].entries

    def key(self, name):
        from wchash import wc_hash_string
        return self.entries[wc_hash_string(name)]

    def set(self, name, entry):
        from wchash import wc_hash_string
        self.entries[wc_hash_string(name)] = entry

    def pack(self):
        arrays = 8 + 0x28 * len(self.sections)
        heads, tables, blob = b'', b'', b''
        data_start = arrays + sum(16 * len(sec.entries) for sec in self.sections)
        for sec in self.sections:
            hashes = sorted(sec.entries)
            order = [h for h in sec.order if h in sec.entries] + [h for h in hashes if h not in set(sec.order)]
            data_off = data_start + len(blob)
            where = {}
            for h in order:
                where[h] = data_start + len(blob)
                blob += sec.entries[h].pack()
            hash_off = arrays + len(tables)
            tables += struct.pack('<%dQ' % len(hashes), *hashes)
            offs_off = arrays + len(tables)
            tables += struct.pack('<%dQ' % len(hashes), *(where[h] for h in hashes))
            heads += sec.lang.encode().ljust(8, b'\0') + struct.pack('<4Q', hash_off, offs_off, data_off, len(hashes))
        return struct.pack('<Q', len(self.sections)) + heads + tables + blob


if __name__ == '__main__':
    t = LocTable(open(sys.argv[1], 'rb').read())
    needle = sys.argv[2].lower() if len(sys.argv) > 2 else ''
    for h, e in t.entries.items():
        if needle in e.text.lower():
            print(f'{h:016x}\t{len(e.blobs)}\t{e.text}')
