# Lava (BUGS.md B8), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 238 node_fluid_pump_hand, 237 node_fluid_drain_sink, 127/226 fluid_system,
205/275 fluid_source_system, 256 node_avoid_fluid, 108/220 gamepath_system, 55 sensor_refill_statusbar,
280 effect_templates, 16 navgraph_query_system, 39 utility_system (plus 22, 40, 57, 109, 155, 214 already
present). Bytes are from the pristine DLL (`game.x86_64.dll.hmod-orig`). All candidate sites are identical in
the live DLL, so no installed mod touches them, and `.hmod` 0xc00..0xd40 is zero. **The sections below are static analysis and one
save read, written before any test.** Each claim is marked [V] read in code or data, or [I]
inferred.

Reports:
- S1/3187992943276256937 (fetched, Mar 2022): with a pump on lava and "Maintain in Mountainhome", 100 water and
  a target of 20 lava means no pumping. Workaround: building-inventory mode or no maintain.
- S0/4695657045621780452 (fetched, Oct 2024): five pumps at lava lakes for sulphur sprouts. Mountainhome mode
  shows 100/20 with no lava anywhere; building mode shows 0/20; "no dwarf came". Replies disagree: one says
  lava pumping works, one blames the water count, one says a farmer with a rake is needed.
- R/174f4l6: **the fetch failed (Reddit is blocked here, www and old).** The two threads above mention only the
  pump. So I never read the original wording of "burns lava" and "walks into lava". Those two symptoms are
  taken from BUGS.md alone.

## Lava on workplaces (2026-11-09). Read this first.
Test: `mkflood` (lava amount 7 on x 504-509 y 970, 510-515 y 971, 516-518 y 972, 519-528 y 973) on a copy of KrazJomsglind
savegame32. It flows downhill and pools (16 tiles, amount 7) in the trough at x 478-493, y 966, which is the floor of storage 3107 and
the walkway between the west and east parts of the colony. Invaders off, `_test_drop_log` for the BT switch lines, live positions from
memory every 0.5 s. The flood script is `re/notes/lava_mkflood.py`; the autosave with the lava already pooled is
`~/.local/share/hammerting-tools/test-saves/lava_pooled.2.save` (copy it into the save folder under a test name).

Why dwarves walked in, all [V]:
- **No direction on edges.** `graph_edge` (graph/public/graph/graph_types.h) has `_node_id[2]`, and the edge cost callback gets
  (user_data, edge, cost, run_context): nothing says which end the step starts from. The old gate checked node 0, and the movement log
  showed a dwarf step from dry node 26686 (494.5, 967) into lava node 26685 along an edge whose node 0 was the lava end.
- **The callback is skipped for edges without data.** graph.x86_64.dll `graph_graph_query_continue_query` 0x1800086f4:
  `test dword [edge], 0x7fffff00; je` past the callback. Flag data is EDGE_DISABLED 1, EDGE_SHOULD_AVOID_STANDING 2, EDGE_HAS_FLUID 4
  (gamestate/ai_types.h). `tile_graph::update_edge_masks` visits only blocks with dirty bits 0x34 (front, fluid, layer; map.h
  MAP_DIRTY_*), so lava at rest after a load gets no fluid flag. And it handles tile edges only: the storage's walkway edges (nodes
  267xx, type 1, cost 1.0-1.5) had data 0 in memory with lava on them. So no lava cost at all applied there, vanilla included.
- **Reversed searches.** Job and hauling costs search from the target back to the walker (`_invert_directional_edges` at run context
  +0x48 flips only directional edges). From a target inside lava, every step "leaves lava". Dwarves claimed items for the flooded
  storage, failed to path, dropped them and retried: 377 haul restarts by dwarf 3794 in 4 minutes.
- Where things are: node positions at tile graph +0x28 (count +0x30) cover building nodes too; edge fluid masks at +0xb8 (count +0xc0,
  262140 in this colony). The run context: `_start_nodes` +0, count +8, `_invert_directional_edges` +0x48, `_edge_mask` +0x4c (bit 2 =
  lava, set only in creatures' own movement queries). The node cost callback is also called only for nodes with data (stations,
  locks), so it can't gate ordinary steps. A negative cost from the edge callback skips the edge; returning 0 keeps the default.

Fix (`lava_no_walk`, reworked): graph.x86_64.dll 0x1800086fa `74 40` -> nops, so every edge goes through the callback. The gate
blocks any edge touching lava except in a query with the lava bit whose start node is in lava. `sweep.s` marks every block holding
lava (amount >= 2) fluid-dirty on the first `update_edge_masks` after `tile_graph::initialize`, and every 128th call clears bit 15
(looked) on all masks so walkway edges are re-read. `lava_escape` now scores only amount >= 2.

