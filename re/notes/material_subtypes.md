# Material subtypes in production inputs (BUGS B3, B4), game.x86_64.dll 1.2.39

VAs, image base 0x180000000 (file offset = VA - 0x180001000 + 0x400). Read from the pristine
`game.x86_64.dll.hmod-orig`. Builds on `production_stall.md` (layouts of queue entries, recipes,
claims). Draft caves: `material_subtypes_cave.s` (assembled with tools/cave.py, 978 bytes at
.hmod+0x600, not installed).

## What "identical" means
- Every item maps to one `global_inventory_entry` (header in game_entity_types.h: `_hash` @0,
  `_claimed_count[5]` @8 = UNCLAIMED, SELL, HAUL @0x18, TRADE, DEFAULT, `_comps[64]`, ...).
  `global_inventory_system_get_entity_entry` 0x1801ff900 = `gis_data+0x70[entity]`; entries are
  looked up by `_hash` (`get_entry` 0x1801ff880), and that hash is the item's total-modifier hash.
- entity.x86_64.dll: `modifier_system_get_hashes_for_total_modifiers` (0x180049c50) returns the
  per-entity hash cached at `modifier_list[0]+0x50`; `modifier_system_match_modifiers`
  (0x180047490) compares exactly that field. So "same entry", "match_modifiers" and the player's
  "total modifier hash" selection are one notion: same item type and the same full modifier set.
- Outputs inherit materials. `default_production_complete_cbck` (0x1802d6c00, every recipe's
  `_complete_fn`, set at load 0x180273ec3) takes, for each input slot whose
  `_remove_input_modifier[s]` (recipe +0xe68+s) is 0, every CLS_ITEM-class modifier comp of the
  slot's FIRST consumed item (`modifier_system_get_entity_modifier_comps_with_classification`,
  0x1802d74c9; relabelled CLS_ITEM, parent index rebased, 0x1802d7510..) and adds them to the
  output. Inheritance accumulates through chains:
  - sheet = SHEET + INGOT_x; beam (3 ingots) = BEAM + INGOT_x; machine parts = + SHEET + INGOT_x;
  - support beam (2 lumber + 2 sheet) = BEAM_SUPPORT + LUMBER_y + SHEET + INGOT_x
    (4 woods x 9 metals = 36 kinds);
  - cut gems: rough = ROUGH + GEM_raw; cabochon = CABOCHON + ROUGH + GEM_raw; ... Star of Mara =
    STAR + BRILLIANT + TRILLIANT + CABOCHON + ROUGH + GEM_raw. Each step needs 3 identical inputs,
    so one Star of Mara needs 3^5 = 243 raw gems of a single kind (ruby/emerald/sapphire/diamond);
  - lathed/burnished/runic bone = + the raw bone kind (ANIMAL, DEMON, RESTLESS, SPIDER, STURDY);
    hilt bone (2 crafted bones) needs two of the same craft AND the same raw bone;
  - granite pillar/slab/block = + CHUNK_GRANITE (one kind only); lumber has 4 kinds
    (DRIFTWOOD, RECLAIMED, VENDAR, CITADEL), ingots 9.
  - rmmod is set only for ASH_BONE slot 0, PARCHMENT slot 0, LEATHER_TOP_GRAIN slot 1 and the
    ORDER_STORE_* recipes; their outputs do not carry that slot's kind.
  - Crit success can add one more modifier (modifier_system_add_modifier at 0x1802d8eb5, chosen
    from profession data), which would make yet another kind. Not checked further.
- So uniform material is intended for crafts: the output takes the first item's material, and
  readiness insists on `count` identical items. For buildings it is not (see B4).

## Claim and readiness rules for a slot with count > 1
`production_queue_entry_wants_entity` (0x180153000), per slot (start rotated by item & 3):
1. n = `calc_input_slot_ready` (0x18014d330). count <= 1: n = number of claimed items, `out`
   gets them all. count > 1: n = size of the largest group of claimed items sharing one
   global_inventory_entry; the first group found wins ties (strictly greater replaces,
   0x18014d9a6); `out` gets only that group's entities (0x18014d9f3..).
