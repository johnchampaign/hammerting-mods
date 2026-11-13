# Greed / wage loop (BUGS.md A7), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `.text` file offset = VA - 0x180001000 + 0x400.
`tools/disasm.py` takes N = VA - 0x180001000 in decimal. Modules dumped for this note: 44
dwelling_system, 48 vault_system, 57 desire_util, 160 action_desire, 172 action_stash_gold,
177 sensor_desire, 183 trees, 235 node_move_to, 258 node_take_gold_for_greed, 259 node_stash_gold,
39 utility_system. The installed DLL differs from the pristine one only at 0x1800a1c97,
0x180153102, 0x1801dfc89 (other mods), so all bytes below are original.
Fixed point: gamefp is 16.16 in an i32. KV_GOLD is a u64 property (type word 3, written as
0x10003). Tags: uppercasehash16 BT_TAKE_GOLD_FOR_GREED = 0x5a65, BT_STASH_GOLD = 0x90dc,
BT_EAT = 0x69a1. Blackboard slot offsets are hash16*2: BB_DESTINATION_ENTITY1 0x15590,
BB_ROOM_ENTITY 0x19e4.

## Data
- `statusbar/statusbar.bin` (u64 n, u64 bytes, n x 0x14b0; layout = `statusbar_type`,
  game_entity.h): STATUSBAR_GREED min 0 / max 1000 (entries STATUSBAR_GREED_MIN/_MAX),
  thresholds 0 VBAD, 0.05 BAD, 0.75 MID, 0.90 GOOD, key KV_STATUSBAR_GREED, gain entry
  STATUSBAR_GREED_GAIN.
- `database/modifier/entry/modifier_entries_cdb.bin` (n x 0x23c8 `modifier_entry`;
  func[k] at +0xc8 + k*0x8c0, deps at +0x80, dep values at +0x880):
  - 17 STAT_LEVEL = KV_LEVEL.
  - 19 STAT_COIN_CAPACITY: FROM_DWARF `dependencies_multiply_and_sum` STAT_LEVEL x 50.
  - 20 STAT_COIN_PER_GREED: FROM_DWARF STAT_LEVEL x 0.01 (raw 0x28f).
  - 51 STATUSBAR_GREED_MAX: FROM_DWARF ATTRIBUTE_WISDOM x 25 + STAT_LEVEL x 25.
  - 32 STATUSBAR_GREED_OVERFLOW = STATUSBAR_GREED_GAIN x 1 (use not traced).
- `database/modifier/modifier/dwarf_modifiers_cdb.bin` record 0 CLS_DWARF (n x 0xdc90
  `modifier`; values at +0x490 x 0x48, configs at +0x4c90 x 0x90): values
  STATUSBAR_GREED_GAIN -0.05, STATUSBAR_GREED_MAX 1000, STAT_COIN_CAPACITY 10; configs
  GREED_MAX compute FROM_DWARF, COIN_CAPACITY compute FROM_DWARF + min 10 + max 15000,
  COIN_PER_GREED compute FROM_DWARF (no base value). STAT_LEVEL max 300.
  Read as: greed max = 1000 + 25 WIS + 25 L, coin capacity = 10 + 50 L (assumes the compute
  adds to the base value; if it replaces it, 50 L clamped to [10, 15000]), coin per greed =
  0.01 L. The combine rule lives in the modifier system (entity DLL), not checked.
- Other greed gain sources: UPGRADE_GOLD_PILE_PERSONAL +0.2 (dwelling upgrade), rings
  (FROM_RING, preciousness/rarity), traits -0.01..-0.02, HAMMERTING_HOUSE_IN_SESSION -0.25,
  morale/hunger thresholds. TRAIT_OUTLAW greed max -250.
- `entity/building/chest_start.entity`: STARTING_CHEST, OVERWORLD_DELIVERY, desire action
  DESIRE_REFILL_STATUSBAR + BT_TAKE_GOLD_FOR_GREED. **This is the only wage source.** No
  vault entity (vault_small/medium/large) has a desire action. `dwelling.entity` has
  DESIRE_STASH_GOLD + BT_STASH_GOLD. `dwarf_base.entity`: SENSOR_DESIRE, desires
  DESIRE_REFILL_STATUSBAR and DESIRE_STASH_GOLD, KV_GOLD, KV_STATUSBAR_GREED.
