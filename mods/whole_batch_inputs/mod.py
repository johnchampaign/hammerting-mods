"""Whole Batch Inputs: production buildings stop reserving inputs for their whole queue.

A queue entry used to reserve (CLAIM_PRODUCE) each arriving input up to its whole queued
amount and keep it until it crafted. Entries missing one input held the others for good:
a cook house whose recipes each held some water and some food, with none complete, starved
and parched the colony. Now an entry asks for one craft's worth, so once it has that, further
items stay free for other entries. An entry can still hold a partial set while it waits.
A recipe with one input can't wait on another input, so it may reserve SINGLE_CRAFTS crafts' worth:
one craft at a time cut ingots by about half in testing.

An earlier version also refused to request anything unless the whole set was available at
once. That was removed; see re/notes/production_stall.md. The game's inventory counts leave out items
on the floor, so ore that was only on the floor counted as none and the foundry stopped, and
a cook house needing 4 ingots starved behind 1-ingot smithy orders.

DLL patch: one call site in production_queue_entry_wants_entity, code in the .hmod section.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = "Production buildings reserve inputs for one craft at a time, or a few for one-input recipes (DLL patch)"

CAVE = dllpatch.CAVE_VA                 # start of .hmod
SINGLE_CRAFTS = 5                       # crafts' worth a one-input recipe may reserve
SYMBOLS = {
    'BASE': CAVE,
    'SINGLE_CRAFTS': SINGLE_CRAFTS,
}
SITE = 0x180153102                      # mov r13, [rsi+0x538]; imul r13, rdx
SITE_OLD = bytes.fromhex('4c8bae380500004c0fafea')
NOP6 = bytes.fromhex('660f1f440000')


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'whole_batch_inputs code cave')
    ctx.patch_dll(SITE, SITE_OLD, cave.call(SITE, CAVE + labels['batch_limit']) + NOP6,
                  'wants_entity slot limit -> cave batch_limit')
