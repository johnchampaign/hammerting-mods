"""Gem Cut Rebalance: a Star of Mara costs 9 raw gems of any kind instead of 243 of one kind.

The White Anvil cuts gems in five steps (Rough, Cabochon, Trilliant, Brilliant, Star of Mara),
and in vanilla every step takes 3 identical items of the step before, so one Star needs
3^5 = 243 raw gems of a single kind. The Star goes into each Large Vault (two for the
Affluence victory) and the Explorer Lantern, while a whole colony may find 50 gems of all kinds.
A Rough Cut slot locked onto one kind also stalled the user's queue when that kind ran out.

Now:
- Rough Cut takes 3 raw gems of any mix and drops their kind (remove_input_modifier, as Bone
  Ash does), so every later cut is one kind;
- Cabochon, Trilliant and Brilliant take 1 of the step before;
- Star of Mara takes 3 Brilliants, also ignoring their kind, so cut gems made before this mod
  (which keep their raw kind) can be combined.
Needs `class_matched_inputs`: without it, slots that drop their kind still wait for identical
items. Recipe records are read at load, so existing saves and queued entries get the new counts.
See re/notes/material_subtypes.md.
"""
import struct

DESCRIPTION = 'A Star of Mara costs 9 raw gems of any kind, not 243 of one kind (needs class_matched_inputs)'

RECORDS = 'database/recipe/recipe_white_anvil_cdb.bin'
RECORD_SIZE = 0xec8
SLOT0_COUNT = 0x80            # u32 count of input slot 0 (name at +0x88)
SLOT0_RMMOD = 0xe68           # u8 remove_input_modifier[0]: output doesn't inherit this slot's material
# recipe tag: (input class, new count, drop input kind)
CHANGES = {
    'CLS_GEM_ROUGH_CUT': ('CLS_GEM_RAW', 3, True),
    'CLS_GEM_CABOCHON_CUT': ('CLS_GEM_ROUGH_CUT', 1, False),
    'CLS_GEM_TRILLIANT_CUT': ('CLS_GEM_CABOCHON_CUT', 1, False),
    'CLS_GEM_BRILLIANT_CUT': ('CLS_GEM_TRILLIANT_CUT', 1, False),
    'CLS_GEM_STAR_CUT': ('CLS_GEM_BRILLIANT_CUT', 3, True),
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
        cls, n, drop_kind = CHANGES[tag]
        assert d[rec + 0x88:rec + 0xc0].split(b'\0')[0].decode() == cls, tag
        assert struct.unpack_from('<I', d, rec + SLOT0_COUNT)[0] == 3, tag
        assert d[rec + SLOT0_RMMOD] == 0, tag
        struct.pack_into('<I', d, rec + SLOT0_COUNT, n)
        if drop_kind:
            d[rec + SLOT0_RMMOD] = 1
        done.add(tag)
    assert done == set(CHANGES), set(CHANGES) - done
    ctx.write(RECORDS, bytes(d))
