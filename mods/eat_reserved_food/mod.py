"""Eat Reserved Food: hungry dwarves may eat food that a production queue has reserved.

A production queue (cook house, tavern, farm store order...) claims its inputs with
CLAIM_PRODUCE as soon as they are queued. The eating code (refill_statusbar_sensor) skips
any item claimed by anything but another meal, so a long cooking queue locks up the
colony's food and dwarves starve next to full storage. This lets a dwarf take food that a
queue has reserved, unless the food is already inside the building that reserved it. When
the dwarf commits to eating it, the queue's claim is released first, so the queue re-plans
as if the food had been hauled away.

DLL patch: three calls in the refill sensor are redirected to a code cave (cave.s) in the
unused tail of .text, and .text's VirtualSize is grown to cover it. See
re/notes/food_ai.md for the call sites.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = "Hungry dwarves may eat food reserved by cooking queues (DLL patch)"

CAVE = 0x180530cf0                      # 16-byte aligned, just past .text's VirtualSize
SYMBOLS = {
    'BASE': CAVE,
    'GET_CLAIM_TYPE': 0x1801d4c60,      # claim_system_get_claim_type
    'IS_CLAIMED': 0x1801d4a10,          # claim_system_is_claimed
    'RELEASE_CLAIM': 0x1801d2b30,       # claim_system_release_claim
    'GET_ITEM_DETAILS': 0x180117a20,    # inventory_system_get_item_details
    'PRODUCE_HASH': 0x1805a4f98,        # CLAIM_PRODUCE wc_tag (0x1805a4f60) + 0x38
    'REFILL_TAG': 0x1805a4fe0,          # CLAIM_REFILL_STATUSBAR wc_tag
}
# call site -> (function it calls now, cave entry label)
SITES = {
    0x1802d4e92: (SYMBOLS['GET_CLAIM_TYPE'], 'filter'),  # desire_filler_cache::process_fillers
    0x1802bf917: (SYMBOLS['IS_CLAIMED'], 'pick'),        # calc_best_filler
    0x1802bfab7: (SYMBOLS['IS_CLAIMED'], 'take'),        # refill_statusbar_job_begin
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    dll = dllpatch.original()
    hdr, vsize, rva, rawsize, _ = dllpatch.section_header(dll, '.text')
    start, end = CAVE - dllpatch.IMAGE_BASE, CAVE - dllpatch.IMAGE_BASE + len(code)
    assert rva + vsize <= start and end <= rva + rawsize, 'cave does not fit in .text slack'
    ctx.patch_dll(hdr + 8, struct.pack('<I', vsize), struct.pack('<I', rawsize),
                  '.text VirtualSize covers the code cave')
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'eat_reserved_food code cave')
    for site, (old_target, label) in SITES.items():
        ctx.patch_dll(site, cave.call(site, old_target), cave.call(site, CAVE + labels[label]),
                      f'refill sensor -> cave {label}')
