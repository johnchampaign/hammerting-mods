# Plant growth and "plants stop growing after a load" (BUGS.md B9), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000; file
offset = VA - 0x180001000 + 0x400. Modules: 38 plant_system.cpp, 142 plant_system.ecs.cpp,
93 command_plant.cpp, 182 sensor_harvest.cpp, 56 craft_util.cpp (default_production_complete_cbck),
53 gamestate.cpp, 22 production_system.cpp. Static reading only; nothing was run, no save opened.
Note: `tools/disasm.py` annotates `jmp` targets but not `callq` (its regex wants `call\s+0x`).

## Data (re/extract/database/plant/plant_records_cdb.bin, 12 records of 0xcc8)
Header types: game_entity_types.h `plant_record` {tag, material, u32 height, fluid_requirement,
relevant_item, plant_stage[8]} with stages at +0x108, 0x178 each: {u32 min_time, u32 max_time,
e_plant_harvest harvest @+8, resource_stack loot @+0x10 (tag hash @+0x48), plant_tender[4] @+0x58
(0x48 each: wc_tag recipe, hash @+0x90, on_complete @+0x98: 0 BOOST_TENDER_LOVE_CARE, 1 ADVANCE)}.
Times are game seconds (10 ticks per second).

| plant | h | stage 0 | stage 1 | stage 2 | stage 3 |
|---|---|---|---|---|---|
| BARLEY, BEETS_RIME/SUGAR, GRAPES, HOPS, SHROOM_TONCAP, WHEAT (gloom wheat) | 1-2 | tender ORDER_SOW_<X> | timed | timed | harvest, back to stage 1 |
| GREEN_ALGAE | 2, fluid WATER | sow | timed 300-500 | timed | harvest |
| SHROOM_CITADEL (gives CLS_LUMBER_CITADEL, "Citadel wood") | 2 | sow (seed) | tender ORDER_SOW_WATER_PLANT | timed 750-1000 | harvest |
| LILAC_TOMB, TAILS_TROLL | 1 | sow | tender ORDER_SOW_WATER_PLANT | timed | harvest |
| SPROUTS_SULPHUR | 1 | sow | tender ORDER_SOW_LAVA_PLANT | timed | harvest |

WHEAT stage 1 = 150-175 s, TONCAP 125-150 s. All stage-3 harvests are PLANT_HARVEST_SET_TO_STAGE_1.
Recipes (recipe_order_cdb.bin, PROF_FARMER, producer class ORDER): ORDER_SOW_<X> takes 1 seed/item;
ORDER_SOW_WATER_PLANT takes 1 CLS_FLUID_WATER (the Water item from the hand pump, also the colony's
drink) and outputs CLS_DUMMY_EFFECT; ORDER_SOW_LAVA_PLANT takes 1 CLS_FLUID_LAVA. Tag hashes:
ORDER_SOW_WATER_PLANT 0x1d59aeefcbb4df84, ORDER_SOW_SHROOM_CITADEL 0xeed9513badf888ae,
ORDER_SOW_WHEAT 0x135e8bc1b707b998, ORDER_SOW_SHROOM_TONCAP 0xac3bae055439ff10. Plant tag
hashes: SHROOM_CITADEL 0x4456b0b636739037, WHEAT 0xc0b7ec3003b5fdda, SHROOM_TONCAP 0xf3be2fd7087e9b79.
recipe_farm_cdb.bin is a different mechanic (BUILDING_CAVE_FARM crafts crops from
KV_STATUSBAR_FECUNDITY, plus ORDER_STORE_* entries); it does not drive plant stages.
"2/4" in the UI is plant_system_get_curr_and_max_stage (0x1801e9e80): curr = stage + 1, max = stages
until one with min_time 0 and no tender. So 2/4 is stage 1, which for Citadel is the water stage.

## Runtime structures
- plant_system (ecs+0x40): gamestate @+0x10, next_check u32 @+0x18 (earliest timer, seconds),
  plant object store @+0x60 (0x38 B each; slot 0 unused), entity->plant index u16[] @+0x70,
  pending-removal list @+0x80, block lookup @+0x90 (24 B, sorted by block), per-type harvest dirty
  flags @+0xa0 (0x20 per type, +0x18).
- plant_data (0x38): entity u16 @+2, stage u16 @+4, type index u16 @+6 (into the plant_record
  container), next_time u32 @+8 (seconds; 0xffffffff = no timer), u32 @+0xc (0), tile x @+0x10,
  tile y-1 @+0x14, harvest workplace (edge from/to/id/t) @+0x18..+0x30, auto_tend u8 @+0x30,
  harvestable u8 @+0x31.
