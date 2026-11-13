"""All Profession Bonuses: traits, statuses and gear that grant "all professions" bonuses now apply.

Morale, energy, food, gold statuses, traits such as Midas Touch or Slagfist, rings and armour grant
PROF_ALL_CRIT_SUCCESSES, PROF_ALL_CRIT_FAILURES, PROF_ALL_SPEEDS and PROF_ALL_LEVELS. Each profession's own
entries (PROF_MINER_SPEED and so on) are generated in code from attributes, level and tool, and never read those
four, so none of these grants did anything.

- Speed, crit success and crit failure entries add PROF_ALL_<kind> with weight 1.
- Wherever a profession level is a dependency (speed, crits, production, and the explorer-level stats vision
  range, move and climb speed, falling damage resistance), PROF_ALL_LEVELS is added with the same weight. The
  stored KV_LEVEL, the level shown and XP are untouched.

The game evaluates one func per source tag in an entry, so the bonuses go into the existing FROM_DWARF func
rather than a func of their own (a second FROM_DWARF func was tried and ignored).
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402
from wchash import wc_hash_string  # noqa: E402

DESCRIPTION = 'Trait, status and gear bonuses to all professions take effect (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x1f00
ALL_BONUS = dllpatch.CAVE_VA + 0x780    # dependency names (24 bytes) and hashes; the generated kind is the index
KINDS = ['PROF_ALL_LEVELS', 'PROF_ALL_SPEEDS', 'PROF_ALL_CRIT_SUCCESSES', 'PROF_ALL_CRIT_FAILURES']
SITE = 0x1802976e8
SITE_OLD = bytes.fromhex('80bdd077000000')    # cmp byte ptr [rbp+0x77d0], 0

ENTRIES = 'database/modifier/entry/modifier_entries_cdb.bin'
ENTRY_SIZE = 0x23c8
EXPLORER_STATS = ['SKILL_VISION_RANGE', 'STAT_MOVE_SPEED', 'STAT_CLIMB_SPEED', 'STAT_FALLING_DAMAGE_RESISTANCE']


def tag(name):
    return name.encode().ljust(0x38, b'\0') + struct.pack('<Q', wc_hash_string(name))


def tag_hash(name):
    """wc_hash as a signed value: llvm-mc's --defsym refuses 64-bit values above INT64_MAX."""
    h = wc_hash_string(name)
    return h - (1 << 64) if h >> 63 else h


def add_level_bonus(d, name):
    """Give func 0 of entry `name` a PROF_ALL_LEVELS dependency weighted like its PROF_EXPLORER_LEVEL one."""
    rec = d.index(tag(name))
    assert (rec - 16) % ENTRY_SIZE == 0, name      # records follow a 16-byte header
    func = rec + 0xc8
    deps = [bytes(d[func + 0x80 + 0x40 * k:func + 0xc0 + 0x40 * k]) for k in range(16)]
    n = next(k for k, t in enumerate(deps) if not any(t[0x38:]))
    level = deps.index(tag('PROF_EXPLORER_LEVEL'))
    weight = d[func + 0x880 + 4 * level:func + 0x884 + 4 * level]
    d[func + 0x80 + 0x40 * n:func + 0xc0 + 0x40 * n] = tag('PROF_ALL_LEVELS')
    d[func + 0x880 + 4 * n:func + 0x884 + 4 * n] = weight


def apply(ctx):
    symbols = {
        'BASE': CAVE,
        'ALL_BONUS': ALL_BONUS,
        'H_COMPUTE': tag_hash('dependencies_multiply_and_sum'),
    }
    table = b''.join(k.encode().ljust(24, b'\0') + struct.pack('<Q', wc_hash_string(k)) for k in KINDS)
    assert len(table) == 0x80
    ctx.patch_dll(ALL_BONUS, bytes(len(table)), table, 'PROF_ALL_* dependency tags')
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'add PROF_ALL_* to generated profession entries')
    ctx.patch_dll(SITE, SITE_OLD, cave.call(SITE, CAVE + labels['add_all_bonus']) + b'\x66\x90',
                  'profession entry commit -> add_all_bonus')
    d = bytearray(ctx.read(ENTRIES))
    for name in EXPLORER_STATS:
        add_level_bonus(d, name)
    ctx.write(ENTRIES, bytes(d))
