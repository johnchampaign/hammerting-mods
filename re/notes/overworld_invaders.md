# Overworld invaders (BUGS.md A8), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 208 enemy_wave_system, 278 its .ecs, 262 node_enemy_wave, 161
action_enemy_wave, 242 node_overworld_attack, 243 node_overworld_faction, 249 node_move_overworld,
248 node_move_gamepath, 46/151 overworld_location, 149 overworld_map.ecs (plus 16, 150, 188, 199
already present). Bytes are from the pristine DLL (`game.x86_64.dll.hmod-orig`); no site below
overlaps an installed mod. Static analysis and save inspection, except the test section below. **The freeze was not
reproduced.** Each claim is marked [V] read in code or data, or [I] inferred.

Reports (fetched, both by the same poster, Apr and Jun 2025): invaders from the outside world
"freeze on the world map near the entrance", "an infinite number", avoided by turning invasions
off at map generation. No save, screenshot or version number. "World map" is ambiguous: it can
mean the overworld hex map or the cave map.

## In-game test (2026-11-02, copies of the user's colony). Read this first.
Still not reproduced: no invader froze in any test. spawn0 is neither confirmed nor refuted.

**Discarded result.** The first version of `mods/_test_ow_wave` guarded itself with a 64-bit compare
on +0x278. That field is a u32 count with the u32 capacity at +0x27c, so the guard could skip the
spawn. The waves it appeared to produce are unreliable evidence. That includes the slimes seen on
tiles (607.5, 1011) and (630.5, 978), probably lair waves, and one standing still for 28 game seconds.
Do not use them for or against spawn0.

Corrected test build: `enemy_wave_system_launch_overworld_attack` called `HMOD_TEST_BURST` times each
time the wave timer is due (a small stand-in argument supplies the system at +0x40). Logs: 46 ticks a
second at top speed, about 4.6x.
- **Forcing a war by save edit does not work.** Pairs (317,327) and (317,328) set to WAR at
  t = 8197 were at peace in the autosave at t = 8942, with no army seen. So the real army, march and
  `attack_target` path was never exercised; only what `launch` does from there on.
- **One attack per timer, in two runs, with and without `fall_when_idle`:** 5 timer firings with
  attack and lair spawns mixed in the log. Every creature died, mostly 8-25 game seconds after
  spawning, and none was left in the member list. That is too short for the 27-game-second autosave
  spacing to record where attack members were placed, so spawn0 was not observed. What killed them so
  fast is not established. This colony has fighters near the entrance, and a colony where nobody can
  reach them could still differ.
- **14 attacks per timer, no cap:** 35 attack members plus 5 lair rats in one tick, difficulty up by
  42, and all six dwarves dead within about 14 real seconds (Defeat screen). No achievement.
- **14 attacks per timer, `invader_cap` at 24:** exactly 24 attack members, then none, plus 5 lair rats.
  After kills the next timers spawned 24 and 25 (the check is before each wave, so the last can
  overshoot; a large wave could overshoot by more). The colony was alive at 8:34, with 99 kills.
- **Not exercised:** the generic wave gate's reject path was not seen firing; its caller reads the
  return as success (0x180459e57) by code reading only. Reload with members in the list.
- Do not apply P1 on this evidence. P2 + P3 are built as `mods/invader_cap`.

## Short version
- There are three sources of cave invaders. All of them run the same AI, `BT_ENEMY_WAVE`. [V]
- Only the overworld attack spawns them at the entrance, on the door path's outer end. That node
  is 19.7 units behind the play plane. Every other source spawns on a tile. [V]
- Neither the overworld attack nor the generic wave has a cap or looks at living invaders. Only
  lair spawners clean up after themselves. [V] This fully explains "multiply without limit" if
  the invaders do not die.
- Why they would stop moving is **not established**. The leading explanation is that the spawn
  node is the fault, because it is the one thing unique to this path. [I]