- Plant entity (create_plant_entity 0x1801eb4d0): FIXED_POSITION, PLANT_COMP {tag, stage,
  auto_tend}, MODIFIER_COMP, GAME_ANIM, PRODUCER_COMP, INVENTORY_COMP, DEBUG_NAME, template
  entity/plant/default_template.entity, model cls_growing_<type>. The plant is its own producer.
- Player sowing (command_plant_execute 0x1802ff400): create_plant_entity(random_stage 0,
  auto_tend 1), then haul_system_set_job_priority(plant, 2) and production_system_set_priority(2).
  exploration_spawn_system also creates wild plants (spawn_entities_from_record).

## How a plant grows
- plant_system::set_stage (0x1801f37c0, ps, p, stage): plays the stage animation. If p->stage ==
  stage: only sets harvestable (+0x31) and its workplace when the stage has loot (0x1801f38a2), then
  returns. Otherwise: production_system_set_destroy_on_completion(plant, 0, stage == 0); p->stage =
  stage; p->next_time = -1; if a tender has on_complete ADVANCE (0x1801f3909) ->
  production_system_set_template_recipe(plant, recipe) + start_production_from_template(plant, 1)
  (0x1801f3a98 / 0x1801f3ab3), no timer. Else if min_time != 0 -> next_time = now_s + min +
  rand(0..max-min) (each part divided by the debug divisor at 0x180591464, at least 1), and
  ps.next_check = min(next_check, next_time) (0x1801f3a29). Else (harvest stage) harvestable.
- Timers, plant_system_update (0x1801ebfa0, update(ecs, dt, time_now)): if next_check << 16 <=
  time_now (0x1801ec851) the whole store is scanned: next_check = -1; for each plant, if next_time
  == time_now >> 16 **exactly** (0x1801ec8de `cmp ecx,esi; jne`) -> set_stage(stage + 1), else
  next_check = min(next_check, next_time). The same update first revalidates plants on changed map
  blocks with valid_position_for_type and destroys invalid ones.
- Tender completion: default_production_complete_cbck (0x1802d6c00, module 56) classifies the
  finished recipe; tag prefix "ORDER_SOW_" (0x1802d7027) gives class 6, which calls
  plant_system_production_complete(ecs, plant, recipe) (0x1802da4bc -> 0x1801e9da0). That looks only
  at the CURRENT stage's tenders: same recipe hash and ADVANCE -> set_stage(stage + 1); BOOST or no
  match -> nothing.
- Harvest (plant_system_harvest 0x1801e9930): spawns loot, fires TDTD_EVENT_PLANT_HARVESTED; if
  auto_tend: SET_TO_STAGE_0 -> set_stage(0), SET_TO_STAGE_1 -> set_stage(1) (0x1801e9c84); else the
  entity is destroyed.
- Nothing else advances a plant. No code times out a tender stage or re-creates its entry; only a
  set_stage with a different stage starts tender production.

What stops growth:
- Timed stage: only a next_time that is already in the past (then it never equals now; the store
  is rescanned every tick and the plant stays). Pausing just stops the clock.
- Tender stage (sow, water, lava): the plant's queue entry never completes: no free input item
  (Water competes with drinking and with producers that hoard it, production_stall.md cause 1), no
  haul to the plant, no farmer job (workplace, path, PROF_FARMER allowed), or the entry is missing.
  Any of these is permanent until the entry completes.
- Fluid requirement (GREEN_ALGAE) is checked only in valid_position_for_type: failing it destroys
  the plant, it does not stall it.

## Save and load
- plant_system/data.bin (EP_SAVE 0x1801ea9a0; format 1, minor 3 = writer version 0xc00000).
  Decoded payload: u64 ntypes; ntypes x {u64 56, u64 56, char name[56], u64 hash} (80 B); u64
  nplants; nplants x 23 B {u16 entity, u16 type index (into the table above), u16 stage, i32
  next_time_s, i32 zero, i32 tile_x, i32 tile_y, u8 auto_tend}; i32 next_check. 1762 bytes =
  8 + 12*80 + 8 + 34*23 + 4, so the user's file holds 34 plants (9 Citadel + 25 Toncap): the
  per-plant state IS in data.bin, after the 12 type entries.
- Load (EP_LOAD 0x1801eb020 -> plant_system_format_1::push_to_system 0x1801f24f0): next_check is
  restored; each saved type is matched to the database BY NAME HASH (not by index); every plant is
  re-added with its saved entity, stage, next_time, tile and auto_tend; harvestable is cleared.
  Plants of a type that no longer exists are destroyed. The other add_plant (tile marking +
  set_stage) is not used on load.
