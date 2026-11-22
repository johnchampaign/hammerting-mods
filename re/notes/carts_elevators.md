# Rail carts and elevators, game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
The sections after "In-game tests" are static analysis of the pristine DLL (`.hmod-orig`) and of game data. Each
claim is marked [V] read in code or data, or [I] inferred. A mechanism marked [V] means the branch exists, not that it
is what a given player hit. Modules read: 118/223 station_system, 200/271 elevator_system, 257 wait node, 108 gamepath,
16 navgraph_query, 52 mainstate callbacks, 235 node_move_to, 263 node_haul (only the vehicle branches), 139 interaction,
178 sensor_dig, 17 graph_position, 117 ai_behavior. No PDB type dump (the heavy-job lock queue was hours long), so
struct layouts come from the code. Reports: threads in the session scratchpad, Reddit zpr38d (Dec 2022).

## In-game tests (2026-11-03, colony copies, `_test_quiet` + `_test_rails`, some with `_test_fed`). Read this first.
Rail pieces were free and unlocked by `_test_rails`. Positions came from `tools/memtrack.py`. No achievements unlocked. Each is 1 run.

| Test | Result |
|---|---|
| Line: Rail Stations at (563, 994) and (563, 1004), Long Elevator Rail at 1000, Elevator Rail at 1002 and 1003. Pieces need exact alignment | **A Handcar works, and dwarves ride it.** Handcar moves 11 times in 180 real s; two dwarves seated. |
| Same line with one piece missing (my stray click cancelled it) | Handcar parks at a station it can reach, nobody rides, no error shown. So a gap looks exactly like "the elevator doesn't work". Those runs are not counted as Cart results. |
| **Report 4.** Complete line, Cart only, Elevator Rail order at 1002 between built pieces | **Reproduced.** Order sat with a red no-path marker for 7.7 minutes of log time, dwarves idle nearby (needs off). Handcar spawned at 15:39.33, piece built at 15:39.91. A Cart does not stand in for it, though a Handcar is what unblocked it in 1 run. |
| Cart on the line | Never moved, never carried anyone, in any run. But no run gave it a haul job, so this does not test cargo. |
| Building down: two Long Elevator Rail sections below the hall station, with a Handcar on the line | Built and dug out without trouble, by a builder. The reported failure at the second section did not occur **with** a Handcar. |
| Reload with Handcar and Carts on a line | Handcar keeps working: 7 moves in 240 real s, riders seated. |
| `rail_fixes` on the same reload | Same: 7 moves, same seated counts, no exceptions. Regression only: neither fixed bug was reproduced. |
| Tear down the station under a Handcar, then the floating Handcar | Tear-down hits the station first, since it can't tell them apart. The floating Handcar then went in 4 s, no crash (`rail_fixes` on). The 2021 crash is not reproduced. In an earlier run in a starving colony the same order sat 7 minutes: hungry dwarves ignored it. |
| Final 21-mod list | 170 real s at top speed with real attack pauses: dwarves work, one rode, no exceptions. |

Not tested:
- **Cargo carts: the "stops without unloading" report is not reproduced or explained.** See the cargo test below. A Cart caught mid-trip by a save, and a destination or rail removed mid-trip, were not tested: trips last seconds.
- "Freeze after several reloads": only one reload per run. Stock and upward digging: see the B7 section below.
- States A to D below: no stall occurred in these short runs. Teardown with two riders, and a rider dying, were not arranged.
- Horizontal rail can't cross some buildings: long pieces at x 579 and 583 were refused beside the foundry at 580. It crossed the quarry at 566.

Other: hungry colonies distort every test here, since dwarves crowd the cook house and ignore orders, so `_test_fed` exists. With needs off and no orders dwarves stand idle, so test jobs must be placed.

