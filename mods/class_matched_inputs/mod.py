"""Class Matched Inputs: buildings count any part of the right kind; stations keep material choices.

calc_input_slot_ready counts a slot needing more than one item as ready only when enough
claimed items are identical (same item and full material modifiers). Crafts need that (the
output inherits the input's material), but building, upgrade and delivery recipes say they
match by classification (use_classification_matching) and readiness ignored it: a building
counted only its largest identical group as delivered, kept accepting mismatched parts, and
dropped the extras on the floor when it completed (BUGS B4: "not counted", "ate six beams").
The Large Vault's 10 Support Beams had to be one wood and metal pair (Affluence victory).
Now those slots, and slots whose material isn't passed on (remove_input_modifier), count every
claimed item. Crafts are unchanged.

Also: clicking the recipe a station already has no longer resets its material choice, amount
and repeat (BUGS B3, "stations forget material choices").

DLL patch, code in .hmod+0x400. See re/notes/material_subtypes.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Buildings count any part of the right kind; stations keep material choices (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x400
SITES = {   # va: (old bytes, cave label); the call is padded with a nop to the old length
    0x18014d3a2: ('4c8b840a800000004983f801', 'relax_count'),   # mov r8,[rdx+rcx+0x80]; cmp r8,1
    0x18014ce6b: ('4c89440118', 'keep_template'),               # mov [rcx+rax+0x18],r8
}
NOPS = {0: b'', 7: bytes.fromhex('0f1f8000000000')}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), {'BASE': CAVE})
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'class_matched_inputs code cave')
    for va, (old, label) in SITES.items():
        old = bytes.fromhex(old)
        new = cave.call(va, CAVE + labels[label]) + NOPS[len(old) - 5]
        ctx.patch_dll(va, old, new, f'{label} -> cave')