- `entity/ui/window/dwelling_assign_menu_entry.entity`: a dwarf can be picked for a dwelling
  only if `AND(NOT(GAME_CTX.DWELLING.IS_VALID), GAME_CTX.KEY_VALUE('KV_GOLD').FLOAT.GREATER(
  FLOAT('99')))`, i.e. no dwelling and carried coin > 99 (tooltip DWELLING_ASSIGN_MONEY).
  This is UI only; dwelling_system_assign_dwelling (0x180239470) has no coin check.
- loc (core.loc): "A dwarf can only carry up to 1 Silver Coin (or 100 Copper Coins)" — the
  pre-scaling fixed cap; now wrong.
- `entity/loot/gold.entity` (cave gold pile): `VAULT_ADD_COIN(VAULT_COIN_CURRENT/500 + 100)`,
  goes to the hoard, not to a dwarf.

## Greed bar and desire
- Greed falls at STATUSBAR_GREED_GAIN (-0.05/s base, per-dwarf modifiers on top).
- desire_util::calc_desire_to_refill (0x1802dd2e0), default curve (GREED uses it):
  r = (cur-min)/(max-min); desire = 0 if r >= 0.75, else 0.1 + 0.9*min(1,(0.75-r)/0.65).
  (HEALTH/BUILDING_HEALTH: active below 0.95; ENERGY: below 0.5; TALKATIVENESS: always 0.)
- should_have_high_rank_util_action (0x1802de6c0) is true only for health, so greed and stash
  always run as ACTION_DESIRE, rank 4 (UTILITY_RANK_ORDER), the same rank as ACTION_WORK
  (utility_action_desire_register 0x1803ab0c0, `movl $4, 0x70(%rbp)` at 0x1803ab159; ACTION_DESIRE_HIGH 7;
  ACTION_WORK 4 at 0x1803beb66). Considerations: vigilance, convenience
  (0x1803adab0: f(desire)/max(1,path_distance)), desire, filler_entity.
- Utility switching (utility_system_update 0x1801fa7f0, get_best_action 0x1801fa6f0): highest
  rank with score > 0 wins; within a rank, best score. The new current action gets boost 1.5
  and a 1 s lock (0x1801fb4d9, 0x1801fb4fe). Instances with cooldown > now are skipped.

## Desire sensor: sensor_desire update_sensor_entity (0x1803cd230)
Per desire with value > 0, per filler (desire action record, stride 0x48, BT hash at +0x44):
1. Non-gold fillers need a family parent (0x1803cd5ca); 0x5a65 and 0x90dc skip this.
2. Root must not be CURRENTLY_IN_OVERWORLD; map cell of root must have explored bit 22
   (0x1803cd6b1).
3. Claimed filler: kept only if claim is CLAIM_DESIRE by this dwarf (0x1803cd6e5..0x1803cd72a).
   **0x5a65 (take gold) skips this check** (0x1803cd6bd `cmp ax,0x5a65; je`, bytes
   `b8 65 5a 00 00 66 44 3b c8 74 6a`). 0x90dc (stash) does not skip it.
4. Path: interaction_system_find_closest_interact_position cached per root; < 0 -> drop.
5. Value via desire_data callback (evaluate_* below), must be > 0x28f (0.01).
6. Score = value / (1 + 0.01*path). Top 3 kept; instances whose filler fell out are removed
   (utility_system_remove_action_instance 0x1803cdb00).
desire_sensor_on_action_done (0x1803cce80): on UT_SUCCEEDED, UT_FAILED, UT_REPLACED,
UT_ABORTED the instance is removed (0x1803cd19b); kept only for UT_REMOVED. The next sensor
update recreates it. stop_current_action_instance (0x1801f8c00) sets cooldown now+5 s on
UT_FAILED (0x1801f901b), but on the instance that on_action_done then deletes, so **desire
actions have no effective retry cooldown**, after success or failure.

