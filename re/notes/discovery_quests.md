# Discovery quests that never complete (BUGS.md B11), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 206 exploration_spawn_system, 47 smart_event_system,
30 unlock_system (plus 26, 124, 128, 132, 152, 224, 276). Nothing here is touched by the
installed mods. Nothing was run in the game; everything below is static reading.

## 1. Who fires TDTD_EVENT_EXPLORATION_DISCOVERY
- Only `exploration_spawn_system::check_explorables(block)` (0x180444370; event built at
  0x1804447e9-0x1804448dc, dispatched through mainstate+0xcb0).
- The explorables list (system+0xb0, count +0xb8, 0x48-byte entries: name[56], u64 hash +0x38,
  u16 entity +0x40, u8 check counter +0x42) is filled in `exploration_spawn_system_create_components`
  (0x180448d30). It holds every entity whose MODIFIER_COMP tag (component 0x29c) matches an
  `exploration_record` (database/explorables/*: CAVE_ROOM_* x9, GROTTO_*, VEIN_CENTER,
  VISION_GROTTO, PROP_FLUID_SOURCE_WALL_33). Cave rooms are placed by map generation
  (biome_cdb), so all 15 ratholes / 10 wells / 1 forge god exist from turn 0.
- Trigger: map visibility calls `on_tiles_explored` (0x180440680). Each 16x16 block that goes
  from state 0 to 1 gets `spawn_block` plus `check_explorables` on its 3x3 block neighbourhood.
  Blocks near PLAYER_BASE entities are pre-set to state 2 and never processed themselves.
  For each explorable in a checked block: counter += 1. It is discovered if the map cell at
  its position has explored bit 22 set, or the counter has reached 9.
- Event args: ARG('0') = entity; ARG('1') = the record name string (e.g.
  'CAVE_ROOM_FOUNTAIN_GOD'), which MISSION_GEN_DISCOVER compares with
  `ARG('1').STRING.EQUALS(...)`; ARG('2') = '<NAME>_EXPLORED'; ARG('3..5') = position;
  ARG('6') = CURRENTLY_IN_OVERWORLD; ARG('7') = lore amount. Mountain lore and explorer XP
  are also awarded here.
- After the loop, discovered entries are swap-removed from the list (0x180445005...).
  The list is saved and restored (`save_file_format_1::push_to_system`, 0x18044beb0, moves it into
  system+0xb0). Discovery is therefore one-shot and persistent. The event never fires again for
  that room, and nothing re-fires on load. Old saves (format minor < 2) stored names with
  "_EXPLORED" appended, and the loader strips it.
- Side gap: a room is only re-checked when a block in its neighbourhood is explored for the
  first time. If its anchor cell becomes explored later, and fewer than 9 checks are possible
  (map edge, base area), the room is never discovered.

## 2. Persistent "discovered" record: unlock_system
- `event_callback_exploration_discovery` (0x1801a5850) queues hash(ARG('2')) =
  wc_hash("<NAME>_EXPLORED"). `unlock_system_update` then calls the unlock routine (0x1801a6180,
  named unlock_system_has_seen in the PDB). That routine appends the hash to the known list
  (system+0x1d8, saved in unlock_system/data.bin) whether or not anything depends on it, and
  removes it from dependency components. A component that becomes empty fires
  TDTD_EVENT_UNLOCK(tag). The smart_event_system callback (0x180265d00) starts the smart event
  with that tag (`add_se_with_objective`). On load the known list is replayed with is_load=1,
  which fires no events.
- `unlock_system_is_known(ecs, hash)` (0x1801a3ce0) = hash in the known list. The ecs is at
  mainstate+0x26f0. No eval property exposes it: IS_LOCKED reads a different list (+0x188,
  locked research/personal unlocks), and RESEARCH_STATUS only answers for research records.

## 3. When the quests start (record dependencies, record+144, 4 x u64)
| record | dependency | discover chain |
|---|---|---|
| MISSION_HEALTH_SPRING (Sacred Well) | RESEARCH_MEDICINE | ('CAVE_ROOM_FOUNTAIN_GOD','1','1') |
| MISSION_GOD_OF_THE_FORGE | RESEARCH_FORMALIZED_LEARNING | ('CAVE_ROOM_DWARF_GOD','1','1') |
| MISSION_RATS_IN_THE_WALLS | CAVE_ROOM_RATHOLE_EXPLORED (0x45f07be42ef91fc0) | ('CAVE_ROOM_RATHOLE','3','3','1') |
| (others) MOPPING_FLOORS: CREATURE_SLIME_GREEN_KILLED; DUST_TO_DUST: CAVE_ROOM_GRAVEYARD_EXPLORED | | |
Record layout (cave_mission_records_cdb.bin, 16-byte header, then 0x537b0-byte records):
tag +0, category +64, version u32 +128, force_single +132, cooldown +136, deps +144, part 0
generation chain +176 (1024 bytes). The parts are 0x48d0 bytes each.

## 4. Why they stall
- The well and forge-god quests only exist after their research. Any well or forge god
  discovered before that already fired its one-shot event and is never counted. The well quest
  can only finish if an undiscovered well is still left. The forge god is unique, so that quest
  is stuck for good.
- The rats quest is started by the first rathole's unlock, one unlock_system_update after the
  event. The designers' floor '1' credits that first rathole. Every other rathole revealed in
  the same exploration batch, or before the instance exists, is lost.
- Completion is checked only inside the event chains (`advance_from_event`, which stops at
  the first false chain). MISSION_GEN_DISCOVER adds no pre-event chain, so raising AMOUNT_DONE
  alone never completes a part. It still needs one more matching discovery.
- Load ("count drops on load"): not supported by the 1.2.39 code. The smart_event LOAD_POST
  (0x1802651b0) re-runs every part's generation chain through
  `smart_event_system_start_event_instance` (0x180268150) with overwrite_state = 8 FALSE bools
  (all TRUE only for an upgraded MISSION_OVERWORLD_ALLIANCE). TYPE, AMOUNT_WANTED and
  AMOUNT_DONE keep their saved values, which are stored raw (16-byte property_comp). The 4-arg
  floor only raises the value. Likely explanations are an older autosave/lastsave, a pre-1.2
  build, or a report confusing the floor (1/3) with progress. Because the generator re-runs on
  load, record edits do reach active instances' chains and args, but not their states.
- Delivery "completed after restart" (not traced to the end): on load `attempt_advancement`
  (0x180266130) finishes a mission whose parts are all `_completed` ("Found already completed
  part" -> attempt_finish 0x180266640). A part flagged completed at runtime whose finish was
  blocked gets finished by the reload.

## 5. Reading discovered state from a save
- unlock_system/data.bin: the u64 hash of "<NAME>_EXPLORED" is in the known list iff at least
  one room of that type was ever discovered. LE bytes: FOUNTAIN_GOD 62096f76eba630fc,
  DWARF_GOD 2d0f7ae5f0d884c5, RATHOLE c01ff92ee47bf045 (RATHOLE and GRAVEYARD are also
  dependencies, so check which list they sit in).
- exploration_spawn_system/data.bin (name built at runtime as "%s%s"; check `save.py list`):
  u64 count, then per undiscovered explorable: length words (0x38), name[56], u64 hash, u16
  entity, u8 counter. Each remaining "CAVE_ROOM_FOUNTAIN_GOD" is an undiscovered well, so
  discovered = map entities of that type minus remaining entries. The entity id gives the room.
- map explored bit 22 at the room's position is only a hint (the 9-check rule can discover a
  room without it). Log book LB_ENT_EXPLORATION_DISCOVERY entries carry 'tag' = name hash.
- Quest state, smart_event_system/data.bin, per instance: record ref, u32 version, u32 seq,
  (v>=3: u64 n + n*16 args, u32, u64), parts (v1: 4, v<=5: 8, else u64 n). Per part: u64
  nstates; per state: u64 len+key, u64 key hash, 16-byte value (u16 type 4 = i64, u16 count 1,
  u32 tag, i64), u64 len+tag string, u64 tag hash. Then u8 _completed (v>=2) and u64
  fail_timer (v>=4). Setting AMOUNT_DONE >= AMOUNT_WANTED and _completed=1 makes the next load
  finish the mission (reward granted by attempt_finish).

## 6. Fixes
**Built: `mods/discovery_counts_found_rooms` (2026-11-04).** It is option A below with one change, found by testing: option A sets `_completed` in the
generator, so a load finishes the mission through start_event_instance's tail call to attempt_advancement. That pays the reward but leaves the mission listed:
`remove_instance` has one caller, `smart_event_system_remove_destroyed_entities`, and the mission's entity wasn't destroyed after a finish during a load [why not
is inferred: not traced]. The saved `_completed` would then finish it again on every load [inferred, not run]. The mod instead queues the part (list in `.hmod`) and marks and finishes it
from the entry of on_event_callback (0x1802653d0), where missions normally finish, after checking the part is in the current instance list.
Tested with the 26 mods: copy of savegame15 (well found before the mission): the mission was gone when the loaded game was first seen, still paused, lore 4 to 9, God of the Forge stayed 0 / 1, Rats 2 / 3. Reloading that
run's autosave: lore still 9, no mission. Copy of savegame9 with lore edited to 60, Medicine bought: lore 60 - 10 + 5 = 55, mission not listed. No exceptions or unlocks.
Not tested: God of the Forge itself (this colony hasn't found it), Spelunker parts, loading another save from a running game (the list check exists for that).
Confirmed by the user in their own game (2026-11-04): after loading savegame15, Fountain of Youth was gone from the missions and Mountain Lore went from 4 to 9.

Options as first designed (A's bytes and `.hmod+0x400` are out of date):
No eval property can tell discovered rooms from undiscovered ones. TAGGED_ENTITIES does not
see cave rooms: their TAG components are STATUSBARS/ROOM/SELECTABLE/LAIR, and the type lives
in MODIFIER_COMP. So a data-only exact count is impossible.

A. Code patch (recommended; untested). Site: MISSION_GEN_DISCOVER lambda_11, floor block.
   - 0x180086219 old `41 80 fe 04 75 63` (cmp r14b,4; jne 0x180086282), new `e9 e2 61 58 00 90`
     (jmp 0x18060c400). The rest of the old block (up to 0x180086282) is then dead.
   - Cave at .hmod+0x400 (0x18060c400, 189 bytes). Source: re/notes/discovery_quests_cave.s
     (tools/cave.py syntax; symbols BASE, TO_I64, FMT, SNPRINTF, WC_HASH, IS_KNOWN, RESUME).
     The cave computes floor = args[3] (4-arg form) or 0. It sets floor >= 1 if
     unlock_system_is_known(mainstate+0x26f0, wc_hash("<TYPE>_EXPLORED")); TYPE comes from
     seip+0x120 and the format from 0x180558930 "%s_EXPLORED". Then
     AMOUNT_DONE = max(AMOUNT_DONE, floor). If AMOUNT_DONE >= AMOUNT_WANTED it sets
     seip->_completed (seip+0x550) = 1, so the tail call to attempt_advancement finishes the
     mission immediately, both at quest start and on load. It ends with jmp 0x180086282.
   - Symbols: to_i64 0x1800d8ae0, sys_snprintf IAT 0x1805313f0, wc_hash IAT 0x180531420,
     unlock_system_is_known 0x1801a3ce0. Live registers r15 seip, rdi args, r12
     mainstate+0x1e80. Scratch at [rsp+0x60] (the chain buffer, written later anyway).
   - Bytes: 31db4180fe04750c488d4f30e8cfc6acff4889c3488d4c2460ba000100004c8d050bc5f4ff4d8d8f20
     010000ff15be4ff2ff488d4c246048c7c2ffffffff48ffc2803c110075f7ff15d34ff2ff4889c2498d8c24
     70080000e88378b9ff84c0740a4885db7f05bb010000004181bf3002000004000100750949399f38020000
     7d1249c787300200000400010049899f380200004181bfa0010000040001007518498b8738020000493b87
     a80100007c0841c6875005000001e9c59da7ff
   - Effect: the well and forge-god quests complete on load or at research once one such room
     was ever found. This works on existing saves. The rats quest is unchanged (it is already
     at 1 when it starts). Side effect: the ACHIEVEMENT_SPELUNKER_EXTRAORDINAIRE parts
     (well, old statue, jackpot mine) also complete retroactively, which can unlock the Steam
     achievement. Untested: finishing a mission inside smart_event LOAD_POST (BEFORE_ALL).
     The engine already does this for all-completed instances.
B. Data-only alternative for well and forge god, mirroring the rats design. Add a second
   dependency (record+152) of wc_hash("CAVE_ROOM_FOUNTAIN_GOD_EXPLORED") = 0xfc30a6eb766f0962
   or "CAVE_ROOM_DWARF_GOD_EXPLORED" = 0xc584d8f0e57a0f2d. Change the part 0 chain to
   `MISSION_GEN_ACQUIRE_KNOWLEDGE('RESEARCH_MEDICINE')` or
   `MISSION_GEN_ACQUIRE_KNOWLEDGE('RESEARCH_FORMALIZED_LEARNING')`. Its pre-chain
   `'<R>'.HASH.RESEARCH_STATUS.EQUALS('ACQUIRED')` is true when the mission starts, so it
   completes at once. The mission then starts (and completes) when research and discovery are
   both done, in either order. Caveats: the quest is never shown in progress. The active
   instance in an existing save completes on load whether or not the room was found. It is
   unverified that dependency components are rebuilt from the database on load (rather than
   restored from the save).
C. Rats: no exact retroactive count. Options: lower to ('CAVE_ROOM_RATHOLE','2','2','1'), or
   edit the save (section 5).

## Forge god check (Nov 2026)
check_explorables(block) only looks at explorables whose own block is that block; on_tiles_explored calls it for
the 3x3 blocks around each block explored for the first time, so a room gets at most 9 checks. In
exploration_spawn/exploration_spawn.bin the explorables list is a u64 count followed by 83-byte records
(u64 0x38, u64 0x38, name[56], u64 hash, u16 entity, u8 counter); other data comes first. West Hirdness (entity 178
at 390,77), East Tharnlaw (205 at 120,88) and KrazJomsglind (138 at 106,87) each have one CAVE_ROOM_DWARF_GOD with
counter 0 and nothing explored in its 3x3 blocks. In all three colonies every undiscovered explorable's counter equals
its explored neighbour blocks and none has its anchor tile explored, so the late-anchor gap has not happened there.