| Run (same copy, normal lava damage) | Result |
|---|---|
| Old gate + escape + burn, fresh flood | Nobody died (burn at a tenth), but every dwarf walked the flooded storage: 5-26 escapes each in 10 min |
| Old gate + escape, pooled lava (autosave from the first run) | One death at 2.5 min, two dwarves stood still in lava 40 s |
| Direction gate (expanding node from the caller's frame) + load sweep | One death; the walkway edges still had data 0 |
| + graph patch | No entries in 4 min, but a haul loop on the flooded storage |
| **Final gate (lava bit + start in lava)** | **No entries in 4 min, the two starting in lava walked out, no haul loop, 4.84x at top speed** |
| **Final, fresh flood** | **The Cave Farm worker escaped in about 10 game s and went back to work; no dwarf died** (a green slime did) |

## Deaths fix attempts (2026-11-02). Read this first.
All on colony copies with invaders off (`_test_quiet`). The flood is the 46-tile test below; the hall strip is
6 tiles of lava in a dip in the main hall floor at x 536-541, y 993, between the east side and the cook house and farm.

| Run | Result |
|---|---|
| Hall strip, no fix | Dwarves cross repeatedly (0 to 6 of them west of it between autosaves), about 300 HP per crossing, no deaths in about 17 game minutes. `natural_healing` was on and heals it back. Without that mod the damage would add up. |
| **Hall strip, `lava_no_walk`** | **Nobody crossed in about 17 game minutes, health steady.** But all six ended up east of it, mostly standing still, because the farm and cook house were cut off. The two who started west got east, so some one-way route exists. 1 run. |
| **Hall strip, `lava_no_walk`, 3 Small Stone Bridges** (2026-11-03) | **Route restored.** Live position tracking over 270 real s (about 21 game minutes): 12 crossings, all on the deck, none by another route, and 0 samples in the lava row. Health steady, no deaths, from t = 8198 to 11367 (about 53 game minutes). 1 run. |
| Normal colony, speed at top setting | 4.7 game s per real s with `lava_no_walk`, 4.7 without (one interval each). |
| Flood, x50 lava cost -> blocked in the cost table | Wiped. Six in lava at the cave farm. |
| Flood, check using the edge's lava flag only | Wiped, deaths at nearly the same ticks as no fix. So the flag was not set on lava at rest. [I] |
| Flood, map read on every edge (first form of the gate) | Five dwarves unhurt up to t = 8477, against three deaths by t = 8358 with no fix. Top speed fell to 0.6 game s per real s (1.6 on a normal colony), so it ran only 170 game seconds. Not a usable form. Dwarf 2139, in lava at load, still died. |
| Flood, `lava_burn` + `lava_escape` | Defeat, about 1.5 minutes later than no fix. 2139 moved. A second run of the same mods came from a failed install and is the same result. |
| Flood, first gate + `lava_escape` | 2139 died at the same tick, 13 s in, without moving. Others unhurt to t = 8403. |
| Flood, final gate + burn + escape | **Defeat at about t = 9188.** Four dwarves at (519.9, 992) in lava beside loose ore, static for 300 game s. How the first got in is not known; a fall at the lip or a job reached after entering are guesses. |

What this does and does not show:
- `lava_no_walk` stops walking from dry ground into lava across a floor strip. It does not make a colony survive lava on its workplaces.
- **Bridges work with `lava_no_walk`.** Small Stone Bridges can be ordered over lava and take 2 Granite Slabs each. Each covers 4 tiles at center-2..center+1, with its deck one row below the center, here y 994 above lava in y 993. Three (centers 535, 539, 543 at y 995) covered the 6-tile strip, partly over solid floor. The builders were not cut off. The colony had the slabs: a colony without them was not tested, and neither was a Walk Bridge, or lava that reaches deck level.
- **The idling is not shown to come from the cut.** The note in the hall strip row above was my inference. With the bridges the dwarves still stood still most of the time (0-23% of samples moving), and by t = 11367 all six were west with "Dwarves Idle" and "Lack of Food" showing. Hunger icons also showed in the run without bridges. So bridges restore the route, but whether work output recovers was not measured.
- **Unexplained:** dwarf 2098 went from (542, 994) at t = 8407 to (525, 993) at t = 8556, before x 536 was covered, and probably before the first span was finished. So some route across exists without the deck, as the two west-to-east moves in the earlier run also suggest. It has not been traced. Once the deck was up, no crossing used it.
- Final gate alone on the flood was not run. The first form's survival there may be only because of its short run.
- `lava_escape` has not been shown to save anyone. `lava_burn` only delays. Neither is recommended.
- I suspected lava cost is lost on a load, because query records are rebuilt from a small save block and hold the mask. **Not proven.** What was observed is above: dwarves walk through at-rest lava after a load.
- Anything on dry ground is blocked by `lava_no_walk`, lava creatures and invaders included. Not observed in play.
- It stores a "looked" marker in bit 15 of the edge's u16 fluid mask. No fluid type uses it. Not checked: what `update_edge_masks` does to it when it rewrites a mask; losing it only costs a re-read.

## Test results (2026-11-02, later runs on copies of the user's colony). Read this first.
Setup: a 5 x 3 pit at x 498-502, y 991-993, carved by clearing bit 21 (front) of those map tiles, which
loads fine because the nav graph is rebuilt on load. Fluid set by save edit. A Hand Pump built over it in
play: it is already unlocked in the colony (Infrastructure > Excavation & Extraction) and took one builder 26 s of
log time. Invaders off (`mods/_test_quiet`). No achievements unlocked.

| Test | Result |
|---|---|
| Pump yields what it stands over | Yes. Same pump, pit switched from water to lava by save edit, then yields lava items (inventory icons). |
| Water pump, Mountainhome, target 20 | Runs and stops: `x11 / 1`, then `x20 / 20`. |
| **Symptom 3, unpatched:** lava pit, 0 lava items, 15-19 water in the colony, target 5 | **Reproduced.** Shows `x15 / 5`, no pumping for about 4 minutes of log time, until I added a Local entry. |
| Workaround, Local maintain, same save | Pumps at once. But the Local count also sums every fluid in the building: `x19 / 20` with 9 water + 10 lava. The target therefore means total fluid held. This corrects the "Local mode" paragraph below. |
| **`pump_fluid_count` (P3), lava pit, same save** | **Works.** Stopped at exactly 5 pumped items, with 13 water and 5 lava in the inventory. |
| P3, water pit, lava in stock | **Works.** `x14 / 5` with 14 water + 10 lava (row 2, Local, shows `x24`). This run also confirms comps[0] of pumped items is CLS_FLUID_x. |
| Fuel, bars at 0 (room 1000), lava beside the cook house | No lava taken in the about 3 minutes watched; bars refilled, coal items were removed. Fits value x 30 / (cost + 10), where coal is worth double with room to spare. |
| **Symptom 1, unmodded:** bars at 700 (room 300) | **Reproduced, 2 runs of 2.** One bar went from exactly 700 to 950, with no coal item removed at all in the first run. Coal adds 500 and charcoal 650, and only lava has value 250. Which building owns that bar was not identified. |
| **`lava_not_fuel`, same save** | **Works, 1 run.** All three bars stayed at 700 for about 7 minutes of log time. |
| **Symptom 2:** lava (amount 7) on the whole floor row of the cook house block (x 504-529, y 993) and the cavity under it (46 tiles) | **Reproduced, 1 run.** Colony wiped: Defeat at tick 84988, about 5 game minutes after load, all six dwarves "killed". First at tick 82123, about 15 game seconds in. Three control runs with the same stock and lava only in the pit had 0 of these six ids killed (up to about 10 minutes of log time). |

Limits of these results:
- The flood is extreme. It does not separate "route crosses lava" from "job site in lava", and at least one dwarf was probably standing in it at load. It shows that dwarves keep walking in until none are left, with no refusal. Autosaves did not run in that session, so there is no health trace, and I did not watch it on screen. Deaths are attributed to lava by elimination.
- Three dwarves were logged "killed", then "resurrected" about 90-100 game seconds later, then "killed" again. What "resurrected" means here is not known. It also appears on the cook house in lava-free runs.
- P1 or F2 alone would not stop this: job choice ignores lava (mask 0 on reversed queries), so a job inside a pool is still taken. P2 and blocking are still untested.
- Water items appear in the colony with no pump (`CLS_FLUID_WATER` spawns in the log before the pump existed, 23 by 17 minutes) and also leave the pump's inventory over time. Source and consumer not traced.
- Loose coal rots: about 157 coal items were removed at 4-6 minutes of log time. So later parts of the fuel runs had little or no coal to choose. The 950 result itself happened before that, with coal still present.

## Earlier in-game test (2026-11-02, copy of the user's colony)
- **`map/map.bin` edits work.** Six tiles set to `0x17` in the top byte at x 571-573, y 994-995 loaded
  as real lava: it ran downhill, and the autosave at t = 8493 held the same 42 units as 6 tiles at
  (509-514, 991), under the cook house, visible and glowing. Place lava knowing it will flow, and
  on a level or walled spot if it has to stay put. Type 2 = lava is confirmed by this.
- **Walking into lava: not reproduced in this run, but see the flood above.** No dwarf-kind entity was killed in about 15 game minutes (ticks 81975 to 91097)
  (top speed, with auto-pauses) with dwarves working next to the pool. It is one colony and one
  pool, so it does not show the bug is absent, and which dwarves crossed was not tracked.
- Entity 2655, the cook house, was repeatedly "killed" and "resurrected" in the log. It also
  appeared in a run without lava, so lava is not shown to be the cause.
- **`lava_not_fuel` (F1) is built and installed.** The game loads and ran 60 s with it, with no errors,
  and the installed archive differs from the original only in the value at 0x2b19d8. The change itself
  (a furnace refusing lava) was not observed: that needs a pump or lava items.
- At this point P3, P1, P2 and F2 were not built. P3 now is (above); P1, P2 and F2 still are not.

## Short version
- **Symptom 3 is a real, exact bug.** The hand pump has one recipe, CLS_FLUID_CRAFT. No item has that as its main
  modifier, so `global_inventory_system_get_matching_inventory` misses its class map and falls back to summing
  every item in tracked type 0, GITT_FLUID_ON_MAP, which is water + lava (`SPECIAL_TYPES`). [V]
- **Symptom 1 is a data entry plus a distance-weighted score.** CLS_FLUID_LAVA carries STATUSBAR_FUEL_INSTANT 250
  (coal 500, charcoal 650), and any item with a positive value is a fuel candidate. Score is about value x 30 /
  (path cost + 10), so near lava beats far coal. No player setting filters it. One data byte fixes it. [V]
- **Symptom 2: the planner discourages lava but does not forbid it.** Lava edges cost x50 and there is no cost cap.
  Lava does 100 HP per game second to a 1000 HP dwarf with no natural healing, applied in 4-second windows. Escape (ACTION_AVOID_FLUID) has
  rank IDLE, so a dwarf with any work stays in. All of that is [V]. **Which of these actually kills dwarves in
  play is not established**: no reproduction, no report text.
- **The chain:** alliance quest <- 10 licorice <- 20 sulphur sprouts <- about 8 lava items, one per harvest. Symptoms
  1 and 3 hit the "lava item" step. In the user's colony the larger obstacle is distance: the nearest lava is
  896 tiles (Manhattan) from the entrance and none of it is explored. [V]

## The systems

### Fluids [V]
- Map tile u32: bits 24-26 amount (0-7), bits 27-30 fluid type, 0 = none (`map.h`). `database/fluid/fluid_cdb.bin`, 2
  records of 0x108: tag, `_modifier` +0x40, `_effect_modifier` +0x80, `_amount_factor_modifier` +0xc0, light +0x100,
  viscosity +0x104, `_effect_amount_threshold` +0x105, `_self_index` +0x106 (set at load, 0x180273d85).

| | modifier | effect | viscosity | threshold |
|---|---|---|---|---|
| WATER | CLS_FLUID_WATER | EFFECT_IN_WATER: STAT_MOVE_SPEED -0.75 | 20 | 5 |
| LAVA | CLS_FLUID_LAVA | EFFECT_IN_LAVA: STATUSBAR_HEALTH_GAIN -10 | 20 | 1 |

- In the user's map, type 1 has 16754 tiles at y 157..992 and type 2 has 1598 tiles at y 57..156. So 1 = water and
  2 = lava. [I, from depth and record order; the type value is not read anywhere that names it]

### Lava as an item [V]
- The only source I found is the hand pump. CLS_FLUID_LAVA appears as an input and in the fluid record, never in a
  loot table. Consumers:
  - `ORDER_SOW_LAVA_PLANT` (recipe_order_cdb.bin rec 20): 1 lava.
  - `CLS_DRINK_DRAGONS_BLOOD` (brewers still rec 1): 1 lava + cinnamon + yeast + barley, fuel 100.
  - `CLS_FLUID_LAVA_DRAIN` (FLUID_DRAIN_SINK): 1 lava, puts it back on the map.
  - Fuel, see symptom 1.
- Hand pump: `MECH_FLUID_PUMP_HAND`, 5 wide. Body ` CCC`/` CCC`/` CBC` above, three rows of `FFFFF` below (room_default.bin rec
  93, layout at +0x1098..+0x11d8). `FLUID_LAVA_AMOUNT_FACTOR` 2 and `FLUID_WATER_AMOUNT_FACTOR` 0.5 on the room.
- Recipe (recipe_fluid_pump_hand_cdb.bin, one record): tag and output CLS_FLUID_CRAFT, no item inputs, cost
  KV_STATUSBAR_MAP_FLUID_LOCAL 1, producer FLUID_PUMP_HAND, PROF_FARMER.
- `update_local_fluid_statusbar` 0x180498420, run by the building's AI through `bt_fluid_pump_hand_update`: sums fluid
  amount over the `F` tiles into STATUSBAR_MAP_FLUID_LOCAL and writes KV_FLUID_TYPE = tag hash of the last wet tile's
  record (0x18049866a). KV stays as it was if no tile is wet.
- `default_production_complete_cbck` (recipe tag == CLS_FLUID_CRAFT, 0x1802d6fd0) reads KV_FLUID_TYPE and uses the
  fluid record's modifier as the output. So what a pump yields depends only on where it stands. There is no "set to
  lava" setting; a pump over both fluids yields whichever wet tile it read last. [V]
- PROF_FARMER has `requires_tool` = 0 (professions_cdb.bin +0xc0), so the forum's "needs a rake" is not supported by the data.

### Fuel [V]
Fuel users (room_modifiers STATUSBAR_FUEL_MAX): foundry and smithy 3000; small foundry, small smithy, brewery, small
cook house, small tavern, small whitesmith, drill crusher 1000; cog drill 800; brazier and lantern post 200.
Exactly three items carry STATUSBAR_FUEL_INSTANT (item_modifiers_cdb.bin): CLS_CHARCOAL 650, CLS_ORE_COAL 500, CLS_FLUID_LAVA 250.

## Symptom 1: burning lava
Mechanism (`re/notes/food_ai.md` has the sensor):
1. `refill_statusbar_sensor::process_modifier_entities`: an item with a positive value for a statusbar becomes a filler
   for it (`cmpl $0,(%rax,%rsi)` / `jle` at 0x1802c5746). [V] There is no list of fuels and no class check.
2. `process_fillers` 0x1802d43f0 drops items with a claim other than CLAIM_REFILL_STATUSBAR, then computes value. [V]
3. `update_hauler_for_needer` 0x1802c5e90: `score = int(value) * 30 / (int(path cost) + 10)`, 0x1802c6452..0x1802c6493. [V]
   Fillers are taken best first. [V, food_ai.md]
4. Value comes from `evaluate_statusbar_filler` 0x1802dd420, which caps by room left in the bar (`cmovl`, 0x1802dd9cd). [V for the
   cap; I for the exact weighting, which I did not fully work through.] So:
   - In a big bar, lava is worth half of coal, so lava wins when its path cost + 10 is under half of coal's. [I]
   - In a bar with 250 or less free (always for braziers, lanterns), values tie and the nearer item wins. [I]

Why it happens "instead of coal": distance, not preference. Pumped lava stored near a workshop competes directly. A
colony with no pumped lava never burns any. [V for the source list]

What a player can do: nothing direct. The filter is the modifier value; I found no per-building or per-item fuel
list. `change_individual_workplace_craft_refill_job_prio` changes job priority, not the choice of item. An item claimed by a
queue (CLAIM_PRODUCE) is safe, but that claim starts when the item enters the building (`production_stall.md`), so
stock in storage is exposed. [V] Keeping coal nearer than lava lowers the odds. [I]

What the lava is then missing from: sowing and drink inputs. Each lava item burned is a lost `ORDER_SOW_LAVA_PLANT`, which
blocks a plant at stage 1 (below). With Maintain Mountainhome, a burned item lowers the count and the pump works again,
so the loss is rate, not a hard stop. [I]

## Symptom 3: the count
Function: `global_inventory_system_get_matching_inventory` 0x180200420. Callers: `refresh_maintain_globally`
0x1801521b0 (0x1801522a8) and the UI property `MATCHING_ENTITIES_GLOBAL` (`property/production_system.h`). [V]

1. rdx = &recipe tag hash (the output hash for deliver-only recipes), lookup in the class map at gis+0x130: `call
   0x18020ab00` at 0x180200460. [V]
2. That map's key is `entry._comps[0]` tag, the item's first modifier (add_entry, 0x180207079..0x180207083). No item has
   CLS_FLUID_CRAFT as this, so the lookup is null. [V for the key; I that comps[0] is CLS_FLUID_x for pumped items]
3. Null path, 0x18020046e: if recipe tag == CLS_FLUID_CRAFT (hash slot 0x1805a0f00), sum the requested claim types over
   **every entry in the array at gis+0xa0** (0x18020047f..0x1802004fa). Count +0xa8 is a u32. [V]
4. gis+0xa0 is tracked type 0 = GITT_FLUID_ON_MAP (`global_inventory_system_get_global_inventory_entries_for_tracked_type`:
   gis + (10 + type)*16). An entry joins type t if it has one of `SPECIAL_TYPES[t]` (0x1805a1010, 0x80 per type:
   {CLS_FLUID_WATER, CLS_FLUID_LAVA}, {CLS_TOOL}, {CLS_NOOB_TOOL}, {CLS_ITEM}, {CLS_EQUIPMENT}; add_entry 0x18020700f). [V]

**The wrong count:** tracked type 0 in `SPECIAL_TYPES`, summed for recipe CLS_FLUID_CRAFT. The function has the queue entry
and could read the pump's KV_FLUID_TYPE, but does not. CLS_FLUID_BEER and CLS_FLUID_SACRED_WATER are not in the
list, so they are not counted. [V]

Result: `refresh_maintain_globally` sees 100 >= 20 and sets queued amount to 0 (0x1801522de..0x1801522ee), so no job exists.
That accounts for the report's "100/20", lava found nowhere, and at least part of "no dwarf comes". [V for the code path; I
that this is what the poster saw]