- EP_LOAD_POST_SINGLETHREADED (0x1801eb100): set_stage(ps, p, p->stage) for every plant. With an
  unchanged stage this only replays the animation and re-marks harvestable stages. It does not
  check or rebuild a tender stage's production entry and does not touch timers.
- Game clock: time_now = frame_id * 0.1 s (main loop 0x180060b55; frame_id + 1 when not paused);
  the gamestate EP_LOAD (0x1802b8260) restores frame_id (+0x88) and time_now (+0xd0). Saved
  next_time values therefore stay valid after a load.
- The tender entry lives only in the production system (production_system.bin: queue entries
  with recipe hash, producer_data including producer_comp flags, extras; claims in claims.bin,
  craft orders in sensor_craft.bin, haul destinations in haul_system/data.bin).
Refuted: stage not saved; plant records matched by index; timers rebased on load; plant entries
re-created for stage 0 on load. None of these happens.

## Causes, ranked
1. (inferred, fits Citadel exactly) Citadel's stage 1 ("2/4") is not a timer but a production
   entry ORDER_SOW_WATER_PLANT on the plant that needs one Water item delivered and a farmer job.
   It waits forever if Water is short (it is the drink; the user's colony had "Lack of Drink" and
   21 Water claimed by the cook house before whole_batch_inputs) or if no farmer can do the job.
   Toncap has no such stage, which fits 25 Toncap growing while Citadel stalls. Deleting and
   replanting restarts at the sow stage and later creates a new water entry.
2. (code path verified, occurrence unknown) The entry is missing or is not the stage's recipe
   after a load (removed, or never re-created). The plant then never advances, and loading never
   repairs it (EP_LOAD_POST same-stage call). Replanting fixes it. Check the save (below).
3. (fragility verified, no trigger found) A timed stage with next_time < now_s never advances,
   because of the exact-equality test. Save/load restores timers and the clock exactly, so no load
   path to this state was found. It is the only way a timed stage (gloom wheat stage 1) can stall
   for good. If the user's save shows it, patch A fixes it and repairs the save on the first tick.
4. Gloom wheat (WHEAT) has no water stage; its 2/4 stall is not explained by plant code unless
   cause 3 shows in a save. Height 2 is shared with Citadel and Algae but only matters for
   placement and validation (failing that destroys the plant).

## Spotting a stalled plant in a save
1. plant_system/data.bin (layout above): list entity, type, stage, next_time_s, auto_tend.
2. now_s = time_now >> 16 from the gamestate file (gamestate_format_3 starts u16 mountainhome,
   u64 frame_id, i64 time_now 16.16, inferred order) or frame_id / 10.
3. Timed stage (stage has min_time > 0 and no ADVANCE tender): stuck if next_time_s < now_s
   (cause 3) or next_time_s == 0xffffffff (no timer). Healthy: now_s < next_time_s <= now_s + max.
   The saved next_check should equal the smallest next_time.
4. Tender stage (Citadel stage 1, next_time_s = 0xffffffff): production_system.bin queue entry
   with producer == plant entity and recipe hash 0x1d59aeefcbb4df84. None -> cause 2. Present ->
   look in claims.bin for CLAIM_PRODUCE refs (plant << 48 | uid << 32 | slot 0) and at Water items
   (tools/saveinspect.py) and job_broker job_craft_prof_farmer.bin (order, producer, uid) for a
   job on that entry. Entry with no claim and no free Water -> cause 1.
Load test: on a backup of the save, inspect, load, unpause about 20 game minutes (Citadel stage 2
is 750-1000 s, wheat stage 1 150-175 s), autosave, inspect again. Control: new game
(`--game-scenario random`), sow wheat and Citadel, save at stage 1, reload once and compare with
an unreloaded run.

## Patch candidates
A. Timers fire when due instead of only on the exact second: 0x1801ec8e0 `75 13` (jne) -> `77 13`
   (ja), file offset 0x1ebce0. ecx = next_time, esi = now_s; unset timers (0xffffffff) never fire.
   Plants already late in a save advance on the first scan. Harmless if cause 3 never occurs.
