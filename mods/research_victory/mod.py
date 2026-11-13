"""Research Victory: a third way to win, by finishing the research tree and banking lore.

The victory fires once every research topic is acquired and the mountainhome holds at least
LORE Mountain Lore and LORE Trade Lore (KV_MOUNTAIN_LORE, KV_TRADE_LORE, the two currencies the
Arcanum spends).

Victories are rows of database/game_overs/game_over_conditions.bin (game_over_record: tag[0x40],
event tag[0x40], eval chain[256]); the game over system checks each row's chain and shows the
victory screen titled with the row's tag, localized, and the text of <tag>_DESC. Row 0,
WIN_DEMO_TIME, only fires in demo builds. Saves keep one game-over slot per row, matched by tag
hash, so this mod gives that row a new chain and new text but keeps its tag: renaming it would
leave saved slots pointing at no record. MOUNTAINHOME.RESEARCH('ALL' | 'ACQUIRED') lists research
tags (unlock_system.h). Like the other victories, choosing Play on! keeps the colony going.

The Victory Conditions panel lists missions of category VICTORY_CONDITION_MISSION, so the mod
appends a display-only mission, MISSION_RESEARCH_VICTORY, copied from MISSION_AFFLUENCE
(smart_event_record: tag 0x40, category 0x40, ..., u64 dependencies[4] +0x90, 16 parts of 0x48d0
from +0xb0, reward after). Missions start when the unlock system unlocks their tag, which happens
once every dependency (research) is acquired (event_callback_unlock -> add_se_with_objective);
the first missions are spawned at new game. Keeping Affluence's dependency, Metallurgy, makes the
two victories appear together. A save that already has Metallurgy never fires that unlock, so
games started before this mod don't list the mission (the victory still works there).
Its three objectives wait on a key value nothing sets, so they never complete; their titles are
localized text whose compiled chains show the live research count and lore. The victory itself
still comes from the game-over row.
"""
import struct

from evalchain import compile_chain
from loc import Entry
from wchash import wc_hash_string

DESCRIPTION = 'New victory: every research topic acquired plus 100 Mountain Lore and 100 Trade Lore'

LORE = 100

RECORDS = 'database/game_overs/game_over_conditions.bin'
DEMO_CHAIN = "AND( GAME_IN_DEMO_MODE, GAME_TIME_SECONDS.SUB(INT('3600')).GREATER('0'))"

MISSIONS = 'database/smart_event/cave_mission_records_cdb.bin'
MISSION = 'MISSION_RESEARCH_VICTORY'
TAG = 0x40                      # wc_tag: name[0x38], u64 wc_hash(name)
PARTS = 0xb0
PART_SIZE = 0x48d0
PART_TITLE, PART_DESC = 0x400, 0x440
REWARD = PARTS + 16 * PART_SIZE
REWARD_KV_CHAIN, REWARD_KV_TARGET = 0x200, 0x2200     # _kv[0] at +0, its chain and target entity
CHAIN_LEN = 0x400
# objective title key: (text, chains filling its %Oproperty_comp)
OBJECTIVES = {
    'MISSION_RESEARCH_VICTORY_TOPICS': ('Research: %Oproperty_comp / %Oproperty_comp',
                                        ["MOUNTAINHOME.RESEARCH('ACQUIRED').COUNT",
                                         "MOUNTAINHOME.RESEARCH('ALL').COUNT"]),
    'MISSION_RESEARCH_VICTORY_MOUNTAIN': ('Mountain Lore: %Oproperty_comp / {lore}',
                                          ["MOUNTAINHOME.KEY_VALUE('KV_MOUNTAIN_LORE')"]),
    'MISSION_RESEARCH_VICTORY_TRADE': ('Trade Lore: %Oproperty_comp / {lore}',
                                       ["MOUNTAINHOME.KEY_VALUE('KV_TRADE_LORE')"]),
}


def put_tag(d, at, name):
    h = wc_hash_string(name) if name else 0
    d[at:at + TAG] = name.encode().ljust(0x38, b'\0') + struct.pack('<Q', h)


