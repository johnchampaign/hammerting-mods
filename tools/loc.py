"""Read and write compiled .loc localization tables.

File layout (integers u64 little-endian):
  0x00 version (1)
  0x08 language, char[8] ("en-US")
  0x10 offset of key hashes      (keys are wc_hash of the key name: MetroHash64)
  0x18 offset of entry offsets   (absolute file offsets)
  0x20 offset of entry data
  0x28 entry count
  hashes[count] sorted ascending, offsets[count], then the entries.

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


class LocTable:
    def __init__(self, data):
        self.version, = struct.unpack_from('<Q', data, 0)
        self.lang = data[8:16].rstrip(b'\0').decode()
        hash_off, offs_off, _, count = struct.unpack_from('<4Q', data, 0x10)
        hashes = struct.unpack_from('<%dQ' % count, data, hash_off)
        offs = struct.unpack_from('<%dQ' % count, data, offs_off)
        self.entries = {h: Entry.parse(data, o) for h, o in zip(hashes, offs)}

    def key(self, name):
        from wchash import wc_hash_string
        return self.entries[wc_hash_string(name)]

    def set(self, name, entry):
        from wchash import wc_hash_string
        self.entries[wc_hash_string(name)] = entry

    def pack(self):
        hashes = sorted(self.entries)
        count = len(hashes)
        hash_off = 0x30
        offs_off = hash_off + 8 * count
        data_off = offs_off + 8 * count
        offs, blob = [], b''
        for h in hashes:
            offs.append(data_off + len(blob))
            blob += self.entries[h].pack()
        head = struct.pack('<Q', self.version) + self.lang.encode().ljust(8, b'\0')
        head += struct.pack('<4Q', hash_off, offs_off, data_off, count)
        return head + struct.pack('<%dQ' % count, *hashes) + struct.pack('<%dQ' % count, *offs) + blob


if __name__ == '__main__':
    t = LocTable(open(sys.argv[1], 'rb').read())
    needle = sys.argv[2].lower() if len(sys.argv) > 2 else ''
    for h, e in t.entries.items():
        if needle in e.text.lower():
            print(f'{h:016x}\t{len(e.blobs)}\t{e.text}')
