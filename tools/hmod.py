#!/usr/bin/env python3
"""Build Hammerting mods into one override archive.

Each mod is mods/<name>/mod.py with DESCRIPTION and apply(ctx). Mods patch the game's own
files (read from game.wkz) through ctx, so several mods can change the same file. The
result is one archive that the game loads with --game-extra-archives.

usage:
  hmod.py list
  hmod.py build <mod> [<mod> ...] [-o out.wkz]
  hmod.py install recommended         install the mods listed in mods/recommended.txt
  hmod.py install <mod> [<mod> ...]   build, then copy to <game>/danger_zone/hammerting_mods.wkz
                                      and apply the mods' DLL patches (or undo old ones)
  hmod.py uninstall                   remove the archive and restore the original DLL
"""
import importlib.util
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dllpatch  # noqa: E402
import wkz  # noqa: E402
from loc import LocTable  # noqa: E402

ROOT = os.path.dirname(HERE)
GAME_DIR = os.path.dirname(wkz.GAME_WKZ)
ARCHIVE_NAME = 'hammerting_mods.wkz'


class Context:
    def __init__(self):
        self._game = wkz.open_archive(wkz.GAME_WKZ)
        self._index = {e['name']: e for e in wkz.entries(self._game)}
        self.files = {}
        self._locs = {}
        self.dll_patches = []
        self.mods = []              # names of the mods being built, in order

    def read(self, name):
        if name in self.files:
            return self.files[name]
        e = self._index[name]
        return bytes(self._game[e['offset']:e['offset'] + e['size']])

    def write(self, name, data):
        self.files[name] = bytes(data)

    def loc(self, name):
        """A localization table, e.g. ctx.loc('cave'); saved automatically."""
        if name not in self._locs:
            self._locs[name] = LocTable(self.read(f'localization/{name}.loc'))
        return self._locs[name]

    def replace_cstr(self, name, old, new, count=1):
        """Replace a NUL-terminated string stored in a fixed, zero-padded buffer."""
        d = bytearray(self.read(name))
        old_b, new_b = old.encode(), new.encode()
        found = 0
        i = d.find(old_b + b'\0')
        while i >= 0:
            end = i + len(old_b)
            while end < len(d) and d[end] == 0:
                end += 1
            # The buffer runs at least to the end of the zero padding; keep one NUL.
            assert len(new_b) < end - i, f'{new!r} does not fit the buffer in {name}'
            d[i:end] = new_b + b'\0' * (end - i - len(new_b))
            found += 1
            i = d.find(old_b + b'\0', end)
        assert found == count, f'expected {count} of {old!r} in {name}, found {found}'
        self.write(name, d)

    def patch_dll(self, va, old, new, note, dll='game'):
        """Replace bytes at virtual address va in game.x86_64.dll, or in another DLL named
        in dllpatch.DLLS (see tools/dllpatch.py)."""
        self.dll_patches.append((dll, va, bytes(old), bytes(new), note))

    def dll_patches_for(self, dll):
        return [(va, old, new, note) for d, va, old, new, note in self.dll_patches if d == dll]

    def finish(self):
        for name, table in self._locs.items():
            self.write(f'localization/{name}.loc', table.pack())


def load_mod(name):
    path = os.path.join(ROOT, 'mods', name, 'mod.py')
    spec = importlib.util.spec_from_file_location(f'hmod_{name}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def available():
    return sorted(d for d in os.listdir(os.path.join(ROOT, 'mods'))
                  if os.path.exists(os.path.join(ROOT, 'mods', d, 'mod.py')))


def expand(names):
    """Names with `recommended` replaced by the list in mods/recommended.txt."""
    out = []
    for n in names:
        if n == 'recommended':
            with open(os.path.join(ROOT, 'mods', 'recommended.txt')) as f:
                out += [m for line in f for m in line.split('#')[0].split()]
        else:
            out.append(n)
    return out


def build(names, out):
    ctx = Context()
    ctx.mods = list(names)
    for n in names:
        load_mod(n).apply(ctx)
    ctx.finish()
    wkz.write(out, sorted(ctx.files.items()))
    if ctx.dll_patches:
        # Check the patches against the original DLLs now, so build fails the same way install would.
        for dll in dllpatch.DLLS:
            orig = dllpatch.base(dll)
            for va, old, new, note in ctx.dll_patches_for(dll):
                off = dllpatch.va_to_offset(orig, va)
                assert bytes(orig[off:off + len(old)]) == old, f'{note}: original bytes differ at {va:#x}'
    return ctx


def main(argv):
    if not argv or argv[0] == 'list':
        for n in available():
            print(f'{n:24} {load_mod(n).DESCRIPTION}')
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == 'uninstall':
        path = os.path.join(GAME_DIR, 'danger_zone', ARCHIVE_NAME)
        if os.path.exists(path):
            os.remove(path)
        for dll in dllpatch.DLLS:
            dllpatch.restore(dll)
        print('removed', path, '; DLLs restored')
        return
    out = os.path.join(ROOT, 'build', ARCHIVE_NAME)
    if '-o' in rest:
        i = rest.index('-o')
        out = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(wkz.GAME_WKZ):
        raise SystemExit(f'Hammerting not found at {GAME_DIR}; set HAMMERTING_DIR to the game folder')
    ctx = build(expand(rest), out)
    for n in sorted(ctx.files):
        print('  ', n)
    for dll, va, _, new, note in ctx.dll_patches:
        print(f'   {dllpatch.DLLS[dll][0]} @ {va:#x} <- {new.hex()}  ({note})')
    print('wrote', out)
    if cmd == 'install':
        dz = os.path.join(GAME_DIR, 'danger_zone')
        os.makedirs(dz, exist_ok=True)
        # A running game maps the archive; replace the file rather than overwrite it in place.
        tmp = os.path.join(dz, ARCHIVE_NAME + '.tmp')
        shutil.copy(out, tmp)
        os.replace(tmp, os.path.join(dz, ARCHIVE_NAME))
        for dll, (name, _) in dllpatch.DLLS.items():
            patches = ctx.dll_patches_for(dll)
            if patches:
                dllpatch.apply(patches, dll)
                print(f'patched {name} ({len(patches)} patches; original kept as {dllpatch.backup(dll)})')
            elif dllpatch.is_patched(dll):
                dllpatch.restore(dll)
                print(f'no {name} patches selected; restored the original')
        print(f'installed; launch options: %command% --game-extra-archives danger_zone/{ARCHIVE_NAME}')


if __name__ == '__main__':
    main(sys.argv[1:])