2. Skip the slot if n >= queued * count (0x180153102..0x180153115).
3. If n >= count and the recipe's `_use_classification_matching` (+0x971) is 0: accept only if
   `match_modifiers(out[0], item)` (0x180153134), i.e. the same kind as the complete group.
4. Otherwise (n < count, or the flag set): if the entry's selected total-modifier hashes for the
   slot (entry +0x120+0x148*s, 8 x u64) are non-empty, accept iff the item's hash is listed, with
   no class check (0x180153159..0x1801531b6). Else deliver-only tag check, the item's main
   (CLS_ITEM-labelled) modifier must classify as recipe `input[s].cls[0]` (only cls[0],
   0x1801532dc), and `match_classifications_with_label` against the entry's filters.
- So while no kind has a full craft's worth, ANY kind of the class is accepted, with no limit
  on the total held (the cap compares the largest group, not the claim count). Haul demand uses
  the same test, cached per item kind (`check_needed_entities` 0x18014e680), with counts
  {per_craft = count, total = r13, delivered = n} (0x18015335c; producer_need_counts). The
  haul bucketizer requests min(total, 3*count) - n (0x1801e2a3b..0x1801e2a6e), so a mixed hold
  keeps asking for more.
- Ready (`ready_to_craft` 0x18014f7a0) needs n >= count per slot; the tooltip's "a/b" is
  count - missing, i.e. the largest group ("materials not counted").
- Completion consumes min(n, count) items of `out` per slot (0x1802d7464..0x1802d76b6: release
  claim, CLAIM_ABOUT_TO_DESTROY, move out, destroy). Never more than the recipe count.
- `_use_classification_matching` is read nowhere else (only 0x18015312b). `_is_never_same` is
  forced on for OVERWORLD_DELIVERY producers (0x180273e7b) and only used by
  start_production_internal.

### Mixed holds in vanilla
- Yes: an entry can hold a set it can never complete and keep it. Example, 2 bones: holds 1
  sturdy + 1 restless, n = 1; it accepts any further bone, and completes only when some kind
  reaches 2. If the colony (outside other claims) has no second item of a held kind, it waits
  forever, and the bones it holds are lost to every other entry. Cut gems are the worst case
  (3 identical per step, few gems of each kind).
- Nothing releases or swaps mismatched items. `check_correct_input` (0x1801536f0; on amount
  change, pause, start, craft completion) releases all the entry's claims and re-offers the
  building's items with that entry as hint, so it takes the same mix back (n < count accepts
  anything). After a craft the leftovers of other kinds stay claimed the same way.
- Queued > 1 crafts lock onto a kind: once one kind has a craft's worth, only that kind is
  accepted until queued * count (step 3). Which kind wins is whatever haulers deliver first
  ("smiths use the cheapest metal unless you pick"); count-1 slots lock to the first item.

### With whole_batch_inputs (cave at 0x18060c000)
- r13 = count, and r13 = 0 unless every slot has n_s + SUM over alternatives (unclaimed + haul)
  >= count_s. Both use n = largest group, so:
  - mixed holds still form: holding 1 sturdy, needing 1 more, with 1 restless unclaimed, the
    slot is "feasible", takes the restless, n stays 1, and the entry turns infeasible holding
    both. Kept until its amount changes, it is paused or it crafts (and then it re-takes them);
  - the SUM counts kinds that cannot join the held group; over-claiming continues while the
    sum of other kinds covers count - n;
  - the lock (step 3) is dead code, since n >= count now always skips.
- Bug: entries with queued amount 0 (not paused) still get r13 = count and reserve one craft
  (vanilla gives r13 = 0). `ready_to_craft` is false for them.

## Player input selection (B3 "stations forget material choices")
- UI: `filter_select_craft_entry.entity` runs `order_craft_toggle_filter(producer, hash, slot)`
  (command handler 0x1802ef420, registered at 0x180012e8f) -> `toggle_template_total_modifier_hash`
  (0x18014d290): toggles the hash in the TEMPLATE's input_status[slot] (producer_data +8 is the
  template entry; hashes at producer_data +0x128 + 0x148*slot), 8 at most.
