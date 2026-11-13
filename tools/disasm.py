"""Disassemble a function of game.x86_64.dll by name (or .text offset), annotating call
targets with PDB public symbols and .rdata string references.

usage: disasm.py <symbol-or-offset> [bytes]
"""
import bisect
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GAME = os.path.expanduser('~/.local/share/Steam/steamapps/common/Hammerting/game.x86_64.dll')
OBJDUMP = os.path.expanduser('~/.local/share/hammerting-tools/llvm/usr/lib/llvm-21/bin/llvm-objdump')
BASE, TEXT = 0x180000000, 0x180001000

syms = []
for line in open(os.path.join(ROOT, 're/pdb/text_syms.tsv')):
    a, n = line.rstrip('\n').split('\t')
    syms.append((int(a), n))
# Static functions from tools/pdbmod.py dumps (address, size, name).
MOD_SYMS = os.path.join(ROOT, 're/pdb/mod_syms')
for fn in sorted(os.listdir(MOD_SYMS)) if os.path.isdir(MOD_SYMS) else []:
    for line in open(os.path.join(MOD_SYMS, fn)):
        a, _, n = line.rstrip('\n').split('\t', 2)
        syms.append((int(a), n))
syms.sort()
addrs = [a for a, _ in syms]
by_name = {n: a for a, n in syms}

dll = open(GAME, 'rb').read()
pe = struct.unpack_from('<I', dll, 0x3c)[0]
nsec = struct.unpack_from('<H', dll, pe + 6)[0]
opt = struct.unpack_from('<H', dll, pe + 20)[0]
sections = []
for i in range(nsec):
    o = pe + 24 + opt + 40 * i
    vsize, rva, rawsize, rawptr = struct.unpack_from('<IIII', dll, o + 8)
    sections.append((rva, vsize, rawptr))


def read_cstr(va):
    rva = va - BASE
    for s_rva, vsize, rawptr in sections:
        if s_rva <= rva < s_rva + vsize:
            off = rawptr + rva - s_rva
            end = dll.find(b'\0', off, off + 300)
            s = dll[off:end]
            if len(s) >= 3 and all(32 <= c < 127 for c in s):
                return s.decode()
    return None


def name_at(text_off):
    i = bisect.bisect_right(addrs, text_off) - 1
    if i < 0:
        return None
    a, n = syms[i]
    return n if a == text_off else f'{n}+{text_off - a:#x}'


def main():
    target = sys.argv[1]
    start = int(target) if target.isdigit() else by_name[target]
    i = bisect.bisect_right(addrs, start)
    length = int(sys.argv[2]) if len(sys.argv) > 2 else (addrs[i] - start if i < len(addrs) else 4096)
    out = subprocess.run([OBJDUMP, '-d', '--no-show-raw-insn', f'--start-address={TEXT + start:#x}',
                          f'--stop-address={TEXT + start + length:#x}', GAME],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r'(call|jmp)\s+0x([0-9a-f]+)', line)
        if m:
            t = int(m.group(2), 16) - TEXT
            n = name_at(t)
            if n:
                line += f'    ; {n}'
        m = re.search(r'# 0x([0-9a-f]+)', line)
        if m:
            s = read_cstr(int(m.group(1), 16))
            if s:
                line += f'    ; "{s}"'
        print(line)


if __name__ == '__main__':
    main()
