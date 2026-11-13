# Diplomatic ("World Conquest") victory, game.x86_64.dll 1.2.39

## Goal (code, not data)
MISSION_OVERWORLD_CONQUEST (database/smart_event/overworld_mission_records_cdb.bin) uses the
generator MISSION_GEN_OW_CONQUEST (property/smart_event_generation.h:1555), which builds three
eval chains on every load (the save keeps only TYPE=CLS_OWLOC, AMOUNT_WANTED, AMOUNT_DONE):
- `STATE_SET( 'AMOUNT_WANTED', OW_LOCATIONS.COUNT)`: snprintf format at 0x18053d268, loaded by
  `lea r8,[rip+..]` at 0x1800a1c94 (buffer 0x100).
- AMOUNT_DONE = locations whose FACTION_ENTITY is the MOUNTAINHOME + locations whose faction has
  RELATION_FACTION state RELATION_FACTION_ALLIANCE with the MOUNTAINHOME.
- done when NOT(AMOUNT_DONE < AMOUNT_WANTED); sets KV_WIN_DIPLOMATIC -> Diplomatic Victory screen
  and the Steam achievement ACHIEVEMENT_WIN_DIPLOMATIC (logged by liveops_property.h).
Eval math available (names in game.x86_64.dll .rdata near 0x538fe4): MUL, DIV, INT_DIV, ADD, SUB,
MOD, MIN, MAX, CLAMP, CEIL, FLOOR, LERP, LESS, GREATER. Numeric literals are quoted ('1').

## Why it is unreachable
West Hirdness: 35 locations = the Mountainhome + 3-4 each for 9 AI factions (BARAZ, DEADWOODS,
FROIA, LOOGUN, MARUNIA, OGOR, SYLVER, VENDAR, ZAKATH). The player never owns another location, so
it needs an alliance with all 9. The only alliance quest (MISSION_OVERWORLD_ALLIANCE) appears
when a faction ESTEEMS the Mountainhome; join_alliance then costs -1500 opinion of the
Mountainhome with every faction outside the alliance (re/notes/relation_crash.md), and the
opinion tick (rnd -30..+20) drifts down. All nine never line up.

## Fix: mods/reachable_diplomacy
The lea at 0x1800a1c94 points to a new chain in .hmod+0x200:
`STATE_SET( 'AMOUNT_WANTED', OW_LOCATIONS.COUNT.MUL('33').ADD('99').INT_DIV('100'))` (33%,
rounded up: 12 of 35). Works on existing saves. overworld.loc description updated.
Tested on the user's save: outliner shows "Control 1 / 12"; a 2% build (target 1) showed the
Diplomatic Victory screen at once. That test unlocked ACHIEVEMENT_WIN_DIPLOMATIC on the user's
Steam account.

## Save formats
- faction_system/data.bin: u64 0xffff, u64 bytes, u16 faction index per entity; names follow
  (FACTION_EMPTY 0, BARAZ, DEADWOODS, FROIA, LOOGUN, MARUNIA, OGOR, SYLVER, VENDAR, ZAKATH,
  DWARF 10, ENEMY, NEUTRAL). Faction entities 319-330, mountainhome 317.
- overworld_location_system/data.bin: u64 n, u64 bytes, n u16 location entities, then per
  location records with OWLOC_<type> (CAPITAL, TOWN, MARKET, MINE, LUMBERMILL, HUNTERS_LODGE,
  MOUNTAINHOME) and market stock classes.

## Reaching the capitals: fog (2026-11-05)
Dwarven Subversion's parent is the faction capital, chosen with no check for fog, so it is usually offered on a hidden hex. The hex marker
uses HAS_LOCAL_MISSION with no fog check, but `hex_info.entity` starts with ENABLE(OVERWORLD_MAP_HEX.VISIBLE). At savegame19 all three offers (Froia, Sylver, Vendar) were hidden.

