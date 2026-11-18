"""Gem Cut Rebalance: a Star of Mara costs 9 raw gems of one kind instead of 243 of one kind.

The White Anvil cuts gems in five steps (Rough, Cabochon, Trilliant, Brilliant, Star of Mara),
and in vanilla every step takes 3 identical items of the step before, so one Star needs
3^5 = 243 raw gems of a single kind. The Star goes into each Large Vault (two for the
Affluence victory) and the Explorer Lantern, while a whole colony may find 50 gems of all kinds.

Now Rough Cut takes 3 raw gems of one kind, as before, Cabochon, Trilliant and Brilliant take 1 of
the step before, and the Star takes 3 Brilliants of one kind. Every cut keeps its raw kind.
Until 1.6.5 the Rough Cut and the Star dropped the kind (remove_input_modifier, as Bone Ash does), so
that any mix of gems would do. But a cut gem's name and icon come from its raw kind ("Rough" + "Ruby"),
so those rough gems had no name or icon, and players couldn't pick them for the next cut (reported on
Steam, 2026-11-18). Gems cut that way stay kindless.
Recipe records are read at load, so existing saves and queued entries get the new counts.
See re/notes/material_subtypes.md.
"""
import struct

DESCRIPTION = 'A Star of Mara costs 9 raw gems of one kind, not 243'

RECORDS = 'database/recipe/recipe_white_anvil_cdb.bin'
RECORD_SIZE = 0xec8
SLOT0_COUNT = 0x80            # u32 count of input slot 0 (name at +0x88)
# recipe tag: (input class, new count)
CHANGES = {
    'CLS_GEM_ROUGH_CUT': ('CLS_GEM_RAW', 3),
    'CLS_GEM_CABOCHON_CUT': ('CLS_GEM_ROUGH_CUT', 1),
    'CLS_GEM_TRILLIANT_CUT': ('CLS_GEM_CABOCHON_CUT', 1),
    'CLS_GEM_BRILLIANT_CUT': ('CLS_GEM_TRILLIANT_CUT', 1),
    'CLS_GEM_STAR_CUT': ('CLS_GEM_BRILLIANT_CUT', 3),
}


def apply(ctx):
    d = bytearray(ctx.read(RECORDS))
    count, total = struct.unpack_from('<QQ', d, 0)
    assert total == count * RECORD_SIZE, 'unexpected recipe record size'
    done = set()
    for i in range(count):
        rec = 16 + i * RECORD_SIZE
        tag = d[rec:rec + 0x38].split(b'\0')[0].decode()
        if tag not in CHANGES:
            continue
        cls, n = CHANGES[tag]
        assert d[rec + 0x88:rec + 0xc0].split(b'\0')[0].decode() == cls, tag
        assert struct.unpack_from('<I', d, rec + SLOT0_COUNT)[0] == 3, tag
        struct.pack_into('<I', d, rec + SLOT0_COUNT, n)
        done.add(tag)
    assert done == set(CHANGES), set(CHANGES) - done
    ctx.write(RECORDS, bytes(d))
