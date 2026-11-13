"""Harvest Wild Crops: ripe wild plants are harvested without a Harvest order.

Crops a farmer sows carry auto_tend, and when one ripens the harvest sensor gives it a job, so a
farmer harvests and resows it on his own. Wild plants (from map generation) have no auto_tend, and
plant_system_update_workplace_positions (0x1801ea3cd) skipped them, so each ripe one waited for the
player to click it and press Harvest (order_interact), which the game only accepts once the plant
is ripe. Now ripe wild plants on explored tiles get the same harvest job. auto_tend itself is left
alone, so a harvested wild plant is still removed, as with the manual order; the Cave Farm's
per-crop limits apply as they do to sown crops.

Jobs are rebuilt for a crop type when one of its plants changes stage, so a ripe wild plant in a
newly explored area is picked up at the next such change. See re/notes/plant_growth.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Farmers harvest ripe wild plants on explored tiles without a Harvest order (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2640
SITE = 0x1801ea3cd
SITE_OLD = bytes.fromhex('807930000f84f8020000')   # cmp byte [rcx+0x30],0; je 0x1801ea6cf
SYMBOLS = {
    'BASE': CAVE,
    'KEEP': 0x1801ea3d7,        # cmp dword [rcx+0x18],0: has a workplace -> job
    'SKIP': 0x1801ea6cf,        # next plant
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'harvest_wild_crops code cave')
    jmp = b'\xe9' + (CAVE + labels['check'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\xcc' * (len(SITE_OLD) - 5), 'ripe wild plants get harvest jobs')
