# Clutter and decay findings (game.x86_64.dll 1.2.39)

Addresses are VAs (image base 0x180000000; PDB `0001:N` = VA 0x180001000 + N).

## Decay system (`decay_system.cpp`, PDB module 211)

`decay_system_update` at VA 0x180463f30 (0001:4599600), 2108 bytes.

- Every item (CLS_ITEM) has a decay record: i32 accum and i32 rate, 16.16 fixed point. In the
  West Hirdness save all 2138 items had rate 65/65536 (~0.001 per second).
- Each tick, for each item NOT claimed (claim_system_get_claimed_entities_mask):
  `accum += rate * dt * A`, and if the item has no parent inventory (lying loose)
  `accum += rate * dt * B` as well. At accum >= 10000 the item is destroyed.
- A and B depend on entity pressure (used vs max entity slots, the 64K limit):
  - used <= 75% of max: A = 1, B = 100      (immediates at 0x180463fc1 and 0x180463fcd)
  - 75–90%:             A = 500, B = 1000   (0x180463fa6, 0x180463fb9)
  - > 90%:              A = 5000, B = 10000 (0x180463ff1, 0x180463fec)
- The base term is scaled by dt but the loose-item term B is added per update, unscaled.
  Measured from autosaves 2, 3 and 4 of West Hirdness (one autosave per 3000 ticks, 300
  game seconds): stored items +0.27, loose items +298 per interval. So the sim runs at 10
  ticks per game second (dt = 0.1, and int(dt*65536)*65 >> 16 truncates the base to
  0.27/300 s). About 1200 of ~1950 items gained nothing (claimed or reserved).
- At normal load a loose item therefore lasts 10000 / 0.99 per s, about 2.8 game hours; a
  stored one ~3.5 years of game time. Past 75% of the entity limit stored items last about
  5.6 game hours and loose ones 17 minutes; past 90%, 34 minutes and under 2 minutes. This is the
  "items silently disappear past ~50K" report (BUGS A1): it is the developers' pressure valve.
- West Hirdness (lastsave): 661 loose items, most 1.4–2.2 h into their 2.8 h.
- The decay time scale constant is a double 65536.0 at 0x1805387c8 (dt -> 16.16).

## `mods/keep_stored_items` (2026-11-05)

The stored factor A in the 75-90% band is the `mov r9d, 0x1f40000` at 0x180463fa6; the mod makes it 0x10000, the rate below 75%. `mods/_test_pressure` (test only) turns that band on at any entity count by replacing the 3/4 limit at 0x180463fbe with 0.

Measured between two autosaves 30 s apart, copy of savegame17, all mods plus `_test_quiet` and `_test_pressure`, normal speed, one run each, unclaimed items that stayed where they were:

| | Stored item gain | Loose item gain |
|---|---|---|
| No fix (A = 500) | +14.77 | +310 |
| `keep_stored_items` (A = 1) | +0.03 | +286 |

Loose gain follows the time between saves, so the difference there isn't the mod. +14.77 per 30 s reaches 10000 in about 5.6 game hours, as read above. No exceptions. Not run at a real 48K entities. The cost is a cliff: without the slow erosion a colony can sit closer to 90%, where stored items rot in 34 minutes. Loose items are what the band still removes (1718 of about 2250 colony items in savegame17, 661 of about 2138 in West Hirdness). Whether a real late colony stays under 90% this way is not known.

## Maintain orders (`production_system.cpp`, PDB module 22)

Repeat types (game_entity_types.h): 0 FIXED_AMOUNT_THEN_REMOVE, 1 FIXED_AMOUNT_THEN_KEEP,
2 MAINTAIN_LEVEL_LOCALLY, 3 CONTINUOUS, 4 MAINTAIN_LEVEL_GLOBALLY. The UI: click Maintain once
for Global, twice for Local.

- `refresh_maintain_locally` VA 0x180152070: for type-2 entries, count =
  production_system_get_matching_output_entities(building inventory). If count <= low mark
  ([entrydata+8]) queue (high - count); if count >= high ([entrydata+4]) queue 0. If the
  building inventory is full, queue 0. Haulers emptying the building makes it craft forever.
- `refresh_maintain_globally` VA 0x1801521b0: same, but count =
  global_inventory_system_get_matching_inventory with claim types {UNCLAIMED, 2, 3}
  (only UNCLAIMED for deliver-only recipes, recipe+0xec0).

## `mods/local_maintain_cap` (2026-11-05)

Two hooks. The count call at 0x18015213d in `refresh_maintain_locally` goes through a cave that returns 0x7fffffff when the colony count (same call and claim types as Global Maintain) is at least FACTOR x high, so the caller sets the amount to 0. Local refresh is event-driven and nothing fires when the colony's stock falls, so the type check at 0x180152ed0 in `production_system_update`, which runs for every entry on every update and handles only Global, also sends type 2 through the same count and into the code at 0x180152f3e. Deliver-only recipes keep their local count. A full building is left to the event path. `production_system_set_entry_maintain` still calls the uncapped count, so changing the level can set an amount for one update.

How the numbers behave (read from `refresh`/`set_entry_maintain`, seen in tests): the queue only refills when the building's count is <= the "start at" mark (0 by default). Between the marks nothing changes, so x9/4 can stay on screen. **The x/y display is not a stock meter**, not even in Global mode; I misread x1/20 as 19 in stock when the colony held 0-2. `set_production_amount` removes an entry that is in type 0 with amount 0, and the mode button cycles Global, Local, then a non-maintain mode, so one click too many can delete an order (seen once, with this mod installed; the rule is the game's, read not tested without the mod).