B. Load-time repair (draft in re/notes/plant_growth_cave.s, 147 bytes at 0x18060c400, .hmod +0x400):
   site 0x1801eb193 `e8 28 86 00 00` (call set_stage) -> `e8 68 12 42 00` (call cave). For each
   plant on load: if its stage's tender[0] is ADVANCE and production_system_get_queue(plant, 0)
   (0x18014e5d0) returns NULL, or the stage is timed and next_time == -1, it sets p->stage = 0xffff
   so set_stage re-runs fully and starts the tender production (or draws a timer) again. Bytes:
   5356574883ec204889ce4889d3410fb7f8488b4610488b4820e842f3a6ff488b40500fb74b06488b04c84869cf7801
   00004801c84883b89801000000743183b8a0010000017537488b4610488b48284881c1081e00000fb753024531c0e8
   6e21b4ff4885c0751766c74304ffffeb0f83b808010000007406837b08ff74e94889f14889da4189f84883c4205f5e
   5be92d73beff
   Only fixes cause 2 (a plant whose entry is present but starved is left alone).
C. Data, for cause 1: make Citadel's water stage a timer. plant_records_cdb.bin record 7, stage 1
   at file offset 23560: min_time u32 @23560, max_time u32 @23564 (e.g. 300 / 400), clear
   tender[0] name 23648..23703, hash @23704 (u64), on_complete @23712 (u32). Plants already at stage
   1 keep their water entry, which then no longer matches a tender, and have no timer: they need B
   (its timed branch re-arms them on load). Same edit for LILAC_TOMB (record 9) and TAILS_TROLL
   (record 10) at 16 + i*3272 + 640. Changes game design (no watering), so it should be opt-out.
   Alternative without design change: make sure Water reaches plants (whole_batch_inputs already
   stops the cook house hoarding it).

## Test of plant_timer_fix (2026-11-01, user's save copy)
Save: 34 plants (25 toncap, 9 Citadel); now 8197 s; 28 ripe wild plants (auto_tend 0) waiting for
a harvest order since second 2413; 2 Citadel at stage 2 with timers 8414 / 8541; nothing stalled.
Test: Citadel 3621 timer set to 8100 (overdue) and next_check 8100. At the next autosave (now 8344)
3621 was at stage 3 (ripe), 3991 (timer 8541, the control) still stage 2. Unpatched the exact
test would never have advanced 3621.

## Harvest jobs (2026-11-13)
- Ripe means the stage has loot. set_stage on such a stage calls 0x1801f3af0, which sets the type's dirty flag
  (types at plant_system+0xa0, 0x20 each: plant index list +8, count +0x10, dirty +0x18, enabled +0x19) and the
  plant's workplace (+0x18) from the nav graph. Every plant is in its type's list (add_plant), wild or sown.
- plant_system::update_harvesting (0x1801f3e70) sets each type's enabled flag from the Cave Farms' queues: status
  0 with no Cave Farm entry for the crop, 1 when an entry has nothing to do (target met), 2 when it wants more;
  enabled = status != 1, and a change marks the type dirty.
- sensor_harvest_update calls plant_system_update_workplace_positions (0x1801ea290): for each dirty, enabled type,
  every plant with auto_tend (+0x30) and a workplace becomes a JOB_HARVEST (update_harvest_jobs). Wild plants
  (auto_tend 0) were skipped at 0x1801ea3cd, so they only got harvested through the plant window's Harvest
  button (order_interact, accepted only when ripe). auto_tend's only other reader is plant_system_harvest
  (0x1801e9c69: reset to stage 0/1, or destroy the plant).
- Map cells: map = [[plant_system+0x10]+0x40], cells u32 at +8, width in 16-tile blocks at +0x30, index
  ((by * wb + bx) << 8) | (ty << 4) | tx; bit 22 explored.
- Removing the enabled gate (0x1801ea372 `cmp byte [rdi+0x19],0; je` -> `jmp +8`) was tried on a copy of
  SouthXanforge_75, where all 23 sown crops sat ripe across savegames 72-75: the job data already had a harvest
  workplace for 6 crop types (7 after), and in 5 game minutes only one Toncap was harvested. So in that colony
  the crops had harvest jobs and farmers didn't take them.
- Why: the job priority. update_harvesting fills a per-type priority array starting at 0 (Low, r14 = 0 from
  0x1801f3ea4) and raises it to a Cave Farm's haul priority only for crops a Cave Farm entry covers; the type
  entry keeps it at +0x1c and update_workplace_positions passes it at 0x1801ea91f. Read live in SouthXanforge_75:
  every type +0x1c = 0, farming skill positive for all 23 dwarves. With +1000 per priority level, Low harvests
  lose to every Normal job. `mods/harvest_priority` raises it to High: all ripe crops but the switched-off
  Toncap were harvested and resown within 4 game minutes.
- A mod giving wild plants (auto_tend 0) jobs at 0x1801ea3cd worked (released in 1.3.0 as harvest_wild_crops)
  but was removed: the user wanted sown crops, which already get jobs.