Local mode is different (corrected by test: it counts every fluid held, see above): `production_system_get_matching_output_entities`, branch at 0x18015095c, counts CLS_FLUID (0x18059b3a0)
items in this building's inventory only, hence "0/20". A pump holds only its own output, so this count is right for
the fluid. [I] As `mods/maintain_hint` says, it never stops if haulers empty the building.

Not explained: the poster's "no dwarf came" if that also applied in Local mode. It could be no free farmer, or an unreachable pump. One
reply says lava pumping works for them.

## Symptom 2: walking into lava

### The path planner: routes through lava when it is shorter [V]
- `tile_graph::update_edge_masks` 0x180332d50: per edge, samples tiles along it. If amount > the fluid's threshold (lava: amount >= 2), it
  sets bit (fluid type) in `_edge_masks[edge]` (tile_graph+0xb8, u16; `cmpb 0x105(%rcx),%dl` at 0x1803339c4, `bts` at 0x180333a04)
  and EDGE_HAS_FLUID in the edge data.
- `fluid_effect::update_entities` 0x180506fa0: for each `SENSITIVE` param of the entity's effect record, sets that bit in its
  movement query's edge mask and passes a cost table (0x18050710a). `entity/creature/dwarf_base.entity` uses
  FLUID_DEFAULT (game_effect.bin): SENSITIVE WATER, SENSITIVE LAVA.
