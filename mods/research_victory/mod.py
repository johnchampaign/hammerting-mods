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
"""
DESCRIPTION = 'New victory: every research topic acquired plus 100 Mountain Lore and 100 Trade Lore'

LORE = 100

RECORDS = 'database/game_overs/game_over_conditions.bin'
DEMO_CHAIN = "AND( GAME_IN_DEMO_MODE, GAME_TIME_SECONDS.SUB(INT('3600')).GREATER('0'))"


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
    desc = type(wealth)(
        'Every tome of the Arcanum stands written and our scribes still hoard more lore than the '
        'shelves can hold! Scholars from far and wide climb to read the runes carved beneath '
        '%Oproperty_comp, and no hold in the Overworld can match its learning. Our story could '
        'end here, but it need not do so. If there be sagas yet untold: Play on! Play on! ',
        wealth.blobs)
    core.set('WIN_DEMO_TIME_DESC', desc)
