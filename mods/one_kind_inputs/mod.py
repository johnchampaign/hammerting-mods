"""One Kind Inputs: a craft slot that needs several identical items collects one kind at a time.

Crafts pass their input's material on, so a slot needing 2 bones or 3 gems is ready only with that
many of one kind. Until a kind reached that count the game let the slot take any item of the class,
and nothing gave a wrong one back (BUGS B3): a Rough Cut entry in the user's colony took a ruby on
top of its 2 sapphires while another Rough Cut entry held the colony's other ruby, so neither gem
could be used, and an entry with a mix kept asking for more. Now a slot holding part of a craft
takes only items like the ones it holds, the rule the game already applied once a slot was full.
Slots whose material isn't passed on (remove_input_modifier) and building recipes still combine any
kinds. An entry that already holds a mix (from before this mod) gives its items back and takes one
kind again, through the game's own check_correct_input.

No availability check: a slot holding 2 sapphires waits for a third, as a full slot of a batch did
before, and the items it doesn't use stay free. The kinds on the floor don't count as available
in the game's inventory counts, so a check would stall food and ingot recipes (see
re/notes/production_stall.md). DLL patch, code in .hmod+0x2200. See re/notes/material_subtypes.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Craft slots needing several identical items collect one kind instead of a useless mix (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2200
LOCK_SITE = 0x180153122                 # production_queue_entry_wants_entity: n < count -> no kind check
LOCK_OLD = bytes.fromhex('483bc2' '7232')                   # cmp rax, rdx; jb 0x180153159
RELEASE_SITE = 0x180152f84              # production_system_update: next queue entry
RELEASE_OLD = bytes.fromhex('488b4308' '488bd8')            # mov rax, [rbx+8]; mov rbx, rax
SYMBOLS = {
    'BASE': CAVE,
    'MATCH_PATH': 0x180153127,          # compare with the group (match_modifiers)
    'SELECT_PATH': 0x180153159,         # selected materials, else the class check
    'CLAIMED': 0x1801d4890,             # claim_system_get_claimed_entities_with_ref
    'CCI': 0x1801536f0,                 # production_system check_correct_input
    'TEST_DIAG': int(os.environ.get('HMOD_OKI_DIAG', '0')),     # test only: counts releases for a memory reader
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x200, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'one_kind_inputs code cave')
    jmp = b'\xe9' + (CAVE + labels['lock'] - (LOCK_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(LOCK_SITE, LOCK_OLD, jmp, 'wants_entity: lock a partial slot to its kind')
    ctx.patch_dll(RELEASE_SITE, RELEASE_OLD, cave.call(RELEASE_SITE, CAVE + labels['release']) + b'\x66\x90',
                  'queue walk: release mixed slots')
