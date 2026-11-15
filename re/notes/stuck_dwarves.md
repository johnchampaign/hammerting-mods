# Stuck / floating dwarves (BUGS.md A10), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 17 graph_position_system, 106 navgraph_system, 109 tile_graph,
114 physics, 150 movement_util, 164 action_fall, 180 sensor_fall, 188 movement_system,
196 locomotion_system, 214 tile_graph_generators, 233 node_fall, 251-255 climb/jump nodes,
59 patch_monolith, plus 234/252/257/261/171/89/52. Bytes below are from the pristine DLL
(`game.x86_64.dll.hmod-orig`); none of the sites is touched by the installed mods.
Source for the graph types is in `re/extract/graph/public/graph/graph_types.h` and the
nearest-edge search is inline C++ in `tdtd/gamestate/public/gamestate/tile_graph_util.h`
(`find_nearest_graph_position`, `find_nearest_tile_graph_edge`, `graph_pos_to_world_pos`).

## Model
- Navgraph (graph.x86_64.dll): nodes `{type:8, data:24, self_id}` (NODETYPE_TILE 1,
  GAMEPATH 2, OVERWORLD 3), edges `{type:8, data:23, dir:1, node[2], self_id, cost}`
  (EDGETYPE WALK 1, CLIMB 2, JUMP 3, JUMP_TO_ROOM 4, DROP 5, RAIL 6). Tile nodes are made by
  `tile_graph` generators per 16x16 map block (walk/diagonal/climb/jump/drop "with head
  space", module 214). Walk support = tile below has walk layer == 2 (HAS_BUILT) or is_front
  (bit 21) (walk_horizontal_with_head_space 0x180480d11), the same test the fall code uses.
  `tile_graph::update` (0x180332c10) rebuilds dirty blocks each frame from gamestate::update
  (0x1802b06b0), then the graph's recycle callbacks run (graph_position, movement, ...).
- `graph_position {u32 nodes[2]; u32 edge; i64 pct (16.16)}`; node only when nodes[1]==0 or
  pct 0/1; invalid when nodes[0]==0.
- `graph_position_component` (0x40 per entity, array at system+0x28): _pos +0 (0x18),
  _last_node_types[2] +0x18, _last_edge_type +0x1a, _last_search_range +0x1b,
  _search_node_types[16] +0x1c, _search_edge_types[8] +0x2c, _search_range[8] +0x34,
  _recalc +0x3c. Created from GRAPH_POSITION_COMP (0x8d65, data copied) or FIXED_POSITION
  (0x812a, zeroed) (create_components 0x180109870). Dwarves have no explicit config.
- The graph position is DERIVED from the world (transform) position, never the reverse,
  except where code teleports: movement behaviours write graph_position_system_update_position
  as they advance, and bt_fall_update teleports on landing.
- Character state that matters: locomotion comp (0x28 bytes: bool gravity +0, animation
  driven +1, script driven +2, map constrained +3, max vel +4, vel +0x10, touch times
  +0x1c..), movement comp (0x90: movement_state + current behaviour +0x70 + prev gp +0x78),
  KV `MOVEMENT_STATE` (u64 hash of MOVEMENT_STATE_STAND/JUMP/CLIMB/DROP, type 0x10003).
- Map cell bits (map.h): material 0-4, content 5-9, health 10-12, order 13-14, room 15-16,
  transport 17-18, walk 19-20, is_front 21, explored 22, fog 23, fluid amount 24-26, fluid 27-30.

## Snapping: graph_position_system::update_dirty_comps (0x180107ac0)
Runs for dirty entities (set_dirty 0x180106290 / set_component_dirty 0x18010d0b0), at the end
of every recycle callback and in graph_position_system_update.
1. Root of the family must be dirty, else the root's position is copied to the child.
2. _pos zeroed. If search_node_types[0..1] == 0, defaults are written (0x180107c9c..0x180107cd0,
   bytes `41 c7 45 2c 01 01 02 02 41 88 45 30 41 c7 45 1c ... 41 c6 45 35 01 41 c6 45 37 01`):
   (TILE,TILE,WALK, range[0]), (GP,GP,WALK, 1), (TILE,TILE,CLIMB, range[2]), (GP,GP,CLIMB, 1),
   (TILE,solo). range[0] and range[2] are not written, so they are 0 for a fresh component.
3. Search list = {last types, _last_search_range} first, then the component list. Last config
   is dropped when last edge == RAIL and entity is PLAYER_CHARACTER (0x180107d30).
4. Per entry (inline find_nearest_graph_position): TILE solo -> node at trunc(x),trunc(y)
   (0x180107ee3); TILE-TILE -> node at own tile with an edge of that type (exact, stops) else
   find_nearest_tile_graph_edge(max_dist = range, chessboard tiles) (0x180108033..0x1801083b1;
   z clamped to [2,3]); GP -> find_nearest_gamepath_graph_edge(range, 3D); OW -> fixed.
   Loop stops when best_dist_sq <= 0.
5. Nothing found: fall back to the entity's OWN gamepath nodes (0x18010858d..0x18010871f;
   buildings). Characters have none, so _pos stays 0.
