# Tool auto-upgrade and the Outdated Equipment alert (BUGS.md B12), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 20 inventory_system, 21 job_broker, 28 name, 29 dna, 35 toolbelt_system,
36 claim_system, 39 utility_system, 40 global_inventory_system, 43 alert_system,
99 command_toolbelt_actions, 137, 139 interaction_system, 145, 162 action_equip, 179 sensor_equip,
194 order_equip. Bytes are from the pristine DLL (`game.x86_64.dll.hmod-orig`); no site below is
touched by the installed mods. Function-pointer globals (`call *0x1805995a0` and so on) were
named from the `*_ptr` publics in `re/pdb/game_publics.txt` (section 3 = .data, VA 0x180591000+N).
Draft caves: `re/notes/tool_upgrade_cave.s`. Nothing here was tested in game, except the section
"mods/equip_missing_tools" at the end.

## The alert (database/alert/alert.bin)
- 18 records of 0xc80 bytes from file offset 0x10: tag char[0x40], category tag char[0x40],
  condition char[0x400] at +0x80, click action char[0x400] at +0x480. Record 5 is
  ALERT_OUTDATED_EQUIPMENT, category ALERT_HINT; its condition starts at file offset 0x3f10
  (161 chars, room for 1023):
  `IFTHENELSE(NOT('RESEARCH_SMITHING'.HASH.RESEARCH_STATUS.EQUALS( 'ACQUIRED' )), FALSE,
  TAGGED_ENTITIES('PLAYER_CHARACTER').FILTER("TOOLBELT.OLD_EQUIPMENT"), TRUE)`.
  Click action: `CAMERA_MOVE_TO_POSITION(DATA.GET_AT(NEXT_CLICK_INDEX).POS)`. It has no outliner
  option key (only ALERT_UNMANAGED_PROFESSIONS has one).
- IFTHENELSE (handler 0x18006b9d0, registered in main_main_register_property_main) reads three
  args: args[0].bool ? args[1] : args[2]. The fourth `TRUE` is ignored.
- eval_alert 0x180237720 evaluates the compiled chain at record +0x1020 of the runtime copy;
  alert_system_update 0x180237970 shows the alert when the result is a TRUE bool (type 9) or a
  list with count > 0 (`cmpw $0, 0xa(%r12)`). So: active while Smithing is researched and at
  least one PLAYER_CHARACTER passes the filter. The listed dwarves are the click targets.
- TOOLBELT (property/toolbelt.h lambda_2, 0x1800ad8e0) returns all num_slots entities of the
  dwarf's toolbelt, empty slots as 0. OLD_EQUIPMENT (lambda_3, thunk 0x180071b10, body
  0x1800b64e0) is TRUE if any non-zero entity has `gies[e]->_is_type[GITT_NOOB_TOOL]`
  (global_inventory_entry +0x2b8a, test at 0x1800b6552).
- GITT_NOOB_TOOL: add_entry (global_inventory_system, 0x180205d60) sets `_is_type[t]` for the 5
  tracked types (loop 0x180206f50..0x180207023, store 0x18020700f) by classifying the item
  against a static table of up to 2 tags per type (.data 0x1805a1010, stride 0x80; names in
  .rdata 0x180547a40..: CLS_FLUID_WATER, CLS_FLUID_LAVA, CLS_TOOL, CLS_NOOB_TOOL, CLS_EQUIPMENT;
  the ITEM row was not read). So NOOB_TOOL = "item is classified CLS_NOOB_TOOL".
- CLS_NOOB_TOOL items (database/modifier/modifier/equipment_modifiers_cdb.bin, 64 records of
  0xdc90 from 0x10; parents and PROF_*_PRODUCTION entries):

  | class (record) | entity files | professions | crafted equivalent |
  |---|---|---|---|
  | CLS_LANTERN_GRANDMOTHER (1) | lantern_grandmother | EXPLORER | CLS_LANTERN_EXPLORER, CLS_LANTERN |
  | CLS_PICKAXE_GRANDFATHER (5) | start_pickaxe, pickaxe_grandfather_iron/_gold | MINER, STONEMASON | CLS_PICKAXE_MINER (same two) |
  | CLS_AXE_GRANDFATHER (10) | start_axe | MILITIA | CLS_AXE_WOODSMAN, swords, spear |
  | CLS_HAMMER_GRANDFATHER (26) | start_hammer | BLACKSMITH, BUILDER, METALLURGIST | CLS_HAMMER_BLACKSMITH (same three) |
  | CLS_LADLE_GRANDFATHER (37) | ladle_grandfather | COOK | CLS_LADLE_COOK, CLS_AXE_BUTCHER |

  Every noob tool has a craftable tool with the same professions, so the alert is satisfiable
  in principle.
