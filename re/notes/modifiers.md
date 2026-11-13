# Modifiers, profession entries and crits (2026-11-06)

## Entry records
`modifier_entry` is 0x23c8 bytes (`database/modifier/entry/modifier_entries_cdb.bin`, records after a 16-byte header):
- +0x00 name tag, +0x40 style tag (`m_profession`, ...), +0x80 group tag, bytes at +0xc4..+0xc7 (flags read by tooltips).
- +0xc8 four funcs of 0x8c0 bytes: source tag +0 (`FROM_DWARF`, `FROM_ITEM`, ...), compute tag +0x40
  (`dependencies_multiply_and_sum`, `dependencies_key_value`, `dependencies_combine`), 16 dependency tags +0x80,
  16 key tags +0x480 (for `dependencies_key_value`), 16 weights +0x880 (i32 16.16).
- A tag is name[0x38] then wc_hash(name). A dependency list ends at the first zero hash; `modifier_system::initialize`
  stops reading funcs at the first zero compute hash.
- The compute functions live in entity.x86_64.dll (registered in `modifier_system::initialize`; multiply_and_sum is
  0x1800606c0). It gets the dependency values from its caller.

## Generated profession entries
`mainstate::mainstate` (game DLL, loop 0x180296c00-0x1802979fe) builds seven entries per profession record, kind r13:
0 `%s_LEVEL` (FROM_DWARF key_value `KV_LEVEL_%s`), 1 `%s_SPEED` (0.01 * level, if `_has_speed`), 2 `%s_CRIT_SUCCESS`
(0.02 and 0.01 * two attributes + 0.03 * level, plus a FROM_ITEM tool func; if `_can_crit`), 3 `%s_CRIT_FAILURE`
(-0.01 * level), 4 `%s_XP_GAIN` (no funcs), 5 `%s_PRODUCTION` (2 and 1 * attributes + 3 * level, plus tool func),
6 `%s_DPS` (combine production and speed). Each is committed at 0x1802976e8. `database_full_init_from_archive` only
stores the names in the profession record.
Data entries that use a profession level: SKILL_VISION_RANGE, STAT_MOVE_SPEED, STAT_CLIMB_SPEED and
STAT_FALLING_DAMAGE_RESISTANCE (explorer level).

## Nothing read PROF_ALL_*
PROF_ALL_LEVELS, _SPEEDS, _CRIT_SUCCESSES and _CRIT_FAILURES are entries without funcs; traits, statuses and gear grant
them, and no entry depended on them. Seen in memory on a copy of KrazJomsglind savegame25: every profession value was
exactly its formula without them.

## One func per source
A second FROM_DWARF func in an entry is ignored (tried: kept its slot through initialize, contributed 0 on a save copy
and in a new random game). The tool func (FROM_ITEM) is the only second func the game uses. To add inputs, extend the
dependency list of the existing FROM_DWARF func; that worked (`mods/all_profession_bonuses`).

## Crit roll
In the produce animation callback (`event_callback_anim`, node_produce.cpp, roll at 0x1804d25ac): crit success and
crit failure values each times 0.1 (0x1999 / 65536), clamped to 0..1, then a PCG roll 0-99: success if the roll is
above 100 - 100 * that, else failure if below 100 * the failure value. So a value of 0.92 is a 9.2% chance, values
above 1 are fine, and negative values mean 0%.

## Reading values
`tools/modvals.py [--funcs] PREFIX...` prints computed values per entity list from the running game (read-only).
Values refresh while the game runs; one list per entity, dwarves near the start of the list array.