6. Types of the result go to _last_* via set_comp_data_on_family (0x1801093fe).
So a character only gets a position from its own tile (range 0) or a gamepath within 1.0.
No neighbourhood search, no teleport here.

## Recycle: graph_position_system_recycle_nodes_edges (0x1801066c0)
- Valid _pos: dirty if nodes[0]/nodes[1] in removed nodes or edge in removed edges
  (0x180106ab5..0x180106b31). Only removals dirty; a position whose node survives keeps it
  even if the node lost its walk edges or its support.
- Invalid _pos (0x180106b36): checks "nodes/edges were added", config present, entity is a
  family root, not CURRENTLY_IN_OVERWORLD, tile/gamepath nodes added, then tests whether
  _pos.nodes[0]/[1] lie in a touched block (0x180106bf0, 0x180106d85). Those nodes are 0, so
  **an entity without a graph position is never re-snapped when new nodes appear**
  (building a block or scaffold under it does nothing by itself). Verified.
- movement_system_recycle_nodes_edges (0x1804010b0) only clears movement _target (+8) and
  _queued_target (+0x48). movement_behavior_update (0x180408410) exits the behaviour when the
  gp no longer equals prev gp (+0x78) or the target is invalid. Deleted-edge-mid-traversal is
  therefore handled (behaviour exit, re-snap); not a stuck cause.
- on_event_physics_on_ground (0x1801079a0): event 0x5aa569f3 with active=1 zeroes _pos without
  dirtying; active=0 dirties.
- Locomotion: first ground touch while affected by gravity (y integer, vel.y <= 0, tile below
  is_front only) dirties the gp (0x180414a71).

## Recovery = fall sensor + BT_FALL (the only one)
fall_sensor_update (0x1803f4710), per entity with SENSOR_FALL (dwarf_base has it), skip if:
- already has a fall instance in the sensor list (0x1803f4e04);
- locomotion script_driven (+2) set (0x1803f4e28);
- gp on a GAMEPATH/OVERWORLD node or gamepath edge (0x1803f4e6f..0x1803f4e87, 0x1803f4f9e);
- gp edge type CLIMB (0x1803f4e9f `80 3c c2 02 0f 84 05 01 00 00`) or JUMP_TO_ROOM
  (0x1803f4ead `80 3c c2 04 0f 84 f7 00 00 00`);
