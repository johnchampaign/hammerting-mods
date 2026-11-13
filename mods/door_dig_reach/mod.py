"""Door Dig Reach: dwarves dig rock that can only be reached from inside a door's frame.

Reported as "Dwarf won't dig any wall beside a door" (S1/4658416565935612822, Mar 2022, two more players): dig orders
beside a door sit undone until the door is torn down, when the door was placed before its hole was dug or fills its
tunnel. tile_graph::add_block_ctx_to_graph disables every edge between a gamepath and a tile node that has no edge to
another tile node (`bts ecx, 8` at 0x180335462, EDGE_DISABLED). A brick door's walkable inner tiles (its lower side
cells) connect only to the door's own path and to the tiles outside them, so with rock outside one of them that edge
is disabled, no dwarf can reach the inner tile, and the rock beside it is out of everyone's reach.

This keeps such an edge enabled when one of the tile's 8 neighbours holds a dig order. Placing a dig order marks its
map block dirty and the block's graph is rebuilt, so the check runs then; once the rock is dug the tile has a normal
neighbour. Without a dig order nothing changes: the colony had 82 such disabled edges, most of them tiles inside
buildings that are reached through the building's path. An order in a different 16x16 map block than the tile only
takes effect when the tile's block is next rebuilt.

Tested on a copy of KrazJomsglind savegame32: rock filled into the two open columns left of the Brickwall Door at
x 452-454, y 958-961, with dig orders on the column touching the door, and control orders on ordinary tunnel walls.
See docs/BUGS.md B13.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves dig rock next to a door that fills its tunnel instead of leaving the orders forever (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2100
SITE = 0x18033545a                      # tile_graph::add_block_ctx_to_graph, gamepath edge to a dead-end tile
SITE_OLD = bytes.fromhex('8b0b' '81e100feff7f' '0fbae908')   # mov ecx,[rbx]; and ecx,0x7ffffe00; bts ecx,8
DISABLE_RESUME = 0x180335466            # shr ecx, 8
ENABLE_RESUME = 0x180335469             # after the shift, as the enabled branch at 0x180335595 rejoins


def apply(ctx):
    symbols = {'BASE': CAVE, 'DISABLE_RESUME': DISABLE_RESUME, 'ENABLE_RESUME': ENABLE_RESUME}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'door_dig_reach code cave')
    jmp = b'\xe9' + (CAVE + labels['dead_end'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'gamepath dead-end edge -> door_dig_reach')