## Cargo cart test (2026-11-03, colony copy, `_test_quiet` + `_test_rails` + `_test_fed`)
A Stone Chest at 572.5 beside the rail, with two Carts on the line, one starting up the shaft at (563, 1000).
- **Hauling works.** About 20 s after the filter was set to everything, the Cart on the shaft rode through the station to (569, 994), the other moved to (573, 994), and the chest went 0/30 to 30/30. Both Carts ended empty (0 items), so no Cart was stranded with a load when the chest filled. 3 runs: 1 fresh, 1 from a full replay of the same save, 1 after the reloads below.
- **Three reloads in a row, then a job: Carts still worked.** Time advanced across the first two reloads (t 13321, 13472, 13622); on the third I pressed play by hand. Then the same 21 s response and full delivery, no exceptions. Parked Carts only: not a reload with a Cart mid-haul.
- After the chest filled, Carts stayed parked beside it and empty. That is no job, not a stall.
- Carts take 15 items from a source in one go, so a 30-slot chest fills in one or two trips. There's no sustained traffic in this setup, so a stall that needs many trips or long play would not show.
- Report dates: the "delivering to storage" halted cart is Dec 2021 (1.19), and a developer said 1.2.1.0 fixed that thread. The "stops without unloading" post is Feb 2022, before 1.2.39 (Mar 2022), so it may be fixed. After 1.2.39 there are only one-line claims from 2025 with no details ("freeze after several reboots", "get stuck and cannot be removed").

Testing notes:
- A new storage has an empty filter and refuses everything ("No Filter!"), until Edit Filter. Its panel checkboxes were all on.
- Bits 15-16 of a tile are the room layer, and `is_valid_pattern` refuses a room on non-zero. The whole main hall (about x 504-597, y 994-999) reads 2, so **a Stone Chest can't be placed there** ("No suitable spot"). Clearing the bits by save edit let it be placed. Why the hall reads 2 was not traced; it may relate to the "invisible no-build zones" in BUGS B6.
- The first autosave comes about 150 s after play, then every 30 s. Two chain runs read a stale `lastsave` because of this. After a load, input can be lost for over 20 s, so check the log for `set_game_speed_play`. `saveinspect`'s parent is not the holder: count u16 owner ids in `inventory_system/data.bin` instead.

## Rail stock and upward digging (B7), 2026-11-08, copies of savegame32, all mods + `_test_quiet` (+ `_test_fed` for digging)
- **Stock.** `_test_rails` with `HMOD_RAILS_PAID=1`: Track Sections unlocked at the Small Foundry and free except fuel. One
  craft gives 5 (spawned as `CLS_RAIL_TRACK`), so 21 crafts made 105 in about 6 minutes of log time. One Railway order on the
  hall floor (log `build` at 15:45) was built at 16:12 (`spawn mech/railway`). So a piece is built from stock without trouble.
  The report (S0/3887227420039649316, Oct 2023) had many orders, "some build, most take forever", blue icons, and a fix by
  dumping the stored rails on the floor.
- **Many orders.** 16 Railways along the hall floor, 4 tiles apart, with 100 free tracks: all built, each 20-60 s after
  placement. The foundry panel's inventory held 1 item, and the autosave had 89 tracks held without a claim and none loose,
  so they were in storage. Then `HMOD_RAILS_PAID=real` (the real recipe: 2 ingots and 3 granite slabs, output 5 carrying
  the metal): 25 tracks, 16 orders, 6 built within 3 minutes. The other 10 were in the ground below the cave entrance floor,
  not the hall (the screenshot was a stale frame). The game added dig orders for their tiles (pickaxe squares) that no dwarf
  could reach, and each piece had a red no-path marker and an "x1" track already delivered. So stock with metal is used
  too, and pieces placed in rock wait for their digging.
- Placing by input: run `place.sh`-style loops (pick the tool with V and a click, wait 5 s, click the spot, check the log
  for `build`, retry once). Escape pauses the game and opens the menu when no tool is active, so don't use it between
  placements. An order icon covers about 3 tiles, so a click 2 tiles away cancels the neighbour: space pieces 4 tiles.
  Screenshots can be minutes stale, so check where orders landed. Holder tracking from saves failed: held items' family
  parent is `logic/biome_region`, and the inventory_system layout was not worked out.
