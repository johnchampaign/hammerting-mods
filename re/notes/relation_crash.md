# Relation crash (A3) and alliance-quest crash (A4), entity.x86_64.dll / game.x86_64.dll 1.2.39

entity.x86_64.dll: base 0x180000000, .text RVA 0x1000 raw 0x400 (file off = VA - 0x180001000 + 0x400),
sha256 c00be66f...a260. PDB dumps: re/pdb/entity/{publics,symbols}.txt, address table entity_syms.tsv.
game.x86_64.dll modules: 3 main.cpp (property lambdas), 31 talk_system, 45 overworld_map_system,
52 mainstate, 59 the_monolithic_patch_function, 243 node_overworld_faction, 263 node_haul.

## Data structures (entity DLL)
- relation_system = ecs->0x40. +0x30 relation store (object_store<relation,u16>, 0x50 per relation =
  two relation_single), +0x40 state machines (0x100 each, count u32 +0x48), +0x50 current time,
  +0x68 key_value system handle.
- relation_single (0x28): owner u16 @0, related u16 @2, state* @8, time @0x10, opinion_delta i32 @0x18,
  opinion_kv_hash @0x20. relation[0] belongs to the lower entity id, relation[1] to the higher.
- state machine (internal, packed): type tag @0 (hash @0x38), auto_state tag @0x40 (hash @0x78),
  auto_opinion i32 @0x80, bilateral @0x84, states {ptr @0x85, count u32 @0x8d}, members {ptr @0x95,
  count @0x9d, 0x12 each}, member bitset @0xa5, lookup {ptr @0xb5, count @0xbd; 6-byte
  {u16 a, u16 b, u16 relation_idx}, sorted, both orders inserted}, opinion_fn @0xc8, user @0xd0,
  tick_opinion_state @0xd8, tick_time @0xe0, next_tick @0xe8, rnd_min/max @0xf0..
- relation_state (0x50): tag @0 (hash @0x38), u32 @0x40, opinion_min @0x44, opinion_max @0x48.
- Opinion is a KV on the owner: key "%s_%hu" (type name, other entity id), e.g.
  "RELATION_FACTION_OPINION_123", hash = wc_hash. Written as PCT_I64 count 1 (0x10004). Set only when
  sm.opinion_fn != NULL, initialised to auto_opinion if absent (set_relation_explicit 0x18008984b..).
- State machines (mainstate ctor 0x18029ef1b..0x18029f331):
  - RELATION_DWARF: SPITEFUL, COLD, NEUTRAL, FRIENDS, LOVING (each 0..1000), auto NEUTRAL 500,
    opinion_fn 0x1802ac6c0, no tick.
  - RELATION_FACTION: WAR, TRUCE, PEACE, ALLIANCE (min = max = 0), auto PEACE, bilateral, no opinion
    KV, no tick.
  - RELATION_FACTION_OPINION: HOSTILE, UNFRIENDLY, NEUTRAL, RESPECTFUL, ESTEEMED (0..1000), auto
    NEUTRAL 500, opinion_fn 0x1802ac670, tick on (rnd -30..20).
- Membership: add_comp (0x180085d30) sets the bitset, appends the member and calls
  set_relation_explicit(auto_state) against every existing member, so pairs exist only between
  members of the same type. Factions and the mountainhome get FACTION + FACTION_OPINION together
  (faction_system NEW_GAME 0x1801595fc.., initialize_scenario 0x1802b370e..). The monolithic patch
  adds them for old saves (0x1802e2608, 0x1802e288e, 0x1802e28aa).
- remove_destroyed_entities (0x18007f770) -> clear_relations_between (0x180086390): removes relations
  and opinion KVs for every type where both are members, then drops membership.
- set_relation_explicit (0x180089600): unknown state tag gives state = NULL (no check). A new pair is
  created through object_store::generate (0x18008971c), which can reallocate the relation store and
  invalidate every relation_single* held by callers. Fires WC_EVENT_RELATION_NEW_STATE synchronously
  (event dispatch calls listeners and eval chains directly).

