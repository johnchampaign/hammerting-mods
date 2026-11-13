"""Pump Fluid Count: Maintain in Mountainhome counts only the fluid this pump yields.

The hand pump's only recipe is CLS_FLUID_CRAFT, which no item has, so the Mountainhome count falls
back to summing every water and lava item. A lava pump with Maintain 20 therefore never runs while
the colony holds 20 water (BUGS B8). The pump records what it stands over in KV_FLUID_TYPE, so this
looks up that fluid's own count instead. See re/notes/lava.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Pump Maintain in Mountainhome counts only its own fluid (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0xc00
SITE = 0x180200460
LOOKUP = 0x18020ab00
SYMBOLS = {'BASE': CAVE, 'CRAFT_SLOT': 0x1805a0f00, 'LOOKUP': LOOKUP, 'KV_GET': 0x180599398,
           'RET_ZERO': 0x18020050d}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'pump fluid count cave')
    ctx.patch_dll(SITE, cave.call(SITE, LOOKUP), cave.call(SITE, CAVE + labels['fluid_lookup']),
                  'pump count -> own fluid')