- **Upward digging.** Dig orders written into `map/map.bin` above a pocket at x 521-524, y 999-1002 (beside the Great Hall).
  A 1-wide column x 522, y 1002-1011: (522, 1002) dug within 3 minutes, the rest left. A 3x7 block x 521-523, y 1002-1008: row
  1002 and (523, 1003) dug, the rest left, with no dwarf near it afterwards. Every dug tile was in reach of a standing spot;
  the rest were not. `get_next_dig_pos` 0x1803d1ef0 takes a stance reach mask (bit dx - 5*dy + 17) and returns the first
  offset in the table (highest first) whose tile has dig status 0x4000, so it never picks a tile outside the mask. Report
  S0/3781371514574012810 (Feb 2023, no replies): a dwarf "stuck" removing tiles with "no success", fixed by ordering closer
  tiles first. Not reproduced. Untested: digging from rail positions, a Handcar or a scaffold, where the stance mask may differ.

## Model
- **The vehicles are ordinary entities, and only one kind takes dwarves.** [V] `mech/cart_passenger` = "Handcar" (tag
  CART_PASSENGER), `mech/cart_hauling` = "Cart" (tag CART_HAULING, inventory 0x28, HAULER_COMP, job worker PROF_HAULER).
  Rail pieces are plain gamepaths: `mech/elevator_railway[_big]`, `railway[_big|_*_incline]`, and `elevator_station`
  (name "Rail Station").
- **Recipes** (`recipe_rooms_cdb.bin`, dependencies at +2440): MECH_PLATFORM ("Elevator Platform"), MECH_CART and
  MECH_RAILWAY_STATION depend on BUILDING_NONE, so they never unlock [V]. So **the platform in the UI text exists as an
  entity and a recipe but is disabled**, and the Handcar replaces it. BUILDING_ELEVATOR (`entity/building/elevator`, the
  only thing with a real platform model) is in no recipe file [V]. `elevator_system_enqueue/unqueue/can_enter/go/exit`
  have no direct callers in game.x86_64.dll [V, rel32/lea scan]. So `elevator_system` is dead code for this feature [I];
  the working elevator is station_system.
- Queries (`database/navgraph_query/navgraph_query.bin`): `rail` and `elevator` differ only by name: search edge type 6,
  cost 1.0, node type 2 [V]. Handcar and Cart both use `rail`; only the disabled platform uses `elevator`.
- Graph (mainstate::mainstate 0x18029d02d..0x18029d4e9) [V]: node tags spawn, exit, exitmulti, mid, interact, lock,
  rail, elevator, station, queue, platform, owexit, owcave, owmid. Edge type 6 for rail and elevator, 1 for the others.
  Node data: station 1 (bit 0x100 in the node word), lock 8, interact 4, spawn 2. A path's edge type comes from its
  **newly created** endpoint, default 1 (0x180321329, 0x180321609..0x18032161c, branch 0x1803214ab) [V], which makes
  rail0_station0 and station0_rail1 both type 6 and the exit paths type 1.
- Weld (`gamepath_system::add_nodes_and_edges`, find_weld_node logic 0x180325e60) [V]: only same-type nodes of another
  entity: rail to rail, elevator to elevator, mid to mid, owexit, owmid. Limit 3276 raw, compared to a summed 16.16
  squared distance, so about 0.22 tile [I for the square root]. No error when nothing welds [I, no check seen].
- Model paths, from `all.gamemodelblob` (0xdd models x 0xc5c90, then 560 gamepaths x 0x1c8, then vec3 samples) [V]:
  ```
  elevator_railway      elevator0 (0,0)  elevator1 (0,1)          big: (0,-2) to (0,2)
  railway               rail0 (-.5,0)    rail1 (.5,0)             big: (-2,0) to (2,0)
  elevator_station      station0 (0,0); elevator0 (0,4); elevator1 (0,0), zero length;
                        rail0 (-2,0); rail1 (2,0); exit0 (-1.5,.2,z3); exit1 (1.5,.2,z3)
  ```
  So a Rail Station joins horizontal and vertical rails. Horizontal rail never welds directly to vertical rail [V].

