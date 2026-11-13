"""Known Capital Missions: Dwarven Subversion is offered only at capitals you have revealed.

The game offers it when a faction comes to esteem you, at the faction's capital, even if that hex is still in
the fog, where the panel can't be opened. See re/notes/diplomacy.md.

- The esteem trigger skips a hidden capital, so nothing is offered, shown or announced.
- A known capital whose faction esteems you and isn't allied gets the offer if it has none, so a capital revealed
  later isn't a missed chance. Each hex is looked at in turn, one per frame.
- A save from before this mod can hold offers at hidden capitals. They fail shortly after loading, and come back
  once the capital is revealed if the faction still esteems you.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarven Subversion is only offered at capitals you have revealed (DLL patch)'

RECORDS = 'database/smart_event/overworld_mission_records_cdb.bin'
ESTEEM_OLD = ("ADD_SMART_EVENT_FROM_TRIGGER( 'MISSION_OVERWORLD_ALLIANCE', 'MISSION_PARENT', "
              "OW_LOCATIONS.FILTER(\"OVERWORLD_MAP_HEX.CAPITAL.STRING.EQUALS(ARG('0').FACTION_ENTITY.FACTION.TAG.STRING)\", "
              "ARG('1').FACTION_ENTITY), 'MISSION_SOURCE_FACTION', ARG('1').FACTION_ENTITY.FACTION)")
ESTEEM_NEW = ("ADD_SMART_EVENT_FROM_TRIGGER( 'MISSION_OVERWORLD_ALLIANCE', 'MISSION_PARENT', "
              "OW_LOCATIONS.FILTER(\"AND(OVERWORLD_MAP_HEX.VISIBLE, "
              "OVERWORLD_MAP_HEX.CAPITAL.STRING.EQUALS(ARG('0').FACTION_ENTITY.FACTION.TAG.STRING))\", "
              "ARG('1').FACTION_ENTITY), 'MISSION_SOURCE_FACTION', ARG('1').FACTION_ENTITY.FACTION)")
CAVE = dllpatch.CAVE_VA + 0x1600
SITE = 0x1802af400
SITE_OLD = bytes.fromhex('66410f6e8424c4000000')   # movd xmm0, [r12+0xc4]
SYMBOLS = {
    'BASE': CAVE,
    'RESUME': 0x1802af40a,
    'FAMILY_PTR': 0x180599070,          # family records, as read at 0x1800ce3a2
    'GET_STATUS': 0x180169ff0,          # objective_system_get_status
    'SET_STATE': 0x18016a0f0,           # objective_system_set_state
    'STATE_FAILED': 5,                  # OBJECTIVE_STATE_FAILED
    'EVENT_NAME': 0x18053ce60,          # "TDTD_EVENT_OVERWORLD_HEX_EXPLORED"
    'EVAL_PTR': 0x180599268,            # property_component_system_evaluate_chain_string_args, as at 0x180267500
    'HASH_PTR': 0x180531420,            # as called at 0x18023d1fc
    'SEND_PTR': 0x180599220,            # as called at 0x18023d21e
    'TEST_REVEAL': int(os.environ.get('HMOD_KCM_TEST_REVEAL', '0')),    # test only
}


def apply(ctx):
    ctx.replace_cstr(RECORDS, ESTEEM_OLD, ESTEEM_NEW)
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x600, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'known_capital_missions code cave')
    jmp = b'\xe9' + (CAVE + labels['tick'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * 5, 'gamestate update -> capital offer check')
