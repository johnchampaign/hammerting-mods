# Production stall (cook house crafts nothing), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). File offset = VA - 0x180001000 + 0x400.
Modules: 22 production_system.cpp, 176 sensor_craft.cpp, 56 craft_util.cpp, 246 node_produce.cpp,
21 job_broker_system.cpp. `ps` = production_system data (ecs+0x40).

## Data structures
- `production_queue_entry` (0x550, array ps+0x80, indexed by uid): uid u16 @0, producer @2,
  next @8, recipe* @0x10, input_status[4] @0x18 (0x148 each: filter_count, filters[4] (wc_tag is
  64 B: char[56] + hash @0x38), total_modifier_hashes[8] @0x108), queued_amount u64 @0x538,
  progress_curr/max gamefp @0x540/0x544, repeat_type @0x548.
- `production_queue_entry_extra` (0x68, ps+0x90 by uid): pause_at @4, unpause_at @8,
  is_paused @0xc, keep_claims_when_paused @0xd, running_id @0x10, claim_type_on_complete @0x18,
  claim_ref @0x58, autosell @0x60.
- `producer_data` (0x15f0, ps+0x40, index = ps->0[entity]): entity @0, queue head @0x558,
  producer_comp: destroy_on_completion @0x778, complete_entries_in_order @0x779, reversed @0x77a.