- `fluid_create` 0x1805055d0 builds the table: **water x10 (0x180505773), lava x50 (0x18050579d)**.
- Edge callback 0x1802ac240 (set in mainstate, 0x18029eecf): EDGE_DISABLED -> blocked. Otherwise the first fluid bit in both
  masks: `c <= 0` -> blocked; else `cost *= c`. So the code has a "forbid" path and the table does not use it.
- dwarf_movement has `_max_cost` 0, which means no limit (`navgraph_query.bin` rec 0 +0x40). Walk edges cost x1, climb x6, jump x4, drop
  and room jump x10. So a lava strip is taken whenever the detour costs more than 50 per lava edge length, and always when it is
  the only route. [V for the numbers; I for a typical cave]
- Only the dwarf's own movement query gets a mask. Reversed interaction queries, used for job and filler costs (`get_path_cost`,
  `update_hauler_for_needer`), have mask 0. So job choice sees lava as free ground. [V: the only callers of
  `navgraph_query_system_set_query_edge_mask` are update_entities and one wrapper at 0x18006e9a5 that I did not trace. I that the walk
  itself uses the masked query]
- Mismatch at a pool's lip: the edge test reads only the sampled tile, while damage takes the max of the dwarf's tile and x +- 1 (below). A
  tile with lava amount 1 next to deep lava costs x1 and still burns. [V]

