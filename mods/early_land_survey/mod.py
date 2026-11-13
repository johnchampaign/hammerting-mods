"""Early Land Survey: Mountain Lore can be earned again from early on.

Research costs Mountain Lore (1326 for the whole tree) and Trade Lore. Trade Lore comes back
through repeatable overworld deliveries, but Mountain Lore is renewable only through the Land
Survey craft (Arcane Workshop: dwarven map + copper ingot + 2 granite chunks -> 1-3 Mountain
Lore), and that recipe depends on RESEARCH_GEOLOGICAL_SURVEYS, about 140 Mountain Lore into the
tree. Until then lore comes only from one-off missions and discoveries, so spending it on other
branches first can leave every remaining card unaffordable for good (BUGS A17). The West
Hirdness colony had 3 Mountain Lore and no Geological Surveys.

This mod makes Land Survey depend on RESEARCH_FORMALIZED_LEARNING instead, the research its
building and its dwarven map input already need. Dependencies are resolved at load, so existing
saves get it. Optionally raise the yield with SURVEY_YIELD. See re/notes/research_tree.md.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import wchash  # noqa: E402

DESCRIPTION = 'Land Survey (renewable Mountain Lore) unlocks with Formalized Learning, not Geological Surveys'

RECORDS = 'database/recipe/recipe_scriptorium_cdb.bin'
DEPENDENCIES = 2440          # recipe_record._dependencies[4], u64 tag hashes
OUTPUT_MIN_MAX = 0x700       # u32 min, u32 max of the first output (record 4: file 0x4230)
SURVEY_YIELD = None          # e.g. (2, 4); None keeps vanilla 1-3


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, total = struct.unpack_from('<QQ', d, 0)
    size = total // count
    recs = [16 + size * i for i in range(count)]
    rec = next(r for r in recs if d[r:r + 0x38].split(b'\0')[0] == b'CLS_LAND_SURVEY')
    old = wchash.metrohash64(b'RESEARCH_GEOLOGICAL_SURVEYS')
    new = wchash.metrohash64(b'RESEARCH_FORMALIZED_LEARNING')
    assert struct.unpack_from('<Q', d, rec + DEPENDENCIES)[0] == old, 'unexpected Land Survey dependency'
    struct.pack_into('<Q', d, rec + DEPENDENCIES, new)
    if SURVEY_YIELD:
        assert struct.unpack_from('<II', d, rec + OUTPUT_MIN_MAX) == (1, 3)
        struct.pack_into('<II', d, rec + OUTPUT_MIN_MAX, *SURVEY_YIELD)
    ctx.write(RECORDS, bytes(d))