## relation_component_system_change_relation (0x18007ea40, 0x46e bytes)
(ecs, one, two, wc_tag type by pointer in r9, i64 value). No validity checks at all.
1. r = get_relation(system, type, one, two) (0x180087740). Picks sr1 (owner one) and sr2.
2. v = KV(sr1.owner, sr1.opinion_kv_hash), inlined get_i64.
3. Find the state index of sr1.state in the matching sm. eval = v + value. If eval > state.max, step
   to the next state (set_relation_explicit, then get_relation again). If eval < state.min, step down.
   Clamp at the ends.
4. KV(sr1.owner, hash) = eval (0x18007ee80). Only one's side is written.

Fault sites (all reported as change_relation, because the PDB symbolises the crash):
| VA | instruction | condition | fault address |
|---|---|---|---|
| 0x18007eac0 | mov r8,[rbx+0x20] | no relation of this type between one/two: pair missing, one == two, a destroyed or 0xFFFF entity, a non-member | 0x20 |
| 0x18007eba9 | mov rcx,[rcx] | owner opinion KV missing or not single i64 (type with no opinion_fn, e.g. RELATION_FACTION) | 0x0 |
| 0x18007eb3e | mov r9,[rax+0x38] | sr1.state == NULL | 0x38 |
| 0x18007ebb7 | movsxd rcx,[rax+0x48] | state NULL and no matching sm | 0x48 |
| 0x18007ebd0 | mov eax,[r8+0x8d] | current state not in the sm (r8 = 0) and eval > max | 0x8d |
| 0x18007ecc4 / 0x18007ecff / 0x18007ee07 / 0x18007ee44 | mov rax,[rbx+8] | relation gone after a state step (a synchronous listener removed it) | 0x8 |

An unknown type faults in relation_system::get_relation (0x180087778), not in change_relation. There
are no fixed-size arrays on the entity side, so overflow is ruled out.

## Callers
Function pointer 0x1805997e0 (game) plus two direct calls in the entity DLL.
- entity relation_component_system_update (0x18007ff00): every tick_time, for every
  RELATION_FACTION_OPINION pair it calls change_relation(a,b) and change_relation(b,a)
  (0x1800803e2, 0x180080447). These pairs come from the lookup, so the relation exists. Remaining
  faults: missing KV or NULL state. After a load this runs on its own timer, which fits "recurs after
  every reload".
- talk_system_resolve_conversation (0x1801b2ed9), RELATION_DWARF (tag 0x18059d830): it first reads
  get_relation(a,b)->opinion_delta without a NULL check (that would crash in the game DLL, not here),
  then calls change_relation(owner, related, random value scaled by opinion_delta). Perks that change
  opinion_delta (via calc_dwarf_opinion) change the size and sign of the value only. A crash here
  needs a missing KV or NULL state.
- join_alliance / leave_alliance, inlined in register_property_overworld_system lambda_43
  (0x1800b76b0): calls at 0x1800b9131 (leave, -2100), 0x1800bbd04 and 0x1800bbd65 (-1500 each),
  0x1800bce05 (+300/550). Type RELATION_FACTION_OPINION (0x180597560). Source in
  re/extract/tdtd/gamestate/public/gamestate/overworld_util.h:115-277.
- Trade/sale (item_util.h:213-272): default_production_complete_cbck 0x1802da05f, buy_items_execute
  (5 calls), bt_haul_update (5). diplomatic_action_execute 0x1802f078b (±200).
  bt_overworld_faction_update (10). Overworld new game 0x18023d63f/69b. All use
  RELATION_FACTION_OPINION. RELATION_DWARF is used only by talk.
- No eval-chain property calls change_relation. SET_RELATION and RELATION exist
  (entity_property.h:2148, 1477) but no database or .entity record uses SET_RELATION.