- `order_set_template_recipe` (craft/recipe.entity, recipe_text.entity, upgrades) ->
  `production_system_set_template_recipe` (0x18014ce40) sets the recipe, amount 1, repeat 0, and
  for each slot zeroes the selected hashes and copies the recipe classes into filters. Every
  click on a recipe, even the one already selected, wipes the material choice.
- `order_new_craft_from_template` -> `start_production_from_template` (0x18014ce00) copies the
  template into a new entry. The entry keeps its copy; nothing can change an existing entry's
  inputs: `production_system_set_production_input` (0x18014d320) is a bare `ret`.
- Saves keep both: the producer writer saves the template through the entry writer
  (0x1801547aa -> 0x180154980), which writes the hashes (0x180154afd). The reader skips them for
  saves older than major version 4.

## B4: construction and building recipes
- All building (rooms_cdb BUILDING_*, MECH_*), upgrade (upgrades_cdb UPGRADE_*) and overworld
  mission/delivery recipes have `_use_classification_matching` = 1; ordinary crafts and
  upgrade_cdb CLS_OWUPGRADE_* have 0. The flag only disables the lock (step 3); readiness still
  needs `count` identical items. With queued = 1 the entry accepts every class-matching item
  while n < count, so a foundry (3 support beams) can take 6 mixed ones and still show 2/3.
- When the craft finally completes, 3 of one kind are consumed; on the last entry of a
  `destroy_on_completion` producer (building spots) `inventory_system_drop_all_items`
  (0x18014e33d -> 0x180117d20, moves to entity 0) dumps the rest on the floor, where they rot in
  about 2.8 game hours unless something picks them up. This is "the foundry ate six beams".
- Large Vault (BUILDING_VAULT_LARGE): 50 CLS_PILLAR_GRANITE (one kind, fine), 20 SLAB_GRANITE
  (one kind), 10 CLS_BEAM_SUPPORT (all 10 of one wood+metal pair: "only Iron or Citadel-wood
  pillars" is whichever pair the colony had 10 of; English name "Support Beam", described as a
  pillar of metal reinforced lumber), 1 CLS_GEM_STAR_CUT (count 1: any, but making one needs 243
  raw gems of one kind). Overworld deliveries like OWMIS_SD_1 (15 beams) also need 15 identical.

## Causes, ranked
B3
1. count > 1 slots need `count` items of one kind; wants accepts any kind until then and never
   lets go (vanilla and whole_batch_inputs). Inherited materials multiply the kinds of crafted
   parts (36 support beams, gem chains).
2. Lock to the first completed kind for the rest of a queued batch (0x180153134) and to the
   first item for count-1 slots: material = arrival order.
3. Material choices live on the template only, are wiped by every recipe click, and cannot be
   set on queued entries.
B4
1. calc_input_slot_ready ignores `_use_classification_matching`: buildings need identical parts,
   over-claim mixed ones, and show the largest group as the delivered count.
2. Leftover claimed parts are dropped and rot when the building spot is destroyed.
3. Vault data: 10 identical support beams and a single-kind Star of Mara chain.

## Patch candidates
Code (all in `material_subtypes_cave.s`, BASE 0x18060c600; one mod replacing
whole_batch_inputs, whose site is retargeted):
- A `batch_limit2` (0x18060c600). Site 0x180153102: old `4c 8b ae 38 05 00 00 4c 0f af ea`,
  new `e8 f9 94 4b 00 66 0f 1f 44 00 00`. Deliver-only keeps queued * count; amount 0 -> 0;
  else r13 = count, and per slot `slot_plan`:
  - relaxed slot (count <= 1, use_classification_matching, or remove_input_modifier[s]):
    feasible iff held + SUM(unclaimed + haul) >= count (the old rule; held = all claimed);
  - strict slot: claimed = `claim_system_get_claimed_entities_with_ref(data+0xb8, producer,
    ref, buf, 0x100)` (0x1801d4890); for each alternative T of
    `get_input_slot_alternatives(data+0x478, recipe hash, s)` (0x1801ff7c0), restricted to the
    entry's selected hashes: held_T = #claimed with `gis_data+0x70[e] == T` (gis_data =
    [data+0x4b8]), tot_T = held_T + T.unclaimed (+8) + T.haul (+0x18). Feasible iff some
    tot_T >= count. Target = feasible T with most held, then most total.
  - any slot infeasible -> r13 = 0. For the asked slot, rax = held_target (becomes the haul
    "delivered" count) and an item whose entry is not the target gets r13 = 0 (refused), so
    claims and haul demand go to one kind only. Item = caller's [rsp+0x2d0] (cave rsp+0x580).
