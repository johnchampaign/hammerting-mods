"""Read and write compiled .strtbl string tables: u64 count, u64 offsets[count], NUL-terminated strings."""
import struct
import sys


def read(path):
    d = open(path, 'rb').read()
    n = struct.unpack_from('<Q', d, 0)[0]
    offs = struct.unpack_from('<%dQ' % n, d, 8)
    base = 8 + 8 * n
    return [d[base + o:d.index(b'\0', base + o)].decode('utf-8') for o in offs]


def write(path, strings):
    blob, offs = b'', []
    for s in strings:
        offs.append(len(blob))
        blob += s.encode('utf-8') + b'\0'
    with open(path, 'wb') as f:
        f.write(struct.pack('<Q', len(strings)) + struct.pack('<%dQ' % len(offs), *offs) + blob)


if __name__ == '__main__':
    for s in read(sys.argv[1]):
        print(s)
