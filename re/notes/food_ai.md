# Food AI (refill_statusbar_sensor), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `.text` file offset = VA - 0x180001000 + 0x400.
PDB `0001:N` = VA 0x180001000 + N; `tools/disasm.py` takes N in decimal.
Module symbol dumps: `re/pdb/mods/modNN.txt`; section contributions: `re/pdb/section_contribs.txt`
(maps any .text offset to its module, so static functions can be named).

## Data structures (from PDB types)
- `sensor_data_refill_statusbar` (760 B): `_needers`@73, `_filler_entities`@89 (array of
  `filler_entity{u16 ent; u32 sb_mask}`), `_modifier_type_entities`@137 (per statusbar type, array of
  `global_inventory_entry*`, only used for UI/`sensor_refill_has_entities_for_modifier`).
- `refill_needer` {needer_ent, faction, sb_mask, urgency, strong_independent_needer, haulers[]}.
- `hauler_data` {hauler_ent, movement_query_id, good_fillers[]}.
- `wanted_filler` (332 B) {filler_ent, score, path_lengths[] of {query_id, graph_position pos @8, cost @32}}.
- `global_inventory_entry` (10072 B): _hash, _claimed_count, _unclaimed_count, ... (GITC enum:
  UNCLAIMED 0, SELL 1, HAUL 2, TRADE 3, DEFAULT 4).

## Candidate set
`on_create_components` (0x1802c4040) queues entities whose components 0x29c / 0x60ed are created.
`process_modifier_entities` (0x1802c5390) keeps every entity whose modifier gives a positive value to
some statusbar (modifier_system_get_by_hash) and appends `{ent, mask}` to `_filler_entities`.
No location test: items on the floor, in storage, carried, all are candidates.

## Filters, desire_filler_cache::process_fillers (0x1802d43f0, 10245 B)
Args: this, needer_ent, fillers, haulers, positions(ctx->_game_positions), gamemap, out,
overworld_bits (tag CURRENTLY_IN_OVERWORLD), family_infos.
Phase 1, per filler (loop 0x1802d4e50):
1. Claimed (claim_system_get_claimed_entities_mask) -> claim_system_get_claim_type; keep only if
   claim tag hash == CLAIM_REFILL_STATUSBAR (tag 0x1805a4fe0, hash 0x1805a5018). Any other claim
   (CLAIM_PRODUCE, CLAIM_HAULING, CLAIM_SELL, CLAIM_TRADE, CLAIM_PERSONAL, ...) drops it.
   Site: 0x1802d4eaa `cmp [rcx+0x38],rax` / 0x1802d4eae `jne` (file 0x2d42ae, `0f 85 3b 01 00 00`).
2. Walk family parents to root. If root has CURRENTLY_IN_OVERWORLD keep; else map cell at the
   filler's game position must have bit 22 (`explored`, map.h) set.
3. get_filler_value (0x1802d0df0) <= 0 -> drop.
Phase 2: for needer + each hauler, reversed navgraph query; interaction_system_find_closest_
interact_position(root, worker,...). Interactee without interact_pos_comp falls back to its own
graph_position_system_position. Final pass (0x1802d6a28) drops fillers whose every path_length
has pos == 0 (unreachable for everyone).
Returns count; 0 -> update_next_needer (0x1802c9261) just clears hauler good_fillers. No fallback.

