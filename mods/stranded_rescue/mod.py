"""Stranded Rescue: a dwarf cut off from the entrance for a long time goes back to it.

A stair or bridge piece can close the only route between a dwarf and the colony (BUGS A10,
re/notes/stuck_dwarves.md). He then has no job or food and starves unless the player finds the piece.
Every 10 game seconds this asks the game's own ALERT_IS_STRANDED about each dwarf, and one who has
been stranded at every check for RESCUE_MINUTES is moved to the entrance through the fall code. A reload
restarts the count. Nobody moves while more than half the dwarves in the cave are stranded, since then
the entrance is more likely the part that is cut off. The alert text says what will happen.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402
from wchash import wc_hash_string  # noqa: E402

RESCUE_MINUTES = float(os.environ.get('HMOD_RESCUE_MINUTES', '10'))    # at most 42
CHECK_SECONDS = 10.0

DESCRIPTION = f"Dwarves stranded for {RESCUE_MINUTES:g} game minutes go back to the entrance (DLL patch)"

CAVE = dllpatch.CAVE_VA + 0x1000
COUNTERS = dllpatch.CAVE_VA + dllpatch.CAVE_SIZE    # zero-filled, one byte per entity
SITE = 0x1802af3c5
SITE_OLD = bytes.fromhex('66440f2ec67434')     # ucomisd xmm8,xmm6; je 0x1802af400
FORCE = [int(a) for a in os.environ.get('HMOD_RESCUE_FORCE', '0 0 0').split()]     # test only: treat as stranded
SYMBOLS = {
    'BASE': CAVE,
    'TEST_FORCE_A': FORCE[0],
    'TEST_FORCE_B': FORCE[1],
    'TEST_FORCE_C': FORCE[2],
    'COUNTERS': COUNTERS,
    'SKIP': 0x1802af400,
    'RESUME': 0x1802af3cc,
    'CHECK_BITS': struct.unpack('<Q', struct.pack('<d', CHECK_SECONDS))[0],
    'THRESHOLD': round(RESCUE_MINUTES * 60 / CHECK_SECONDS),
    'HASH_PLAYER': wc_hash_string('PLAYER_CHARACTER'),
    'TAGGED_PTR': 0x180599198,          # tagged entities, as read at 0x1800af5ee
    'HAS_TAG_PTR': 0x1805991b8,         # as called at 0x1801dc1ee
    'IN_OVERWORLD': 0x18053a218,        # "CURRENTLY_IN_OVERWORLD"
    'FAMILY_PTR': 0x180599070,          # family records, as read at 0x1803f4eb7
    'IS_STRANDED': 0x180072ce0,         # ALERT_IS_STRANDED's function
    'ENTRANCE_DATA': 0x1803a2df0,       # get_entrance_data
    'WORLD_POSITIONS': 0x1800e9720,     # fixed_transform_system_get_world_positions
    'FORCE_STOP': 0x180400fa0,          # movement_system_force_stop
    'SET_WORLD': 0x1800e9740,           # fixed_transform_system_set_world_position
    'QUERY_ID': 0x180400a70,            # movement_system_get_query_id
    'UPDATE_POSITION': 0x180106690,     # graph_position_system_update_position
    'SET_START': 0x1800f2010,           # navgraph_query_system_set_start_positions
}


def apply(ctx):
    assert 1 <= SYMBOLS['THRESHOLD'] <= 255, 'the counters are one byte'
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x400, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'stranded_rescue code cave')
    jmp = b'\xe9' + (CAVE + labels['tick'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90\x90', 'gamestate update -> rescue tick')
    # Runs after teardown_hint, which may already have extended this text.
    found = 0
    for entry in ctx.loc('dubious_entries').entries.values():
        if entry.text.startswith('Some of your dwarves are stranded, unable to reach the Entrance:'):
            entry.text += (f'\nA dwarf still stranded after {RESCUE_MINUTES:g} minutes is moved back to the '
                           'Entrance, unless most of them are stranded.')
            found += 1
    assert found == 1, found