## Take wages
Filler value, evaluate_refill_statusbar_desire_filler (0x1802ddd90), gold branch for
filler BT 0x5a65 (0x1802ddf58..), per statusbar whose key is KV_STATUSBAR_GREED with desire > 0:
- missing = int(max - cur) (0x1802de50f)
- space = int(STAT_COIN_CAPACITY) - KV_GOLD (0x1802de541/0x1802de544, `48 63 c8 49 2b 08`)
- coins = min_unsigned(vault gold_current, space) (0x1802de54b `48 3b c8`, 0x1802de54e
  `48 0f 42 c1` cmovb)
- g = min_unsigned(missing, 10*coins) (GREED_PER_GOLD = 10; 0x1802de55e `49 3b c9`,
  0x1802de561 `4c 0f 42 c9` cmovb)
- value = g * f(desire ratio) * desire. vault gold_current = vault_system_get_status
  (0x18026b100) field +0x20 of vault data, i.e. the whole Mountainhoard.
So value > 0 iff greed < 75%, hoard > 0, missing >= 1 and space != 0. **space < 0
(carried > capacity) wraps to a huge unsigned number and the value stays positive.**

Behaviour BT_TAKE_GOLD_FOR_GREED (bt_create_tree_take_gold_for_greed 0x1803fc4a0) =
sequence(move_to_entity(BB_DESTINATION_ENTITY1), take_gold_for_greed(BB_ROOM_ENTITY)); both
BB slots = the chest (desire_action_begin 0x1803ad3d4..0x1803ad499).
Node update bt_take_gold_for_greed_update (0x1804e5980):
- vault = hoard gold_current; carried = dwarf KV_GOLD; cur, max = STATUSBAR_GREED.
- cpg = STAT_COIN_PER_GREED, scaled by the scenario's CLS_DIFFICULTY_ENEMY_* class
  (0x1804e5ac3..0x1804e5cd3): VERY_EASY x0.25, EASY x0.5, HARD x1.5, VERY_HARD x2.5; then
  cpg = max(cpg, 6/65536) (0x1804e5afa..0x1804e5b06). gpc (greed per coin) = 2^32 / cpg_raw.
- missing = max - cur; if < 0 -> exit (0x1804e5bb0 `0f 88 11 04 00 00`).
- if int(capacity) < carried -> exit (0x1804e5cf1 `4d 3b 10`, 0x1804e5cf4 `0f 82 cd 02 00 00`).
- n = min(ceil(missing*cpg), capacity - carried, vault) (0x1804e5d01..0x1804e5d70).
- KV_GOLD += n; vault_system_add_coin(-n) (0x1804e5ddf); greed += floor(n*gpc) (0x1804e5df8);
  floating text GOLD / STATUSBAR_GREED.
- Returns BT_SUCCESS (1) on every path, including both early exits (0x1804e5fc7
  `41 8b c7`, r15d = 1) and n = 0.
desire_util::calc_gold_amount_for_greed_refil (0x1802deb70) just returns 1 (UI property
DESIRE_TAKE_GOLD_FOR_GREED_AMOUNT; the clamp to available gold is commented out in property/ai.h).

## Stash
- Filler value, evaluate_stash_coin_desire_filler (0x1802de850): 0 unless the filler dwelling's
  dweller (dwelling_system_get_dweller) is this dwarf, some statusbar desire > 0 and the GREED
  desire > 0 (greed < 75%); value ~ greed desire * f(ratio) * 3 * KV_GOLD. So stashing only
  happens while greed is below 75%, and only into the dwarf's own dwelling.
- BT_STASH_GOLD (0x1803fc200) = sequence(move_to_entity(BB_DESTINATION_ENTITY1),
  stash_gold(BB_ROOM_ENTITY)). bt_stash_gold_update (0x1804e7090): dwelling KV_GOLD += dwarf
  KV_GOLD, dwarf KV_GOLD = 0, BT_SUCCESS. No KV_GOLD_MAX check; never fails once reached.
- ACTION_STASH_GOLD (utility_action_stash_gold_register 0x1803bd9a0, begin 0x1803be080) sets
  BT_STASH_GOLD without blackboard entities; no code adds instances of it (unused).
- dwelling_system_assign_dwelling (0x180239470): moving a dwarf copies the old dwelling's
  KV_GOLD over the new dwelling's (the new one's coin is lost) and zeroes the old; unassigning
  zeroes it. No claim is added.