### station_system (`ecs+0x40`)
[V] +0x350 stations (0x18: u16 entity, u32 station node +4, vehicle_cost array +8/+0x10; vehicle_cost 0x10 {u16 vehicle,
i64 cost +8}). +0x360 vehicles (0x30: last anim +0, u16 entity +8, query def +0x10, u16 query +0x18, **u8 passenger
+0x1a**, queue ptr +0x1b, count +0x23, cap +0x27; packed). Queue entry 0x20: u16 rider +0, target graph_position +8.
+0x370 pending gamepath entities.
- A vehicle is created in new_navgraph_query_callback 0x18035e340 for a query named `station` (NAVGRAPH_QUERY_COMP).
  passenger = has tag CART_PASSENGER (0x18035e3b9..0x18035e41a) [V]. Nothing "assigns" a vehicle to a line: its line is
  whatever its Dijkstra over edge type 6 reaches [V].
- A station is any gamepath entity with a node with data bit 0x100 (add_stations 0x180362850, from
  finalize 0x18035f050 and EP_LOAD) [V]. An entity with no station node at that moment is dropped from the list for good.
- `station_system_update` 0x18035f070, per vehicle [V]:
  1. Position invalid, or last edge type != query type (0x18035f1f2, 0x18035f203): snap to the nearest edge of that type
     in the 4 nearest 16x16 blocks (0x18035fe51..0x360799). No movement that tick. No rail in range: stays where it is,
     with no gravity, which is the floating cart.
  2. Target = **first queue entry with a reachable node** (0x18035f320..0x18035f372). Entries are never popped here.
  3. None reachable: a passenger vehicle goes to the cheapest reachable station (0x18035f3ba..); a Cart simply stops
     (0x18035f37d `cmp [+0x1a],0; je`).
  4. Vehicles do not check each other, so they can stack [V, no such test in the function].
  5. End of tick (0x1803608b2..0x360b7e): vehicle_cost of every station is cleared and refilled from **passenger**
     vehicles only (0x1803608f0).
- node_cbck 0x1802ac310, for every non-vehicle query [V]: a station node entered by a non-rail edge costs -1 (impassable)
  when calc_best_vehicle finds nothing (0x1802ac381..0x1802ac392), otherwise vehicle cost / 10. Leaving by rail costs 0.
- are_positions_accessible_to_vehicle 0x18035d9b0 tests **all** vehicles, Carts included (no +0x1a test) [V]. It decides
  which rail interaction positions exist (interaction_system::update_comp_rail_positions 0x18038af50).

### Save and load
- station_system/data.bin holds only the station entity list (format_1::init_from_system 0x180363d00 reads +0x350;
  version 2 header; 16 bytes in a colony with no stations) [V]. **Vehicles and queues are not saved** [V]. Vehicles come
  back through query restore in EP_LOAD_AFTER_ALL (0x1800f3214) [I for the callback firing there]; queues start empty.
- Already known (stuck_dwarves.md): graph positions are not saved and re-snap, locomotion flags reset, movement
  behaviours are not restored. No EP_SAVE/EP_LOAD for ai_behavior_system in the symbols of the modules dumped [I].
- Family links (dwarf child of cart) have save passes in entity.dll [V], so a rider stays in the cart across a load.
- So after a reload: empty queues, riders replanned, and a rider's wait node re-enters with a parent and re-enqueues to
  its cart (0x1804e4ae5, 0x1804e4c3a). **Every queue-based stall below therefore clears on reload** [I, follows from the
  above]. This is the best code-based reading of "save and reload fixes it".
- Ruled out: the saved edge-type remap (0x1801075xx: 4->5, 5->6, 6->4) rotating per cycle. The save path does a table
  lookup (init_from_system 0x18010c4c0, `cmp ecx,[rbx+4*rax+0x60]`), so it looks inverted on save [I, not fully traced].
  Also ruled out: arrival mismatch (is_same_pos 0x18014a7c0 matches the inline test in update [V]) and missed graph
  additions (queries go dirty when an added edge touches a reached node, 0x1800f4d52..0x1800f4df4 [V]).

## Report 1: "no platform, dwarves don't use it"
Confidence: high for "dwarves never use it without a Handcar"; the "order of building" claim has no code support.
- No platform can be built [V, recipe above]. Dwarves can only enter a station when a **Handcar** reaches it [V, node_cbck
  and passenger-only vehicle_cost]. A **Cart never carries dwarves**, never appears in station costs, and does not move
  unless it has its own haul job [V]. That fits "it just stays there and dwarves don't use it" if the player built
  Carts [I; the thread does not say which].
