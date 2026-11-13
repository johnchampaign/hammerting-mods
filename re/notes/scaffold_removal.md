# Scaffold / ladder removal (BUGS.md A15), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 98 command_teardown, 64 command_build, 86 command_order_cancel,
126/225 building_system, 49 player_command, 80 command_jobs_misc, 112 order_system.ecs,
120 job_broker.ecs, 138 claim.ecs, 87/88/90 (plus 176 sensor_craft, 139 interaction_system,
21 job_broker, 214 tile_graph_generators already present). Bytes are from the pristine DLL
(`game.x86_64.dll.hmod-orig`); no site below is touched by the installed mods.
Static analysis, except the section "In-game test" below. Where they disagree, the test wins.

## In-game test (2026-11-02, copy of the user's colony, 16 mods installed)
Times are session-log clock. Evidence is the log (`order_teardown`, `unspawn`) plus tooltips.

| Target | Result |
|---|---|
| Column x=595, top piece (595,1003), ent 2599 | Ordered 11:04; piece and producer unspawned 13:14 |
| Same column, middle piece (595,999), ent 1755 | Ordered 13:53; unspawned 14:52 |
| Probably column x=579, middle (producer 4106) | Ordered 20:01; still 0% when the game auto-paused at 26:17 |
| `building/infirmary_small` (a misaimed click, second run) | Ordered 04:14; unspawned 04:55 |

- The order marker reads "Craft / Tearing down a building. / 0% percent complete / Click to
  cancel order." The 4106 order never showed the ORDER_NO_PATH text and was not in the
  Impossible Orders alert. Its target is inferred: a no-tool hover near that spot named Small
  Scaffold Stair, but the log never named the piece because it did not complete.
- After the two x=595 removals the alert "Stranded Dwarves ... unable to reach the Entrance"
  named Svante, on column x=579. That dwarf may have been cut off by the removals (inferred, not
  traced). Svante's Building is disallowed in the Job Broker; the five allowed builders were
  elsewhere. So 4106 may simply have been out of reach of every builder, with the game not
  saying so. This was not separated from other causes: the clean rerun meant to do so hit the
  Infirmary instead.
- Cause 2 below ("mid-column pieces have no position") is refuted for (595,999). Causes 3 and 4
  and the refusal in cause 1 were not exercised. No refusal of a scaffold was seen on a click:
  a hover at the (595,999) spot once showed "Must have a valid target", yet a click there later
  was accepted. Tooltips lag, so hover readings alone are not evidence.
- "Unreachable"-looking markers in this colony are mostly build orders, not tear-downs: 38
  pending `logic/player_command_producer`, 17 built `mech/stairway_scaffold_small`. Impossible
  Orders listed Small Scaffold Stair x7, Small Stone Bridge x4 and Dwelling x3, among others,
  with "0/2x Granite Chunk" on the one hovered. The red no-entry marker's text was not read.
- Tear down takes the entity under the cursor, so a click near a scaffold can hit the building
  behind it and removes it without confirmation. Whether that was a bad aim or a picking
  priority was not checked.
- Untested: bottom pieces, columns x=429 and x=474, the one-tile-offset piece (428,1001), bridges,
  4x4 ladders, patches P1-P4, and "already an order here".
- Column positions: higher tile y is higher on screen. x=595 rises from the floor (y=994) at 995-1003.

## The user's "won't let me tear it down" (2026-11-04, copy of savegame17, all mods plus `_test_quiet`)
Tear-downs ordered at log 1:51, 5:54 and 5:56 of the user's session were still at 0% at their save at 8:11, with about 30 pause toggles in between and no no-path text. In the test, with no input but key 3 from log 3:00, they ran at 4:28 (626, 953), 4:34 (578, 1024) and 5:01 (578, 1022), in between the pending build orders. So they weren't stuck, and that fits the 0% for six minutes in the test above; update_teardown_jobs makes the farthest one normal and the rest low, so they also lose to normal build orders by 1000 in the score (`job_broker.md`). Whether priority or just the queue set the timing wasn't measured. The Tear down tool's hover on a piece with an order reads "There's already an order here", and on anything else "Must have a valid target". A left click on the marker logs `order_cancel_single`. `mods/teardown_hint` adds this to the texts.