### Damage [V]
`fluid_effect::update` 0x180505dc0 handles an entity only while `entity & 3 == floor(now seconds) & 3` (0x180505e3c, 0x180505ee1), so one game second in four. Own tile dry -> remove the effect. Own tile wet: amount = max of
own, x-1, x+1 (0x180506043..0x1805060fe); if amount > threshold, add the fluid's `_effect_modifier` (0x1805061b5). EFFECT_IN_LAVA is
STATUSBAR_HEALTH_GAIN -10; per `natural_healing` the gain applies each tick (10 per game second). CLS_DWARF has HEALTH_MAX
1000 and no gain. So **100 HP per game second, 10 seconds from full to dead, and damage does not heal** without medicine. Because the effect
is only added or removed in that window, exposure is lumpy: a dip that falls between windows does nothing, and one caught by a window keeps
burning until the next window even after he has left, about 3 s or 300 HP. Three or four brief touches can kill. Short crossings add up. [V for the
rates and the window; I for the consequence, and that this occurs in play] `FLUID_FIRE_RESISTANT` (ruby crab, lava rat, lava slime)
replaces the lava effect. There is no dwarf equivalent.

### Steering away: ACTION_AVOID_FLUID is rank IDLE [V]
- `utility_action_avoid_fluid_register` 0x1803a68d0: `movl $1` into `_rank` (struct offset 0xa0) at 0x1803a697e. Ranks: IDLE 1, ORDER 4,
  COMBAT 6, ... Compared: work 4, desire 4, sleep 4, retreat 6, combat 6, move_to 7, fall 9.