- "Handcars moved vertically, carts didn't" is the same fact [V].
- "Put carts on the elevator rail, not horizontal": a vehicle reaches only what connects through Rail Stations [V]. A
  horizontal piece beside a shaft is not connected, and welding needs alignment within about 0.22 tile [V/I].
- "Buggy if carts are placed first": **I found no order dependence.** Snap retries every tick, and queries refresh on
  added edges [V]. One player said a reload "suddenly" fixed it. I have no branch for that. Candidate: a station entity
  whose nodes were not ready at finalize is lost until reload (0x180362937). gamepath is created before station in
  mainstate, so this should not happen [I].
- "Moved 3 tiles and froze": no specific branch found. A misaligned piece gives no error and splits the graph [I].

## Report 2: stuck carts, "reload fixes it"
Confidence: medium for riders; **the cargo cart report is not explained**.
Four no-timeout states, all [V]:
- **A. Entry left behind by a dead or finished rider.** "Arrived but not at a station" returns success with no dequeue
  (0x1804e5084..0x1804e510d), and exit skips the dequeue when arrived (0x1804e4deb). That keeps a Handcar parked under a
  dwarf working on a rail position [I, intent]. `station_system::destroy_entities` 0x180362d20 removes only stations and
  vehicles, never rider entries. Exit does run for destroyed dwarves (ai_behavior_system_remove_destroyed_entities,
  0x180357302) but has this same skip. So a dwarf who dies, or later does not move, while holding such an entry leaves it
  at the point the vehicle serves first. **The Handcar parks there for good and queued riders wait forever.** The u16 id
  can be reused later.
- **B. Abort in the arrival window.** Same exit skip: a BT aborted while the vehicle is at the rider's station leaves an
  entry [V]. Short window unless a Handcar is already parked there [I].
- **C. Rider in a cart with no usable target.** Not arrived with a parent returns running forever; the 256-tick re-enqueue
  is for riders with no parent (0x1804e56f9..0x1804e57d7). If the target's nodes were removed the entry is silently erased
  (station_system_recycle_nodes_edges 0x18035d500), then update returns fail **without detaching** (0x1804e506f ->
  0x1804e5004). The dwarf stays seated until a later wait node. This fits "dwarves sat in carts at a junction" [I].
- **D. Waiting rider.** Re-enqueues every 256 ticks and returns running; no give-up [V]. Selection (0x18035c21e) takes any
  strictly shorter queue regardless of cost, and a switch puts him at the tail, so with several Handcars he can hop [I].
- Cart's own move: btn_move_to_update returns running while not arrived and never checks out_vehicle, so a vanished own
  entry waits forever (0x18048f1af) [V]. In bt_haul_update (0x1804f0ba3 -> 0x1804f8434) the same wait exists, but its
  target refresh (0x1804f0a70) re-enqueues when the position changes, which removal normally causes [V/I].
- **Not determined:** why a loaded Cart stops at a station or beside its target without unloading. bt_haul_update is about
  40 KB and I read only its vehicle branches. Arrival looks consistent. The fact that a reload clears it only says the
  state is runtime. "Can't be unloaded manually" and "20+ carts on elevator rails" have no branch either.
- "Freeze after several save/reload cycles": not determined.
- **`mods/cart_timeout` (2026-11-22).** A Cart's behaviour tree is BT_CART, an empty node (bt_cart_enter/update just return); its
  deliveries are job-broker haul jobs that run the dwarves' bt_haul (0x1804ef230 update), which calls
  station_system_is_vehicle(mainstate+0x2330, entity) and, for a vehicle, station_system_enqueue_vehicle (0x1804f0aff) instead of
  movement_system_move_to. enqueue_vehicle first dequeues the vehicle's old entry; bt_haul_exit never dequeues it.
  station_system_dequeue(sys, rider) removes a rider's entry from every vehicle queue, and a Cart is its own rider. The mod hooks
  the update's entry and, for vehicles only, returns BT_FAILURE after LIMIT game seconds without a position change, after
  dequeuing. In SouthXanforge a hauling Cart moved on every update; it stood still only between jobs, when the update doesn't run.

