"""Discovery Counts Found Rooms: discovery missions credit a room found before they started.

A room's discovery event fires once, ever, and a mission only counts events while it is active. Sacred
Well starts with Medicine and God of the Forge with Formalized Learning, so a room found earlier never
counts, and the forge god is unique, so that mission could never finish. MISSION_GEN_DISCOVER now
raises AMOUNT_DONE to 1 if a room of its type was ever found, at mission start and on every load.
At the target the part waits in a short list, and finishes at the next event callback: finishing during a
load pays the reward but never removes the mission, so every later load would pay again.
Rats in the Walls already starts at 1, so it is unchanged. The Spelunker achievement's parts use the
same generator, so its well and old statue parts also count old finds. See re/notes/discovery_quests.md.

DLL patch: MISSION_GEN_DISCOVER and on_event_callback, code and the list in the .hmod section.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Discovery missions credit a room found before they started (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0xb00
DRAIN = dllpatch.CAVE_VA + 0xec0
COUNT = dllpatch.CAVE_VA + 0xf60        # u32, then the list: 16 part pointers, up to 0xfe8
LIST = dllpatch.CAVE_VA + 0xf68
SYMBOLS = {
    'BASE': CAVE,
    'COUNT': COUNT,
    'LIST': LIST,
    'TO_I64': 0x1800d8ae0,              # property_comp::to_i64
    'FMT': 0x180558930,                 # "%s_EXPLORED"
    'SNPRINTF': 0x1805313f0,            # sys_snprintf IAT
    'WC_HASH': 0x180531420,             # wc_hash IAT
    'IS_KNOWN': 0x1801a3ce0,            # unlock_system_is_known
    'RESUME': 0x180086282,
}
SITE = 0x180086219
SITE_OLD = bytes.fromhex('4180fe047563')
EVENT_SITE = 0x1802653d0                # on_event_callback: mov [rsp+8], rbx
EVENT_SITE_OLD = bytes.fromhex('48895c2408')
ADVANCE = 0x180266130                   # attempt_advancement


def apply(ctx):
    code, _ = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x100, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'discovery_counts_found_rooms code cave')
    jmp = b'\xe9' + (CAVE - (SITE + 5)).to_bytes(4, 'little', signed=True) + b'\x90'
    ctx.patch_dll(SITE, SITE_OLD, jmp, 'discovery floor -> cave')
    code, labels = cave.assemble(os.path.join(HERE, 'cave_drain.s'),
                                 {'BASE': DRAIN, 'COUNT': COUNT, 'LIST': LIST, 'ADVANCE': ADVANCE})
    assert len(code) <= 0xa0, 'drain cave outgrew its share of .hmod'
    ctx.patch_dll(DRAIN, bytes(len(code)), code, 'discovery drain cave')
    ctx.patch_dll(EVENT_SITE, EVENT_SITE_OLD, cave.call(EVENT_SITE, DRAIN + labels['drain']),
                  'on_event_callback -> drain')