How hexes get revealed (`overworld_map_system_explore_hex_near_entity` 0x18023cb40, `explore_overworld_from_trade_value` in item_util.h):
- Only sales pay for it, plus the Expedited Expeditions reward (3 hexes within 8). The "explore for 1 Trade Lore and 100 coins" text has no UI that I found.
- Sale value adds to KV TOTAL_SALE_VALUE on the mountainhome. Over 50 buys a hex within 1 of the town sold to. If none, over 200 buys one within 3 for 200, then over 500 one within 8 for 500. Otherwise it stays banked.
- A hex with road byte +0xf6 non-zero is eligible only if a neighbour along a flagged edge (+0xf0..+0xf5, directions in `tools/owhex.py`) is explored. All locations are on roads, and both maps seen have one road network, 103 and 119 hexes.
- savegame9 to savegame19, 45 reveals: 5 on roads, 2 of them locations. At savegame19: 63 of 217 hexes, pot 229, 72 hexes eligible of which 3 on roads, and none within 1 of any of the 5 known places. Road steps to Sylver 8, Vendar 8, Froia 10.
- Only that function sets +0xf7 in play, with +0xc8 on the system (update_hex_visibility) and TDTD_EVENT_OVERWORLD_HEX_EXPLORED. The other writes are map generation, load and copies.

Correction: I first told the user Vendar's capital could never be revealed because its road ran off the map. That came from a parser bug that gave each hex the next hex's coordinates. With `tools/owhex.py` all road edges are two-way and on the map.

## mods/known_capital_missions (2026-11-05)
The user chose to offer Dwarven Subversion only at revealed capitals, rather than reveal them for it. This replaces `mods/reveal_mission_locations`, which revealed hidden hexes with missions and is no longer installed.
- The esteem trigger's chain gains OVERWORLD_MAP_HEX.VISIBLE in its filter. ADD_SMART_EVENT_FROM_TRIGGER does nothing on an empty argument (overworld_system.h:569).
- The cave at 0x1802af400 (gamestate::update, also while paused, about 10 frames a second when measured paused) looks at one hex per frame. On a hidden hex it sets the first INACTIVE child objective to FAILED. On a known capital that esteems the player, isn't allied, and has no live Dwarven Subversion child, it evaluates the add chain with `property_component_system_evaluate_chain_string_args` (slot 0x180599268).
- Property ecs is mainstate + 0x1e80: mainstate.h order, stride 0x78, base 0x80. The +0x68 at 0x180267500 is off another pointer; using it on the mainstate ended the game during load.
- A second reward slot on MISSION_DWARVEN_EMBASSY_TRIGGER (two ADD_SMART_EVENT in one completion) froze the sim right after the reveal: frame counter stopped, no exception logged. Cause not found; no record in the game uses two slots. Don't use it.

Tests on copies of savegame20, one run each, no exceptions, no unlocks. Opinions set with save edits, on the faction's `RELATION_FACTION_OPINION_354` KV. 1040 crossed for Loogun, but Deadwoods at 1040 did not; 1400 did. `HMOD_KCM_TEST_REVEAL=<hex entity>` reveals that hex with the real event after 2048 frames.
| Case | Result (next autosave) |
|---|---|
| Old offers at hidden Froia, Sylver, Vendar | All gone; the three factions still Esteemed |
| Test reveal of Froia's capital, already Esteemed | One Dwarven Subversion at 562, on Suthville's Missions tab, with Embassy, Water and Mote & Beam; Sylver and Vendar stayed hidden with none |
| Loogun crosses to Esteemed, capital hidden | No offer |
| Deadwoods crosses to Esteemed, capital revealed | One offer at 391 |
Not seen: whether failing an old offer shows a notification (nothing on the one screenshot, taken about 45 s after unpausing). Not tested: long play, a reveal from a real sale, delivering, completing an alliance, an alliance that later breaks (the check would offer again if still Esteemed).