## What the objects are
- `mech/stairway_scaffold_small` = "Small Scaffold Stair" (MECH_STAIRWAY_SCAFFOLD_SMALL),
  `_big` = "Large Scaffold Stair", `mech/stairway_scaffold` = "Scaffold Stair" (4x4 'B'
  transport footprint, no walk tiles: probably the "4x4 ladder" of the reports).
  `MECH_LADDER_SMALL` is "Small Wooden Ladder" (1 tile 'C').
- Each is a room (database/room/room_default.bin, 99 records of 0x30a0 bytes after a 16-byte
  header: tag char[56] + hash +0x38, values i32 16.16 at +0x80 = CENTER_X/Y/Z, REPEAT_X/Y,
  OFFSET_Y, layout u8[3][64][64] at +0x98 = ROOM, TRANSPORT, WALK). Layouts (rows top-down):
  ```
  SCAFFOLD_SMALL  center (1,2) repeat (2,2)  transport rows 2-3 "BB", walk rows 2 and 4 "WW"
  SCAFFOLD_BIG    center (2,3) repeat (4,4)  transport rows 0-3 "BBBB", walk "W  W","WWWW","W  W"
  SCAFFOLD        center (2,2)               transport 4x4 "BBBB", no walk
  BRIDGE_SMALL_STONE center (2,1) repeat (4,4) transport + walk row 2 "BBBB"
  ```
- Entity components (entity/mech/stairway_scaffold_small.entity, table at +0x90 of
  {u32 type, u32 0, u64 offset}, type = low 16 bits of uppercasehash): STRING, DEBUG_NAME,
  ROOM_COMP, DB_COMP, ARCHETYPE, BUILDING_COMP, FACTION_COMP (u16 1), MODIFIER_COMP, TAG x2,
  GAMEPATH_COMP (model/mech/stairway_scaffold_small.model, i.e. the stairs are a gamepath).
- A dragged build makes one separate producer, then one separate room entity, per repeat
  (build_execute 0x1802ea980 loops over calc_count_and_offset). Scaffold pieces are not
  parent/child of each other. Construction "scaffolding" (RECIPE_SPECIAL_SCAFFOLDING_SETUP /
  _TEARDOWN, BT_BUILD_SCAFFOLDING_*, "Tearing down scaffolding.") is a different thing: the
  temporary rig used to build BUILDING_* rooms, not these mechs.

