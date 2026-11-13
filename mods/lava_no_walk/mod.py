"""Lava No Walk: dwarves never walk from dry ground into lava.

Lava's path cost and the check for it sit on each dwarf's movement query, and job and hauling queries
have neither, so job choice treats lava as free ground and dwarves take jobs inside a pool. This
blocks every edge that touches lava in the edge cost callback, except in a creature's own movement
query (the only kind with the lava bit in its mask) that starts on a lava tile, so a dwarf caught by
a flow can still walk out (BUGS B8, re/notes/lava.md). The edges' own lava flags are only updated
where fluid moves, so it reads the map once per edge and keeps the answer in a spare flag bit.
Anything else on dry ground, lava creatures included, can no longer enter lava either.

The first version blocked an edge when its first node was dry. Edges are stored without a direction,
so a dwarf could step in from the other end, and one caught in lava could find his way out blocked.
And the path search calls the edge callback only for edges with flag data, which the game sets on
tile edges where fluid moves: after a load, lava at rest had none, and a building's walkway edges
never get one, so a storage whose floor had filled with lava was walked as dry ground (a dwarf died
there in a test). Now the path search calls the callback for every edge (graph.x86_64.dll), the
first edge update after each new tile graph marks every block with lava as fluid-dirty, and every
128th edge update makes the gate read every edge's tiles again. Code in .hmod+0xd40 and +0x2480.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves never walk from dry ground into lava (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0xd40
SITE = 0x1802ac280
SYMBOLS = {'BASE': CAVE, 'RESUME': 0x1802ac287, 'BLOCKED': 0x1802ac2f0}
SWEEP = dllpatch.CAVE_VA + 0x2480
INIT_SITE = 0x180330e20                 # tile_graph::initialize
UEM_SITE = 0x180332d50                  # tile_graph::update_edge_masks
ENTRY_OLD = bytes.fromhex('48894c2408')  # mov [rsp+8], rcx
# graph_graph_query_continue_query (graph.x86_64.dll): `je` past the edge cost callback for edges with no data
# bits. Building walkways have none, and the fluid flag is set only on tile edges.
GRAPH_SITE = 0x1800086fa


def jump(site, target):
    return b'\xe9' + (target - (site + 5)).to_bytes(4, 'little', signed=True)


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x180
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'lava gate cave')
    ctx.patch_dll(SITE, bytes.fromhex('488b80b8000000'), jump(SITE, CAVE + labels['lava_gate']) + b'\x90\x90',
                  'edge cost -> lava gate')
    code, labels = cave.assemble(os.path.join(HERE, 'sweep.s'),
                                 {'BASE': SWEEP, 'INIT_RESUME': INIT_SITE + 5, 'UEM_RESUME': UEM_SITE + 5})
    assert len(code) <= 0x100
    ctx.patch_dll(SWEEP, bytes(len(code)), code, 'lava sweep cave')
    ctx.patch_dll(INIT_SITE, ENTRY_OLD, jump(INIT_SITE, SWEEP + labels['rebuilt']), 'new tile graph -> sweep pending')
    ctx.patch_dll(UEM_SITE, ENTRY_OLD, jump(UEM_SITE, SWEEP + labels['sweep']), 'update_edge_masks -> lava sweep')
    ctx.patch_dll(GRAPH_SITE, bytes.fromhex('7440'), b'\x90\x90', 'path search: edge cost callback for every edge',
                  dll='graph')