## Report 3: crashes
- on_event_teardown 0x18035e980 is **wrong for two or more riders** [V]. The loop variable [rsp+0xe0] is never advanced
  (0x18035eb3a..0x18035eb4a). family lists are circular (entity.dll set_relation 0x18002bbd0: detach links a node to
  itself), so the second pass sees next == self and exits. **Only the first child is detached.** Then the queue count is
  zeroed. family_component_system_remove_destroyed_entities reaches entity_entity_manager_destroy_entities (0x18002e1b9)
  after a tree walk, so the other riders are probably destroyed with the cart [I, outline only]. Whether that crashes is
  not determined. Fits "crash when a person is on it and it is deconstructed" as a candidate only.
- Unchecked pointer: `movzx edx,[r8]` at 0x18035e9cc with r8 = 0 when the event has no entity property (0x18035e9bc)
  [V]. The one sender I know (notes: bt evaluate_wants_to_produce) reads `teardownee`, so reaching it needs a missing
  property [I].
- A floating cart in the update loop: the snap path has bounds checks and an 0x800 cap (0x360062) [V]. **I found no crash
  in station_system for a floating cart.** destroy_entities looks safe for it. Those reports have no stack in 1.x.
- The stored stacks are from 0.1.3.x: assert `n0_is_station != n1_is_station` in the wait node's enter, and
  station_system_enqueue under recycle. The release build has no such assert: enter uses node1 if node0 is not a station
  (0x1804e4ce0..0x1804e4ce9), which can give a non-station target and so state A [I].

## Report 4: "can't reach the next section when building down"
Confidence: medium, [I] as an explanation.
- Positions: footprint neighbours, with tile nodes only where there is support, and gamepath points within 1 tile
  (scaffold_removal.md, 4 nearest blocks checked 0x1803659c2 [V]). Rail positions exist only if some vehicle reaches them
  [V]. A worker reaches a rail point only through a station with a Handcar [V].
- So the first section below a Rail Station is built from its walkable deck, and the next has only rail positions below
  the deck [I]. That needs a connected Handcar (a Cart is enough to make the position exist, but not to carry the
  builder). It would make the failure depend on what is connected, which fits "sporadic" [I].
- Exits connect to tiles through gamepath_connect (0x18047f4ab, not read), so a blocked exit tile could explain "a plant
  or object in the way" [I, unverified].

## Report 5: stock not used, dig order
- Rail pieces take CLS_RAIL_TRACK (1 or 2; station 4 plus parts and slabs) by recipe BUILDING_SPOT, PROF_BUILDER [V], and
  a separate producer per piece [V, scaffold_removal.md]. Sources and worker reach follow sensor_craft and haul
  (production_stall.md). **I did not find why stored rails were ignored** while ground items were used. Blue icon meaning:
  not read. A piece with no reachable position is UNABLE by has_path, same text as other failures [V, earlier note].
- Dig: sensor_dig reserves foundations (tile_reserver::reserve_tiles_for_pos 0x1803ebfb0, is_foundation_needed 0x1803ea9e0,
  map order state 0x6000; text "This tile is reserved for later. Dwarves need it to reach higher."). get_next_dig_pos
  0x1803d1ef0 scans offsets from 0x180554d00 in order [V]: (0,2) (-1,2) (-1,3) (1,2) (1,3) (0,3) (-1,1) (-1,0) (1,1) (1,0)
  (-2,1) (-2,0) (2,1) (2,0) (-1,-1) (1,-1) (0,-1) (0,0) (0,1), so **highest first**, limited by a stance mask. That
  supports "assumes digging from below/downward" but **the stuck branch itself is not identified**. update_block and
  update_dig_sites (19 KB) not read.

## Candidate patches (none built). `.hmod` free: 0x640-0xc00 per CLAUDE.md (check `_test_ow_wave` at 0x600).
1. **rider_cleanup** (state A). 0x18035f060 `48 8b 49 40 e9 b7 3c 00 00` -> `e9 <cave>` + nops. Cave: save rcx/rdx/r8, for
   each u16 id call station_system_dequeue 0x18035cd80 (rcx = ecs, dx = id), restore, `mov rcx,[rcx+0x40]`, jmp 0x180362d20.
   Dequeue is already a no-op for non-riders [V]. Low risk.