- `utility_system__get_best_action` 0x1801fa6f0 stops at the first rank that changes (0x1801fa76d), so the best rank wins and score
  only decides inside a rank. [V for the code; I that the list is sorted by rank]
- Score: tile fluid amount of any fluid (0x1803a7030), clamped to 0..1, so any wet tile scores 1.0. It beats idling but nothing else.
- `bt_avoid_fluid_update` 0x1804e2580 searches nearby and moves to a picked node (`movement_system_move_to` 0x1804e471e). I read its outline only.

### Planner vs flow
| Case | What the code does | Status |
|---|---|---|
| Route crosses lava, detour is long or absent | Dwarf walks in at x50, no check while crossing, 100 HP/s | Code path [V]; in play unknown |
| Standing at a work site when lava flows in (digging into a pocket, an opened lake) | Work rank 4 beats avoid rank 1; he stays until the job ends or he dies | Code path [V]; in play unknown |
| Lava flows onto a path in progress | Edge masks update; **I did not establish whether a moving dwarf replans** | Open |
| Idle dwarf in lava | Avoid runs, unless nothing dry is reachable | [V], outline only |

Both first rows fit "walks into lava and dies". **The evidence does not separate them.** A save or video from a death would.

## The licorice chain [V unless marked]
1. `MISSION_OVERWORLD_ALLIANCE`: faction ESTEEMS you; deliver 10 CLS_LICORICE_DWARVEN to its capital; `JOIN_ALLIANCE` on completion (crash path:
   A4, `relation_crash.md`, guarded by `relation_crash_guard`). With `reachable_diplomacy` (12 of 35 locations, 3-4 per faction) that is
   about 3-4 alliances, so 30-40 licorice. [I]
2. `CLS_LICORICE_DWARVEN` (recipe_cauldron_cdb.bin rec 22, file 0x14540): CAULDRON, PROF_COOK (requires a tool), 2 CLS_SPROUTS_SULPHUR + 1
   CLS_OIL_MUSHROOM + fuel 25, RESEARCH_GASTRONOMIC_HERITAGE.
3. `CLS_OIL_MUSHROOM`: MEDICINE_CABINET, PROF_HEALER, from CLS_SHROOM. Not related to lava.
4. Plant `SPROUTS_SULPHUR` (plant_records_cdb.bin rec 11, `fluid_requirement` empty, so no lava tile needed), on `fertile_soil`:
   - stage 0: tender ORDER_SOW_SPROUTS_SULPHUR, 1 sprout;
   - stage 1: tender **ORDER_SOW_LAVA_PLANT, 1 lava item, ADVANCE**, so growth waits for it;
   - stage 2: timed 750-1000 s;
   - stage 3: harvest LOOT_SPROUTS_SULPHUR 2-3, back to **stage 1**, so every further harvest needs another lava item.
5. First sprouts: wild `SPROUTS_SULPHUR_PATCH`, UNDERWORLD biome (exploration_spawn_records_cdb.bin).
6. Lava items: hand pump on a lava pool (1 CLS_BLOCK_GRANITE, PROF_BUILDER), PROF_FARMER to run it.

Budget per alliance: 20 sprouts = about 8 harvests = about 8 lava items, about 875 game seconds per harvest per plant, plus 10 oil and 250 fuel.

**Which step the bugs block:** step 6, and the stock needed for 4.
- Symptom 3 blocks pumping outright in Mountainhome mode once water + lava >= target. A colony that keeps water as drink hits this at once. Workaround exists (Local or a fixed amount). [V]
- Symptom 1 drains stock between pump and plant; it is not a hard stop. [I]
- Symptom 2 is a risk along the way, in deep lava-bearing rock. No code ties it to this chain.
- Neither blocks steps 1-3.

**User's colony (`save-backup-2026-11-02/lastsave.2.save`):** 1598 lava tiles, 0 explored; nearest is 896 tiles (Manhattan) from the entrance
at (549, 994), y 57..156. So digging there comes first. Water: 77 tiles explored, nearest 101. [V for counts, using map bit 22 as explored
and type 2 as lava [I]]

## Fix candidates

### F1. Data: lava is not fuel (symptom 1). Recommended
`database/modifier/modifier/item_modifiers_cdb.bin`, record 50 CLS_FLUID_LAVA at file 0x2b1430. Slot 3 at record +0x568 (file 0x2b1998) is
STATUSBAR_FUEL_INSTANT; its i32 16.16 value at record +0x5a8, **file 0x2b19d8: `00 00 fa 00` (250) -> `00 00 00 00`**. In a mod, find the
record and slot by tag and assert the old value, as `mods/natural_healing/mod.py` does. The `jle` above then skips it.
- Alternative: clear the 0x48-byte slot and the parallel entry at record +0x4e40 (0x90 stride, table from +0x4c90). Use this if a "+0 fuel" tooltip appears.
- Risks: lava fuel is gone; coal and charcoal remain, and there is no recipe that needs lava specifically as fuel. A claim already held by a refill job finishes or fails; not traced. Whether an existing save's items read the value from the database at load is [I]: `modifier_system/modifier.bin` stores names, and I did not check for stored values.