- The user's colony has both options on, no army, no war and no invaders yet. **The war gate opens
  at t = 10800 s; the colony is at t = 8197.5 s.** [V]
- The attack seen in the test is a lair wave of 5 rats, not this bug. Those invaders walk, fight and
  die normally, which is evidence that the AI itself works for tile-spawned members. [I]

## The systems

### Options [V]
`scenario_settings` (`gamestate/defines.h`): `_enemy_waves_enabled`, then
`_overworld_war_on_mountainhome_enabled`, both defaulting to TRUE. Version < 4 saves inherit the second
from the first. New Game UI: `entity/ui/main_menu/scenario_options.entity` keys `ENEMY_WAVES` and
`OVERWORLD_ATTACKS_ON_MOUNTAINHOME`, parsed by the `savegame_scenario_new` command (0x180300c89,
0x180300cd9).
- In memory: gamestate+0x1220 (waves), +0x1221 (war).
- In a save: `gamestate/gamestate.bin` offset 0x15ac (waves), 0x15ad (war), 0x15ae u64 radius.
- +0x1220 is read once, in `enemy_wave_system_update` (0x18045924e). +0x1221 is read once, in
  `bt_overworld_faction_update` (0x18049f6ef).

### Source 1: lair spawners (cave rooms tagged LAIR) [V]
`enemy_wave_system` state: +0x260 targets (u16 list), +0x270 wave members (count +0x278), +0x280
spawner records (0x70 each), +0x290 spawner queue (count +0x298), +0x2a0 wave counter, +0x2a8 threshold
cache, +0x2b0 next check time. All saved, in that order.
- `enemy_wave_system_update` 0x1804591e0: `update_query`, then the +0x1220 gate, then if now >= +0x2b0
  `update_spawners` 0x180457f50.
- On success, +0x2b0 = now + rand(0.75 X, 1.25 X), X = i32 16.16 at 0x180597104 = 540 s; difficulty adds
  +120/+60/-60/-120 s (0x1804592bc..0x18045946d).
- `update_spawners` takes the head of the queue and calls `try_spawner` 0x1804568c0. Size +0x58 grows
  with time: +1 after 2700 s, +1 if discovered (+0x49), +1 after 10800 s, +1 after 36000 s, +1 if +0x4a,
  +1 above 7 (0x180458686..0x1804586f2).
- **Before re-arming it kills the spawner's previous members**: STATUSBAR_HEALTH -10000 on each entry of
  the record's own list +0x5c (`movl $0xd8f00000,%r9d` at 0x180458b49). So one lair has at most one wave
  alive. The only self-limiting source.

### Source 2: generic wave [V]
Same update: when the mountainhome's STATUSBAR_ENEMY_WAVE reaches its threshold,
`try_spawn_wave` 0x1804564e0 (tile search), `find_generic_wave_record` 0x1804547b0,
`spawn_wave_from_record` 0x180454e50. It sets KV_ENEMY_WAVE on each member, moves it to a chosen tile
(0x180454fdf) and appends to +0x270. No check of +0x278. Success: +0x2a0 += 1 (0x18045a06d).

### Source 3: overworld attack (the QoL4 option)
1. **War.** `bt_overworld_faction_update` (one 198 KB function, wants_war block at 0x18049f6ae):
   - `now >= 0x2a300000` (10800 s = 3 game hours) unless a debug flag is set (0x18049f6bc). [V]
   - If the other party is the mountainhome and gamestate+0x1221 is 0, skip (0x18049f6e8..0x18049f6f7). [V]
   - Then opinion checks ("wants_war: Fac %hu vs %hu ..."). [V]
2. **Army.** Same function 0x1804cb227..0x1804cb4a9: a faction at war with no OVERWORLD_UNIT of its own
   and >= 300 MANPOWER and >= 300 MIGHT pays 300 of each and calls `overworld_map_system_create_unit`
   ("OWUNIT_ARMY", record `database/overworld_unit/owunit_cdb.bin`, AI AU_OVERWORLD_ARMY). At peace, its
   army is destroyed. **So at most one army per faction, nine in this world.** [V]