## Alliance quest (database/smart_event/overworld_mission_records_cdb.bin)
- MISSION_OVERWORLD_ALLIANCE_TRIGGER (0x537b10): MISSION_GEN_OW_RELATE('RELATION_FACTION_OPINION',
  'IS', 'RELATION_FACTION_OPINION_ESTEEMED', 'FACTION_OVERWORLD', 'FACTION_DWARF'). It fires on
  WC_EVENT_RELATION_NEW_STATE; trigger chain at 0x5890c0.
- MISSION_OVERWORLD_ALLIANCE (0x4e4360): deliver 10 CLS_LICORICE_DWARVEN to MISSION_PARENT (the
  faction capital). Fails when opinion is OTHER_THAN ESTEEMED, or when the location's controller is
  OTHER_THAN MISSION_SOURCE_FACTION. This is the only alliance quest, so "Dwarven Licorice / Elves" is
  this quest with an elf faction.
- Completion "force_alliance" (string at 0x535910, buffer 0x2000 bytes):
  `MOUNTAINHOME.JOIN_ALLIANCE(STATE_GET('MISSION_PARENT').FACTION_ENTITY)`
- JOIN_ALLIANCE (overworld_system.h:872) calls join_alliance(F = faction, MH):
  1. get_relation(FACTION, F, MH)->state (game DLL, unchecked).
  2. leave_alliance(F): for each ally A, set PEACE and change_relation(A, F, -2100).
  3. joiner_rels = F's FACTION relations (pointers into the relation store). Then set ALLIANCE for
     MH's allies with F, and for F with MH.
  4. For each X in joiner_rels that is not an ally: change_relation(X, F, -1500) and
     change_relation(X, MH, -1500). Then for each Y in X's relations (not F, not MH):
     get_relation(FACTION, F, Y)->state (unchecked), then change_relation(X, Y, +300/550).
  The opinion pairs are taken from a different type's relation list (FACTION) and are never checked.
  The relation_single pointers stay alive across set_relation calls and synchronous event listeners.

## Causes, ranked
1. (Code verified; trigger inferred) change_relation is passed a pair with no RELATION_FACTION_OPINION
   relation, faulting at 0x18007eac0 (read 0x20). The most likely source is join_alliance step 4,
   (X,MH) or (X,Y), or a stale X read through a dangling joiner_rels pointer. This happens if the
   FACTION and FACTION_OPINION membership sets differ (old-save patch path, destroyed or recycled
   faction ids), or if a listener created a new pair and reallocated the store. It fits A4: the
   failure is deterministic for one faction set, and re-rolling the quest changes the state.
2. (Code verified; trigger inferred) A FACTION_OPINION or DWARF relation exists but the owner's opinion
   KV is missing, faulting at 0x18007eba9 (read 0x0). The background tick hits every OPINION pair
   after each load, which fits A3's "every reload". Talk hits dwarf pairs, which fits the perk
   observation, since perks only make the talk path run with larger and more negative values.
3. (Code verified; no data path found) NULL or foreign state pointer, faulting at 0x18007eb3e or
   0x18007ebd0. This only happens through a corrupted save or a bad state tag; SET_RELATION is unused.
4. (Unlikely) The relation is removed during a state step, faulting at the [rbx+8] sites.

## Patch candidates
- Code: entity.x86_64.dll change_relation.
  - (a) At the first get_relation result (je at 0x18007ea8a), send NULL to the function epilogue
    (0x18007ee85; rsp is balanced after the prologue). The short je cannot reach that far, so the
    0x20-byte selection block at 0x18007ea87 has to be rewritten. That fits in place (the cmova/jmp
    pair can be expressed more compactly).
  - (b) Make the inlined get_i64 (0x18007eb74..0x18007eba9) fall back to the value field of the
    zeroed property_comp at [rsp+0x48] instead of dereferencing NULL. This fits in place: the
    count > 1 branch is never used for opinion KVs. The closing set_value then repairs the KV.
  - (c) NULL-state check and re-fetch checks after state steps: these need a code cave. .text vsize
    is 0xca2d8 against raw size 0xca400, so 0x128 bytes of file slack sit at the end of .text, plus
    int3 padding between functions.
  - Tooling: dllpatch.py only handles game.x86_64.dll. An entity patch needs its own pristine backup
    plus sha256 check, and the file-offset formula above.