2. **exit_dequeue** (state B, partly A). 0x1804e4deb `80 bc 24 98 10 00 00 00 0f 85 b4 00 00 00`: send the `jne` to a cave:
   if target_is_station [rsp+0x10a0] goes to 0x1804e4df9 (dequeue). Otherwise get family info (slot 0x180599070, rcx = r14),
   parent = [rax+2*(5*rdi)]; no parent goes to 0x1804e4df9, parent goes to 0x1804e4ead. Keeps the parked-under-worker case.
3. **teardown_riders** (report 3). 0x18035eb3a `0f b7 94 24 e0 00 00 00 66 3b fa 74 05 66 85 d2 75 94` -> `e9 <cave>` +
   nops. Cave: movzx edx,[rsp+0xe0]; cmp di,dx; je 0x18035eb4c; mov [rsp+0xe0],di; movzx edx,di; test dx,dx; jne 0x18035eae0;
   jmp 0x18035eb4c. Clear bug, small change.
4. **move_to_no_entry**. 0x18048f1af `80 7d 6f 00 74 8b` -> `e9 <cave> 90`. Cave: cmp word [rbp-0x55],0; je 0x18048f1cb
   (fail); cmp byte [rbp+0x6f],0; je 0x18048f140; jmp 0x18048f1b5. Effect on the cart's BT after failure is untested.
5. **seated_detach** (state C). 0x1804e506f `74 93` (rel8; the detach path 0x1804e4fdb is out of rel8 range, so it needs a
   cave and more room). The dwarf would fall from a shaft: needs a design decision.
6. **Text only**: make the Rail Station, Handcar and Cart descriptions say Handcars carry dwarves and connections need
   Rail Stations; MECH_PLATFORM stays off (it lacks the CART_PASSENGER tag, so enabling it would not give dwarves a ride [V]).
Not proposed: a vehicle watchdog on stale entries. There is no spare field for a timer, so it needs a design.

## How to test (use `_test_rails`, `_test_quiet`, a colony copy; Steam achievements as usual)
- Logging: every station_system and wait-node message is gated by `[0x1805a77f0]+0xa` (haul: +8), channel "RAIL" [V].
  Where that byte is set, and whether the release log writes it, is unknown. Forcing it would make the tests far easier.
- R1: stations + rail + Cart only, then + Handcar: expect no dwarf use, then use. Misalign a rail by 1 tile: expect no use, no error.
- A/1: Handcar line, two riders queued, have a dwarf working on a rail position (build a piece from the Handcar), then
  kill or remove him (save edit). Without the patch the Handcar parks and others wait; a reload clears it.
- 3: two dwarves seated on one Handcar, tear it down. Without the patch expect one to vanish or a crash; with it both freed.
- R4: long shaft with and without a Handcar connected, down past a second section: check ORDER_NO_PATH on each.
- Cargo: reproduce the stall, then inspect the cart's order and inventory before reloading. Static reading did not settle it.

## Could not determine
Why a Cart stops without unloading; "freeze after several reloads"; floating-cart teardown crash; "station built on the same
x as a rider" crash (no 1.x stack); why stored rails were ignored; the blue icon; the stuck dwarf in upward digging; how often
states A to D happen in play.

## Handcars through monster lairs (B14, 2026-11-09, copies of savegame32). Fixed by `mods/ride_then_fight`
Report S1/3193621324037871655 (Mar 2022): rail through dens, riders "bounce back and forth", hit but never killing.
- **Mechanism [V in logs].** A seated rider within reach of an enemy picks ACTION_COMBAT_MELEE (rank 6, over his job at 4).
  `bt_do_weapon_attack_enter` calls movement_system_set_stopped, which exits his BT_WAIT_FOR_VEHICLE with reason stop and
  dequeues him, but he stays a family child of the Handcar. With his entry gone the Handcar serves the others or heads for the
  cheapest station, so the swing ends up to 19 tiles from where it started (`playing anim: attack` at 644.6, `finished` at
  625.7) and misses. When the BT ends, BT_MOVE_TO_JOB or BT_SLEEP_IN_ROOM re-enqueues a target on the other side and the
  Handcar comes back past the enemy. Seated riders' world positions are right (local array reads 0,0, world array = the cart's
  position), so aim is not the problem; the moving seat is.