### F2. Data: lava hurts less (symptom 2, deaths only)
`database/modifier/modifier/dwarf_modifiers_cdb.bin`, record 124 EFFECT_IN_LAVA at file 0x6ad5d0, value at +0x4d0, **file 0x6adaa0: `00 00 f6 ff` (-10.0) ->
`00 00 fe ff` (-2.0)**: 50 s from full to dead instead of 10. Applies to every creature using that effect. Changes neither routing nor rank. With `natural_healing`
(+0.05 per tick) crossings stop accumulating. This is the only data-only option I found for symptom 2. It is a mitigation: lava becomes less
dangerous for everyone.

### P1. Lava edges cost much more (symptom 2, routes)
`fluid_create`, VA 0x18050579d: `48 c7 44 ce 50 00 00 32 00` (x50) -> `48 c7 44 ce 50 00 00 e8 03` (x1000).
Copied into each entity's query on load (`effect_system` post-load pass 0x180460aa0 calls update_entities with is_load=1, and the flag is not read),
so saves get it. [V for the replay; I that it runs after `restore_queries_after_load`]
Risks: longer walks around lava; still crosses if it is the only route, by design. Cost is i64 16.16, so no overflow at these sizes. Job choice still ignores lava (mask 0 on reversed queries), so a dwarf can pick a job and then walk a long way round.

**Not recommended: blocking.** Imm `00 00 ff ff` gives `c <= 0`, so edges are blocked. Then a job past lava looks reachable to reversed queries and fails for the dwarf's own query (likely a loop; untested), and a dwarf caught by a flow may have no edge out. If tried, test exactly that.

### P2. Lava-only escape at a real rank (symptom 2, flows)
Two sites together:
- Rank, VA 0x1803a697e: `c7 45 40 01 00 00 00` -> `c7 45 40 05 00 00 00` (PREPARATIVE: above work and desire, below combat).
- Score only for lava, VA 0x1803a70a4: `0f b6 54 88 03` -> `e9 57 5c 26 00`, cave at 0x18060cd00 (`.hmod` +0xd00, 39 bytes; assembled with llvm-mc, decoded, not run):
```
0f b6 54 88 03           movzx edx, byte [rax+4*rcx+3]
89 d0                    mov eax, edx
83 e0 78                 and eax, 0x78
83 f8 10                 cmp eax, 0x10          ; type 2 = lava [I]
75 0d                    jne zero
83 e2 07                 and edx, 7
c1 e2 10                 shl edx, 16
41 89 12                 mov [r10], edx
4c 89 d0                 mov rax, r10
c3                       ret
41 c7 02 00 00 00 00     zero: mov dword [r10], 0
4c 89 d0                 mov rax, r10
c3                       ret
```
Risks:
- Without the score change, the rank alone would pull workers out of any water, so do not ship it alone.
- With it, idle dwarves no longer leave water, a small regression (slowness only).
- A dwarf on a lava-only route enters, gets pulled out, re-picks the job: a loop at the edge. He lives, but the job can starve. It needs P1 to be rare.
- Whether a running work behaviour can be interrupted (`_can_be_stopped`) was not read. **If it cannot, P2 does nothing for the case it targets.**
- Lava amount 1 scores 1.0 too, which is fine here.

### P3. Count only the pump's own fluid (symptom 3). Recommended
VA 0x180200460: `e8 9b a6 00 00` -> `e8 9b c7 40 00`, cave at 0x18060cc00 (`.hmod` +0xc00, 200 bytes; assembled with llvm-mc via `tools/cave.py` and decoded, not run):
```
  mov rax,[0x1805a0f00]  ; cmp [rdx],rax  ; je pump  ; jmp 0x18020ab00      ; not a pump: vanilla
pump:
  push rcx ; sub rsp,0x40 ; mov [rsp+0x30],r11                              ; caller reads r11 after the call
  xorps xmm0,xmm0 ; movups [rsp+0x20],xmm0
  mov rcx,[rbx] ; mov rcx,[rcx+0x28] ; add rcx,0x1520                       ; gis->gamestate->mainstate->key_value ecs
  movzx edx,word [rdi+2]                                                    ; entry->producer
  mov r8,0xc0c3affce0cc531c ; lea r9,[rsp+0x20]                             ; KV_FLUID_TYPE
  call [0x180599398]                                                        ; key_value_component_system_get_value
  mov r11,[rsp+0x30] ; mov rax,[rsp+0x28]
  cmp dword [rsp+0x20],0x10003                                              ; type 3, count 1, as the pump writes it
  mov rcx,[rsp+0x40] ; lea rsp,[rsp+0x48] ; jne unknown
  mov rdx,0x06e6d8d33729c486 ; cmp rax,rdx ; lea rdx,[cls_lava]  ; je known ; LAVA
  mov rdx,0xae40785ecb6d7f8e ; cmp rax,rdx ; lea rdx,[cls_water] ; je known ; WATER
unknown:
  lea rdx,[0x1805a0f00] ; jmp 0x18020ab00                                   ; vanilla fallback: sums all
known:
  call 0x18020ab00 ; test rax,rax ; jne done
  add rsp,8 ; jmp 0x18020050d                                               ; fluid never existed: count 0
done:
  ret
cls_lava:  dq 0x858a26a36c16c5af
cls_water: dq 0xa76eb257674850db
```
Full bytes, base 0x18060cc00:
`488b05f942f9ff4839027405e9efdebfff514883ec404c895c24300f57c00f11442420488b0b488b49284881c1201500000fb7570249b81c53cce0fcafc3c04c8d4c2420ff154ec7f8ff4c8b5c2430488b442428817c242003000100488b4c2440488d642448752c48ba86c42937d3d8e6064839d0488d153c000000742248ba8e7f6dcb5e7840ae4839d0488d152e000000740c488d156542f9ffe960debfffe85bdebfff4885c075094883c408e95a38bfffc30f1f4000afc5166ca3268a85db50486757b26ea7`