## UI and command
- Build menu (`entity/ui/window/build_menu.entity`) button LABEL__TEARDOWN_COMMAND runs
  `SET_ACTIVE_COMMAND(COMMAND(CTX))` for command `order_teardown` (ORDER_TEARDOWN "Tear down a
  building"). Key binding option OPTION_COMMAND_DESTROY "Command: Tear down"
  (GAME_INPUT_COMMAND_DESTROY in gamemedia.dll); default key not decoded, read it in
  Options > Controls. Then click the scaffold.
- Registered in `dynamic initializer for 'defs'` 0x18001f6e0 (flags MAIN_MENU, BUILD,
  NO_PREVIEW), is_valid 0x1803017f0, execute 0x1803023f0.
- **teardown_is_valid 0x1803017f0** (arg: target entity, property type 2 / tag 0x1a486). Every
  refusal sets CMD_ERR_NO_TARGET ":cross: Must have a valid target." except the last:
  1. no entity under the cursor;
  2. **entity has a family parent** (family_info[e]._parent != 0, 0x180301902
     `66 44 39 34 48 74 4b`);
  3. room record tag BUILDING_ENTRANCE_CAVE (0x18030197c);
  4. room whose faction != FACTION_DWARVES_DB_INDEX (0x1803019f9 `66 39 0c 70 0f 84 d2 00 00 00`);
  5. not a room and no tag HARVESTABLE (0x180301a4f);
  6. any ORDER_CRAFT order whose producer has KV `teardownee` == target ->
     CMD_ERR_ALREADY_ORDER ":cross: There's already an order here." (0x180302385).
  The text is the command's hover tooltip (format ":cross: %s\n" at 0x18054f098).
- **teardown_execute 0x1803023f0**: with g_instant_construction_completion (0x1805a4078,
  debug) the target is destroyed at once with TDTD_EVENT_ON_TEARDOWN. Otherwise it creates
  `entity/logic/player_command_producer.entity` at the target's **world position**
  (FIXED_POSITION, PRODUCER_COMP, ACTION_COMP, tag BUILDING_SPOT; no ROOM_COMP, so the map is
  not touched), sets template recipe RECIPE_SPECIAL_TEARDOWN (`database/recipe/recipe_special.bin`:
  BUILDING_SPOT, PROF_BUILDER, no BT), starts production, and stores KV
  `teardownee` = target (type 0x10002, tag 0x1a486) on the producer (0x180302939).
- Cancel (command_order_cancel command_execute 0x1802f65e0): an ORDER_CRAFT is cancelled when
  its producer's world position lies inside the dragged rectangle (0x1802f6e7d..0x1802f6ec7),
  i.e. drag Cancel over the scaffold's pivot tile, not just any tile of it.

## Job: sensor_craft (module 176)
- sensor_craft_update 0x1803c6f00 loops over craft orders (0x38-byte records: +8 order,
  +0xa producer, +0xc workplace, +0x14/+0x1c job list of 8-byte {job id, u16 queue entry},
  +0x24 has-path, +0x25 has-tool, +0x26 "teardown, single position").
  - Workplace positions = interaction_system_get_positions(producer) (0x1803c6ffe), then
    filter_interaction_positions (0x1803c70ed) -> job_broker_system_set_workplace_positions.
  - A new job whose recipe is RECIPE_SPECIAL_TEARDOWN is appended to the teardown list
    (sensor +0x18/+0x20, 0x18 bytes {i64 dist, u32 prio, u32 job, u8 player_set, u16 producer})
    and **sets order +0x26 = 1** (0x1803c7a49 and 0x1803c7b49, `41 c6 46 26 01`).
  - HAS_PATH (0x1803c815c..0x1803c8194): order data +2 = any job of the order passes
    job_broker_system_has_path_to_compatible_worker; true when the order has no jobs.
- **filter_interaction_positions 0x1803c54e0**: when +0x26 is set, keep only ONE position:
  the producer's interaction position closest to the cave entrance by the entrance's
  "movement" query (get_entrance_data 0x1803a2df0: KV_ENTRANCE_ENTITIES of the game entity,
  cached in sensor +0x28; interaction_system_find_closest_interact_position 0x1803890c0, result
  in a static at 0x1805bca40). If the entrance reaches none, all positions are kept.
- **update_teardown_jobs 0x1803c1620** (on a new teardown job and every 27th tick,
  0x1803c96ef..0x1803c971f): per teardown job, distance from the entrance to its closest
  position; the farthest reachable job gets JOB_PRIO_NORMAL (1), every other one without a
  player-set priority JOB_PRIO_LOW (0). Unreachable ones get dist -0x10000 and are never the
  NORMAL one. So teardowns run one at a time, far end first.
- Completion (bt_create_node_evaluate_wants_to_produce, 0x1804d8419..0x1804d84bf): read
  `teardownee`, trigger TDTD_EVENT_ON_TEARDOWN, inventory_system_drop_all_items, destroy it.
- Job end / producer change / entity destroyed -> try_teardown_job_cleanup 0x1803c2bb0 (drop
  from the list, rerun update_teardown_jobs). sensor_craft_load_post 0x1803c9de0 rebuilds the
  list after loading.

## Interaction positions: sensor_util::calc_valid_interact_positions 0x180363fa0
Runs from interaction_system::update_position_comp for dirty comps; comps are dirtied when
one of their nodes/edges is recycled or their block (+neighbours) gains nodes
(interaction_system_recycle_nodes_edges 0x180387b80).
1. Footprint: if the producer's queue holds RECIPE_SPECIAL_TEARDOWN (0x180364451) the room
   record of `teardownee` is used and a teardown flag is set (0x1803644cd). Every footprint
   tile with any layout byte (except 0x20) seeds add_possible_interaction_positions_from_tile
   0x180368870 (neighbour tiles by the reach config; a tile is rejected if MAP_IS_WALK_FILLED:
   walk layer == HAS_BUILT or is_front). The producer's own pivot tile is removed unless
   ctx+0xa (0x1803646c2).
2. Per candidate tile (0x180364ed0): rejected if filled; **only tiles with support below**
   (walk==2 or is_front at y-1, 0x180364f51) look for a tile-graph node / nearest edge in the
   tile (tile_graph::get_nodes_from_tiles 0x180364fa2). Tiles in mid air go straight to 3.
3. Gamepath points within 1 tile of the candidate (gamepath_system_get_block_gamepath_nodes,
   node type 2). **For a teardown only points with z > 0 are accepted** (0x180365b67
   `80 7c 24 38 00 74 09`, then `test r12d; jle skip`).
Walk edges need 2 tiles of head space (walk_horizontal 0x180481170 passes 2), and stacked
SCAFFOLD_SMALL units have a W platform every 2 rows, so inside a column most platform tiles
probably carry no walk node (inferred, not checked in a running map).

## Reachability: job_broker_system::has_workers_in_range 0x18012b4a0
- If any job of the workplace is possible (+0x47) and not +0x46: true when some compatible
  worker (worker +0x76 mask by job type) has distance >= 0 to this workplace (worker +0x56,
  filled by update_worker_distances 0x180135b30).
- Otherwise per worker, per workplace position: its node(s) reached in the worker's own
  navgraph query (result +0xc), an edge position also needs the edge type's cost > 0.
- No positions -> false. ORDER_NO_PATH in `entity/ui/in_world/order_status.entity`
  (`ENABLE(NOT(GAME_CTX.ORDER.HAS_PATH))`, getter 0x1800d3960 reads order data +2):
  ":blocked: No dwarf who is able and allowed to do this job can find their way here."

## Why "remove refused" and "every connected scaffold not reachable", ranked
1. **Already ordered (verified gate, likely trigger).** Once a teardown order exists, a new
   click is refused with "There's already an order here." The order is invisible as a job if
   it is LOW priority or unreachable; it stays until cancelled over the scaffold's pivot tile.
   A player who sees "not reachable" and clicks again gets "refused".
2. **Work positions exist only on a narrow set of spots (verified rules, inferred effect).**
   For a teardown a position must be a supported tile with a tile node, or a gamepath point
   with z > 0, around the footprint. The stairs themselves are a gamepath (GAMEPATH_COMP from
   the model); if its z <= 0 they are excluded, and inside a scaffold column the platform
   tiles may lack walk nodes. Then a scaffold whose only neighbours are other scaffolds has no
   position at all -> HAS_PATH false -> "not reachable", for every piece except the ends of
   the column. Removing an end piece changes which pieces have positions; a piece with no
   positions anywhere (the "bugged" one) blocks everything reached only through it.
3. **One position only, chosen from the entrance (verified).** With +0x26 the order keeps the
   single position closest to the entrance. If that spot is on a neighbouring piece that is
   itself being removed, claimed, or reachable only by non-builders, the order is "not
   reachable" although other positions would work. Connected pieces pick positions on each
   other, so one bad piece propagates.
4. **Serial priority (verified, effect depends on the broker).** Only the farthest reachable
   teardown is NORMAL, the rest LOW; if the broker will not start LOW jobs while a NORMAL one of
   the same type waits, one stuck far piece stalls all others (not checked in calc_assignments).
5. **"Must have a valid target" (verified gates, no scaffold-specific trigger found).** The
   picked entity has a family parent, or its faction is not the dwarves'. The scaffold's
   FACTION_COMP is 1 in data; the picker's choice of entity under the cursor was not traced.

## Patch candidates (pristine bytes)
- P1 (no cave): let teardowns use every interaction position, not only the one nearest the
  entrance. NOP both `movb $1, 0x26(%r14)`:
  0x1803c7a49 `41 c6 46 26 01` -> `0f 1f 44 00 00`, 0x1803c7b49 same. HAS_PATH then means "a
  builder reaches any position". Risk: the builder may work from the far side or from the
  piece itself and be left stranded or falling when it disappears (fall_when_idle helps).
- P2 (no cave): accept gamepath points at any z for teardowns: 0x180365b6c `74 09` -> `eb 09`
  (site 0x180365b67 `80 7c 24 38 00 74 09` -> `80 7c 24 38 00 eb 09`). Lets the stairs'
  own and neighbours' gamepath nodes count. Risk: for buildings the worker may stand on the
  building's own back-plane path.
- P3 (no cave, only if test 5 shows a parented target): skip the family check,
  0x180301902 `66 44 39 34 48 74 4b` -> `66 44 39 34 48 eb 4b`. Risk: tearing down a child
  entity (e.g. a model or attachment); prefer a cave that substitutes the family root.
- P4 (no cave): stop the serial ordering: in update_teardown_jobs skip lowering others,
  0x1803c19a0 loop: `40 38 73 10 75 1e` -> `40 38 73 10 eb 1e` (cmpb sil,0x10(rbx); jne ->
  jmp). Every teardown keeps its own priority. Only needed if
  cause 4 is confirmed.
- No data patch applies: the rules are code; recipe_special.bin has no conditions.
Start with P1+P2 as one opt-in mod; P1 alone if P2 shows workers standing inside buildings.

## Test plan (user's colony: 17 stairway_scaffold_small, some bridge_small_stone)
Back up the save folder first (`~/.local/share/hammerting-tools/save-backup-*`).
1. Before ordering: in a save copy, list orders: `saveinspect`/`save.py` on
   production_system (template recipe hash wc_hash("RECIPE_SPECIAL_TEARDOWN") =
   0xa520486b0fb9cfe6), key_value_system key `teardownee` (wc_hash 0xe01409e169cdab07,
   type 0x10002, value = scaffold entity id), order_system ORDER_CRAFT
   (0x116d9aea641cc40d). Any hit = cause 1 already present: that scaffold refuses new orders.
2. In game, Build menu -> Tear down, hover each scaffold: ":cross: There's already an order
   here." (cause 1) or ":cross: Must have a valid target." (cause 5) is shown in the tooltip.
3. Order the top piece of a column, a middle piece, the bottom piece, an isolated piece and a
   bridge. The in-world order marker shows the ORDER_NO_PATH tooltip when unreachable. The Job
   Broker lists the teardown jobs ("Tearing down a building.") with their priority: one NORMAL,
   the rest LOW is cause 4's precondition.
4. Note which pieces show "not reachable": middle pieces only -> cause 2; pieces whose nearest
   spot to the entrance is on an ordered neighbour -> cause 3. Cancel by dragging Cancel over
   each pivot tile and confirm the order disappears (order_system entry gone in the save).
5. Repeat with P1, then P1+P2 installed; a piece that becomes reachable identifies the cause.
6. Restore the save folder afterwards.