- has a family parent (0x1803f4ed0).
Then: gp invalid -> ACTION_FALL at once (0x1803f4ee8). gp valid -> only if KV MOVEMENT_STATE is
missing or == STAND (0x1803f4ef1..0x1803f501c) is the tile below checked (walk==2 or is_front,
0x1803f501e..0x1803f5087); no support -> ACTION_FALL (utility_system_add_action_instance
0x1803f50cb). ACTION_FALL rank 9 (0x1803b36a7), BT_FALL. The sensor has no save/load
callbacks (sensor_create_fall 0x1803f3e30); its list is rebuilt after load.
- bt_fall_enter (0x18048b400): stores start tile y, movement_system_force_stop (runs the current
  movement behaviour's exit), clears the gp (0x18048b6e7), gravity on (0x18048b7a7).
- bt_fall_update (0x18048b830): landed when frac(y) < 0.01 and tile (x, y-1) is walk==2 or
  is_front (0x18048c284..0x18048c2ea). Fall > 4 tiles -> damage (STAT_FALLING_DAMAGE_RESISTANCE).
  Snap: radius r = 0, 16, 32, ... 96 (`cmp $0x64` 0x18048c5b7, `add $0x10` 0x18048c9c8);
  r=0 accepts every edge type, r>0 only WALK and CLIMB (multipliers 0x18054d410). Found with
  r>0 -> teleport to (tile.x+0.5, tile.y) (0x18048c9b9). Then update_position and return
  SUCCESS (0x18048ca07..0x18048ca32) **even when nothing was found**, so the gp stays 0 and the
  sensor starts the next fall at once (fall/land loop). Not landed -> ledge grab (CLIMB edge at
  own tile, unless KV IGNORE_LEDGES_WHILE_FALLING > now) else RUNNING (3, 0x18048d08b).
  No timeout: BT_FALL runs until landing.
- bt_fall_exit (0x18048b7d0): gravity off, gp dirty.
Embedded in rock: no node in a solid tile -> gp 0 -> fall -> lands at once (support below) ->
r=0 fails -> r=16 finds the nearest walk/climb edge and teleports. Recovers within 96 tiles.

## MOVEMENT_STATE bookkeeping (verified)
movement_update_set_state (0x1803a27e0) writes the KV. STAND is written only by the exits of
walk_stairs (0x1804dda2f), climb (0x1804de383), drop (0x1804dfb2d), jump_horizontal
(0x1804e06ce) and jump_vertical_to_room (0x1804e213e). Enters write CLIMB/DROP/JUMP. **The
exit of jump_vertical writes CLIMB, unconditionally** (0x1804e1819 `4c 8d 05 38 ab 07 00` =
lea r8,"MOVEMENT_STATE_CLIMB"). Plain walking never writes a state and
movement_update_stand_state (0x1803a2570, support-checked STAND) has no callers. So after any
vertical jump that is not followed by a climb, the dwarf keeps MOVEMENT_STATE_CLIMB while
walking and idling, possibly for hours, and the fall sensor never tests his support while his
gp is valid. The KV is saved; behaviours are not, so the state also survives reload.

## Save / load (verified)
- graph_position_system/data.bin (EP_LOAD 0x180107510, format <= 4): u16 entity list, u8 x9
  per entity (last edge type, 8 search edge types), u8 x18 (2 last node types, 16 search node
  types), u8 x8 (search ranges); formats 2-3 carry one more array that is skipped. Saved edge
  enum is remapped on load: 4->DROP 5, 5->RAIL 6, 6->JUMP_TO_ROOM 4. **No positions are saved**;
  every component is dirtied (0x18010788c) and re-snapped from the transform position by the
  rules above. _last_search_range and _recalc are not restored (0).
- locomotion_system/data.bin: saved, but EP_LOAD (0x180412160) discards it and resets every
  component (all flags 0, max vel 10, map constrained 1, 0x1804122a0); EP_LOAD_POST
  (0x180412330) sets script_driven for CURRENTLY_IN_OVERWORLD. So gravity/script flags never
  survive a reload (a mid-fall dwarf is re-detected by the sensor).
- movement_system: behaviours and paths are not restored; EP_LOAD_AFTER_ALL only adds the
  entrance's KV_ENTRANCE_ENTITIES component.
- key_value_system: MOVEMENT_STATE survives (see above).
- Mid-edge / mid-jump / mid-climb / mid-fall at save: re-snap uses the own tile only; failing
  that the dwarf falls on the first sensor tick and lands/teleports. Repaired, unless one of the
  sensor exemptions applies.

## Ways to end up permanently stuck, ranked
1. **Valid gp, no support, fall check suppressed (verified gates, trigger inferred).** The
   sensor tests support only for STAND/missing MOVEMENT_STATE and never for gp on CLIMB or
   JUMP_TO_ROOM edges or gamepaths. Recycle only re-snaps when the dwarf's own node/edge is
   deleted. So: dig/remove the block under an idle dwarf whose tile node survives (it still
   has a climb or other edge, e.g. next to a wall) -> gp still valid -> if his state is a stale
   CLIMB/JUMP/DROP (every vertical jump leaves CLIMB; reload keeps it) he stands in the air.
   Same if the re-snap lands him on a CLIMB edge through his tile (default list searches
   TILE CLIMB). He keeps a path start, so whether he can still walk off depends on the edges
   left at that node (climb edges usually exist; an isolated node = cannot be moved).
   Fits "after digging / block removed, hovering", "digging into pits", and a reload making
   many dwarves misbehave at once (MOVEMENT_STATE persists, positions are re-derived).
2. **No gp and the sensor never fires (verified gates).** script_driven stuck (set by
   jump_horizontal, jump_vertical_to_room, move_gamepath, wait_for_vehicle; reset only by
   their exits or a reload), family child, overworld tag, or a fall instance that never
   finishes. Recovery from no-gp exists only through the sensor, and recycle never re-snaps a
   no-gp entity (bug above), so building under them does not help. This is also the cart
   case (A13: carts float after their rail is removed; they have no fall sensor).
3. **BT_FALL that never ends (inferred).** No timeout; ends only on landing (support exactly
   below at integer y) or ledge grab. Anything that stops vertical motion without that support
   (gravity removed by another system, collision with something other than tile/walk layer)
   leaves the dwarf hovering in "falling", unselectable for work, fall instance blocking a new
   one. Not observed in code paths checked (locomotion collision and landing agree).
4. **Fall/land loop (verified).** Landing snap fails within 96 tiles -> SUCCESS with gp 0 ->
   immediate new fall. Also r=0 snap accepts JUMP/DROP/J2R/RAIL edges through the landing tile,
   which can start a dwarf mid-jump-edge ("endless jump loops", inferred).
5. **Snap radius 0 (verified, low impact).** Characters 1 tile off the graph get no gp and
   must fall; harmless when the sensor works, harmful with 2.
Not causes: deleted edge mid-traversal (handled), graph_recycle id reuse (removed ids dirty
the component in the same callback), saved stale locomotion flags (reset on load).

## Patch candidates
- P1 (cave, fixes 1 for idle dwarves): in fall_sensor_update, apply the MOVEMENT_STATE gate
  only while a movement behaviour is running. At 0x1803f4ef1 replace
  `0f 57 c0 48 8d 0d e5 e4 15 00` (xorps xmm0,xmm0; lea rcx,"MOVEMENT_STATE") with
  `e9 <rel32 cave>` + `90 90 90 90 90`. Cave:
  ```
  mov  rax, [rbp+0x488]        ; sensor_context_t*
  mov  rax, [rax]              ; gamestate*
  mov  rcx, [rax+0x28]         ; mainstate*
  add  rcx, 0x17f0             ; movement ecs (as in bt_fall_enter)
  movzx edx, di                ; entity
  call 0x180401010             ; movement_system_is_active (behaviour at +0x70)
  test al, al
  jz   0x1803f501e             ; idle -> support check
  xorps xmm0, xmm0
  lea  rcx, [0x1805533e0]      ; "MOVEMENT_STATE"
  jmp  0x1803f4efb
  ```
  Volatile registers are all reloaded after 0x1803f4ef1; rsp is call-aligned there. Keeps the
  CLIMB/J2R edge exemptions (miners dig while hanging on climb edges).
- P2 (no cave, alternative/addition to P1): jump_vertical_exit writes STAND instead of CLIMB:
  0x1804e1819 `4c 8d 05 38 ab 07 00` -> `4c 8d 05 d0 1b 07 00` (lea r8,"MOVEMENT_STATE_STAND"
  0x1805533f0). Risk: a STAND tick between the vertical jump and a following climb could start a
  fall at the wall; test before shipping. P1 alone covers the idle case without this risk.
- P3 (no cave, fixes the recycle bug in 2): re-snap no-gp roots when tile/gamepath nodes are
  added: 0x180106bf0 `8b 03 89 85 10 01 00 00` -> `e9 06 03 00 00 90 90 90` (jmp 0x180106efb,
  set_component_dirty). Cost: every recycle that adds nodes re-searches all no-gp root
  entities with a config (dropped items in the air, carts); measure.
- P4 (no cave, minor): default tile ranges 1 instead of 0: at 0x180107ccb replace
  `41 c6 45 35 01 41 c6 45 37 01` with `41 c7 45 34 01 01 01 01 90 90` (range[0..3] = 1).
  Only for fresh components; saved configs keep theirs.
- Not proposed: removing the CLIMB/J2R exemptions (drops miners off walls), a BT_FALL timeout
  (needs a cave and a sensible fallback position).
- Data: none; the rules are code. dwarf_movement (database/navgraph_query/navgraph_query.bin,
  208-byte records) allows WALK 1, CLIMB 6, JUMP 4, DROP 10, J2R 10, RAIL 0.2.

## Save repair and what a stuck dwarf looks like in a save
Positions come only from fixed_transform_system/data.bin (per-entity vec3 16.16 arrays; field
order not decoded here: five arrays, written at 0x1800ecf4f..0x1800ecf83). On load the gp is
recomputed from it, so moving the transform position of a stuck dwarf onto a standable tile
(support below, head space) is a full repair. Check per dwarf:
- key_value_system: key MOVEMENT_STATE (wc_hash 0x8a1c59e656e6971c; IAT 0x180531420 is
  wc_sys!wc_hash, MetroHash64 seed 0), type 0x10003, value STAND 0xa644f39ecff55772,
  CLIMB 0x7e54014e79c19a09, JUMP 0x22f409b441dc3674, DROP 0x6dfa22d485f74f87 (computed with
  tools/wchash.py, not yet seen in a save). Non-STAND on an idle dwarf = rank 1 gate. Repair:
  set it to STAND or delete the key.
- fixed_transform position -> tile (floor x, floor y); map cell of (x, y-1): no is_front and walk
  layer != 2 = unsupported; own cell is_front = embedded.
- graph_position_system/data.bin: last edge/node types (saved enum: 2 = CLIMB, 6 = J2R) and
  search ranges (expect 0/1).
- family_component_system: parent != 0 means the sensor ignores him.
- Tag CURRENTLY_IN_OVERWORLD on a cave dwarf -> script_driven after load.
Test idea: let a dwarf vertical-jump and walk (state CLIMB), dig the block under him next to a
wall, unpatched he should stay up; with P1 he falls when idle.

## Test of fall_when_idle (2026-11-01, user's save copy)
Before: dwarves 2098 and 4112 had MOVEMENT_STATE 0x22f409b441dc3674 (JUMP), the others
0xa644f39ecff55772 (STAND). Two autosave intervals with the patch: all six alive, no health drops
beyond a rat fight (the save has a rat attack that destroys and then restores the cook house
about 7 game minutes in, also seen unpatched), levels rose (7->13, 9->12, 29->30), all states
STAND. No spurious falls seen. The hover bug itself was not reproduced.

## Dwarf cut off in the East Tharnlaw cavern (2026-11-04)
Every run from savegame16 (t 10875) left one dwarf with no job and no food for good: 2209 at 609.5, 945 (4 runs with `whole_batch_inputs`, 1 without `fall_when_idle`), or 2236 at 609.5, 955 (2 with `whole_batch_inputs` off, 1 with no mods). He isn't hung: live, his utility action cycles between ACTION_SLEEP and ACTION_IDLE. Hunger and morale fall to 0. Health fell slowly in the longest runs (2293 to 1959 over about 1750 game seconds, natural_healing on).

**Cause: he is on the wrong side of a link that closes.** Read live with `tools/navreach.py` and a before/after copy of the graph, watching a copy of savegame16 at normal speed:
- The other six dwarves reach the same set of nodes, 1417 before and 1346 after. He reaches 86, with no overlap and no edge between the two groups. Those 86 are the cavern floor from 570, 959 to 626, 950 and the column at x 607-610.
- It happens as the stair piece at 609, 954 finishes (log 2:54.6, 51.5 s after play; the graph gains that piece's gamepath edges in the same step). Dwarves don't get out afterwards. In this run 2236 was at 609.0, 952 at that moment. So far it has been whoever is on the column, probably its builder [inferred]; 2209's Builder XP rose in the runs where he got stuck.
- Edges gone at that step: JUMP 626,950-625,948; JUMP (one way, up) 625,948 to 625,951; DROP (one way, down) 625,951 to 625,948; CLIMB 625,951-626,952. New there: WALK 625,952-626,952, CLIMB 624,951-625,952.
- Map change behind them: tile 625,951 has walk 0 in savegame16 and walk 2 (HAS_BUILT) in every later autosave. 626,951 was already 2. They are the bottom landing of stair `mech/stairway_scaffold_small` 4795 at 626, 953 (rows 951 B, 952 T, 953 B), built by the user between savegame15 and 16 with bridge 623, 954. So the only route between the cavern and the colony was a 3-tile jump up through the one open tile of that landing, and it closes when the landing is completed.
- It stays closed: walk 2 is saved, so a reload keeps him cut off. That's why reloading the cut-off save didn't help, and why moving him to the floor at 610.5, 943 didn't (the same pocket).
- Also cut off with him: the orders at 609, 958 and 960, and any of 591, 947-951 not yet built.

Not known: why 625,951 was unset in savegame16, and why the next stair piece, 17 tiles away in another map block, sets it. Whether finishing any stair or bridge does it was not tested. Nor whether the mod-off dwarf differs for any reason but timing. Bridge 3016 finishing at 643, 970 at log 2:34.9 did not change reach.

**Reconnecting works (in-game test, 1 run, all mods plus `_test_quiet`, copy of the save with 2209 already cut off).** Small Scaffold Stair ordered directly under the stairs at 626, 953, so at 626, 951 (rows 949 B, 950 T, 951 B at x 625-626). The game accepts it although 626,949 is solid.
- Reach merged as soon as the order was placed, before any building: 2209 went from 86 nodes (no overlap) to the shared 1562. Why wasn't traced. A pending order's footprint marks walk tiles `w`, so reopening the gap at 625,951 is a guess.
- The piece then got built, and reach stayed shared (1599 for all at the end). The piece finished about 12-30 s of log time after key 3, with the two open orders on the 609 column also built. Those were the spawns in that window; which spawn was which wasn't matched.
- Within about 4.5 real minutes at key 3, 2209 was back at work around the colony (positions from 517 to 676), hunger 0 to 2098, morale 0 to about 986, health 1959 to 2255.
- Loading the last autosave of that run: all seven dwarves share the same 1599 nodes, read twice over 30 s. So unlike the cut, the link survives a reload. No exceptions, no unlocks.
Not tested: placing the piece before the y 954 piece finishes (what a player continuing from savegame16 would do), long play.

**The user's savegame17 (2026-11-04), read from the save, not played.** 2209 is at 626.5, 950, directly under stair 4795, and 625,951 is walk 2. No piece or order at 626, 951. The user ordered tear-downs believing the stair was the block: producer 5400 at 626, 953 (log 1:51, same position as 4795), then 1870 and 5100 at 578, 1024 and 1022 (log 5:54, 5:56, same positions as 2019 and 4719). All three are still pending. Their targets are matched by position and spawn time; the `teardownee` values were not decoded. Why 5400 hadn't run is still unknown; its tooltip read "Tearing down a building. 0% percent complete. Click to cancel order." with no no-path line.

Tested on a copy of savegame17 (1 run, all mods plus `_test_quiet`, about 14 log minutes, no reload). Live, 2209 read 86 nodes with no overlap. A left click on the marker logged `order_cancel_single` and removed 5400; reach didn't change. Then V, Small Scaffold Stair, cursor at the tile under the landing, with his no-entry icon over the same spot: "Command is valid here", and the click logged `build` (log 9:16). 18 s later reach was still 86, unlike the earlier run where it merged at once; by the next read, about 70 s after the click, he shared the whole set. The piece spawned at log 10:40 (3986 at 626, 951), and the log and wall clock don't line up closely enough to say which came first. At the end all seven shared 1585 nodes. His autosave positions ran from 517 to 578, and his bars went morale 300 to 1045, hunger 1030 to 1252, health 2275 to 2325. The two x 578 tear-downs left in place ran at log 10:57 (2019 and 4719 gone) with no loss of reach. No exceptions, no unlocks.

**Tearing the stair down frees him too (1 run, copy of savegame17, no input but speed, all mods plus `_test_quiet`).** I had told the user it probably wouldn't, by counting tiles; that was wrong, and the user's guess was right. All three tear-downs ran untouched, within about 1.5 real minutes of key 3 at log 3:00: 4795 at log 4:28, 2019 at 4:34, 4719 at 5:01, and tiles 625-626, 951 went back to walk 0. Afterwards all seven dwarves shared 1574 nodes, and 2209 was at 652.5, 997 with hunger 1903. The route he took out wasn't traced. So both fixes work: tearing down loses the stair, and adding a piece keeps it (1585 nodes at the end of that run).

## `mods/stranded_rescue` (2026-11-05)
**Hook.** `gamestate::update` (0x1802aefe0) is `update(delta, time_now, real_delta, heartbeat)`: r12 gamestate, xmm8 delta, xmm6 0. Delta is game time: the 10-second check took about 10 s at normal speed and 2 s at key 3, and it stops when paused. The cave replaces the `delta == 0` test at 0x1802af3c5, before the frame's systems run. It isn't `eval_alert`: `alert_system_update` hands that to a function pointer, possibly a worker thread, and a player can switch alerts off.

**Test.** `ALERT_IS_STRANDED` is at 0x1800af5a0, with a thunk at 0x180072ce0 that takes the chain data in rcx. It reads only +0 gamestate, +0x30 u16 type (2), +0x32 u16 count, +0x34 u32 tag (0x1a486), +0x38 the entity, and +0x40 the out pointer (value at out+8).

**Move.** `get_entrance_data` (0x1803a2df0, from the mountainhome's KV_ENTRANCE_ENTITIES) gives the entrance, 318 at 556.5, 987 in this colony. Then force stop, `set_world_position` to tile x + 0.5 and whole y with his own z, and clear his graph position and query start as `bt_fall_enter` does. With no graph position the fall sensor starts BT_FALL, which lands him on that tile and sets both again. Mainstate offsets: family 0xe18, gp 0x11d8, movement 0x17f0, query 0x18e0, tag 0x2498, transform 0x2678. Counters are one byte per entity in the memory-only part of `.hmod`.

**Tests**, all on copies of savegame17 with the 28 mods and `_test_quiet`, one run each. No exceptions and no unlocks in any of them.
- Real rescue, 1-minute timer: only 2209's counter rose, one per 10 s. About 56 s after unpausing he was on the way from the entrance, then walking to work. All seven shared 1376 nodes. Health stayed 2275, so no fall damage; hunger 1070 to 1758 and morale 320 to 482 by the next save.
- Guard, 1-minute timer, 2080, 2236 and 3236 forced plus the real 2209 (4 of 7): counters stopped at 6, 2209 stayed at 626.5, 950, and nobody was moved over 95 s. The alert showed the new line and named only 2209.
- Stress, 1-minute timer, 2080 and 2236 forced (3 of 7 with 2209): one dwarf moved per check. In 320 s, part at key 3, 2080 and 2236 were moved 13 times each and 2209 once, from whatever they were doing. Health rose for everyone. Reach stayed shared when read mid-run. The save from this run loaded with all seven sharing the same nodes after 40 s.
- Shipping value, 2080 forced with the default 10 minutes, at key 3: 2080 and the real 2209 reached 60 and moved about 122 real seconds in. 2209 was still at 626.5, 950 at count 50.

**Dead end.** Editing `fixed_transform_system/data.bin` to put dwarves in the pocket doesn't strand them: live they read the colony's reach, their counters stayed at 0, and at least one walked out in seconds. Probably the saved route data, not traced. That's why the guard and stress runs force the check instead.

Not tested: a dwarf in the overworld or seated in a vehicle (both are skipped in the code, read not run), a colony whose entrance really is cut off, more than one dwarf really stranded at once, long play. Items he was carrying and jobs he held weren't checked one by one. A stuck dwarf with no graph position reads as not stranded, so this doesn't cover the hovering cases above.

## Dwarf frozen in a diagonal shaft (2026-11-15, GreatHvitforge savegame79)
Torner (2151) stood at 546.5, 692 from before the 13:46 autosave to the 13:49 save, with a haul claim (type 2) on a
loose copper ore at 523, 685, and no idle alert. The tile is in a 2-wide diagonal shaft (545..556, 691..701,
explored between 13:07 and 13:46): each step has floor and one open tile above, and the next step up is diagonal
under solid rock. The live tile graph has no node anywhere in the shaft (no edges, so no nodes), so his tile has
none. His "movement" query still reported the colony's 1383 reachable nodes, so the job broker kept giving him
jobs and ALERT_IS_STRANDED (and stranded_rescue) didn't fire. Saved graph_position types looked normal (WALK, tile).
Reloading the save freed him: two seconds after unpausing he was at 485.5, 718 and walking normally. How he got
into the shaft is not known.
Follow-up the same day (tests on `hmtest_shaft`, a savegame79 copy with the shaft refilled and ordered dug again):
- The dug shaft is walkable: one WALK edge, 544,690 -> 555,701, cost 16.5, with no nodes between. Torner's 546.5, 692
  lies on it exactly at a step point. A reload fails to snap him (no node at his tile, range 0), so he falls and is
  put back on the graph; that is why the reload freed him. Dwarves crossed the re-dug shaft many times without stalling.
- Diagonal WALK edges run walk_stairs (`movement_register_core_behaviors` 0x1803a29c0: WALK edges with equal y use the
  plain walk, otherwise stairs). bt_walk_stairs_enter writes MOVEMENT_STATE_JUMP (0x1804dd756) and its exit STAND.
  Torner's saved MOVEMENT_STATE was JUMP at 13:46 and 13:49 while every other dwarf read STAND or CLIMB, so he was
  inside a stairs (or jump) behaviour, standing on a step point, for at least 3 minutes. Save KV layout:
  key_value.bin = arrays (u16 entity ids), (u64 count per entity), (u64 key hashes, flattened), (16 bytes per key:
  u64 type 0x10003, u64 value hash).
- Each stairs step: event_callback_stairs_anim_done (0x1804dc980) puts the dwarf at the step's end and plays the next
  step, or at the walk's end turns animation driving off and sets the byte bt_walk_stairs_update (0x1804dda70)
  waits for. The update has no timeout. The world position changes only at step ends.
- Simulations with `mods/_test_stairs_drop`: dropping a step's animation-done event left the dwarf animation driven
  with no animation, and the game crashed about a second later in locomotion_system_update (0x180413b08), so
  Torner's stall was not that. Not setting the walk-end byte did not stall the dwarf (something else ends the
  behaviour). What stalled Torner is still unknown.
- `mods/stairs_timeout` (experimental): bt_walk_stairs_update returns BT_FAILURE once the dwarf's position has not
  changed for 10 game seconds. Never fired in about 20 game minutes of normal play; a 0.05-second limit fired 4,000+
  times with no errors (dwarves on stairs then re-planned in a loop, the rest played on).
- Soak test (2026-11-15, copy of savegame79, recommended mods minus stranded_rescue, plus stairs_timeout,
  _test_drop_log for the GAMESTATE-MOVE stairs lines and _test_no_achievements): 45 real minutes at speed 3, ticks
  113703-232707 (about 3.3 game hours), 15,611 stairs walks, 24 attack pauses. No timeout, no stall, no crash. The
  stall that held Torner is rare and its trigger is still unknown. Ruled out: hit reactions (ANIMHASH_HIT_REACT is
  only referenced by init_animhash) and weapon attacks (played from the bt_do_weapon_attack node, which runs only
  after the walk node has exited). stairs_timeout now also stores the last dwarf it freed and his position after
  its counter (.hmod 0x2f84), for the next time.