- Decoded: "some dwarf has a Grandfather/Grandmother tool in any toolbelt slot". It does not ask
  whether the tool is used (the best tool for a job), whether a better tool exists, whether it is
  reachable or claimed, or whether the dwarf may do that profession. Localization
  (dubious_entries.loc): "Some of your dwarves are still using the worn and outdated
  Grandfathers' tools ..." with the advice to craft tools and equip them by hand.

## Toolbelt state (toolbelt_system, module 35)
- Component 0x410 bytes (array at system+0x2f0, count +0x2f8): +0 u16 dwarf, +4 u32 num_slots,
  +8 u64 current slot (-1 none), +0x10 u16 tools[6], +0x1c 6 x 16-byte cache, +0x7c
  toolbelt_auto_upgrade_setting[6] of 0x43 bytes: +0 _enabled, +1 _is_compatible_with_current_tool,
  +2 _upgrade_to_recommended, +3 _allowed_professions[64] (index = profession record index,
  database_get_record_index; record order in professions_cdb.bin: 0 ARCANIST, 1 BLACKSMITH,
  2 BUILDER, 3 COOK, 4 EXPLORER, 5 FARMER, 6 HEALER, 7 METALLURGIST, 8 MILITIA, 9 MINER,
  10 STONEMASON, 11 TAILOR, 12 WHITESMITH, 13 HAULER, 14 TRADER, assuming load order = file order).
- New components (toolbelt_system::add_component 0x1801ceac0, 0x1801ceb33..0x1801ceb3c): every
  slot enabled = compatible = recommended = 1, allowed all 0.
- UI button `toolbelt_autoupgrade` (command 0x180303a60) cycles recommended -> custom
  (recommended = 0) -> off (enabled = 0) -> recommended. `toolbelt_autoupgrade_set_profession_allowed`
  (0x180303b90) finds the slot by tool entity and sets one allowed byte. Neither calls
  refresh_autoupgrade (set_autoupgrade_setting 0x1801c6560 has no calls).
- _is_compatible_with_current_tool is not read by the upgrade code below.

### refresh_autoupgrade (toolbelt_system::refresh_autoupgrade 0x1801d06d0)
Called from add_tool_to_toolbelt (0x1801c5ff8), inventory_moved_cb (0x1801c70f3) and
autoupgrade_key_value_change_cbck (0x1801c7290, KV changes such as PROF_*_ALLOWED).
1. Only slots with a tool, enabled (+0x7c) and recommended (+0x7e) (0x1801d07c0..0x1801d07db);
   their allowed bytes are zeroed (0x1801d07ec). Empty slots are skipped: their allowed bytes
   stay as they were.
2. For each such slot and each profession: skip if the dwarf has KV `PROF_X_ALLOWED` (record
   +0xb8 hash) with u64 0 (0x1801d0870); keep it if the tool's PROF_X_PRODUCTION (record +0x420,
   _modifier_production hash) is > 0 (0x1801d08f0). tool_to_upgrade (0x78 B): slot, tool, count,
   prof[8], value[8]. prof_to_upgrade (0x40 B, one per profession): prof, the DWARF's
   _modifier_level value (record +0x360, 0x1801d09b3), favorite (KV PROF_X_FAVORITE, 0x1801d09db).