## desire_action_begin (0x1803ad380)
- `claim_system_is_claimed(filler)` (0x1803ad3c4, `jne 0x1803ad859` at 0x1803ad3ce,
  `0f 85 85 04 00 00`) -> BT_WAIT_AND_RETURN instead of the action.
- Gold BTs (0x5a65, 0x90dc) add no CLAIM_DESIRE (0x1803ad4e9..0x1803ad4fb), so dwarves never
  block each other at the chest. A chest claimed by anything else (none found in code; claim
  adders are item/haul/order/equip paths) would give endless BT_WAIT_AND_RETURN, because the
  sensor keeps offering the chest (step 3 above).

## Save-load clamp (the developers knew carried > capacity happens)
the_monolithic_patch_function (0x1802e0440) for saves older than 1.2.31 (0x1802e1521..
0x1802e1542): for every PLAYER_CHARACTER, if KV_GOLD > int(STAT_COIN_CAPACITY) set KV_GOLD =
capacity (0x1802e15a0..0x1802e16c3; an unused copy at 0x1802e8d00). Saves from 1.2.31..1.2.39
and live play get no clamp. recruit_system_spawn_recruit (ref at 0x18023333a) copies KV_GOLD
from the recruit template unchecked (value not traced).

## Numbers (normal difficulty, WIS 10)
max greed G = 1250 + 25L; top-up from 75% = 0.25 G * 0.01L coins; cap = 10 + 50L.

| L | G | coin/greed | full refill | 75%->100% | cap | top-ups to fill purse |
|---|---|---|---|---|---|---|
| 1 | 1275 | 0.01 | 13 | 4 | 60 | 15 (cap < 100: never dwelling-eligible) |
| 5 | 1375 | 0.05 | 69 | 18 | 260 | 14 |
| 10 | 1500 | 0.10 | 150 | 38 | 510 | 13 |
| 20 | 1750 | 0.20 | 350 | 88 | 1010 | 11 |
| 30 | 2000 | 0.30 | 600 | 150 | 1510 | 10 |
| 50 | 2500 | 0.50 | 1250 | 313 | 2510 | 8 |
Very hard x2.5: L30 top-up 375 (4 per purse), L50 full refill 3125 > cap 2510, and above L40
gpc < 1, so a 1-coin payment (space or hoard limited) adds 0 greed. Hoard drain per dwarf =
0.05/s * 0.01 L * diff = 0.5 L * diff coins per 1000 s (L30 normal 15, very hard 37.5).

## Loops, ranked
1. **No-progress success at the chest, retried without cooldown (code verified, trigger
   partly inferred).** Filler positive while the node does nothing, the node returns SUCCESS,
   on_action_done deletes the instance, the sensor recreates it, the dwarf runs it again at
   once: "camps at the starting chest". Verified trigger: KV_GOLD > int(capacity) (filler
   unsigned wrap 0x1802de54e vs node exit 0x1804e5cf4). Survives reload (state is in KV_GOLD).
   Sources of over-capacity purses: saves from 1.2.31-1.2.38 (no clamp), recruit templates,
   any capacity drop (none found in data). Lesser no-progress case: very hard, L > 40, 1-coin
   payments add 0 greed until the purse fills.
2. **Single wage point (data verified).** Only chest_start pays. All dwarves walk to the
   entrance; vaults, however full, are never visited. Chest gone, unexplored, cut off or in
   fluid -> no wages ever (no loop, greed dies). Chest claimed by anything -> endless
   BT_WAIT_AND_RETURN ("jog in place"). Any failure of the move to the chest (sensor path
   check passes, move_to fails) also retries with no cooldown (jogging).
3. **Purse/dwelling deadlock (data verified).** Purse empties only by stashing into the
   dwarf's own dwelling; the UI only offers a dwelling when KV_GOLD > 99; level-1 cap is 60 (or
   50). Purse full -> space 0 -> filler 0 -> no wages -> greed 0, morale penalties. Not a
   movement loop, but permanent.
4. **Stash vs work flip-flop (inferred, not checked in game).** Stash and ACTION_WORK share
   rank 4; stash convenience falls with path length; a far dwelling loses to work whenever a
   job appears (needs > 1.5x the current score). Each lost stash deletes the instance; the
   purse stays full, so wages stop (variant "Stashing coins" / "Going to work").