3. **March.** `bt_overworld_attack_update` 0x18049b620, one node, no states:
   - `faction_system_get_enemies` within 100.0 (0x640000), `are_enemies` = RELATION_FACTION at war.
   - Enemy within 0.6: an ARMY, or a HEX for which `can_attack_hex` 0x18049a860 is true
     (KV_STATUSBAR_OVERWORLD_FORTIFICATION > 0) -> `attack_target`.
   - Otherwise nearest such target by the `overworld_movement` query, `movement_system_move_to`.
   - No target: walk to the enemy capital and `sue_for_peace` 0x18049a540 within 0.6; none reachable:
     `movement_system_set_stopped` (0x18049c13a) and stand. No timeout. [V]
4. **Crossing.** `attack_target` 0x18049a900 runs on whole seconds with now_s % 3 == entity % 3
   (`now` is frame x 0.1 s, so whole seconds do occur [V, from saves]). If the target has KV_LOCATION and
   its faction entity is the mountainhome (0x18049abb1..0x18049abbd): `enemy_wave_system_launch_overworld_attack`
   0x180451ff0, then the army is destroyed (0x18049abde). The fortification is not touched. [V]
5. **Spawn.** `launch`: +0x2a0 += 3 (0x180452002), `find_generic_wave_record`,
   `spawn_overworld_wave_from_record` 0x180455360:
   - Entrance entity = KV_ENTRANCE_ENTITIES on the mountainhome. pos = its world position.
   - `spawn_loot` with the record's tables (up to 256 entities), KV_ENEMY_WAVE on each.
   - `gamepath_system_get_entity_gamepath_nodes` on the entrance; nodes with data bit 0x200
     (`NODE_IS_SPAWN`, test at 0x1804555e4) are collected; **if any, pos = the first one's position**
     (0x180455ad4..0x180455b0e).
   - `fixed_transform_system_set_world_position` on each (0x180455b47), then append to +0x270. No check
     of +0x278.

Nothing on the overworld "transitions": the army dies and new creatures appear in the cave. [V]

### Where that is [V]
`all.gamemodelblob`, paths of `model/building/entrance_cave.model` (local coordinates):
`spawn0` (5.342, 2.789, -19.729) -> `mid0` (0.043, 0.166, -2.364) -> `exitmulti0/1/2` ((0,0,0), (-2.519,0,0),
(2.486,0,0)). In this colony the entrance is at (549.5, 994, 0), so invaders are placed at about
(554.84, 996.79, -19.73). Walking creatures and dwarves in the save have z between -6 and 3. The node is
the far end of the door path, out of the play plane and above the floor.

### Wave AI [V]
All wave creatures (slime, rat, skeleton, goblin, imp variants; `enemy_spawn_cdb.bin` loot tables) are
`SENTIENT_MOVING_ENEMY` {ACTION_DEAD, ACTION_IDLE, ACTION_ENEMY_WAVE} with `jumping_creature_movement`.
ACTION_ENEMY_WAVE: rank 4, score 1.0 while KV_ENEMY_WAVE != 0, tree BT_ENEMY_WAVE. Combat
(`combat_system_update` 0x1804282d0, radius 20) is a separate higher-rank action.

`bt_enemy_wave_update` 0x1804ea300 always returns RUNNING (0x1804ea84b). No timeout, no exit, no failure.
Every 5 s:
- Current move target: cleared if stopped or arrived, otherwise waits for the 5 s (0x1804ea625..0x1804ea639).
- **gp invalid: nothing** (0x1804ea65e).
- Reads the `wave_spawning` query (`enemy_wave_system_get_query`): walk 1, climb 2, jump 4, drop 8, room jump
  10, node types TILE + GAMEPATH, max cost 10000, inverted. **Node not reached: nothing** (0x1804ea73f..0x1804ea744).