## Picking: calc_best_filler (0x1802bf8c0)
Fillers sorted best-first. Returns first that is unclaimed, or claimed CLAIM_REFILL_STATUSBAR with
claim ref == (worker<<32 | filler<<16 | needer) by this worker. Else -1. Stops at filler_ent 0.
refill_statusbar_job_begin (0x1802bf9c0) repeats the same test inline (0x1802bfb00/0x1802bfb04);
none valid -> BT_WAIT_AND_RETURN. Otherwise claim_system_add_claim(CLAIM_REFILL_STATUSBAR) and
BT_HAUL_TO_ENTITY (or BT_HAUL_TO_ENTITY_DELIVER if already in worker's inventory),
INTERACTION_PICKUP / INTERACTION_FEED.

## Floor items
- Dropped items: inventory_system_drop_items -> move_items(dst_ent 0, INVENTORY_TYPE_NONE), so no
  parent; root == item.
- Global inventory (global_inventory_system_refresh 0x1801ff940): every item gets a global entry,
  but only items with a parent are counted in _claimed_count[GITC] (claim tag -> HAUL 2 / SELL 1 /
  TRADE 3 / other 4 / unclaimed 0): `testw %di,%di; je` on the family parent at 0x1801fff05. So floor
  items are NOT in the global counts. Confirmed in game (production_stall.md, Nov 3).
- Haul: add_haulable_items (0x1801dac60): item with parent 0 accepted only if destination flag
  0x58 bit0 (HAUL_SOURCE_TAKE_FROM_GROUND) is set (0x1801dc378 `test byte [r14+0x58],1`). This is the
  per-storage UI toggle (property HAUL_SOURCE_GROUND_ENABLED, entity/ui/storage_settings.entity).
  Haul claims (CLAIM_HAULING) are only taken at pickup (node_haul claim_item_for_haul), so while a
  hauler is walking to floor food, refill ignores it.
- Default of the TAKE_FROM_GROUND bit not determined (copied from a temp struct in add_dest_entity
  0x1801deee3).

## Claim registration
mainstate::mainstate (0x1802960fc..) builds the claim-type table (CLAIM_DESIRE, HAULING, INTERACT,
PERSONAL, PRODUCE, REFILL_STATUSBAR, SELL, TRADE, DWELLING, ABOUT_TO_DESTROY) with one flag byte each
(only CLAIM_TRADE has 1). Code, not data.

## Patch candidates
- process_fillers 0x1802d4eae jne -> 6x nop (`90 90 90 90 90 90`) at file 0x2d42ae: claimed-by-anything
  items become candidates (still need valid claim type read).
- calc_best_filler and job_begin also reject them; they need the same change, but there the reject
  path also covers "claimed by another dwarf's refill", so a plain nop lets two dwarves target one
  item. A type-aware check (accept CLAIM_PRODUCE only) needs a code cave.
- Behaviour of claim_system_add_claim on an item already claimed CLAIM_PRODUCE, and of production
  when its claimed input is eaten, not checked.

## eat_reserved_food test (2026-11-01)
Mod `mods/eat_reserved_food` (code cave, three call sites above) loads and runs without crashing,
but the case it handles never came up in the user's colony:
- The cook house's CLAIM_PRODUCE claims (28 items) were the same set for the whole day, and all
  28 sat in the cook house's own inventory: one count-prefixed u16 list in
  `inventory_system/data.bin` (37 food items, the rest unclaimed meals). Building inventories are
  256-byte slots around 2.5 MB into that file; the 313-item list at ~4.6 MB is `chest_start`.
  The patch leaves claimed items in the claimant's own inventory alone (they may be mid-craft).
- Raising six queue entries from 5 to 60 added no claims, so a queue reserves inputs for the
  job in hand, not for its whole length. Starvation from "big queues" is most likely food that
  queues have hauled into the building, not food reserved in storage.
- The cook house did not cook all day (Crab Broth stayed at 3); "Algae Pancakes", the top queue
  entry, was listed under Impossible Orders. Whether an impossible top entry blocks the queue and
  keeps its inputs claimed is not checked.
- Claims added to a save by hand (claims.bin: u64 n, 13-byte records, u64 n, u64 8n, then one
  claim-type wc_hash per record: CLAIM_PERSONAL 0x193aa8418515d88d, CLAIM_HAULING
  0x3d140b6bd3b09239, CLAIM_PRODUCE 0xe1f3d9238adef41e, CLAIM_SELL 0xb4ed75bdac9d3582; the record's
  type byte is an index, not the type) are dropped within minutes when no queue owns them.

## Stranded dwarf with a home (2026-11-12, SouthXanforge savegame73, `_test_drop_log` replay)
- `sleep_action_begin_func` 0x1803bcab0: `dwelling_system_get_dwelling` (0x180239710) non-zero -> BT_SLEEP_IN_ROOM with the dwelling
  written to the blackboard (0x1803bcb1f), else BT_SLEEP_ON_FLOOR (0x1803bcb2d). No path check. [V]
- Sleep score clamp((0.75-e)/0.55)^2 (panic_spiral.md) beat the hunger desire at energy 22%, hunger 57%; with the home out of reach
  BT_SLEEP_IN_ROOM ends within 0.2 s, BT_IDLE runs 5 s, sleep is picked again. 43 sleep attempts, 16 eat attempts (all in the first
  minute) over about 5 game minutes. [V, 1 run]
- Candidate fix: in that function, take the floor branch when the dwarf can't reach the dwelling, e.g. when `stranded_rescue`'s
  per-entity stranded counter (.hmod data from 0x3000) is non-zero. Not written.
- Open: her first BT_EAT targeted Lichen near (618, 350) (150 hunger, about 56 tiles) over Rime Beets 4 tiles away (300 hunger).
  Depth (z 3.5 vs 2.5), claims and reachability were ruled out (haulers took the beets once the shaft opened); not explained.
- Item depth: harvests and kills drop items at z 3.0-3.5; moving two beets to z 2.5 changed nothing.