- Code alternative: in game lambda_43, check each get_relation result before the change_relation calls
  (needs a cave in game.x86_64.dll; the existing .hmod section could host it).
- Data (A4 workaround only, cause 1): replace the completion expression with
  `SET_RELATION('RELATION_FACTION', 'RELATION_FACTION_ALLIANCE', MOUNTAINHOME, STATE_GET('MISSION_PARENT').FACTION_ENTITY)`
  using ctx.replace_cstr. This sets the bilateral alliance state that the victory check reads
  (RELATION(...).STATE.TAG == ALLIANCE) without the opinion loops. It skips leave_alliance and the
  KV_ALLIANCE_HASH / ALLIANCE_A..E bookkeeping, so the AI's alliance logic may misbehave. Untested.

## Save evidence (tools/save.py; not opened here)
- The crash report's exception address separates the causes: entity+0x7eac0 = missing pair,
  +0x7eba9 = missing KV, +0x7eb3e / +0x7ebd0 = bad state.
- relation_system/data.bin, per type (format from push_to_system 0x180088ac0): type tag, member list
  (u16), relations {u16 e1, u16 e2, u16 state_idx1, u16 state_idx2, u64 time1, u64 time2}, state-tag
  table. Check that the RELATION_FACTION and RELATION_FACTION_OPINION member sets are equal. Check
  that every faction pair, including MH, has an OPINION relation, especially X–MH for factions related
  to the quest faction. Check that state indexes are within the tag table and that every member entity
  is alive.
- key_value_system/data.bin: for each OPINION or DWARF relation (e1,e2), e1 must hold
  wc_hash("RELATION_FACTION_OPINION_<e2>") (or "RELATION_DWARF_<e2>") as 0x10004, and the reverse.
  A missing entry confirms cause 2.
- The quest instance's MISSION_PARENT and FACTION_ENTITY show the F passed to join_alliance.

## Fix: mods/relation_crash_guard (2026-11-01)
Two in-place patches in entity.x86_64.dll (tools/dllpatch.py DLLS['entity']):
- 0x18007ea87 (32 bytes): `je` on a NULL relation now goes to the epilogue 0x18007ee85
  (`0f 84 f5 03 00 00`); the old `xor ebx,ebx; xor edi,edi` path is gone.
- 0x18007eb74..0x18007eba9 (53 bytes, the 9-byte loop exit at 0x18007eb9e kept): rcx defaults to
  &value ([rsp+0x48], zeroed before the lookup); only an i64 with count > 1 uses the stored
  pointer. A missing or odd opinion KV now reads 0 and is rewritten by the closing set_value.
Not reproduced. Regression test on the user's save (patched, 3 autosave intervals): 150-156 of
156 faction opinions changed per interval (unpatched: 154-156), dwarf relationship 2316/2320
changed both ways in the third interval (unpatched: 0-8 per interval). Save check: all 186
opinion KVs (156 faction, 30 dwarf) have their reverse, so this save is not at risk.
key_value_system/key_value.bin: entities[u16], keys per entity[u64], key hashes[u64],
values[{u64 type, u64 value}], each array as u64 count, u64 bytes, data; keys follow entities
in order. Opinion keys are wc_hash("RELATION_FACTION_OPINION_<id>") / ("RELATION_DWARF_<id>").
Not covered: NULL or out-of-list relation state (0x18007eb3e, 0x18007ebd0) and a relation
removed during a state step (0x18007ecc4..0x18007ee44); no data path to them was found.
