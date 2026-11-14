"""Harvest Priority: ripe crops are harvested at High priority, so farmers don't leave them standing.

Farmers harvest a ripe sown crop through one harvest job per crop type. plant_system::update_harvesting
(0x1801f3e70) gives that job priority Low (0), raised only by a Cave Farm entry for the crop to the Cave
Farm's hauling priority. The job broker adds 1000 per priority level, so any dwarf with a Normal craft or
haul job never picked a harvest, and ripe crops stood for hours: in the user's SouthXanforge colony 22 of 23
sown crops were ripe in every save from savegame72 to savegame75, all crops had harvest jobs and positive
farming skill, and every job's priority was 0 (read from memory). The player had to press Harvest on each
plant instead (138 times in one session of another colony).

The priority handed to the job (0x1801ea91f in plant_system_update_workplace_positions) is now at least
HARVEST_PRIO (2, High; 1 is Normal). Harvesting is short, and the game already gives a newly sown crop's own
deliveries High. A Cave Farm entry that has nothing queued still switches a crop's harvest off. See
re/notes/plant_growth.md and re/notes/job_broker.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Farmers harvest ripe crops at High priority instead of Low, so crops no longer stand ripe (DLL patch)'

HARVEST_PRIO = 2                # 0 Low, 1 Normal, 2 High

CAVE = dllpatch.CAVE_VA + 0x2640
SITE = 0x1801ea91f
SITE_OLD = bytes.fromhex('448b471c4d8bcf')     # mov r8d,[rdi+0x1c]; mov r9,r15
SYMBOLS = {
    'BASE': CAVE,
    'BACK': 0x1801ea926,
    'HARVEST_PRIO': HARVEST_PRIO,
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x40, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'harvest_priority code cave')
    jmp = b'\xe9' + (CAVE + labels['prio'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\xcc' * (len(SITE_OLD) - 5), 'harvest jobs get at least High priority')