- **Cost < 5.0: nothing, "arrived"** (0x1804ea785).
- Otherwise walks parent edges up to cost 150 and `movement_system_move_to` (0x1804ea82d); the result is
  ignored.

Query seeds (`update_query` 0x180458e00): the graph position of each +0x260 target (PLAYER_BASE tag, from
`create_components` 0x180452fd9..) **with BUILDING_HEALTH > 0** (0x180458ffb), plus nodes up to two edges
away. In this save the entrance is in the list but has no KV_STATUSBAR_BUILDING_HEALTH, so it is not a seed.
I first suspected "arrived at the entrance". That is refuted. [V]

## Why the count grows [V]
- +0x278 is read only by the list code in `remove_destroyed_entities`, `spawn_wave_from_record` and
  `spawn_overworld_wave_from_record`. Neither the timers nor `launch` nor `create_unit` consult it.
  `TDTD_EVENT_ENEMY_WAVE_DEFEATED` (0x180454706) is the only consumer of "the list is empty", and it does
  not gate spawning.
- Invaders leave only by dying. Their +0x270 entry has no age and no cull, unlike lair lists (+0x5c).
- An attack also raises difficulty by 3 against 1 for a generic wave (+0x2a0), selecting larger wave
  records. So invaders that never die pile up, and each batch is stronger.
- The rate is bounded only by faction economy (300 + 300 per army) and marching time, times up to nine
  factions, plus the independent generic wave. Regeneration rates were not measured.

## Why they could freeze: ranked
1. **The spawn node (spawn0).** [I, the leading candidate] It is the only difference between this path and
   the two that work. The creature is teleported off the plane; its graph position should resolve through the
   default search list to the gamepath (nothing else lies within range 1.0 there; tile (554,996) is above
   the floor). From there it needs the door path, which creatures otherwise never use. `bt_move_gamepath_*`
   has no dwarf check and both queries allow GAMEPATH nodes, so **I found no line that blocks it**. Untested:
   whether the path's directional edges admit the inverted query, whether a wave creature's position resolves as
   expected, and whether the behaviour advances for a creature. The fall sensor does not rescue a creature on
   a gamepath (`stuck_dwarves.md`). Whether dwarves can reach or hit a creature that stays at z = -19.7 was not
   checked; if not, that is what would keep it alive.
2. **No seed reachable.** [V as a code path; I as a cause] All PLAYER_BASE buildings at 0 health, or the base
   not walkable from the door, leave the member idle indefinitely. It explains a frozen group but not why
   the reports link the bug to the option.
3. **Armies standing on the overworld.** [V as a code path] An army with no target stands still with no timeout.
   This matches "world map" literally, but at most nine armies can exist, so it does not match "infinite".
   It can only be part of the report.
4. **Entity pool / ~64K limit.** Not supported: the spawn is unguarded but no freeze follows from a full pool
   in anything I read.
5. **Paused sim.** Not supported: spawning and the AI run in the same sim update, and nothing pauses one alone.

## The user's colony (West Hirdness, `save-backup-2026-11-02/lastsave.2.save`) [V]
| Fact | Value |
|---|---|
| Waves / war option | 1 / 1 (offsets 0x15ac, 0x15ad) |
| Game time | 8197.5 s (frame 81975), war gate 10800 s, about 43 min away at normal speed |
| Faction relations | all 78 pairs PEACE, in every one of the 19 saves in the backup |
| OVERWORLD_UNIT entities | 0, in all 19 saves |
| Wave members (+0x270) / KV_ENEMY_WAVE keys | 0 / 0 |
| Mountainhome hex | entity 439, faction DWARF, fortification 1000, so attackable |
| Faction strength | every faction 500 MANPOWER, 500 MIGHT: can field an army at once |
| Opinion of the mountainhome | BARAZ 3, VENDAR 12, DEADWOODS 140, SYLVER 148, ... several low enough to be hostile [I] |
| ENEMY-tagged creatures | 27, in lairs and wandering; nearest big group x 416..457 at y 985, none at the entrance |
| Next check (+0x2b0) | 8519.9 s; queue head = `cave_room/rathole[36]` at (438, 985), discovered |