3. Professions are sorted (favorite first, then level), qsort 0x1801cb960.
4. Assignment (0x1801d1280..0x1801d134a): for each profession, scan the tool entries that offer it:
   `cmp 0x8(%rdi),%eax; jge` at 0x1801d12bb compares the running best TOOL value eax with the
   dwarf's LEVEL in that profession, then takes the entry's value. So the pick is the first slot
   offering the profession, replaced by a later one only while the running value is below the
   level: slot order, not tool quality (bug; intended compare is with the entry's value). A
   profession with level 0 is never assigned. The chosen slot gets allowed[p] = 1 and its entry
   is removed (swap 0x1801d134a): **each slot gets at most one profession**; the rest stay
   unassigned, and a slot whose professions all went elsewhere gets none.

### Auto-upgrade: sensor_equip_try_equip_upgrade 0x1803ef3a0
Runs every 15 s (sensor_equip_update 0x1803f14b9: timer +0x60, `add $0xf0000`) over all dwarves.
- Candidates (sensor+0x20, built in sensor_equip_load_post 0x1803f2600 and when items appear) are
  global inventory entries of tool kinds; one is skipped unless `gie->_claimed_count[UNCLAIMED]`
  (+8) > 0 (0x1803efcdc). Per candidate, its kind's PROF_X_PRODUCTION values (sensor+0x30/+0x40).
  Noob tools are candidates like any other tool.
- A dwarf with its busy byte set (sensor+0x50, one byte per entity) is skipped (0x1803efc16).
- Current values: modifier_system_get_by_hash over the belt's tools (empty = 0) for every
  profession's production hash (0x1803efc84).
- For each candidate c and each slot s whose setting is enabled (0x1803efd23), over the
  professions p allowed in s (0x1803efd54..0x1803efe69):
  gain = max(0, min(c_p - s_p, min over other slots o with o_p != 0 of c_p - o_p)),
  loss = max(0, min(s_p - c_p, min over o of s_p - o_p)); score = sum(gain - loss).
  The best (slot, candidate) with score > 0 wins, strictly greater (0x1803efe80), so ties go to
  the lower slot index. An empty slot (s_p = 0) has no loss: it is filled whenever its allowed
  set contains a profession the candidate is the best at.
- Item: modifier_system_for_entities_with_total_modifier_hash over the kind with filter
  total_modifier_is_valid 0x1803ec290 (drops every claimed item: market stock, production
  reservations, other belts, pending equips), then sensor_util::find_approx_closest_entity
  0x1803eff7c (dwarf's movement navgraph query, so roughly reachable only). Overworld markets
  never appear (their stock is claimed).
- Arbitration (0x1803f0510): entries {dwarf, item, value, slot}; for an item wanted by several
  dwarves the highest value wins, the others drop that item. Winner: ACTION_EQUIP instance
  (utility_system_add_action_instance 0x1803f058e), equip def {dwarf, item, slot, auto} pushed
  to sensor+8, claim CLAIM_PERSONAL (global 0x1805a4508 = hash of "CLAIM_PERSONAL") with
  equip_claim_ref = item<<16 | dwarf | auto_equip<<32 | INVENTORY_TYPE_TOOLBELT(2)<<40 |
  slot<<48 (0x1803f0811), busy byte = 1 (0x1803f0829). One upgrade per dwarf per pass.
- ACTION_EQUIP is rank 7 (panic_spiral.md); considerations distance 0x1803b0f70, not-claimed
  0x1803b0fd0 (0 if someone else claims it), is-ordered 0x1803b1090 (1.0 order, 0.5 auto).

### Completion
- equip_action_end 0x1803b0da0: UT_SUCCEEDED releases the equip claim, fires
  TDTD_EVENT_EQUIP_ITEM, calls on_done; UT_REMOVED calls on_done (releases only if action +0x22);
  UT_FAILED calls on_done without releasing; REPLACED/ABORTED do neither.
- sensor_equip_on_action_done 0x1803ee0c0: removes the def first, then UT_REMOVED returns,
  UT_SUCCEEDED (auto) clears the busy byte (0x1803ef334), toolbelt_system_add_tool_to_toolbelt
  (0x1803ef34d) and set_current_tool (0x1803ef361); every other reason only removes the action
  instance (0x1803ef366). **On UT_FAILED the busy byte and the auto-equip claim stay**: the dwarf
  never auto-upgrades again this session and the tool stays reserved for him (BUGS 5,
  "reserved tools can't be found"). sensor_equip_update re-checks only defs still listed
  (0x1803f1c50..0x1803f1de9). On load, sensor_equip_load_post (0x1803f26d0..0x1803f2703) releases
  auto-equip claims whose item is not parented to the claimer, so a reload clears it.
- toolbelt_system_add_tool_to_toolbelt 0x1801c4dc0 (dwarf, tool, slot): un-wields the current tool
  back to the belt, releases the old tool's claim (0x1801c5082), writes the slot (0x1801c508d),
  claims the new tool (0x1801c510b), moves the old tool to the backpack, dropping backpack items
  ("%hu needs to drop %lu items") if it is full, then refresh_autoupgrade. The old tool ends up
  unclaimed in the backpack: a candidate for anyone (including this dwarf's other slots). There
  is no check for another tool of the same kind or professions on the belt.
- A tool leaving a dwarf (drop command 0x180303770 moves it to the ground; hauls; transfers):
  toolbelt inventory_moved_cb 0x1801c6fd0 -> remove_tool_from_component 0x1801d2200 clears the
  slot entity and cache, releases the toolbelt claim, **keeps the slot's setting**, then
  refresh_autoupgrade, which skips the now-empty slot. The empty slot keeps the allowed
  professions of the tool that left.
- Nothing ever removes a redundant tool from a belt.

## Causes, ranked
1. **Redundant noob tools are never removed (code).** The alert checks every slot. A
   Grandfather tool stays forever when its slot has no allowed profession (all assigned to other
   slots, at most one per slot, by slot order; or the dwarf's PROF_X_ALLOWED is 0, e.g. a non-cook
   with the ladle), or when its professions are covered by a better tool elsewhere on the belt
   (then only a tool better than that one can replace it). The dwarf does not use it
   (toolbelt_system_get_best_tool_for_job picks the better tool), but the alert stays.
2. **Duplicates from stale empty slots (code).** After a tool leaves a slot (cause list above),
   the empty slot keeps its professions and try_upgrade refills it with the best candidate, and
   with equal scores the lower slot wins over the slot holding the old tool. The dwarf now has
   two tools of one kind; refresh then hands the professions to one of them, and the noob tool
   keeps none: cause 1 for good. Same path: dropping a tool (or having it replaced) and the dwarf
   picking the same tool back into the empty slot when it is the best at a stale profession
   (drop -> re-equip), as long as the dropped item still counts as unclaimed in the global
   inventory (backpack yes; a tool dropped loose on the ground was not checked).
3. **No strictly better unclaimed tool (design).** score > 0 requires beating the slot's tool and
   every other belt tool on the slot's professions; tools in markets, reserved by production or a
   pending equip, on other belts, or unreachable never count. Crafted tools of poor material can
   be worse than the Grandfather tools.
4. **Failed auto-equip (code read).** UT_FAILED leaves the dwarf busy and the tool reserved until
   reload: no more upgrades for him; others cannot take the tool.
5. **Assignment by slot order (code).** The compare at 0x1801d12bb makes recommended professions go
   to the first slot that offers them, not the best tool, so upgrades for a profession are aimed
   at the wrong slot; a profession at level 0 is never upgraded.

## Patch candidates
Data (ctx.replace_cstr on database/alert/alert.bin, old = the 161-char condition above):
- D1 alert only for a noob tool the dwarf actually uses for a profession he may do (751 chars):
  `IFTHENELSE(NOT('RESEARCH_SMITHING'.HASH.RESEARCH_STATUS.EQUALS( 'ACQUIRED' )), FALSE,
  TAGGED_ENTITIES('PLAYER_CHARACTER').FILTER("OR(OR(OR(T(MINER),T(BUILDER)),OR(T(COOK),T(MILITIA))),T(EXPLORER))"), TRUE)`
  with T(X) = `AND(TOOL_BEST('PROF_X'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_X_ALLOWED',U64('1')).EQUALS('0')))`.
  Full string:
  ```
  IFTHENELSE(NOT('RESEARCH_SMITHING'.HASH.RESEARCH_STATUS.EQUALS( 'ACQUIRED' )), FALSE, TAGGED_ENTITIES('PLAYER_CHARACTER').FILTER("OR(OR(OR(AND(TOOL_BEST('PROF_MINER'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_MINER_ALLOWED',U64('1')).EQUALS('0'))),AND(TOOL_BEST('PROF_BUILDER'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_BUILDER_ALLOWED',U64('1')).EQUALS('0')))),OR(AND(TOOL_BEST('PROF_COOK'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_COOK_ALLOWED',U64('1')).EQUALS('0'))),AND(TOOL_BEST('PROF_MILITIA'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_MILITIA_ALLOWED',U64('1')).EQUALS('0'))))),AND(TOOL_BEST('PROF_EXPLORER'.HASH).OLD_EQUIPMENT,NOT(KEY_VALUE_OR_DEFAULT('PROF_EXPLORER_ALLOWED',U64('1')).EQUALS('0'))))"), TRUE)
  ```
  TOOL_BEST (toolbelt.h get_best_tool) looks the
  profession up by hash ('PROF_MINER' hash 0xe1f4c7a9a51923b7 matches record +0x38) and ASSERTs
  it exists, so a typo crashes in release: test it. MINER stands for the pickaxe, BUILDER for the
  hammer (all 8 professions do not fit: 1148 chars). Untested: OR/AND arity 2 is what the data
  uses; OLD_EQUIPMENT on a single entity reads count 1; entity 0 is skipped.
- D2 opt-out: condition `FALSE` (hides the alert).
Code (ctx.patch_dll; caves in .hmod at 0x18060c580..0x18060c5fd, assembled with tools/cave.py,
symbols in tool_upgrade_cave.s):
- C1 clear stale professions (causes 1, 2): 0x1801d22c0
  `48 8b c7 48 03 c0 44 89 7c c3 24 66 44 89 7c 7b 10` -> `e9 bb a2 43 00` + 12 x `90`, cave
  clear_slot at 0x18060c580: the original stores, then if the slot is in recommended mode zero
  its 64 allowed bytes, jmp 0x1801d22d1. Empty slots then behave like a fresh dwarf's (never
  auto-filled); custom-mode slots keep the player's choice. Side effect: a tool taken away is no
  longer auto-replaced in that slot.
- C2 failed equip (cause 4): 0x1803ee4a8 `0f 85 b8 0e 00 00` -> `0f 85 13 e1 21 00`, cave
  failed_equip at 0x18060c5c1: on UT_FAILED of an automatic equip (data +0x10 order == 0)
  clear sensor+0x50[dwarf] and claim_system_release_claim_if_claimed(mainstate+0x530, dwarf,
  item); then jmp 0x1803ef366 as before. Risk: a dwarf may retry an item that keeps failing every
  15 s at rank 7.
- C3 assign by tool value (cause 5): 0x1801d12bb `3b 47 08` -> `3b 01 90` (`cmp (%rcx),%eax`, rcx =
  &value[r8]): each profession goes to the slot with the best tool (ties: lowest slot). Does not
  lift the one-profession-per-slot rule.
- Not built: removing redundant tools automatically (would need inventory_system_move_items from
  a cave in refresh_autoupgrade).
Recommended: D1 + C1 + C2 (+ C3). For an existing colony, also drop the noob tools by hand: with
C1, or in vanilla after setting that slot's auto-upgrade to off (two clicks of the slot button),
the slot is not refilled.

## Save check (do not run on the live save folder without a backup)
- `toolbelt_system/toolbelt.bin` (save.py wrapper head u32 = version << 22, 0xc00000 = v3; then
  LZ4). Writer write_object 0x1801cc2f0: u64 n; per component, packed: u16 dwarf, u32 num_slots,
  u64 current slot, u64 6, u64 12, u16 tools[6]; if version >= 2: u64 6, then 6 x {u8 enabled,
  u8 compatible, u8 recommended, u64 64, u64 64, u8 allowed[64]}.
- `claim_system/claims.bin`: u64 n, 13-byte {u16 entity, u16 claimer, u64 ref, u8 type index},
  then u64 n, u64 8n, n claim-type hashes (CLAIM_PERSONAL 0x193aa8418515d88d). Toolbelt claim:
  ref bit 32 clear, (ref >> 40) & 0xff == 2, slot = (ref >> 48) & 0xff. Pending auto-equip: bit 32
  set (a reload releases it if the item is not on the claimer). Market stock: claimer ow_hex_*.
- `key_value_system/key_value.bin` (layout in relation_crash.md): per dwarf PROF_X_ALLOWED (u64,
  0 = no), PROF_X_FAVORITE, KV_HAS_TOOLS_FOR_FAVORITES. Key = wc_hash(name).
- Names: debug_name_system via tools/saveinspect.py Entities (e.g. `item/start_pickaxe[1234]`);
  noob kinds: start_pickaxe, start_hammer, start_axe, ladle_grandfather, lantern_grandmother,
  pickaxe_grandfather_*. Tool production values are modifier_system state (not decoded); judge by
  kind/material or the in-game tooltip.
```python
import struct, sys
sys.path.insert(0, 'tools')
from save import Save
from saveinspect import Entities
P = 'ARCANIST BLACKSMITH BUILDER COOK EXPLORER FARMER HEALER METALLURGIST MILITIA MINER STONEMASON TAILOR WHITESMITH HAULER TRADER'.split()
NOOB = ('start_pickaxe', 'start_hammer', 'start_axe', 'ladle_grandfather', 'lantern_grandmother', 'pickaxe_grandfather')
path = sys.argv[1]
s, E = Save(path), Entities(path)
head, d = s.unpack('toolbelt_system/toolbelt.bin')
o, ver = 8, head >> 22
belted = set()
for _ in range(struct.unpack_from('<Q', d, 0)[0]):
    ent, nslots, cur = struct.unpack_from('<HIQ', d, o); o += 14
    cnt = struct.unpack_from('<Q', d, o)[0]; o += 16
    tools = struct.unpack_from(f'<{cnt}H', d, o); o += 2 * cnt
    sets = []
    if ver >= 2:
        k = struct.unpack_from('<Q', d, o)[0]; o += 8
        for _ in range(k):
            en, cp, rec = d[o:o + 3]; c = struct.unpack_from('<Q', d, o + 3)[0]; o += 19
            sets.append((en, rec, [P[i] for i in range(min(c, len(P))) if d[o + i]])); o += c
    print(E.names[ent], 'slots', nslots, 'current', cur)
    for i in range(nslots):
        t = tools[i]; belted.add(t)
        en, rec, allowed = sets[i] if sets else (None, None, [])
        kind = E.kind(t) if t else '-'
        print(f'  {i}: {kind}{"  NOOB" if any(n in kind for n in NOOB) else ""}  '
              f'auto={"off" if not en else "recommended" if rec else "custom"} allowed={allowed}')
TOOLS = ('pickaxe', 'hammer', 'axe', 'ladle', 'lantern', 'chisel', 'needle', 'pen_', 'rake', 'sack', 'sword', 'spear')
for e in E.items():
    k = E.kind(e)
    if e not in belted and any(t in k for t in TOOLS):
        print('spare', e, k, E.where(e), E.claims.get(e))
```
(Snippet untested: check that n is the dwarf count and the names are dwarves before trusting it.)
Read: a NOOB slot with allowed [] or with a better tool of the same kind on the same belt is
cause 1; an empty recommended slot with a non-empty allowed list is a stale slot (cause 2); a
spare better tool with a claim by a dwarf that does not hold it is cause 4; spare tools that are
'market' or claimed by a building are cause 3.

## User's colony (2026-11-01, lastsave)
All 6 dwarves: 3 slots; slot 1 = item/start_axe (NOOB, MILITIA), slots 0/2 crafted tools
(STONEMASON/MINER + BLACKSMITH/METALLURGIST/COOK/BUILDER). Spares: lantern_grandmother, 3
start_pickaxe, 4 start_hammer (some loose). No crafted weapon exists; RESEARCH_BLADE_FORGING and
RESEARCH_SPEAR_MAKING are not acquired. The alert is correct for this colony. No mod shipped.

## mods/equip_missing_tools (2026-11-03)
Gap: a slot is scored only over its allowed professions, and refresh_autoupgrade gives a slot only professions
its current tool offers. So a tool for a profession no belt has scores <= 0 and is never taken (savegame13:
Cook's Ladle finished, cook house unable to cook, no belt changed). Every slot was full.

Patches, both in sensor_equip_try_equip_upgrade, code in `.hmod` 0x800-0xa80:
- 0x1803efe80 `cmp r9d, ebx; jle +0x42` -> score_slot adds 0x40000000 to the pair's score if the slot is in
  recommended mode, has MILITIA not allowed (index 8), every profession of its current tool is on another
  belt tool (on_belts >= 2), and the candidate offers a profession with on_belts == 0 that this dwarf is
  allowed and has a level in. It sets r14 to that profession, whose level is then the arbitration value.
- 0x1803efff3 `mov eax, [rsp+0x48]; mov [rbp-0x76], bx` -> unused_slot_first adds 0x10000000 to the arbitration value
  (entry +4; 0x1803f0510: highest wins per item) when the score was exactly the bonus: the slot's tool does nothing
  for its dwarf. The low byte of the stored score at rbp+0x9d0 is overwritten by the level call's flag, so it compares >> 8.
- on_belts sums gie +0x28 (`_claimed_count[4]`, "other" claims, which includes CLAIM_PERSONAL) over the sensor's tool kinds that
  offer the profession. A pending equip counts at once in the sense that no second dwarf took a tool in any run.

Not covered: the gate at 0x1803efcdc needs a stored or held unclaimed item (floor items are not counted), so a tool lying on
the floor is not a candidate [code read]. Tools come out of production buildings held, which is how these were taken. A second tool of
a covered profession still needs equipping by hand.

Tests, no input from me or the user beyond resuming play, 0 exceptions and 0 unlocks in each. g13 = copy of savegame13 with the smithy on High
hauling; g14 = copy of savegame14, where Kabbe already had a ladle. All but the first used `_test_quiet` for 30-second autosaves.
| Run | Version | What changed on belts |
|---|---|---|
| g13, 1 autosave | first | Kabbe: pickaxe -> ladle, axe -> lantern (left unarmed). Trondur: unused pickaxe -> needle |
| g13, 7 | + keep weapon | Kabbe: pickaxe -> ladle, hammer -> lantern. Trondur: unused pickaxe -> needle |
| g14, 5 | + keep weapon | Dwarf 2236: stonemason pickaxe -> needle, while Trondur and Högne had unused slots |
| g13, 6 | + unused slot first | Trondur: unused pickaxe -> needle. Högne: unused pickaxe -> lantern. Kabbe: hammer -> ladle (Cook). Spares untouched |
| g14, 5 | + unused slot first | Trondur: unused pickaxe -> needle. Nothing else from this mod |
Final version: other belt changes in the g13 run (Geirhild, Gully) kept the same profession, so they are ordinary upgrades. Belts held
from the third autosave to the end of the g13 run and from the first in the g14 run, about 1.5-2.5 minutes each, so long-term stability is not shown.
A second ladle and lantern in the g13 runs stayed free. One CLS_FOOD_ROAST spawned in the final g14 run; I did not confirm which building made it.
The installed list has `autosave_interval` and `invader_cap` where these runs had `_test_quiet`; only the first version ran with them.

## mods/failed_equip_release (2026-11-07), cause 4 fixed
- The C2 design, built at a new place: 0x1803ee4a8 `jne 0x1803ef366` (`0f 85 b8 0e 00 00`, taken for every end reason but
  UT_SUCCEEDED and UT_REMOVED) jumps to a cave at `.hmod` 0x100. For UT_FAILED (1) of an automatic equip (action data +0x10 = 0)
  whose def matched (tool word at [rsp+0x50] != 0), it clears the busy byte ([sensor+0x50][dwarf]) and calls
  claim_system_release_claim_if_claimed(mainstate+0x530, dwarf, tool), then jumps on to 0x1803ef366 as before.
  equip_action_end calls on_done for FAILED, SUCCEEDED and REMOVED only (0x1803b0f2f); REPLACED and ABORTED keep the def.
- Evidence in the user's colony: auto-equip claims (CLAIM_PERSONAL, ref bit 32) in saves: savegame27 1, savegame29 1,
  autosave_2 (16:29) and savegame30 (17:00) both 4970 -> dwarf 5518, in a session with one load at its start. Claim types are
  the trailing hash list of `claim_system/claims.bin`, one hash per claim in order (not indexed by the record's last byte).
- Test: `_test_equip_fail` turns the first 2 automatic UT_SUCCEEDED ends into UT_FAILED (at equip_action_end entry, before the
  tool moves; the tool is still in storage then, as after a real failure). Copies of savegame30, `_test_quiet`, key 3. Both
  runs hit 3807 (tool 5965) and 5518 (tool 4970), the same pairs as the user's save. Without the fix: no further equip by
  either in 30 game minutes (25 equips by others), both claims pending in the last autosave. With it: 5518 took 4970 7 game
  seconds later, 3807 took 5965 27 s later and then upgraded five more times like the other dwarves (each swaps 3-4 times
  after a load in both runs, passing the same weapons around); 0 pending claims at the end, no exceptions.
- Not tested: a tool that fails every time (the dwarf may retry it every sensor pass), natural failures.
