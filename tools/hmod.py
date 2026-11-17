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
  hmod.py strings <mod> [<mod> ...]   build, then list the texts a language has no translation for
                                      in build/strings.json
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dllpatch  # noqa: E402
import wkz  # noqa: E402
from loc import Entry, LocTable  # noqa: E402

ROOT = os.path.dirname(HERE)
GAME_DIR = os.path.dirname(wkz.GAME_WKZ)
ARCHIVE_NAME = 'hammerting_mods.wkz'

# The game's other languages. Each has one table with every key (localization/imported_<code>.loc), and a key
# missing from the player's language shows as the key itself, with no fallback to English. So every text the
# mods add or change in the English tables is copied into each of these, translated where
# mods/translations/<code>.json ({English text: translation}) has it, and in English otherwise. A mod can
# also give a text per language (set_localized), as mods_menu does for the Mods and news windows.
LANGUAGES = ('de-DE', 'es-ES', 'fr-FR', 'it-IT', 'ja-JP', 'pl-PL', 'pt-BR', 'ru-RU', 'zh-CN')
CHAIN_MARK = '%Oproperty_comp'


def language_table(lang):
    return f"imported_{lang.lower().replace('-', '_')}"


def load_translations(lang):
    path = os.path.join(ROOT, 'mods', 'translations', f'{lang}.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Context:
    def __init__(self):
        self._game = wkz.open_archive(wkz.GAME_WKZ)
        self._index = {e['name']: e for e in wkz.entries(self._game)}
        self.files = {}
        self._locs = {}
        self._translations = {lang: load_translations(lang) for lang in LANGUAGES}
        self.untranslated = {lang: set() for lang in LANGUAGES}
        self.texts = {}             # English text -> the game's original texts in each language, if it replaced one
        self._localized = {}        # key hash -> {language: text}, for texts a mod builds per language
        self.languages = ('en-US',) + LANGUAGES
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

    def tr(self, text, lang):
        """text translated into lang, or text itself (English) if there is no translation."""
        if lang == 'en-US':
            return text
        out = self._translations[lang].get(text)
        if out is None:
            self.untranslated[lang].add(text)
            return text
        return out

    def set_localized(self, table, key, texts):
        """Set key in an English table to texts['en-US'] and in each other language to texts[lang],
        for texts a mod assembles from translated pieces (mods_menu)."""
        from wchash import wc_hash_string
        self.loc(table).set(key, Entry(texts['en-US']))
        self._localized[wc_hash_string(key)] = texts

    def finish(self):
        changed = {}
        for name, table in self._locs.items():
            orig = LocTable(self.read(f'localization/{name}.loc')).entries
            changed.update({h: e for h, e in table.entries.items()
                            if h not in orig or (orig[h].text, orig[h].blobs) != (e.text, e.blobs)})
            self.write(f'localization/{name}.loc', table.pack())
        for lang in LANGUAGES:
            name = f'localization/{language_table(lang)}.loc'
            table = LocTable(self.read(name))
            for h, e in changed.items():
                text = self._localized[h][lang] if h in self._localized else self.tr(e.text, lang)
                if h in table.entries and h not in self._localized:
                    self.texts.setdefault(e.text, {})[lang] = table.entries[h].text
                # A chain fills each %Oproperty_comp in order, so a translation needs as many.
                if text.count(CHAIN_MARK) != len(e.blobs):
                    print(f'warning: {lang} translation has the wrong number of {CHAIN_MARK}; using English: '
                          f'{e.text[:60]!r}')
                    text = e.text
                table.entries[h] = Entry(text, e.blobs)
            self.write(name, table.pack())


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
    if cmd == 'strings':
        # Texts that some language has no translation for, with the game's own translations of the text each
        # replaced, for whoever writes the translations (mods/translations/README.md).
        missing = sorted(set().union(*ctx.untranslated.values()))
        rows = [{'en': t, 'missing': [lang for lang in LANGUAGES if t in ctx.untranslated[lang]],
                 'replaces': ctx.texts.get(t, {})} for t in missing]
        path = os.path.join(ROOT, 'build', 'strings.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f'{len(rows)} texts lack a translation in some language; wrote {path}')
        return
    for n in sorted(ctx.files):
        print('  ', n)
    for dll, va, _, new, note in ctx.dll_patches:
        print(f'   {dllpatch.DLLS[dll][0]} @ {va:#x} <- {new.hex()}  ({note})')
    print('wrote', out)
    gaps = {lang: len(s) for lang, s in ctx.untranslated.items() if s}
    if gaps:
        print('texts shown in English for lack of a translation:', ', '.join(f'{k} {v}' for k, v in gaps.items()))
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
