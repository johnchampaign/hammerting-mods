#!/usr/bin/env python3
"""Dump the functions of PDB modules (including static ones, which the publics lack) into
re/pdb/mod_syms/<modi>.tsv, which tools/disasm.py also reads.

Module indexes are listed in re/pdb/game_modules.txt (llvm-pdbutil dump -modules).

usage: pdbmod.py <modi> [<modi> ...]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDBUTIL = os.path.expanduser('~/.local/share/hammerting-tools/llvm/usr/lib/llvm-21/bin/llvm-pdbutil')
PDB = os.path.expanduser('~/.local/share/Steam/steamapps/common/Hammerting/game.x86_64.dll.pdb')
OUT = os.path.join(ROOT, 're/pdb/mod_syms')

PROC = re.compile(r'S_[GL]PROC32 \[size = \d+\] `(.*)`\n\s+parent = \d+, end = \d+, '
                  r'addr = 0001:(\d+), code size = (\d+)')


def dump(modi):
    text = subprocess.run([PDBUTIL, 'dump', '-symbols', f'-modi={modi}', PDB],
                          capture_output=True, text=True, check=True).stdout
    rows = sorted({(int(a), int(n), name) for name, a, n in PROC.findall(text)})
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f'{modi:04d}.tsv'), 'w') as f:
        for a, n, name in rows:
            f.write(f'{a}\t{n}\t{name}\n')
    return len(rows)


if __name__ == '__main__':
    for m in sys.argv[1:]:
        print(m, dump(int(m)))