- B `release_mixed` (0x18060c8d8). Site 0x180152ed0 (production_system_update, walk over every
  queue entry; r14 = production data, rbx = entry): old `83 bb 48 05 00 00 04`, new
  `e8 03 9a 4b 00 66 90`; the cave ends with the same `cmp dword [rbx+0x548], 4` for the `jne`.
  For unpaused, non-deliver entries: if a slot holds items and (amount is 0, or the entry is
  infeasible, or held > held_target), call `check_correct_input(data, producer, entry)`, which
  releases and re-offers; A then lets the entry take back only its target kind. Converges (a
  second pass finds held == held_target or nothing held). This also clears existing vanilla
  mixed holds after load. Cost: 4 slot_plans per entry per update; if too slow, gate it on a
  tick counter or move it to sensor_craft_update.
- C `relax_count` (0x18060c996). Site 0x18014d3a2 (calc_input_slot_ready): old
  `4c 8b 84 0a 80 00 00 00 49 83 f8 01`, new `e8 ef f5 4b 00 0f 1f 80 00 00 00 00`, keeping
  `77 31` after it. Slots of recipes with use_classification_matching, or with
  remove_input_modifier[s], count every claimed item (the count <= 1 path). Fixes B4 1 and 2
  (no over-claim, true delivered count, any 10 support beams), deliveries, ash bone/parchment.
  A depends on C (same "relaxed" rule).
- D `keep_template` (0x18060c9c0). Site 0x18014ce6b (set_template_recipe): old
  `4c 89 44 01 18`, new `e8 50 fb 4b 00`. Clicking the template's current recipe again returns
  early and keeps material choice, amount and repeat. A different recipe still resets them.