Basis: lookup 0x18020ab00 clobbers rax, rcx, rdx, r8, r9, r10 only [V]; gis+0 = gamestate (ctor 0x18020d63b) [V]; KV ecs at mainstate+0x1520 (0x1802d706e) [V]; entry+2 = producer (`game_entity_types.h`) [V]; comp layout {u16 type, u16 count, u32 0, u64 value} (0x1802d7082..) [V]. Stack is 16-aligned at the call.
Risks:
- Depends on comps[0] of a pumped item being CLS_FLUID_x. If it is not, the count is always 0 and the pump never stops, which is no worse than Local mode, and the test shows it at once.
- The fishing pier shares BT_FLUID_PUMP_HAND, but its recipes have other tags, so it is untouched. [I]
- The KV read runs per Maintain refresh per pump entry: negligible.
- The `.hmod` slot is clear of everything in CLAUDE.md and the drafts in re/notes. `.hmod` is 4 KB.

**No data-only fix exists for symptom 3:** the count is keyed on one recipe tag and SPECIAL_TYPES is code. Two recipes (tag CLS_FLUID_LAVA, CLS_FLUID_WATER) are not viable: completion and the map draw are gated on tag == CLS_FLUID_CRAFT (0x1802d6fd0, 0x1804d8084), so a "lava" recipe would ignore the pool. [V for the gates; I for the outcome]
A 1-instruction alternative: `jne` at 0x180200479 -> always, so the count is 0 and the pump never stops. That equals the Local workaround. Not proposed.

**Workaround without a mod:** Local maintain or a fixed amount (S1 poster's report; code agrees).

### Coverage
| Symptom | Candidates | Good fix? |
|---|---|---|
| 1 burns lava | F1 | Yes, data only |
| 3 pump count | P3 | Yes, code; workaround exists |
| 2 route through lava | P1 (F2 softens) | Partial: an only route is still walked |
| 2 caught by a flow | P2 (F2 softens) | Uncertain; depends on interruptibility |

Recommendation: F1 + P3 first; both are narrow. F2 is cheap if deaths are the complaint. Hold P1 and P2 until a test or a save shows which case is real.

## Test plan (copies only)
CLAUDE.md rules apply: back up the save folder, check the session log for the user's `--game-load` before closing a game, and **run Steam offline**: the licorice chain has achievements (`ACHIEVEMENT_CANDY_MAN`, craft 5 licorice; one on harvesting sprouts).

The obstacle: the user's colony has no reachable lava, and pump output depends on the map. Options:
- A copy with `map/map.bin` edited: from offset 16, u32 tiles, index `((y>>4)*68 + (x>>4))<<8 | (y&15)<<4 | x&15`, set top byte `(2<<3)|7`. Pick dug tiles near the base. **This edit is unproven: fluid_system may re-simulate it, the tile graph may not rebuild without a dirty mark, and `fluid_source` may not care.** Save-edited live state has reverted before (`overworld_invaders.md`), so check right after loading and after one save.
- A new game with `--game-scenario random` and digging, which is slow but honest.

- **T1, symptom 3 baseline (no patch, user's colony copy; water only).** Build a pump on explored water. Maintain Mountainhome, target below the current water count. Expect x/target with x = all water, queue 0, no worker. Refutes the cause if it pumps. Then Local: expect it to pump.
- **T2, P3.** Same with a second pump on edited lava. Expect water pump count = water, lava pump 0/20 and pumping, count rising to 20 with water untouched. If both show 0 forever, comps[0] is wrong.
- **T3, symptom 1 baseline.** Lava items in storage, foundry low, coal farther than lava. Expect a dwarf hauling lava (session log, autosave, `saveinspect`). Move coal closer; expect coal. This tests the score claim; if lava is taken with coal much nearer, the score reading is wrong.
- **T4, F1.** Same; expect no lava hauled, tooltip checked, an existing save with lava loaded. If it still burns, values come from the save.
- **T5, route.** Two work sites, one past a thin lava strip with a walk-around of about 20 tiles (expect avoidance at x50) and about 100 tiles (expect crossing). Log health every save. Then P1: expect the long way.
- **T6, flow.** Lava on a tile under a dwarf with a long job queued; then an idle dwarf. Expect working dwarf stays and dies (about 10 s), idle one leaves. Then P2: both leave, or it shows the work action cannot be interrupted.
- **T7, F2.** Time from entry to death: expect about 50 s, and about 10 s unpatched. Confirms -10 per tick. Also step a dwarf out after 1 s: health should keep falling for up to about 3 s, which tests the window reading.
- **T8, regression.** Water pump Maintain still stops at target. Fishing pier works. Idle dwarves in water under P2 only slow. Lava creatures unaffected.

## Could not establish
- The Reddit source: never read. Symptoms 1 and 2 rest on BUGS.md wording.
- Whether real deaths are route or flow. No save, no reproduction.
- Whether a dwarf replans when lava reaches his path; whether work actions can be preempted by rank alone.
- The exact filler value weighting, and how `bt_avoid_fluid_update` picks its target (outline only).
- The S0 poster's "no dwarf" in Local mode.
- Water and lava type values and comps[0] of a pumped item are inferred, not observed; T2 settles both.
- The room dependency hash on the pump recipe (0xc881337829c046b9, recipe_rooms rec 37 +0x988) sits at a research_cdb.bin offset without a tag before it, so I did not name its research.