- `recipe_record` (0xec8, database/recipe/*.bin after u64 count, u64 bytes): tag @0,
  input[4] @0x80 (0x108: u64 count, cls[4] @8), key_value_costs[4] @0x4a0 (0x88: i32 16.16 amount,
  tag @8, e.g. KV_STATUSBAR_FUEL), profession_tag @0x8e0, profession* @0x920, behavior_tag @0x928,
  is_never_same @0x970, use_classification_matching @0x971, deliver_only @0xec0.
- `profession_record` (database/profession/professions_cdb.bin, 0x4e8): tag @0, favorite @0x40,
  allowed @0x80 (hash @0xb8), requires_tool @0xc0, can_crit @0xc1, has_speed @0xc2.
  PROF_COOK (record 3): requires_tool = 1. Healer, farmer, explorer, arcanist, hauler, trader: 0.
- CLAIM_PRODUCE ref = producer<<48 | entry_uid<<32 | input_slot (producer_claim_ref). Claimant is
  the building, not a dwarf. Tags: CLAIM_PRODUCE 0x1805a4f60 (hash 0x1805a4f98), CLAIM_HAULING
  0x1805a55a0 (hash 0x1805a55d8).
- `craft_sensor_order` (0x38, sensor_data_craft+8; code offsets): order entity +8, producer +0xa,
  workplace +0xc, prio +0x10, jobs ptr +0x14 / count +0x1c (`craft_sensor_job` {job_id u32,
  entry uid u16}), has_path +0x24, has_tool +0x25, profession* +0x28, input_status +0x30
  (1 nothing missing, 2 missing but haulable, 3 missing and not haulable). sensor_craft.bin saves
  only order/producer/workplace/jobs (init_from_system 0x1803cb5a0); the flags are recomputed.
- `order_craft_data_t` (order->_data): producer @0, has_path @2, has_tool @3,
  missing_resources[32] @8 (0x110: cls[4], total_hash @0x100, is_statusbar @0x108, missing @0x109,
  haulable @0x10a, on_the_way @0x10b), profession* @0x2208. `order`: executing @0x14,
  status @0x18 (0 ORDER_UNABLE, 1 UNCLAIMED, 2 CLAIMED, 3 CRITICAL).
- Entity states (game_entity.h): 0 DESTROYED, 1 INACTIVE, 2 OUT_OF_FUEL, 3 AUTO_INACTIVE.

## Readiness: production_system_ready_to_craft (0x18014f7a0)
False if queued_amount == 0 (0x18014f7f2) or extra.is_paused (0x18014f840). Per input slot with
count > 0: n = calc_input_slot_ready(slot) (0x18014d88e); n < count -> not ready, out_missing =
count - n. Per key-value cost: statusbar named after the first '_' (KV_STATUSBAR_FUEL ->
STATUSBAR_FUEL) on get_key_value_cost_target (0x1802dc660) must be > 0 and >= amount *
(1 - progress) (0x18014fa8f / 0x18014fa96). Cauldron recipes need fuel 25 (yeast 10). Then fluid
space (FLUID_DRAIN_SINK only) and check_upgrade_is_valid (0x1802dc040).

calc_input_slot_ready (0x18014d330): claim_system_get_claimed_entities_with_ref(ref for this
uid/slot) (0x18014d38f). Count <= 1: returns the number of claimed items. Count > 1: returns the
size of the largest group of claimed items sharing one global_inventory_entry (same item type and
modifiers), so 5 mixed flowers are not 5 flowers. Only claims count; items merely lying in the
building do not.

## Claims (inputs)
- Added only when an item enters the building inventory: inventory_moved_cb (0x1801523c0) ->
  inventory_changed (0x180153490). For each added item: try the hint entry, else walk the queue
  from the head (0x180153530..0x18015356c); the FIRST entry whose wants test passes gets it.
  A CLAIM_HAULING claim aimed at this producer is released (0x180153615), then
  claim_system_add_claim_if_unclaimed(CLAIM_PRODUCE) (0x180153676), skipped for deliver_only.
  Item removed from the inventory: claim_system_release_claim_if_claimed (0x18015368f).
- production_queue_entry_wants_entity (0x180153000): paused entry wants nothing unless
  keep_claims_when_paused and the item already sits in this building (0x18015303f..0x180153078).
  Per slot (start rotated by item & 3): skip if n >= count * queued_amount (0x180153102 ..
  0x180153115). So an entry reserves inputs for its whole queued amount, not one craft. Once a
  slot holds one craft's worth, only items whose modifiers match the claimed ones are accepted
  (modifier_system_match_modifiers, 0x180153134). Else filter by total-modifier hashes, deliver-only
  bitset, CLS_ITEM and the recipe classifications. Haul demand uses the same test
  (production_system_check_needed_entities 0x18014e680 -> 0x18014e9e8).
- Released by: release_production_queue_entry (0x180152b70, all 4 slots, called when amount
  reaches 0 with repeat FIXED_THEN_REMOVE: 0x18014dad0 / 0x18014dcdb); check_correct_input
  (0x1801536f0), which releases the entry's claims and then re-offers every unclaimed item in the
  building through inventory_changed with that entry as hint. It runs on set_entry_paused
  (0x18014fd18), set_production_amount (0x18014dcb4), start_production_internal (0x18015400d) and
  craft completion (0x18014e3d8). Because the entry is the hint, it takes the same items back.
- Nothing releases the claims of an entry that stays unready. Entry order (entry_move
  0x180151020) does not touch claims. Claims belong to the building, so dwarf death, job teardown
  (try_teardown_job_cleanup, remove_job) or reassignment leave none behind. After removing an
  entry its items stay unclaimed until another entry's check_correct_input runs or the item moves.
- Hand-made orphan claims were seen to vanish within minutes (food_ai.md). The code that does
  this was not found.

## Jobs: sensor_craft_update (0x1803c6f00)
Phase A, per craft order (= per producer):
- state_system_get_states(producer): producer_is_active = !DESTROYED && !INACTIVE &&
  !AUTO_INACTIVE (0x1803c716b..0x1803c7187). OUT_OF_FUEL is not checked here (fuel is a KV cost).
- Walk the WHOLE queue (0x1803c74e0..0x1803c7bed): every entry gets its own broker job
  "JOB_CRAFT_<profession>" (add_job 0x1803c767b). possible = producer_is_active &&
  ready_to_craft(entry) (0x1803c7b99); job_broker_system_set_job_possible(job, possible,
  JOB_IMPOSSIBLE_MISSING_RESOURCES) (0x1803c7bbd). The reason tag (0x1805bc880,
  "JOB_CRAFT_MISSING_RESOURCES") is the same whatever the actual cause.
- The walk stops after the first entry only if producer_comp.complete_entries_in_order
  (0x1803c7bd1 / jne 0x1803c7bd8). Otherwise an impossible entry does not hide the ones below it.
- Jobs for entries that no longer exist: try_teardown_job_cleanup + remove_job (0x1803c7c48).
Phase B, order status (0x1803c8050..0x1803c96e0):
- has_tool = some player character has toolbelt_system_get_best_tool_for_job != -1, checked
  only if the profession requires a tool (0x1803c80d3..0x1803c8139).
- has_path = any job has job_broker_system_has_path_to_compatible_worker (has_workers_in_range
  0x18012b4a0) (0x1803c8176).
- For every unpaused entry (0x1803c8d6f), ready_to_craft's missing list is summed into
  order_data.missing_resources (0x1803c8dc6..0x1803c9366). Haulable counts come from
  haul_system_get_destination_haulables (0x1803c81de), on-the-way counts from active hauls.
  Any resource with haulable < missing -> input_status 3 (0x1803c9543..0x1803c9559).
- order.status: has_path && input_status != 3 -> UNABLE becomes UNCLAIMED, else UNCLAIMED
  becomes UNABLE (0x1803c9688..0x1803c96b0). Tool state does not affect it.
- The "Impossible Orders" alert (database/alert/alert.bin ALERT_IMPOSSIBLE_ORDER) is
  ORDERS('FACTION_DWARF').FILTER(ORDER_STATUS('ORDER_UNABLE')). An order is named by
  ORDER_CRAFT_LOCALIZED = "Craft: " + PRODUCER.QUEUE('SCAFFOLDING_SETUP').FIRST.RECIPE.NAME, the
  top entry. "Craft: Algae Pancakes" therefore means the cook house's order is UNABLE because of
  any entry, or because no worker has a path. It does not single out Algae Pancakes.

## Worker side
- craft_job_begin (0x1803c1a00): order status CLAIMED (2), executing = dwarf, blackboard gets
  producer and entry, behaviour from recipe/profession (ai_behavior_system_set_behavior
  0x1803c1c69). craft_job_is_done (0x1803c1ca0) = !ready_to_craft(job's entry).
- The produce BT re-picks its entry with calc_best_production_queue_entry (0x1802db610), called
  by bt_eval_produce_update (0x1804d90dd) and node_produce. Walks from the head:
  - not ready: skip, unless complete_in_order and queued > 0 -> return NULL (0x1802db6bd);
  - KV[profession.allowed] on the dwarf (PROF_COOK_ALLOWED) must be PCT_U64 != 0, otherwise
    skip (0x1802db6f7..0x1802db728);
  - requires_tool && toolbelt_system_get_best_tool_for_job == -1 -> skip (0x1802db77f /
    0x1802db788). A tool is a toolbelt item whose modifiers include the profession's tag (prof
    +0x420) with value > 0 (0x1801c6650).
  NULL -> eval score 0 (0x1804d910e), so the dwarf does not produce.
- Job broker matching (allowed bitset per worker from KV, is_worker_allowed_for_job_type
  0x18012b770; navgraph reachability of workplace positions in has_workers_in_range) was read
  only in outline. Whether the broker refuses tool-less cooks before calc_best does was not checked.
- Building health: no check in the craft path. The workplace comes from
  interaction_system_get_positions + filter_interaction_positions (0x1803c54e0). Scaffolding
  entries (RECIPE_SPECIAL_SCAFFOLDING_SETUP) are queue entries hidden from the UI list.

## Cook house recipes (recipe_cauldron_cdb.bin, all PROF_COOK, fuel 25)
Greencake/Algae Pancakes: algae + flour. Gloom Flour: 2 gloom wheat. Hard Tack: flour + water.
Brochette: bacon. Broth: crab shell + water. Fish Soup: plain fish + water. Flower Water: 5 flowers
+ water. Roast: meat. Lichen Soup: 2 lichen + water. Water (CLS_FLUID_WATER) is an item made at
the hand pump (PROF_FARMER), not a fluid.

## Causes of the observed state, ranked
1. Every entry lacks an input, and entries near the top hold the inputs the others need. Arriving
   items go to the first entry that wants them, up to count x queued_amount, and those claims are
   never released while the entry stays unready. Raising amounts to 60 makes the top entries hold
   more. Five of nine recipes need water. Check: group the 28 claims by ref (uid, slot) against
   the recipe counts. No entry complete -> this cause.
2. Some entry is complete but no dwarf can cook. PROF_COOK requires a tool: no player character
   has a toolbelt item with the cook modifier, or every dwarf has PROF_COOK_ALLOWED == 0, or no
   worker has a path to the workplace. Check: job_broker jobs of the cook-house workplace with
   possible = 1; dwarves' toolbelt contents; the PROF_COOK_ALLOWED KV.
3. Fuel 0 < STATUSBAR_FUEL < 25: "has fuel", but no cauldron recipe is ready.
4. Building state INACTIVE or AUTO_INACTIVE: every job is impossible.
5. complete_entries_in_order set (producer_data +0x779): an unready top entry blocks everything.
6. For a slot with count > 1, claimed items of mixed variants (largest identical group < count).
7. Stale claims whose ref names an entry uid that does not exist (after load). Unlikely, given
   the cleanup seen in food_ai.md.

## Patch candidates
- Claim one craft's worth instead of the whole queue: production_queue_entry_wants_entity
  0x180153102 `4c 8b ae 38 05 00 00 4c 0f af ea` (r13 = queued * count) -> `49 89 d5` (r13 = count)
  + `0f 1f 84 00 00 00 00 00` (file 0x152502, 11 bytes). Haul demand becomes one craft per entry.
  Claims that already exist are untouched until the next check_correct_input of their entry.
- Cooks without tools: data patch professions_cdb.bin PROF_COOK requires_tool (record 3, +0xc0)
  -> 0. calc_best then uses tool index -1 as for healers. Code alternative:
  0x1802db786 `74 22` -> `eb 22` (all professions).
- Release the claims of an entry that stays unready (input_status 3): needs a code cave in
  sensor_craft_update after 0x1803c8dc6 (call release_production_queue_entry's loop
  claim_system_release_claims_with_ref 0x1801d32a0 for that uid, then check_correct_input for the
  other entries). Not written.
- Without a patch: delete or zero the impossible entries (this releases their claims), then
  change the amount of the entries that should get the items (check_correct_input re-claims
  them for that entry first).

## Confirmed in the user's save (autosave 2026-11-01 11:12, cook house 2655)
Claims by (entry uid, slot), from claims.bin refs:
- 0x21 Algae Pancakes (Greencake): slot 0 = 3 algae; slot 1 (flour) empty.
- 0x29 Gloom Flour: slot 0 = 1 gloom wheat of 2.
- 0x24 Crab Broth: slot 1 = 2 water; slot 0 (crab shell) empty.
- 0x23, 0x3f (Hard Tack and Fish Soup): slot 1 = 5 and 4 water; slot 0 (flour / plain fish) empty.
- 0x41 Flower Water: 2 flowers of 5, 5 water.
- 0x44 Lichen Soup: 1 lichen of 2, 5 water.
- 0x40 Brochette (bacon), 0x42 Roast (any CLS_MEAT): no claims.
No entry is complete, so cause 1 holds: 21 water (the colony's drink; "Lack of Drink" alert was on)
and 7 raw foods sit claimed in the cook house for good. Flour depends on Gloom Flour, which waits
for a second gloom wheat. Not resolved: why Roast gets none of the ~38 raw meats (meat_crab,
meat_mystery, haunch_rat) in the colony. Many sit in 2-3 item inventories with crab shells (dead
creatures' loot); whether haulers take from those, and whether those classes match CLS_MEAT, is
unchecked.
Save layout seen: job_broker_system/user_data/job_craft_prof_<prof>.bin = 6-byte records
(order entity, producer, entry uid); production_system.bin queue entries carry
[u16 ?, u16 ?, u16 uid, u16 producer][u64 next uid][u64 recipe tag hash].

## Fix: mods/whole_batch_inputs (2026-11-01)
Hold-and-wait removed by all-at-once requests (Havender). The slot limit in
production_queue_entry_wants_entity (0x180153102, `r13 = queued * count`) calls a cave in .hmod
(0x18060c000): deliver-only recipes keep the old limit; otherwise r13 = count (one craft), and
r13 = 0 unless every slot s of the recipe has calc_input_slot_ready(ps+0x4f0, entry, s) +
sum over global_inventory_system_get_input_slot_alternatives(ps+0x478, recipe hash, s) of
(_claimed_count[GITC_UNCLAIMED] @+8 + _claimed_count[GITC_HAUL] @+0x18) >= count. Haul demand
uses the same test, so infeasible entries stop requesting haulers too.
Not atomic: two entries can both see the last unit of an input, and the loser holds at most
one craft's worth until it next crafts or its amount changes. Existing partial holdings are
kept until check_correct_input runs for that entry (amount change, pause, craft).
Test on the user's save (lastsave, entries nudged +/- once): cook house claims 28 -> 6 (only
the un-nudged Lichen Soup kept its set); 16 water, 3 algae, 2 flowers, 1 gloom wheat freed;
9 of the freed water used within one autosave interval; quarry kept crafting (19 slabs);
smithy, foundry, quarry and construction orders reserved full batches; no errors.
Roast Meat (any CLS_MEAT) holding no meat is not a stall: it is a Maintain entry showing x5/5
with a grey (idle) status icon, i.e. 5 roasts in stock. Raw meat in the save (lastsave): 162
items; 123 are overworld market stock (claim type 9 by ow_hex), 27 sit in 1-3 item inventories
of live wild creatures (rats: haunch + hide/bone, crabs: meat + shell, others: one mystery meat;
36 creatures), 12 lie loose. Meat classes (item_modifiers_cdb.bin: CLS_MEAT_CRAB,
CLS_MEAT_MYSTERY, CLS_HAUNCH_RAT) all derive from CLS_MEAT. Raw meat has no HUNGER modifier, so
it is not eaten raw.
Save formats seen: tag_component_system.bin = u64 n, then per tag {u64 0x38, u64 0x38,
name[56], u64 hash, u64 count, u64 bytes, count u16 entities, 8208 bytes (bitset)}. Items carry
no CURRENTLY_IN_OVERWORLD tag (only ow_* map entities do). The queue UI's "xN / M" is the
current matching stock against the target, not a crafted count.

## Correction: the all-at-once test was removed (2026-11-03)
The cave's feasibility test (above) caused two stalls in the user's colony (savegame11, game
time 5986), because it read gie._claimed_count, which leaves out floor items (0x1801fff05):
- Small Foundry: Copper Ingot x10, 425 copper ore on the floor, none stored. Unclaimed = 0, so
  r13 = 0, no haul demand, order UNABLE ("Waiting for 1x Copper Ore. 0/1 found"). It had kept
  working only while the chest held copper ore; the 12 stored ore ran out and it stopped.
- Small Cook House (4 ingots, 4 slabs): 0 ingots free, so it asked for nothing, not even the 6
  free slabs. Its haul job vanished. 1-ingot smithy orders took each ingot as it was made.
Same save, same mods apart from whole_batch_inputs, about 210-330 game seconds each:
| Version | Ingots | Copper ore moved | Cook house |
|---|---|---|---|
| With the test | 0 | 0 of 425 | no claims, no haul job |
| With the test, buildings exempt | 0 | 0 of 425 | 4 claims within 150 s, then waits for ingots |
| Mod off (user raised foundry priority in this run) | 11 | 11 | haul job open, no claims |
| Test removed, r13 = count (no input) | 3 | 3 | haul job open, no claims |
With the test, few entries asked for anything, so 4 haul jobs were open and the cook house was served
quickly. Without it about 10 are open. Continuing the last run to about 680 game seconds: still 3 ingots,
the foundry's haul job open with no copper ore consumed after t 6255, and no claims at any of the 5
construction sites, while dwarves kept hauling to the cave farm and infirmary. The user's raised foundry
priority in the mod-off run gave 11 ingots, so priority may decide this. The job broker's choice
(assign_workers, VA 0x18012ce20) has not been read.
The order's "Craft: <recipe>" in Impossible Orders is the queue's top entry and says nothing about
which entry is short (see above); the user's already-complete Simple Lantern showed this.
The test was removed rather than fixed: floor counts need a scan of 64K entities per check, and
the patch site runs before the class filter, so per entry x slot x item kind. r13 = count remains.
That keeps the main fix (an entry stops absorbing supply after one craft's worth) but a partial
set can be held again: at most one craft per entry, and new supply stays free once entries are
full. The original test on the Nov 1 save (28 claims -> 6) was with the removed version and has
not been repeated.

## Full inventory slots (BUGS B2, 2026-11-04)
Capacity is INVENTORY_COMP (`inventory_component_config`: u64 item count, u64 capacity) in `.entity` files. The table row is u16 0x72ee, u16 size, u32 0, u64 file offset.
Small production buildings 120, large 240, fishing pier 60, chest 48, storage 600, chest_start 320, upgrade unit 64, `logic/player_command_producer` 126 (126s in the save match order and build sites [inferred]).
Haul demand is limited by free slots: bucketize passes capacity - count (0x1801e1f50), and bt_haul_update trims the load the same way (0x1804f52b3). inventory_system_move_items also stops at capacity.
Sums of inputs for one craft of every recipe on a station: anvil 60, cauldron 53, brewers still 40, farm 21, dwelling upgrades 29. Largest build is Large Vault, 81 parts. So with `whole_batch_inputs`
(one craft per entry) a normal queue can't fill those slots from claims. Not excluded: many duplicate entries of the same recipes, and deliver-only mission recipes (up to 75 items, whole amount), whose building wasn't checked.
Forum reports: the dwelling one (18 slots) is from Jan 2022, before 1.2.39; the upgrade unit has 64 now [read from files, not tried in game]. The factory one (80 queued, no slot for water) is the whole-queue reservation.

Test: copy of savegame16 with saved capacities edited to cook house 30, foundry 7, smithy 5 (each about its current count), `_test_quiet`, no input, key 3, 330 s of log time, 1 run each.
| Items per 66 s of log time | With whole_batch_inputs | Without |
|---|---|---|
| Cook house food and flour | 7, 2, 15, 11, 7 | 2, 16, 5, 0, 0 |
| Ingots | 2, 10, 10, 14, 12 (48) | 8, 14, 29, 40, 41 (132) |
Without the mod the cook house sat at 33 slots, 30 claimed, in all 7 autosaves over 3 minutes and cooked nothing at the end: the reported deadlock. With it, claims moved between 4 and 11 and it kept cooking. Holding fewer claims is what
keeps it free, and finished goods didn't clog: the smithy at capacity 5 made 34 items. So no new mod. Ingots came about 2.75 times faster without the mod, in this one run with the foundry capped at 7. Why was not
traced; carrying one craft's worth per trip is a guess. Not tested: a building with 120 real items, duplicates, missions.

### Cost of whole_batch_inputs at normal capacity (2026-11-04)
Copy of savegame16, unedited, `_test_quiet`, no input, key 3, items in 330 s of log time. Order W1, N1, N2, W2.
| | With (2 runs) | Without (2 runs) |
|---|---|---|
| All items spawned | 309, 275 | 370, 394 |
| Ingots | 50, 36 | 84, 88 |
| Smithy items | 51, 33 | 59, 63 |
| Cook house food and flour | 30, 28 | 31, 34 |
| Quarry products | 35, 34 | 32, 38 |
| Cook house claims, last autosaves | 5-7 | 21-28, slots 56 |
So the mod costs about half the ingots and a quarter of all output in this colony, and cooking barely changes. Without it, cook house claims kept rising, which is the road to the stall. Foundry claims read 1 in both cases, so they don't explain it.
Why is not traced. A guess: demand of one craft per entry makes a hauler carry one ore per trip.

### One-input recipes may reserve 5 crafts (built, 2026-11-04)
A recipe with one input can't hold a partial set against another input, so `whole_batch_inputs` now gives it min(queued, 5) crafts. Multi-input recipes keep one craft, deliver-only keeps the whole amount. 177 of 312 recipes have one input
(smelter 9 of 10, anvil 20 of 34). Used input slots are contiguous in every recipe, so input[1].count == 0 (recipe+0x188) identifies them. `SINGLE_CRAFTS` in mod.py sets the 5; other values weren't tried.
Same save and conditions as the table above (W = one craft, N = mod off):
| | New, 2 runs | W | N |
|---|---|---|---|
| All items | 347, 338 | 309, 275 | 370, 394 |
| Ingots | 77, 81 | 50, 36 | 84, 88 |
| Smithy items | 52, 57 | 51, 33 | 59, 63 |
| Cook house food and flour | 24, 22 | 30, 28 | 31, 34 |
| Quarry products | 36, 31 | 35, 34 | 32, 38 |
Ingots and smithy items in the last fifth of the new runs fell to 3-5 and 0-3. N1 also fell (8, 6). Queues running out would fit but wasn't checked. Cooking was lower in both normal-capacity runs and why isn't known: dwarves busier at the foundry is a guess. Food stock and hunger weren't measured.
Frozen cook house test again (capacities 30, 7, 5, 1 run): cook house food 7, 13, 4, 5, 3 (32), claims moved between 3 and 14, ingots 94. No freeze. No exceptions or unlocks in any run.
Worst case for slots is now higher: every recipe queued at 5 or more is 156 on the anvil and 124 on the white anvil, over 120 on small buildings; cauldron 89, smelter 65, farm 105. It takes nearly every recipe queued at once. Not tested: long play, scarce ingredients shared by several one-input recipes.

### Hunger in those runs, and a cut-off dwarf in all of them (2026-11-04)
Read from each run's last autosave (t about 12360). Six of the seven dwarves ended between hunger 1029 and 2262 (start 1374-1985) in every version, and cooked food stayed at 37-38 (start 39), so the lower cooking did not make anyone hungry in about 1500 game seconds. Longer play is still unmeasured.
One dwarf was cut off from the colony in every run and starved to hunger 0 or close (`stuck_dwarves.md`, end): 2209 at t 10915 with the mod on, 2236 at t 11084 with it off. So every run had six working dwarves, not seven, and mod-off runs kept their seventh about 170 game seconds longer and lost a different dwarf. That muddies small differences in the tables above. W lost the same dwarf as New and still cooked 30, 28, so it doesn't explain the cooking drop.

## Which queue entry a building crafts (2026-11-06)
`calc_best_production_queue_entry` 0x1802db610 walks the queue in order and returns the first entry for which `production_system_ready_to_craft` is true, a KV gate on the recipe passes ([recipe+0x920]+0xb8 non-zero) and a required tool exists. A not-ready entry with an amount stops the walk if `production_system_should_complete_queue_in_order`. So an entry at the top that is always ready (Maintain on something being consumed, like Gauze used as medicine) starves every entry below it. Seen on a copy of savegame27: 39 Gauze, no Balm of Ooze, although the balm entry held both inputs.
