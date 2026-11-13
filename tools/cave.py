"""Assemble code caves for DLL-patch mods (see mods/eat_reserved_food for an example).

A cave source is Intel-syntax x86-64 for llvm-mc. Absolute addresses come in as
--defsym symbols, and BASE is the cave's own address. llvm-mc will not take label
arithmetic inside a memory operand, so RIP-relative operands and calls are written as
opcode bytes plus `.long TARGET - BASE - (label - start)`, where `start` is the first
label and `label` follows the instruction.
"""
import hashlib
import json
import os
import struct
import subprocess
import tempfile

LLVM = os.path.expanduser('~/.local/share/hammerting-tools/llvm/usr/lib/llvm-21/bin')
# Assembled caves, keyed by source and symbols, so installing needs no llvm-mc.
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cave_cache')


def coff_text(o):
    """Raw bytes of the .text section of a COFF object."""
    nsec, = struct.unpack_from('<H', o, 2)
    opt, = struct.unpack_from('<H', o, 16)
    for i in range(nsec):
        h = 20 + opt + 40 * i
        if o[h:h + 8].rstrip(b'\0') == b'.text':
            size, ptr = struct.unpack_from('<II', o, h + 16)
            return o[ptr:ptr + size]
    raise KeyError('.text')


def assemble(source, symbols):
    """(code bytes up to the label `end`, {label: offset}) for an llvm-mc source file.
    Results are kept in tools/cave_cache; without llvm-mc, only cached caves can be built."""
    with open(source, 'rb') as f:
        text = f.read().replace(b'\r\n', b'\n')     # a Windows checkout may have CRLF
    key = hashlib.sha256(text + repr(sorted(symbols.items())).encode()).hexdigest()
    cached = os.path.join(CACHE, key[:32] + '.json')
    if not os.path.exists(os.path.join(LLVM, 'llvm-mc')):
        if not os.path.exists(cached):
            raise SystemExit(f'{source}: no cached build for these settings, and assembling it needs '
                             f'llvm-mc in {LLVM}')
        with open(cached) as f:
            c = json.load(f)
        return bytes.fromhex(c['code']), c['labels']
    code, labels = _assemble(source, symbols)
    os.makedirs(CACHE, exist_ok=True)
    with open(cached, 'w') as f:
        json.dump({'source': os.path.relpath(source, os.path.dirname(CACHE)).replace(os.sep, '/'),
                   'code': code.hex(), 'labels': labels}, f, sort_keys=True)
    return code, labels


def _assemble(source, symbols):
    with tempfile.TemporaryDirectory() as tmp:
        obj = os.path.join(tmp, 'cave.o')
        args = [f'--defsym={k}={v:#x}' for k, v in symbols.items()]
        subprocess.run([os.path.join(LLVM, 'llvm-mc'), '-triple=x86_64-pc-windows-msvc',
                        '-filetype=obj', *args, source, '-o', obj], check=True)
        nm = subprocess.run([os.path.join(LLVM, 'llvm-nm'), obj], capture_output=True, text=True,
                            check=True).stdout
        labels = {n: int(a, 16) for a, _, n in (line.split() for line in nm.splitlines())}
        code = coff_text(open(obj, 'rb').read())[:labels['end']]
        # Every target is resolved to a constant; a relocation would mean a wrong address.
        relocs = subprocess.run([os.path.join(LLVM, 'llvm-objdump'), '-r', obj], capture_output=True,
                                text=True, check=True).stdout
        assert 'RELOCATION RECORDS' not in relocs, relocs
    return code, labels


def call(site, target):
    """A 5-byte `call rel32` at site."""
    return b'\xe8' + struct.pack('<i', target - (site + 5))
