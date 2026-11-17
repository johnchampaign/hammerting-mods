"""Read and write .entity files (UI windows, buttons and other spawnable entities).

A file with one record is that record. A file with more starts with u16 record count, u16 total
component count, u32 file size and zeros to 0x90, then the records. A record is u16 1, u16
component count, u32 record size, 0x88 bytes (usually zero; kept as they are), a table of
(u64 key, u64 offset from the record start) per component, then the components in table order.
A key is the component's byte size << 16 | its 16-bit type, so a component that changes size
changes its key. Checked against all 1,070 entity files in game.wkz.

Component types used by mods:
  0x71ed  u16 index of the parent record
  0x7895  record name (LABEL__...), NUL-terminated
  0x005f  id: wc_tag (char[0x38], u64 wc_hash), looked up by CHILD_WITH_ID and friends
  0x8126  trigger: u64 trigger hash, 16 zero bytes, u64 flags, u64 n, then n bytes: either
          chain_blob() and the source (an action), or a wc_tag event name to send
  0x795d  plain text: u64, u64, u64 text size, then the text and its NUL
  0xb903  text with chains: u64, u64, u64 text size, text and NUL, chain_blob() for
          each %Oproperty_comp, then the source text with the chains written in (`$O` after each)
  0xef05  localized label: u64, u64 2, u64 wc_hash(key), u64 key size, key and NUL
All three start with the same two u64s: the font (a hash), then u32 flags and a float wrap width.

A long text in the player's language is a label (localized_label): a 20 KB one shows in full and scrolls.
A chain's value ('KEY'.LOCALIZE in a 0xb903) is cut off after 4,096 bytes, six such chains in one text
crashed the game, and 18 KB of literal text around one ran it out of memory.

usage: entity.py <file.entity>    lists records, their parents and component types
"""
import struct
import sys

from evalchain import compile_chain
from wchash import wc_hash_string

PARENT, NAME, ID, ACTION, TEXT, CHAIN_TEXT, LABEL = 0x71ed, 0x7895, 0x005f, 0x8126, 0x795d, 0xb903, 0xef05
HEADER = 0x90


class Record:
    def __init__(self, comps, pad=bytes(HEADER - 8)):
        self.comps = [[t, bytes(b)] for t, b in comps]      # [type, data] in table order
        self.pad = pad

    @classmethod
    def parse(cls, d, o):
        one, count, size = struct.unpack_from('<HHI', d, o)
        assert one == 1
        table = [struct.unpack_from('<QQ', d, o + HEADER + 16 * k) for k in range(count)]
        ends = [off for _, off in table[1:]] + [size]
        comps = []
        for (key, off), end in zip(table, ends):
            assert key >> 16 == end - off, 'component size does not match its key'
            comps.append((key & 0xffff, d[o + off:o + end]))
        return cls(comps, d[o + 8:o + HEADER])

    def pack(self):
        off = HEADER + 16 * len(self.comps)
        table, body = b'', b''
        for t, b in self.comps:
            table += struct.pack('<QQ', len(b) << 16 | t, off)
            body += b
            off += len(b)
        return struct.pack('<HHI', 1, len(self.comps), off) + self.pad + table + body

    def find(self, t):
        """Indexes of the components of type t."""
        return [i for i, (ct, _) in enumerate(self.comps) if ct == t]

    def get(self, t):
        i, = self.find(t)
        return self.comps[i][1]

    def set(self, t, data):
        i, = self.find(t)
        self.comps[i][1] = bytes(data)

    @property
    def name(self):
        return self.get(NAME).rstrip(b'\0').decode()

    @property
    def parent(self):
        return struct.unpack('<H', self.get(PARENT))[0] if self.find(PARENT) else None

    @parent.setter
    def parent(self, i):
        self.set(PARENT, struct.pack('<H', i))

    def copy(self):
        return Record(self.comps, self.pad)


