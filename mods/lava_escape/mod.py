"""Lava Escape: a dwarf standing in lava stops working and leaves.

ACTION_AVOID_FLUID has rank IDLE, so a dwarf with any job stays in lava until it kills him. This
raises it to PREPARATIVE, above work and desires and below combat, and scores it for lava only, so
wet workers are not pulled out of water. Idle dwarves no longer step out of water (BUGS B8,
re/notes/lava.md). Only lava deep enough to burn (amount 2 or more) counts: shallower lava does no
harm, and lava_no_walk lets dwarves walk on it, so reacting to it made dwarves step in and out. With
lava_no_walk, a dwarf working on the Cave Farm when lava flowed over it got out in about 10 game
seconds and went back to work (copy of KrazJomsglind savegame32, normal lava damage, 1 run).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves standing in lava stop work and leave (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0xd00
RANK_SITE = 0x1803a697e
SCORE_SITE = 0x1803a70a4


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), {'BASE': CAVE})
    assert len(code) <= 0x40
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'lava only score')
    ctx.patch_dll(RANK_SITE, bytes.fromhex('c7454001000000'), bytes.fromhex('c7454005000000'),
                  'avoid fluid rank IDLE -> PREPARATIVE')
    jmp = b'\xe9' + (CAVE + labels['lava_only'] - (SCORE_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SCORE_SITE, bytes.fromhex('0fb6548803'), jmp, 'fluid score -> lava only')
