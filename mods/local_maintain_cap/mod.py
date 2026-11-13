"""Local Maintain Cap: Local Maintain stops once the colony has plenty of the item.

Local Maintain counts only the building's own inventory, so once haulers carry the output away it
crafts forever, and the surplus ends up on the floor and fills the entity limit (BUGS B1, A1). This
sets the queued amount to 0 while the colony holds FACTOR times the entry's high mark, counted as Global
Maintain counts (floor and storage), and resumes when it falls below that. Under the cap Local
Maintain works as before. Deliver-only recipes are left alone. See re/notes/clutter.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

FACTOR = int(os.environ.get('HMOD_LMC_FACTOR', '4'))

DESCRIPTION = f"Local Maintain stops at {FACTOR} times its level in the whole colony (DLL patch)"

CAVE = dllpatch.CAVE_VA + 0x1400
COUNT_SITE = 0x18015213d
TICK_SITE = 0x180152ed0
TICK_OLD = bytes.fromhex('83bb4805000004' '0f85a7000000')  # cmp [rbx+0x548],4; jne 0x180152f84
SYMBOLS = {
    'BASE': CAVE,
    'FACTOR': FACTOR,
    'TEST_DIAG': int(os.environ.get('HMOD_LMC_DIAG', '0')),     # test only: keeps the last counts for a memory reader
    'MATCHING': 0x18014fdd0,            # production_system_get_matching_output_entities
    'GLOBAL': 0x180200420,              # global_inventory_system_get_matching_inventory
    'GLOBAL_PATH': 0x180152edd,
    'RATE': 0x180152f3e,
    'NEXT': 0x180152f84,
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x200, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'local_maintain_cap code cave')
    ctx.patch_dll(COUNT_SITE, cave.call(COUNT_SITE, SYMBOLS['MATCHING']), cave.call(COUNT_SITE, CAVE + labels['count']),
                  'refresh_maintain_locally count -> cave')
    jmp = b'\xe9' + (CAVE + labels['tick'] - (TICK_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(TICK_SITE, TICK_OLD, jmp + b'\x90' * 8, 'production update loop -> cave')
    # Runs after maintain_hint, which may already have extended this text.
    found = 0
    for entry in ctx.loc('dubious_entries').entries.values():
        if entry.text.startswith('Maintain amount in building inventory') and not entry.blobs:
            entry.text = ('Maintain amount in building inventory (counts only this building, so it crafts again '
                          f'when haulers carry the items away, until the whole colony holds {FACTOR} times this '
                          'amount. Use Mountainhome for goods that get stored)')
            found += 1
    assert found == 1, found
