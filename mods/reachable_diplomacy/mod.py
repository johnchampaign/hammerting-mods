"""Reachable Diplomacy: the World Conquest (Diplomatic) victory asks for a share of the map.

Vanilla wants every overworld location (35 on the West Hirdness map) owned by the
Mountainhome or by a faction allied with it. The player owns only the Mountainhome, so that
means an alliance with all nine AI factions at once. Each alliance costs the Mountainhome
1500 opinion with every faction outside it, the alliance quest needs the faction to Esteem
you, and faction opinions drift down over time, so all nine never line up.

The goal is generated in code (MISSION_GEN_OW_CONQUEST in smart_event_generation.h): an eval
chain `STATE_SET('AMOUNT_WANTED', OW_LOCATIONS.COUNT)` rebuilt on every load. This mod points
that code at a chain asking for TARGET_PERCENT of the locations, rounded up, so it reaches
existing saves as well as new games. With 35 locations and 33% that is 12: the Mountainhome
plus about three allied factions.

DLL patch: the chain text goes in the .hmod section; one lea at 0x1800a1c94 points to it.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import dllpatch  # noqa: E402

TARGET_PERCENT = 33
DESCRIPTION = f'Diplomatic victory needs {TARGET_PERCENT}% of overworld locations owned or allied, not all (DLL patch)'

STRING_VA = dllpatch.CAVE_VA + 0x200    # whole_batch_inputs owns .hmod+0..0x200
LEA_SITE = 0x1800a1c94                  # lea r8, [rip+...] -> the format string for snprintf
LEA_OLD = bytes.fromhex('4c8d05cdb54900')  # -> 0x18053d268 "STATE_SET( 'AMOUNT_WANTED', OW_LOCATIONS.COUNT)"


def apply(ctx):
    t = TARGET_PERCENT
    assert 0 < t <= 100
    # snprintf format: no '%'. Literals are quoted, as in vanilla's ADD('1').
    chain = (f"STATE_SET( 'AMOUNT_WANTED', OW_LOCATIONS.COUNT.MUL('{t}').ADD('99')"
             f".INT_DIV('100'))").encode() + b'\0'
    assert b'%' not in chain and len(chain) <= 0x100
    ctx.patch_dll(STRING_VA, bytes(len(chain)), chain, 'World Conquest AMOUNT_WANTED chain')
    rel = STRING_VA - (LEA_SITE + 7)
    ctx.patch_dll(LEA_SITE, LEA_OLD, LEA_OLD[:3] + rel.to_bytes(4, 'little', signed=True),
                  'conquest mission generator -> new AMOUNT_WANTED chain')

    table = ctx.loc('overworld')
    old = 'the entire Overworld beyond our halls'
    hits = [e for e in table.entries.values() if old in e.text]
    assert len(hits) == 1, f'{len(hits)} entries contain {old!r}'
    hits[0].text = hits[0].text.replace(old, f'{t}% of the Overworld locations beyond our halls')