- `bt_do_weapon_attack_update` 0x18048ade0 waits while movement_system_is_active (comp +0x70 behaviour set); the BT is
  BT_COMBAT_MELEE_WEAPON = sequence(equip_best_items, do_weapon_attack). Movement is locked only by stairs, climb and jumps.
- Fix: melee consideration (0x1803aa540) returns 0 when the combateer has a family parent (records from import slot
  0x180599070 called with gamestate+0xe18, 10 bytes per entity, u16 parent first). Dwarves on foot have parent 0 in saves.
  The rider then rides on; ACTION_COMBAT_APPROACH re-enqueues him to a station ("switching to new queued target") and he walks back.
- Test setup: corridor carved x 572-678, y 973-979 (floor y 972), Rail Stations at 590, 622, 670, Long Railways every 4 tiles
  between, Handcar 5322, Killer Plant 2849 moved to (646, 973), dig orders at x 679-681. An enemy within 20 tiles of a station
  is targeted before riders leave it (plant at 606: the rider got off and walked), and a moved goblin walks into the colony.
  Without the fix: 44 and 104 seated swings, plant alive 162 and 231 game s. With it: 0 seated swings, plant dead 2.8 game s
  after its first attack, 6 rides afterwards, no exceptions. Rider health was not read (statusbar save format not decoded).
- Placing pieces: Rail Station from V at (757, 750) on screen, Long Railway (941, 610), Handcar (1216, 610); after the
  foundry double-click and -14/+6 zoom, px = 1150 + 17.2 (x - 622) at screen y 508 for floor y 973; one more scroll out
  gives 12.7 px per tile. A new order's tile is in memory: the CraftOrder entity named in `Spawned order ent N` sits in the
  position array (found by two buildings' known positions). Saves are kept in `~/.local/share/hammerting-tools/test-saves/`
  (`hcar_line2` has the 3-station line, `hcar_t3` adds the plant and dig orders).

## Crowding at the top station (2026-11-12, user's colony savegame68, `_test_quiet` + `_test_drop_log`)
The user saw dwarves "stuck on one another at the top of the elevator": two Handcars serve a network from y 958 down
to y 477 (shafts at x 501, 533, 569, 724) for 13 dwarves. Waiting dwarves all stand on the station node in the rail
plane (z 1), so they overlap. Three runs from copies of the save, logs with GAMESTATE-RAIL/-MOVE on:
- **No deadlock.** Every wait ended; the longest at the top station (node 2786) were 635-1116 ticks. Reloading
  clears the queues (they aren't saved), and the dwarves left at once. A monitor of Handcar positions from memory
  plus queues rebuilt from the log found neither Handcar ever standing still with riders queued: both run nonstop,
  about 25 game seconds from the middle levels to the top. It is a capacity limit: a Handcar drives to its first
  queue entry and takes only riders queued on it.
- **Defect: waiting riders chase the nearest Handcar.** station_system_enqueue (re-run every 256 ticks for a waiting
  rider) counts riders ahead per vehicle (his index if queued on it, else its queue length) but at
  0x18035c21e..0x18035c22d takes any vehicle whose count is not smaller if its cost is lower. A switch dequeues him
  and appends him at the back, and the Handcar he left retargets. Seen in the log: 6253, 3124 and 4447 switched
  2338 -> 6960 -> 2338 within 250-500 ticks. `mods/rail_queue_keep` makes fewer-ahead win, a tie keep his vehicle,
  then cost. Over the same 5847 ticks from the same save: switches 41 -> 29, total wait ticks 28700 -> 31689,
  rides 120 -> 121. So it removes the chasing without a measurable change in waiting in one 10-minute run each.
  (A first count of "aborted" waits matched `should_stop: 0`; only 18 waits really ended on `reason: stop`.)
- Play advice: one Handcar per busy section, or more Handcars on the shared network (sheets and machine parts).
