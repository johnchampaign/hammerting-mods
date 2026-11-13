"""Builders Finish: a builder keeps a bonus for the build he is on, so he doesn't leave it near the end.

Reported in Mar 2022 (S0/3187992458103779388): dwarves leave a building "two hammerswings before they finish"
and another dwarf completes it. The Job Broker scores the job a dwarf is already doing with a bonus that fades
over his first 300 s on it (x5 to x1, +1500 to 0; job_broker_system::calc_assignments 0x18013759c). Hauling
keeps a fixed +10000 on top, so a load is never dropped; crafting, including JOB_CRAFT_BUILDER, keeps nothing.
A building is 5 units of work against 1 for an ordinary craft (recipe +0x980; about 33 s per unit at normal
speed), so with the walk to the site a builder passes 300 s near the end of a build and any job of the same
priority can take him away.

This gives JOB_CRAFT_BUILDER a fixed +900 for its current job. Other jobs of the same priority no longer pull a
builder off a build; a job one priority level higher (+1000) still can. Other professions are unchanged, so
crafters still rotate between workshops. See re/notes/job_broker.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402
from wchash import wc_hash_string  # noqa: E402

DESCRIPTION = 'Builders finish the build they are on instead of being pulled away near the end (DLL patch)'

FLAT = 900
CAVE = dllpatch.CAVE_VA + 0x680
SITE = 0x1803c39ee
SITE_OLD = bytes.fromhex('48c7457c00000000')   # mov qword ptr [rbp+0x7c], 0
RESUME = 0x1803c39f6


def signed(h):
    """llvm-mc's --defsym refuses 64-bit values above INT64_MAX."""
    return h - (1 << 64) if h >> 63 else h


def apply(ctx):
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'FLAT': FLAT << 16,
               'H_BUILDER': signed(wc_hash_string('PROF_BUILDER'))}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x40
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'builders_finish code cave')
    jmp = b'\xe9' + (CAVE + labels['builder_bonus'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'sensor_craft_init -> builder_bonus')