**Tests**, copies of savegame17, Copper Ingot on the Small Foundry set to Local at level 1, key 3, one run each, about 7 minutes. `HMOD_LMC_DIAG=1` keeps the last counts in the cave for a memory reader; `HMOD_LMC_FACTOR` sets the factor. No exceptions in any run.
- Factor 4: the colony held 0-2 ingots, so the cap never fired. `global=1 local=0 queued=1`, normal behaviour. About 60 refreshes per real second.
- Factor 1: `global=1 local=0 queued=0` every time, and at `global=0` the queue went back to 1 within seconds, with no input. So the cap stops and lifts.
- Without the mod: the screen showed x0/1 then x1/1, the same as with it at factor 4, so the display alone can't tell them apart.
- Shipping build, factor 4, no readout: loaded, ran about 90 s at key 3, and the new tooltip displayed in full. No exceptions.

Not tested: the shipping factor actually firing (needs a colony with 4 x level in stock), long play, the output rate of colonies that rely on Local Maintain, performance with many Local entries (each costs a colony count per update, as Global already does). A colony with thousands of items already gets no help beyond new crafts stopping.


## Fishing pier output and a full chest (B10, 2026-11-05, read only)
- savegame21 (East Tharnlaw): 1,869 loose items, 102 of them fish (none stored, none claimed, decay up to 5544/10000). The only
  storage, `building/chest_start`, holds 320 of 320 (iron ore and coal), so haulers have nowhere to put anything.
- The pier's recipe CLS_FISH (recipe_fishing_spot_cdb.bin) outputs through LOOT_FISHING_DYNAMIC. In
  `default_production_complete_cbck` (0x1802d6c00) a LOOT_ output goes through spawn_loot (0x1802d955e), and the spawned items are
  then passed to `inventory_system_add_items` for the queue entry's producer (0x1802d9a9d). The pier's queue entry (uid 0x42) has
  producer 4750 = `building/fishing_pier`, yet no fish id appears in inventory_system/data.bin. So the add doesn't keep them [inferred:
  rejected or over capacity, not traced], and the catch stays on the floor.
- Correction, traced on a running copy: the catch never reaches that first add. Fishing takes the second loot path: after
  `strcmp(output, "LOOT_FISHING_DYNAMIC")` (0x1802da80e) and the dynamic selection (0x1802dc8d0), `mov byte [rbp+0xd980], 1`
  at 0x1802dab81 makes 0x1802daed4 skip `inventory_system_add_items` (0x1802db590) and give the spawned fish a random velocity
  instead (the loop at 0x1802db380). [rbp+0xd990] = 1 there too, and drives a fishing-only call at 0x1802db5a8 afterwards.
  A test-only counter (`mods/_test_pier_diag`, `.hmod` 0x1e00) on the first path's item check read 0 while fish spawned.
- `mods/pier_keeps_catch` changes that 1 to 0. Copy of savegame21, key 3, about 6 minutes, one run, no exceptions: 21 new fish
  held (19 in one inventory in the building-inventory region, 2 elsewhere, probably hauled), loose fish 102 -> 100 (none added).
  Not tested: a full pier (the add likely leaves the rest where they spawned), long play, a colony with free storage.
- Global Maintain can't see floor items: `global_inventory_system_refresh` skips items with no parent (`testw %di,%di; je` at
  0x1801fff05), and its counts are kept incrementally per item category, so counting floor items would be a deeper change.

## Loose pile in KrazJomsglind (savegame26, 2026-11-06)
- Loose items 427, 725, 808 in savegames 24-26; the oldest at 25%, 36%, 49% of their rot, so some are never picked up.
- Storage there: chest_start 320/320 (full), stone chests (capacity 30 each, not 48), and a Storage (600) built just before
  savegame26, nearly empty. Every storage has source mask 0xff at byte +13 (all sources), so take-from-ground is on.
- Job Broker desired workers: all 17 types 1 (u16 array at job_broker_system/data.bin +1384, same order as the type tags
  listed from offset 24 at an 80-byte stride; JOB_HAUL is index 0).
- inventory_system/data.bin: an inventory's slots are a u16 count followed by that many u16 item ids (0 = empty slot);
  chest_start's list was at 0x462308 and the Storage's at 0x462b08 in these saves. Capacities are a u64 per entity at
  0x8ea498 (cap 600 at entity 3843).
- Test, copies of savegame26, `_test_quiet` + all_profession_bonuses, key 3, 10 real minutes (about 46 game minutes),
  15 autosaves each, one run each, no exceptions or pauses:
  | | Loose start / peak / end | Of the 808, stored / still loose | Held items end |
  |---|---|---|---|
  | Unchanged | 808 / 1139 / 622 | 472 / 294 | 1124 |
  | JOB_HAUL desired 3 | 808 / 830 / 631 | 472 / 298 | 1127 |
  Mining dropped 319 ore and 28 rubies in the first autosave of the unchanged run; with 3 haulers the pile didn't jump
  (dwarves mined less). Held rose about 60 per autosave and flattened at about 1125: at the end the Storage held 599/600
  (498 ore), chest_start 320/320 (306 ore), the chests 30/30. So storage space, not haulers, set the end state.
- The 294 left behind are in the same open area as the hauled ones (flood fill over open tiles), mostly deep (x 500-580,
  y 940-960) or far east (x 680-800, y 1000-1020). Haul takes the nearest eligible item, so far items wait while new
  drops arrive nearer. Rubies were among the items left loose while ore filled the storages.