def parse(d):
    n, total, size = struct.unpack_from('<HHI', d, 0)
    assert size == len(d)
    if n == 1:
        return [Record.parse(d, 0)]
    assert d[8:HEADER] == bytes(HEADER - 8)
    recs, o = [], HEADER
    while o < len(d):
        recs.append(Record.parse(d, o))
        o += struct.unpack_from('<I', d, o + 4)[0]
    assert len(recs) == n and sum(len(r.comps) for r in recs) == total
    return recs


def pack(recs):
    if len(recs) == 1:
        return recs[0].pack()
    body = b''.join(r.pack() for r in recs)
    total = sum(len(r.comps) for r in recs)
    return struct.pack('<HHI', len(recs), total, HEADER + len(body)) + bytes(HEADER - 8) + body


def insert(recs, at, new):
    """Insert records at index `at`, keeping parent indexes pointing at the same records. Parent
    indexes inside `new` refer to the list after insertion."""
    for r in recs:
        p = r.parent
        if p is not None and p >= at:
            r.parent = p + len(new)
    recs[at:at] = new


def remove(recs, at):
    """Remove the record at index `at` (which must have no children), keeping the other parent
    indexes pointing at the same records."""
    assert all(r.parent != at for r in recs), 'record has children'
    del recs[at]
    for r in recs:
        p = r.parent
        if p is not None and p > at:
            r.parent = p - 1


def chain_blob(src):
    """A compiled chain as actions and texts store it: u8 1, u8 1, u16 0, u16 size, the compiled
    chain, then the source and its NUL (for texts the caller adds the source text instead)."""
    blob = compile_chain(src)
    return struct.pack('<BBHH', 1, 1, 0, len(blob)) + blob


def action(template, src):
    """An action component that runs src on the same trigger as template, an existing action
    component (its first 32 bytes: trigger hash, zeros, flags)."""
    body = chain_blob(src) + src.encode() + b'\0'
    return template[:32] + struct.pack('<Q', len(body)) + body


def action_source(data):
    _, _, _, size = struct.unpack_from('<BBHH', data, 40)
    return data[46 + size:].rstrip(b'\0').decode()


def tag(name):
    return name.encode().ljust(0x38, b'\0') + struct.pack('<Q', wc_hash_string(name))


def text(data):
    """The text of a TEXT component."""
    n, = struct.unpack_from('<Q', data, 16)
    return data[24:24 + n - 1].decode()


def set_text(data, new):
    b = new.encode() + b'\0'
    return data[:16] + struct.pack('<Q', len(b)) + b


def chain_text(data, src):
    """A CHAIN_TEXT component holding one %Oproperty_comp, rewritten to show the chain src."""
    head, n, n2 = struct.unpack_from('<QQQ', data, 0)
    assert n == n2 and data[24:24 + n] == b'%Oproperty_comp\0', data[24:24 + n]
    return data[:24 + n] + chain_blob(src) + (src + '$O').encode() + b'\0'


def localized_label(data, key):
    """A LABEL component in the font and wrap width of the TEXT component data (all three text
    components start with the same two u64s), showing the localized text of key."""
    b = key.encode() + b'\0'
    return data[:16] + struct.pack('<QQ', wc_hash_string(key), len(b)) + b


def label(data, key):
    """A LABEL component showing the localized text of key."""
    head, two = struct.unpack_from('<QQ', data, 0)
    b = key.encode() + b'\0'
    return struct.pack('<QQQQ', head, two, wc_hash_string(key), len(b)) + b


def main(path):
    recs = parse(open(path, 'rb').read())
    for i, r in enumerate(recs):
        name = r.name if r.find(NAME) else '?'
        types = ' '.join(f'{t:04x}:{len(b)}' for t, b in r.comps)
        print(f'{i:3} parent {r.parent}  {name:28} {types}')


if __name__ == '__main__':
    main(sys.argv[1])
