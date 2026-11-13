"""Compiled eval-chain blobs, as embedded in .loc entries and .entity files.

Blob layout:
  u64  MetroHash64 of the source text
  u8   token count, u8 string count, u16 string pool size
  tokens: [u8, u8, u16] header + u32 property id, where the id is
          uppercasehash(PROPERTY_NAME) from core/hash.h
  string pool: the source text, then any string literals, each NUL-terminated
"""
import struct

from wchash import wc_hash_string


def uppercasehash(name):
    h = 0
    for c in reversed(name):
        h = (h * 29 + ((ord(c) - ord('A')) & 0xff)) & 0xffffffff
    return h


def retarget(blob, old_src, new_src, renames):
    """Copy a compiled blob whose source is old_src into one for new_src, where
    new_src differs only by the property names in renames ({old: new})."""
    b = bytearray(blob)
    for old, new in renames.items():
        o, n = struct.pack('<I', uppercasehash(old)), struct.pack('<I', uppercasehash(new))
        assert b.count(o) == 1, f'{old} token not found exactly once'
        b[b.index(o):b.index(o) + 4] = n
    i = b.index(old_src.encode() + b'\0')
    b[i:i + len(old_src)] = new_src.encode()
    ntok, nstr, pool = struct.unpack_from('<BBH', b, 8)
    struct.pack_into('<BBH', b, 8, ntok, nstr, pool + len(new_src) - len(old_src))
    struct.pack_into('<Q', b, 0, wc_hash_string(new_src))
    return bytes(b)


def _parse_chain(s, i):
    """Parse NAME(args).NAME... or 'literal'.NAME... at s[i:]; returns (segments, next i).
    A segment is (name, [argument chains]) or (None, literal text)."""
    def skip(i):
        while i < len(s) and s[i].isspace():
            i += 1
        return i
    segs = []
    i = skip(i)
    while True:
        if s[i] in '\'"':
            j = s.index(s[i], i + 1)
            segs.append((None, s[i + 1:j]))
            i = j + 1
        else:
            j = i
            while j < len(s) and (s[j].isalnum() or s[j] == '_'):
                j += 1
            name, i = s[i:j], skip(j)
            args = []
            if i < len(s) and s[i] == '(':
                i = skip(i + 1)
                while s[i] != ')':
                    a, i = _parse_chain(s, i)
                    args.append(a)
                    i = skip(i)
                    if s[i] == ',':
                        i = skip(i + 1)
                i += 1
            segs.append((name, args))
        i = skip(i)
        if i < len(s) and s[i] == '.':
            i = skip(i + 1)
            continue
        return segs, i


def compile_chain(source):
    """Compile eval-chain source into a blob, in the format described at the top of this file.
    Arguments come before the chain that uses them; a token's u16 is its offset in the argument
    table (nargs, then the index of each argument's last token), and offset 0 means no arguments."""
    segs, end = _parse_chain(source, 0)
    assert not source[end:].strip(), source[end:]
    pool = source.encode() + b'\0'
    tokens, table = [], bytearray(b'\0')

    def emit(chain):
        for k, (name, arg) in enumerate(chain):
            if name is None:
                continue
            arg_at = []
            for a in arg:
                arg_at.append(emit(a))
            arg_off = 0
            if arg_at:
                arg_off = len(table)
                table.extend([len(arg_at), *arg_at])
            arg.clear()
            arg.extend(arg_at)
            chain[k] = (name, arg, arg_off)
        last = None
        for k, seg in enumerate(chain):
            if seg[0] is None:
                nonlocal pool
                tokens.append(struct.pack('<BBHI', 2, 1, len(pool), 0))
                pool += seg[1].encode() + b'\0'
            else:
                tokens.append(struct.pack('<BBHI', 1, 1 if k == 0 else 0, seg[2], uppercasehash(seg[0])))
            last = len(tokens) - 1
        return last

    emit(segs)
    return (struct.pack('<QBBH', wc_hash_string(source), len(tokens), len(table), len(pool))
            + b''.join(tokens) + pool + bytes(table))