5. **QoL4 scaling (data).** Wage per refill ~ L(1250+25L)/100 x difficulty vs cap 10+50L:
   faster purse fill (8-15 top-ups per purse, 4 on very hard) makes 3 and 4 bite sooner; the
   filler's fixed 10 greed/coin disagrees with the node's 100/(L x diff) (affects ranking only).

## Patch candidates
Data (hmod ctx.read/write on the .bin; no code cave):
- D1 purse floor: CLS_DWARF (dwarf_modifiers_cdb.bin record 0) value STAT_COIN_CAPACITY 10.0
  -> e.g. 200.0, and its min config (flags 0x10, 10.0) -> 200.0. Every dwarf can pass the >99
  dwelling rule; fixes 3 for level 1.
- D2 flatten wages: modifier_entries_cdb.bin entry 20 STAT_COIN_PER_GREED dep value raw 0x28f
  (0.01/level) -> smaller (e.g. 0x83 = 0.002) or swap the dependency for a constant. Entry 51
  STATUSBAR_GREED_MAX STAT_LEVEL x25 -> 0 to stop max greed growing with level.
- D3 dwelling rule: `FLOAT('99')` in dwelling_assign_menu_entry.entity is a compiled chain
  (bytecode before source); a same-length edit ('99' -> '09') needs checking that the
  bytecode holds the literal.
Code (game.x86_64.dll, original bytes):
- C1 (fixes 1, no cave): make the gold filler's two mins signed so carried >= capacity gives
  value <= 0: 0x1802de54e `48 0f 42 c1` -> `48 0f 4c c1`; 0x1802de561 `4c 0f 42 c9` ->
  `4c 0f 4c c9`. Same result for non-negative inputs.
- C2 (2, low priority, no cave): sensor checks claims for gold fillers too, so a claimed
  chest is skipped instead of looping: 0x1803cd6c6 `74 6a` -> `90 90`.
- C3 (cave, 1/2): real retry cooldown or n == 0 -> fail: at 0x1804e5d74 replace
  `49 8b c7 48 c1 e0 10` (mov rax,r15; shl rax,16) with a jmp to .hmod 0x18060c300 that tests
  r15 and returns via 0x1804e5fc7 when 0. Only useful together with a cooldown, because
  on_action_done (0x1803cd19b) deletes the instance on failure too.
- C4 (cave, 2): extra wage points: give vaults the chest's desire action (entity data:
  copy chest_start's DESIRE_REFILL_STATUSBAR component into vault_*.entity), not tried.

## Save fields that show a dwarf in the loop
- key_value_system: dwarf KV_GOLD (u64) vs 10 + 50*KV_LEVEL; KV_GOLD > cap = loop 1,
  KV_GOLD == cap without dwelling = 3. KV_LEVEL, KV_ATTRIBUTE_WISDOM give G; KV_STATUSBAR_GREED
  below 0.75 G means the wage desire is active.
- dwelling_system/data.bin: dwarf -> dwelling (dweller comp +2), dwelling KV_GOLD.
- vault_system/data.bin: hoard gold_current / gold_max (+0x20/+0x28 of the system data).
- claim_system/claims.bin: any record whose entity is building/chest_start[N]
  (debug_name_system) = loop 2.
- Scenario difficulty class (CLS_DIFFICULTY_ENEMY_*), chest_start position and explored bit.

## Test (2026-11-01, user's save, unpatched)
Save edit: dwarf 2098 (Hilding, level 26, WIS 14) KV_GOLD 573 -> 2000 (purse 1310), greed 1442/2000
(< 75%), hoard about 10 silver 92 copper. Over several game hours he went from level 26 to 27 and
kept gaining XP; greed fell to 1247/2025 (unpaid). No chest loop: with work available the
wage action loses. The reported loop needs something else as well (no work, or the chest
unreachable/claimed). Save formats used: key_value.bin as in relation_crash.md; KV_GOLD and
KV_LEVEL are type 0x10003 (u64), KV_STATUSBAR_GREED 0x10007 (16.16 gamefp).