So the colony does not have the bug yet and has the preconditions for it. I expect wars to begin soon after
t = 10800 s. [I]

### The "under attack" alert in the test
Not the overworld system. `LB_ENT_ROOM_UNDER_ATTACK` is any TDTD_EVENT_DWARF_UNDER_ATTACK on a ROOM-tagged
target (`spawn/logic.bin`), with no link to the source of the attacker. [V]
Session logs: `2026-11-02_09-10-41` spawns five `rat_fat` at 15:51 and all five die at 16:16..16:24;
`2026-11-02_09-43-34` spawns five at 7:21, with a pause at 7:28. [V] The check is due 322 game seconds after
the load, and the queue head is the rathole, whose size is 4 + 1 (past 2700 s). [V] The cook house at (511,993)
is the western-most PLAYER_BASE building and so the nearest target to that rathole. [V] Hence: same
`enemy_wave_system` and `BT_ENEMY_WAVE`, lair source, normal behaviour. [I] The 7 s gap is short for 73 tiles;
the alert in that run may have had another attacker, or the game speed was raised. Not resolved.

## Patch candidates

### D1. Data only: turn war off in an existing save (recommended for the colony until tested)
`gamestate/gamestate.bin` byte 0x15ad 01 -> 00, through `tools/save.py` (`repack`). This is the workaround made
retroactive and it needs no DLL patch. Blocks new declarations against the mountainhome; there are none to
undo here. [V] Nothing else reads the flag. [V] I did not rule out quests or events declaring war by another
route. Loses the feature. It is not a fix, and enemy waves can stay on: nothing in the code ties the freeze to
them, although the reports' workaround disables both. For new games the checkbox already does the same, so a
mod flipping the UI default adds little; I did not work out where that default is stored.

There is **no data-only fix for the bug itself**: the spawn choice, cap and AI are code. The closest data edit
is removing `spawn` nodes from the 180 MB `all.gamemodelblob`, which would also affect any other user of the
node, so it is not proposed.

### P1. Spawn at the door exit, not the door's far end (1 byte)
`spawn_overworld_wave_from_record`, 0x180455ad2: `74 3e` (je) -> `eb 3e` (jmp). Skips the assignment of the spawn
node's position, so pos stays the entrance's world position, which equals `exitmulti0`, where dwarves
come out. The array is still freed at 0x180455b12 (registers there are valid on both paths).
Risks: all members stack on one spot at z = 0 (generic spawns also stack; separation not checked). Invaders now
appear inside the base at the door without warning, which is what the feature intended. If cause 1 is wrong this
changes nothing about the freeze, and costs nothing. Existing frozen invaders are not moved.

### P2. Cap the overworld attack (cave)
Skip the spawn while 24 or more wave members are alive. The army is still consumed. `.hmod` 0x540..0x556.
Site 0x180452002 (`add qword [rbx+0x2a0],3`): `48 83 83 a0 02 00 00 03` -> `e9 39 a5 1b 00 90 90 90`.
Cave 0x18060c540:
```
83 bb 78 02 00 00 18     cmp dword [rbx+0x278], 24
73 0d                    jae skip
48 83 83 a0 02 00 00 03  add qword [rbx+0x2a0], 3
e9 b4 5a e4 ff           jmp 0x18045200a
48 83 c4 20  5b  c3      skip: add rsp,0x20; pop rbx; ret
```
Decoded with llvm-mc; not run. Frozen invaders count toward the cap, so with P2 alone 24 frozen ones switch
overworld attacks off for good. That bounds the bug and is not a cure.

