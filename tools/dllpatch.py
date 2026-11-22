#!/usr/bin/env python3
"""Byte patches to the game's DLLs, for fixes that live in code rather than data.

DLLS lists the DLLs that can be patched ('game' = game.x86_64.dll, 'entity' =
entity.x86_64.dll, 'graph' = graph.x86_64.dll, the path search). Patches always start from the pristine 1.2.39 DLL, which is backed up
next to it as <name>.hmod-orig the first time anything is patched. Each patch names the
bytes it expects to find, so a patch written for another build fails instead of corrupting
it. Steam's "Verify integrity of game files" also restores the originals.

game.x86_64.dll patches apply to the original plus one appended, zero-filled executable
section, .hmod (CAVE_VA, CAVE_SIZE bytes), where mods put code caves; its old bytes are
zeros. CAVE_BSS more bytes follow in memory only, for mod data that starts at zero. All three DLLs have image base 0x180000000, so a VA alone does not say which DLL.

usage:
  dllpatch.py status
  dllpatch.py restore        put the original DLLs back
"""
import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wkz  # noqa: E402

GAME_DIR = os.path.dirname(wkz.GAME_WKZ)
DLLS = {  # name: (file, sha256 of the 1.2.39 original)
    'game': ('game.x86_64.dll', 'c23c1881948916ec861f997a57817e01ecd1c1fed9501989e0b13b259811676e'),
    'entity': ('entity.x86_64.dll', 'c00be66fa907f78ac5b237bfaa49b7a16f30d7f0ca2559ecba67a9ec99e0a260'),
    'graph': ('graph.x86_64.dll', 'd0f198f5f267739747b9b00d03a97e098b2af32536583bc5cee46f73a0a23ab1'),
}
GAME_DLL = os.path.join(GAME_DIR, 'game.x86_64.dll')
BACKUP = GAME_DLL + '.hmod-orig'
IMAGE_BASE = 0x180000000
CAVE_VA = 0x18060c000          # .hmod: the first page after the original image
CAVE_SIZE = 0x4000
CAVE_BSS = 0x10000             # after the file-backed part: stranded_rescue's per-entity counters


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def va_to_offset(dll, va):
    """File offset of a virtual address. Values below IMAGE_BASE are file offsets already
    (for header fields such as a section's VirtualSize)."""
    if va < IMAGE_BASE:
        return va
    pe = struct.unpack_from('<I', dll, 0x3c)[0]
    nsec = struct.unpack_from('<H', dll, pe + 6)[0]
    opt = struct.unpack_from('<H', dll, pe + 20)[0]
    rva = va - IMAGE_BASE
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vsize, s_rva, rawsize, rawptr = struct.unpack_from('<IIII', dll, o + 8)
        # The raw size bounds what is in the file; it may exceed the virtual size (slack
        # at the end of .text that code caves use once the section is grown to cover it).
        if s_rva <= rva < s_rva + rawsize:
            return rawptr + rva - s_rva
    raise ValueError(f'{va:#x} is not in a file-backed section')


def path(dll='game'):
    return os.path.join(GAME_DIR, DLLS[dll][0])


def backup(dll='game'):
    return path(dll) + '.hmod-orig'


def pristine(dll='game'):
    """The original DLL's bytes, backing it up first if it is still in place."""
    want = DLLS[dll][1]
    if os.path.exists(backup(dll)):
        data = open(backup(dll), 'rb').read()
        assert sha256(data) == want, f'{backup(dll)} is not the 1.2.39 DLL'
        return data
    data = open(path(dll), 'rb').read()
    assert sha256(data) == want, \
        f'{path(dll)} is not the pristine 1.2.39 DLL and there is no backup; verify the game files in Steam'
    shutil.copy2(path(dll), backup(dll))
    return data


def with_cave_section(dll):
    """dll with the empty .hmod section appended (code, execute, read)."""
    d = bytearray(dll)
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = struct.unpack_from('<H', d, pe + 20)[0]
    hdr = pe + 24 + opt + 40 * nsec
    first_raw = min(struct.unpack_from('<I', d, pe + 24 + opt + 40 * i + 20)[0] for i in range(nsec))
    assert hdr + 40 <= first_raw and not any(d[hdr:hdr + 40]), 'no room for another section header'
    size_of_image = struct.unpack_from('<I', d, pe + 24 + 56)[0]
    assert size_of_image == CAVE_VA - IMAGE_BASE, 'unexpected image layout'
    assert len(d) % 0x200 == 0
    d[hdr:hdr + 40] = struct.pack('<8sIIIIIIHHI', b'.hmod', CAVE_SIZE + CAVE_BSS, CAVE_VA - IMAGE_BASE,
                                  CAVE_SIZE, len(d), 0, 0, 0, 0, 0xe0000020)  # code, read, execute, write
    struct.pack_into('<H', d, pe + 6, nsec + 1)
    struct.pack_into('<I', d, pe + 24 + 56, size_of_image + CAVE_SIZE + CAVE_BSS)
    return bytes(d) + bytes(CAVE_SIZE)


def _replace(dll, data):
    tmp = path(dll) + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    shutil.copymode(backup(dll), tmp)
    os.replace(tmp, path(dll))


def apply(patches, dll='game'):
    """patches: list of (va, old_bytes, new_bytes, note). Writes the patched DLL."""
    data = bytearray(pristine(dll))
    if dll == 'game':
        data = bytearray(with_cave_section(data))
    for va, old, new, note in patches:
        assert len(old) == len(new), note
        off = va_to_offset(data, va)
        found = bytes(data[off:off + len(old)])
        assert found == old, f'{note}: expected {old.hex()} at {va:#x}, found {found.hex()}'
        data[off:off + len(new)] = new
    _replace(dll, bytes(data))


def restore(dll='game'):
    if os.path.exists(backup(dll)):
        _replace(dll, pristine(dll))


def section_header(dll, name):
    """(file offset of the section header, virtual size, rva, raw size, raw pointer)."""
    pe = struct.unpack_from('<I', dll, 0x3c)[0]
    nsec = struct.unpack_from('<H', dll, pe + 6)[0]
    opt = struct.unpack_from('<H', dll, pe + 20)[0]
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        if dll[o:o + 8].rstrip(b'\0') == name.encode():
            return (o,) + struct.unpack_from('<IIII', dll, o + 8)
    raise KeyError(name)


def original(dll='game'):
    """The original DLL's bytes without touching the game folder."""
    return open(backup(dll) if os.path.exists(backup(dll)) else path(dll), 'rb').read()


def base(dll='game'):
    """What patches apply to: the original DLL (game: with the empty .hmod section)."""
    return with_cave_section(original(dll)) if dll == 'game' else original(dll)


def is_patched(dll='game'):
    return sha256(open(path(dll), 'rb').read()) != DLLS[dll][1]


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    for name in DLLS:
        if cmd == 'restore':
            restore(name)
        print('patched' if is_patched(name) else 'original', path(name))