- Optional: let mixed materials into crafts too (e.g. treat every slot as relaxed in C). That
  changes outputs (first item's material wins) and the gem economy, so it should be opt-in.

Data only (newly crafted items only; existing items keep their modifiers). Bytes in the
extracted files `database/recipe/*.bin` (record = 16 + i*0xec8; rmmod = +0xe68+slot), 0 -> 1:
- recipe_anvil_cdb.bin #5 CLS_BEAM_SUPPORT: 0x5860 and 0x5861 (lumber, sheet). All new support
  beams become one kind: buildings and the Large Vault take any 10.
- recipe_smelter_cdb.bin CLS_SHEET #9 0x9380, CLS_BEAM #0 0xe78, CLS_MACHINE_PARTS #7 0x75f0,
  CLS_RAIL_TRACK #8 0x84b8 (slot 0): metal parts stop carrying the ingot kind.
- recipe_white_anvil_cdb.bin CLS_GEM_ROUGH_CUT #3 0x3ad0: rough gems lose the raw kind, so the
  chain needs only triples of one raw kind for the first step (81 triples), not 243 of one kind.
  Shipped as `mods/gem_cut_rebalance` (2026-11-12; in 1.6.5 the kind is kept again, since cut gems take their name
  and icon from it and kindless rough gems showed blank and could not be picked for the next cut), with counts Rough 3, Cabochon/Trilliant/Brilliant 1, Star 3 and the
  same byte on the Star slot (#7, 0x75f0), so a Star costs 9 raw gems of any kind.
Trade-off: the material modifiers may feed item stats/price (ME_* entries); not checked.
Under C these rmmod bytes also make the slot relaxed.

## Checking a save for mixed holds (read-only)
- claim_system/claims.bin: u64 n, then 13-byte {u16 entity, u16 claimer, u64 ref, u8 type};
  type 4 = CLAIM_PRODUCE by a building. ref = producer<<48 | uid<<32 | slot.
- Group type-4 claims by (claimer, uid, slot); recipe from production_system.bin entries
  ([u16, u16, u16 uid, u16 producer][u64 next][u64 recipe tag hash]); count = recipe
  input[slot].count (record +0x80+0x108*slot).
- Kind per entity: debug_name_system names give raw kinds (bone, gem, lumber, ingot files).
  Crafted parts share one entity file per output, so their inherited material is only in the
  modifier system's save data (per-entity modifier comps with label CLS_ITEM). Not decoded yet;
  `save.py list` shows the file names.
- Mixed hold: count > 1, two or more kinds, largest kind < count. Over-claim: group size >
  count (vanilla buildings). Waste: claims on entries with amount 0 (whole_batch_inputs bug).
- Not verified: building inventory capacity (whether mixed parts fill it and block delivery),
  and how often production_system_update runs.

## Shipped (2026-11-01)
- mods/class_matched_inputs: caves C (relax_count) and D (keep_template) at .hmod+0x400.
- mods/whole_batch_inputs: amount-0 entries now want nothing (queued == 0 -> r13 = 0).
- Not shipped: caves A (per-kind feasibility) and B (release mixed holds) for crafts that inherit
  material; draft in material_subtypes_cave.s.
  Superseded 2026-11-09 by mods/one_kind_inputs (see the section at the end); the draft's feasibility
  rule would bring back the floor-item stall that whole_batch_inputs dropped, so it stays unused.
Test (user's save copy, one autosave interval): Cave Farm entry 17 (CLS_ASH_BONE, 2 bones,
remove_input_modifier 1) held 1 bone_sturdy + 1 bone_restless since the morning saves; with C
the hold cleared (crafted). Constructions before the first autosave: 5 scaffolds + 1 bridge,
vs 2-4 scaffolds (+0-1 bridge) in earlier runs without C. D not tested in game.

## one_kind_inputs (2026-11-09)
- Seen in the user's colony on a copy of savegame32 (vanilla rules plus the shipping mods, speed 3,
  about 50 game minutes): Whitesmith 4273 entry 117 (Rough Cut, 3 CLS_GEM_RAW) took a ruby on top of
  its 2 sapphires while Whitesmith 4721 entry 160 held the colony's other ruby, so all four gems were
  locked; Arcane Workshop 2354 entry 58 (Runic Bone, 2 CLS_BONE) held 1 restless + 1 sturdy from
  savegame30 on, and took a second sturdy during the test (2 + 1 then).
- lock (0x180153122, `cmp rax, rdx; jb 0x180153159` -> jmp): when 0 < n < count and the slot keeps
  its material (remove_input_modifier 0), go to the match path (0x180153127), so the item must
  match_modifiers the largest group's first entity. Building recipes still skip it there (+0x971).
  No availability counting, on purpose: floor items are not in the inventory counts (production_stall.md).
- release (0x180152f84, `mov rax,[rbx+8]; mov rbx,rax` -> call): in production_system_update's
  queue walk, for strict slots of non-deliver, non-building entries, compare the global inventory
  entries ([[gamestate+0x11a0]+0x70][e]) of the slot's claimed items; two kinds -> check_correct_input
  (data, producer, entry). The re-offer goes through lock, so the entry comes back with one kind.
- Test, same copy, the same 50 game minutes with the mod: mixed slots 3 -> 1 (the left one is chunk_granite
  next to a crafted granite chunk, which share an inventory entry, so it isn't a mix); entry 58 held
  2 restless, entry 117 2 sapphires and then a newly mined third (ready), no ruby taken, rubies free.
  A diagnostic build (HMOD_OKI_DIAG=1, count at .hmod+0x2360) counted 1 release (entry 58) in about
  7 minutes, so released entries don't churn. Game speed over the same 3-minute window: 4.91x with
  and 4.91x without. No exceptions. 1 run each.
- Not tested: an entry locked on a kind the colony can never complete waits (as a full slot of a
  batch did before); cancel or pause it to free the items.