### P3. Cap the generic wave (cave, same cap)
`.hmod` 0x560..0x571. Site 0x180459e4b (`call spawn_wave_from_record`, rcx = system):
`e8 00 b0 ff ff` -> `e8 10 27 1b 00`. Cave 0x18060c560:
```
83 b9 78 02 00 00 18     cmp dword [rcx+0x278], 24
73 05                    jae fail
e9 e2 88 e4 ff           jmp 0x180454e50
31 c0  c3                fail: xor eax,eax; ret
```
A return of 0 takes the existing "failed" path at 0x180459f39, which is a smaller statusbar change and no +0x2a0
increment. Decoded with llvm-mc; not run. Only useful together with P2 or P4.

### P4. Timeout-like cull (not assembled)
In place of P2's `skip`: when the cap is hit, apply STATUSBAR_HEALTH -10000 to every +0x270 member through
`statusbar_system_modify_value` 0x1801bbe30 (`rcx = system+0x168`), the same way lairs do at 0x180458b34..0x180458b5a,
then carry on and spawn. It clears frozen invaders, which P2 does not. Needs about 60 cave bytes and a saved
register pair, and must copy the list, as deaths may mutate it. Risks: it also kills invaders in a real fight
(harmless when the cap is large), and loot and death effects fire at the door. A true per-invader timeout is not
minimal: the BT instance is 0x28 bytes (allocated at 0x1804ea170) with no spare field and is not saved.

**Recommendation:** after test T1, P1 + P2 + P3 if the invaders do freeze at spawn0, with P4 replacing P2's skip if
frozen ones must be cleared. Add a `cleanup` of existing ones by P4 only for saves that already have them.

## Test plan (copy of a save only)
Rules from CLAUDE.md apply: never touch `lastsave` or `autosave_<Colony>_*` without a backup, check the session log
for the user's own `--game-load` before closing a game. No victory is involved here, but keep Steam offline if unsure.

Force a war rather than wait for t = 10800 s. In a copy, in `relation_system/data.bin`, the FACTION pairs follow the
member list that starts `3d 01 3f 01 40 01` (first occurrence). Each pair is 56 bytes: u16 a, u16 b, u64 2, u64 4,
u16 state, u16 state, ... with WAR = 0, TRUCE = 1, PEACE = 2, ALLIANCE = 3. Set (317, 328) and (317, 327) to 0, 0 and
`repack`. Whether the faction update keeps that war, or sues for peace before the army arrives, is unknown, so use
two factions. [I]

- **T1, baseline, no new patches.** Load, run at normal speed. Look for a group of `spawn: game:N 'creature/...'`
  log lines with no lair due. Save twice, a minute apart. For each entity with the KV_ENEMY_WAVE key (hash
  0xc19ec3545e5000b7) read position (`fixed_transform_system/data.bin`: u64, u64, then 12 bytes per entity id)
  and compare. Screenshot the entrance.
  - Same position near (554.84, 996.79, -19.73) in both saves: cause 1 confirmed.
  - They walk: cause 1 refuted. Keep the army alive and look at the overworld for cause 3.
- **T2, P1.** Same copy. Expect members appearing at (549.5, 994) and moving to the nearest building, then fights
  and deaths in the log.
- **T3, P2 + P3.** Force several attacks; the +0x270 count in the save (second array in
  `enemy_wave_system/data.bin`) must stop at about the cap, and resume after kills.
- **T4, regression.** Lair waves unchanged (`rat_fat` x5 at the 8520 s check). Reload a save with members in +0x270.
- **D1 check.** Set 0x15ad to 0 in a copy, advance past 10800 s (or edit a war-free copy at a later time) and confirm no
  "Fac wants war" effect on the mountainhome relation.

## Could not establish
- The freeze itself: not reproduced, no save from a reporter. Cause 1 is inference from "the one difference".
- Whether "world map" means the overworld or the cave; the code supports the cave reading on count alone.
- Army regeneration rate, wave interval under war, and the real number of invaders over time.
- Whether anything besides the faction update can start a war with the mountainhome.