def put_chain(d, at, chain):
    assert len(chain) < CHAIN_LEN, chain
    d[at:at + CHAIN_LEN] = chain.encode().ljust(CHAIN_LEN, b'\0')


def add_panel_mission(ctx):
    d = bytearray(ctx.read(MISSIONS))
    count, total = struct.unpack_from('<QQ', d, 0)
    size = total // count
    names = [d[16 + i * size:16 + i * size + 0x38].split(b'\0')[0].decode() for i in range(count)]
    assert MISSION not in names
    rec = bytearray(d[16 + names.index('MISSION_AFFLUENCE') * size:][:size])
    assert rec[TAG:TAG + 0x38].split(b'\0')[0] == b'VICTORY_CONDITION_MISSION'
    template = bytes(rec[PARTS + PART_SIZE:PARTS + 2 * PART_SIZE])      # the fullness objective
    put_tag(rec, 0, MISSION)
    rec[PARTS:REWARD] = bytes(16 * PART_SIZE)
    for i, key in enumerate(OBJECTIVES):
        at = PARTS + i * PART_SIZE
        rec[at:at + PART_SIZE] = template
        put_chain(rec, at, "MISSION_GEN_GET_KV('KV_HMOD_RESEARCH_VICTORY_PANEL', '1', '1')")
        put_tag(rec, at + PART_TITLE, key)
        put_tag(rec, at + PART_DESC, MISSION + '_OBJECTIVE_DESC')
    put_tag(rec, REWARD, '')                 # no reward: the mission never completes
    put_chain(rec, REWARD + REWARD_KV_CHAIN, '')
    put_chain(rec, REWARD + REWARD_KV_TARGET, '')
    d += rec
    struct.pack_into('<QQ', d, 0, count + 1, total + size)
    ctx.write(MISSIONS, bytes(d))

    cave = ctx.loc('cave')
    cave.set(MISSION, Entry('Mountainking of Lore'))
    cave.set(MISSION + '_DESC', Entry(
        f'Complete every research topic in the Arcanum and keep {LORE} Mountain Lore and {LORE} '
        f'Trade Lore in hand at the same time. Let no hold in the Overworld match our learning!'))
    cave.set(MISSION + '_OBJECTIVE_DESC', Entry(
        f'All research must be acquired while we hold at least {LORE} of each kind of lore.'))
    for key, (text, chains) in OBJECTIVES.items():
        cave.set(key, Entry(text.format(lore=LORE), [compile_chain(c) for c in chains]))


def apply(ctx):
    over = LORE - 1
    chain = (f"AND( MOUNTAINHOME.RESEARCH('ACQUIRED').COUNT.EQUALS(MOUNTAINHOME.RESEARCH('ALL').COUNT), "
             f"MOUNTAINHOME.KEY_VALUE('KV_MOUNTAIN_LORE').GREATER('{over}'), "
             f"MOUNTAINHOME.KEY_VALUE('KV_TRADE_LORE').GREATER('{over}') )")
    assert len(chain) < 256, len(chain)
    ctx.replace_cstr(RECORDS, DEMO_CHAIN, chain)
    core = ctx.loc('core')
    assert core.key('WIN_DEMO_TIME').text == 'The End of Time'
    core.key('WIN_DEMO_TIME').text = 'Mountainking of Lore'
    wealth = core.key('WIN_AFFLUENCE_DESC')
    assert len(wealth.blobs) == 1 and wealth.text.count('%Oproperty_comp') == 1
    desc = Entry(
        'Every tome of the Arcanum stands written and our scribes still hoard more lore than the '
        'shelves can hold! Scholars from far and wide climb to read the runes carved beneath '
        '%Oproperty_comp, and no hold in the Overworld can match its learning. Our story could '
        'end here, but it need not do so. If there be sagas yet untold: Play on! Play on! ',
        wealth.blobs)
    core.set('WIN_DEMO_TIME_DESC', desc)
    add_panel_mission(ctx)
