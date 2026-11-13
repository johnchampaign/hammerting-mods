# Death panic spiral (BUGS.md A6), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 24 health_system, 32 statusbar_system, 55 sensor_refill_statusbar,
57 desire_util, 85/89/91/191/195 orders, 117, 155-174 utility actions, 175-182 sensors,
185 trees_combat, 199 combat_system, 204/207/208/209, 261 node_sleep, 53, 19, 54, 119, 123,
210. Bytes below are from the pristine DLL (`game.x86_64.dll.hmod-orig`, sha256 c23c1881); no
site below is touched by the installed mods.
Fixed point: gamefp 16.16. "r" below = STATUSBAR_HEALTH cur / max (min ignored; min is 0).

## Utility selection (recap, utility_system)
- Ranks (`utility_rank`, ai_utility_types.h): 1 IDLE, 2 LOW_DESIRE, 3 DEFAULT, 4 ORDER,
  5 PREPARATIVE, 6 COMBAT, 7 HIGH_DESIRE, 8 PERSONAL_ORDER, 9 INVOLUNTARY, 10 SCRIPT.
- Per consideration: raw score clamped to [min,max], normalised (evaluate_scores 0x1801fa150),
  transformed (linear: in*slope + shift, 0x1803a70d0), clamped to [0,1] unless
  `_allow_non_clamped` (evaluate_considerations 0x1801fa530). Instance score = boost x product
  (evaluate_actions 0x1801fa630). Current action boost 1.5, 1 s hold (greed_loop.md).
- get_best_action 0x1801fa6f0: highest rank with score > 0 wins, best score inside the rank
  (strictly greater, so ties keep list order); instances with cooldown > now skipped.

## Rank table (dwarf)
| action | rank | set at | score | gates |
|---|---|---|---|---|
| ACTION_MOVE_SELECTED_TO (direct move) | 8 | 0x1803b881b (r14d=8) | path x can_claim | none on health |
| ACTION_DESIRE_HIGH (heal with medicine) | 7 | 0x1803ac71b | vigilance x convenience x desire x filler | r <= 0.40 + instant-heal filler (below) |
| ACTION_MOVE_TO (move order), ACTION_EQUIP | 7 | 0x1803b7b56, 0x1803af7de | | |
| ACTION_COMBAT_MELEE | 6 | 0x1803a9846 | impact (slope 1) x prio (slope 2) | weapon; enemy in hit area; no health gate |
| ACTION_COMBAT_APPROACH | 6 | 0x1803a7e5e | has_target x 0.3 x prio x health | r > 0.25 |
| ACTION_MOVE_TO_ATTACK (player attack order) | 6 | 0x1803b4d5e | distance x is_taken x prio x health | r > 0.25, weapon |
| ACTION_RETREAT | 6 | 0x1803bb108 | min(1, 1.5 x 4(0.25 - r)) | r <= 0.25, target, >= 20 tiles from entrance |
| ACTION_TALK | 5 | 0x1803be21e | | |
| ACTION_DESIRE (heal, eat, wages) | 4 | 0x1803ab159 | as DESIRE_HIGH | health desire r < 0.95 |
| ACTION_WORK, ACTION_SLEEP, ACTION_MOVE_TO_INTERACT | 4 | 0x1803beb66, 0x1803bbea6 | sleep: clamp((0.75-e)/0.55)^2, e = energy ratio | |
| ACTION_ENEMY_WAVE (enemies only, KV_ENEMY_WAVE) | 4 | 0x1803aef4e | | |
| ACTION_IDLE_WANDER / AVOID_FLUID | 1 | | | |
| ACTION_DEAD | 10 | | | |

Considerations in detail:
- consideration_health (approach 0x1803a9710, move_to_attack 0x1803b6d60): `r > 0x4000`
  (0.25) -> 1 else 0, at 0x1803a976d / 0x1803b6dbd `3d 00 40 00 00`. Applies to every
  combateer, so wounded enemies also stop approaching.
- prio (approach 0x1803a9680, move_to_attack 0x1803b6cd0): KV TAG_PROF_MILITIA_ALLOWED (u64)
  == 0 -> 0, absent or nonzero -> 1. Melee prio (0x1803aa750): KV PROF_MILITIA_PRIO (type 4)
  absent -> 0.5 x 2 = 1, value v -> clamp(v); no data sets this key.
- approach has_target (0x1803a9330): combat target == instance target, path, PROF_MILITIA tool
  -> 1, transform slope 0.3 (0x1803a7f11 `cc 4c`). So approach scores 0.3 (0.45 when current).
- melee impact (0x1803aa540): needs a PROF_MILITIA tool if the dwarf has a toolbelt;
  attacking -> 100 (clamped 1), else combat_system_estimate_damage_impact (damage on enemies
  in the hit area, clamped to 1).
- move_to_attack distance (0x1803b6780): needs a PROF_MILITIA tool and a path,
  0.1 + 0.9 f(distance); is_taken (0x1803b6c50) 1 if own/unclaimed, 0.5 if claimed.

## Combat targets: combat_system_update (0x1804282d0)
Per combateer comp (0x70 bytes): skip if `enabled` (+0x68) is 0; rescan timer +0x54 (2 s);
skip if it already has an approach instance (+0x48). If the entity has a toolbelt and no
PROF_MILITIA tool -> target cleared (0x1804287e0): **unarmed dwarves never get a combat target**
(so they never approach, attack or retreat). Else find_enemies within 20 tiles (0x1804288e0
`c7 44 24 50 00 00 14 00`), max 16, closest reachable, current target's distance x 0.8, and an
ACTION_COMBAT_APPROACH instance is added (0x180428ea0). No health check here.

## ACTION_RETREAT (utility_action_retreat_register 0x1803bb060, initial action of DWARF)
- Consideration (0x1803bb980), linear slope 1.5 (0x1803bb1aa `00 80 01 00`), clamp [0,1]:
  1. r > 0.25 -> 0 (`be 00 40 00 00` at 0x1803bbc0c, compare 0x1803bbc26/`jg` 0x1803bbc28).
  2. no combat target and not running -> 0.
  3. entrance = first entity of mountainhome KV_ENTRANCE_ENTITIES; chessboard distance d.
  4. running: (now - start) > 30 s -> 0 (0x1803bbd19 `48 81 fa 00 00 1e 00`); d < 15 -> 0.
  5. d < 20 -> 0 (0x1803bbd31 `3d 00 00 14 00`). 6. no path to the entrance -> 0.
  7. score = 4 x (0.25 - r) (0x1803bbdc6), so final = min(1, 6(0.25 - r)): 1.0 at r <= 0.083.
- Begin (0x1803bb740): stores start time, **combat_system_set_enabled(dwarf, 0)** (clears
  target and approach instance), BT_MOVE_TO_ENTITY to the entrance. End (0x1803bb960): combat
  re-enabled with the rescan timer at 0.5 s, so a dwarf still >= 20 tiles away re-targets and
  retreats again (30 s cycles, no cooldown). UI: "Retreating".
- During retreat the dwarf cannot be targeted by its own combat; enemies keep it as a target
  (approach range 20 tiles, current target preferred) and follow. Melee can still win the slot
  (1.0 vs retreat 6(0.25-r)); a current retreat (x1.5) beats melee when r < 0.139.

## Healing desire
- calc_desire_to_refill (0x1802dd2e0), health branch: t = clamp((0.95 - r)/0.55, 0, 1),
  desire = 0.1 + 0.9 t (0.1 even at full health).
- Rank choice in the desire sensor (update_sensor_entity 0x1803ce709..0x1803ce733): HIGH iff
  desire value >= 0.9 (`81 fa 66 e6 00 00`, i.e. r <= 0.461), filler value >= 149
  (`41 81 f8 00 00 95 00`) and the desire's callback (if any) returns true. Only
  DESIRE_REFILL_STATUSBAR has one (mainstate registration, struct +0x70 = 0x1802de6c0); the
  other desires (feast, idle wander, stash gold) have none, so they too go HIGH when both
  gates pass (greed_loop.md says stash is always rank 4: not true in this extreme).
- should_have_high_rank_util_action (0x1802de6c0): recomputes the health curve for the
  dwarf and needs desire >= 1.0, i.e. **r <= 0.40** (constant -0.95 at 0x1802de746
  `05 cd 0c ff ff`, divisor 0.55), and modifier_system_get_by_name(filler,
  "STATUSBAR_HEALTH_INSTANT") > 0 (0x1802de81b; function pointer 0x180599598). Always checks
  health, whatever bar the filler refills. Not "below 95%" as the task brief said.
- Instant-heal fillers (item_modifiers_cdb.bin): MEDICINE_GAUZE 350, MEDICINE_SLIMEBALM 500,
  MEDICINE_SHROOMPASTE 150 (may miss the 149 value gate; filler value formula not traced),
  drinks MULLED_WINE 300, MUSHROOM_SWIG 500, WILD_RUM 200, FOOD_BREAD_STONE 200, feasts
  200-950, FLUID_SACRED_WATER 500, some mushrooms. Negative: DRAGONS_BLOOD -100, MOONSHINE -50.
- So with medicine reachable a dwarf at <= 40% drops combat (7 > 6) and walks to it, even
  past enemies, and does not fight back on the way. Without such a filler the health desire is
  rank 4 or absent and never displaces combat. Healers can also carry medicine to needers
  (sensor_refill_statusbar, a job, rank 4; not traced).

## Natural regeneration: none found
- Damage writes STATUSBAR_HEALTH directly (property/attack_effect.h `statusbar_system_modify_value
  (..., STATUSBAR_HEALTH, -damage)`). statusbar_system_update (0x1801bd3b0): cur += gain
  (modifier STATUSBAR_HEALTH_GAIN), clamped to [min,max], per update.
- CLS_DWARF (dwarf_modifiers_cdb.bin record 0) has no STATUSBAR_HEALTH_GAIN value (slots
  0-17 used, health only has MAX 1000). Its value config computes it FROM_DWARF:
  modifier_entries_cdb.bin entry 33 STATUSBAR_HEALTH_GAIN = 1.0 x STATUSBAR_ENERGY_OVERFLOW;
  entry 28 STATUSBAR_ENERGY_OVERFLOW = 1.0 x STATUSBAR_ENERGY_GAIN, but no modifier table
  has a value or config for ENERGY_OVERFLOW and no DLL contains the string "OVERFLOW".
  **Inferred: overflow is never computed, so base health gain is 0.** (If the entity DLL
  computes dependencies without a config, health gain = energy gain: -0.05 awake, positive
  only while sleeping. Test below settles it.)
- Positive gains in data: UPGRADE_BEER_ON_TAP and UPGRADE_PORTRAIT_FAMILY +0.05 (upgrade
  modifiers, config flag 0x2 propagate-from-children; whether they reach dwarves through
  CLS_DWARF's flag 0x4 "affecting entities" is not traced). Negative: mental-break bars
  -0.01..-0.03, TRAIT_HYPOCHONDRIAC -0.01, EFFECT_IN_LAVA -10.
- Max health = 1000 + 25 ROBUSTNESS + 25 LEVEL (entry 45), TOUGH_AS_NAILS/CLAN_TOUGHBROW +250,
  RUGGED_MINDSET +300, BATTLE_SCARRED -250. Sleep ends when energy is full or after 60 s of
  KV_SLEEP_DURATION (bt_sleep_update 0x1804e9945), so it gives no health either.

## Orders and militia
- No drafted/soldier/combat-ready state exists (no such strings in game.x86_64.dll).
  PROF_MILITIA_ALLOWED and PROF_MILITIA_PRIO can only switch combat off.
- The attack order (ORDER_ATTACK, create_order_attack_entity 0x18040cd80) is offered by
  sensor_generic_order as ACTION_MOVE_TO_ATTACK, rank 6, with the same r > 0.25 gate. It
  loses to DESIRE_HIGH (7) and is zeroed below 25%, so wounded dwarves ignore attack orders.
- Only ACTION_MOVE_TO (7, ties DESIRE_HIGH) and ACTION_MOVE_SELECTED_TO (8) override; they
  move the dwarf, but on arrival a dwarf at <= 25% still will not approach.
- Below 25% a dwarf re-engages only by melee when an enemy is already in its hit area.

## Causes, ranked
1. **Hard 25% gate on approach and attack orders (code verified).** Armed dwarves at
   r <= 0.25 never chase, never obey attack orders, only melee what reaches them.
2. **No health regeneration (data verified, overflow semantics inferred).** Once below 25%
   a dwarf stays a non-combatant until it gets an instant-heal item. Damage accumulates over
   waves; each wave removes more fighters. Matches "rush medicine".
3. **Retreat loop (code verified).** Armed + targeted + r <= 0.25 + >= 20 tiles from the
   entrance: own combat off, run to the entrance for 30 s, repeat 0.5 s later. Enemies chase
   and hit it. Overworld raids probably enter at the entrance (not traced), so the retreat
   can run into them.
4. **Heal at rank 7 (code verified).** At r <= 0.40 with medicine/healing drink reachable the
   dwarf leaves the fight and does not defend itself on the way; chasers push it under 25%.
   Spiral: 40% -> leaves fight -> hit while walking -> < 25% -> if medicine ran out, stuck
   passive forever; nobody else fights the enemies on it once all armed dwarves are wounded.
5. Unarmed dwarves get no combat target at all (verified), so only armed militia ever retreat.

## Patch candidates
Data (no code cave):
- D1 regen: CLS_DWARF value slot 18 (dwarf_modifiers_cdb.bin, file offset 0x10 + 0x490 +
  18 x 0x48 = 0x9b0): tag "STATUSBAR_HEALTH_GAIN" zero-padded to 0x40 bytes, gamefp at +0x40
  (0x9f0), e.g. 0x199a = 0.1/update (~2 game h from 25% to 100% if updates are per second),
  is_percent byte +0x44 = 0. Assumes compute adds to the base value, as for
  STATUSBAR_ENERGY_GAIN (base -0.05 plus a FROM_DWARF compute; dwarves do tire).
- D2 no retreat: ai_utility/default.bin record DWARF (record 0 at 0x10, wc_tag = char[56] +
  u64 hash, initial actions at 0x50 + 0x40 i, loop stops at the first zero hash
  0x1801f8bd0): move bytes [0x150,0x210) (WORK, TALK, SLEEP) to 0x110 and zero
  [0x1d0,0x210). New utility components only; whether loaded dwarves re-add initial actions
  is not known (utility_system saves _actions/_instances).
Code (ctx.patch_dll, no cave needed for any):
- C1 attack orders ignore health: 0x1803b6dbd `3d 00 40 00 00` -> `3d 00 00 00 00`.
- C2 approach gate 25% -> 10%: 0x1803a976d `3d 00 40 00 00` -> `3d 99 19 00 00` (enemies too).
- C3 retreat threshold 25% -> 10%: 0x1803bbc0c `be 00 40 00 00` -> `be 99 19 00 00` (also
  scales the score: max input 0.4 -> score <= 0.6). C3' disable retreat: 0x1803bbc28
  `0f 8f a4 01 00 00` -> `e9 a5 01 00 00 90`.
- C4 heal below combat: ACTION_DESIRE_HIGH rank 7 -> 5 at 0x1803ac71b
  `c7 45 70 07 00 00 00` -> `c7 45 70 05 00 00 00` (still beats work/eat; fights first,
  heals when no combat action scores). C4' keep rank 7 but only below 15%: 0x1802de746
  `05 cd 0c ff ff` -> `05 cd 4c ff ff` (-0.70; threshold = 0.70 - 0.55).
Recommended minimal set: C1 + C2 + C3 + C4 (+ D1 for runs without medicine).

## Save fields
- key_value_system per dwarf: KV_STATUSBAR_HEALTH (0x10007 gamefp) vs max = 1000 + 25
  KV_ATTRIBUTE_ROBUSTNESS + 25 KV_LEVEL + traits; r <= 0.25 = combat-gated, <= 0.40 =
  high-rank heal. PROF_MILITIA_ALLOWED (u64), PROF_MILITIA_PRIO (normally absent),
  KV_LEVEL_PROF_MILITIA, KV_SLEEP_DURATION, KV_STATUSBAR_ENERGY.
- Mountainhome KV_ENTRANCE_ENTITIES: entrance entity; distance >= 20 tiles = retreat range.
- utility_system: current action ACTION_RETREAT / ACTION_DESIRE_HIGH and its instance
  (cooldown, boost, score). combat_system: combateer `enabled` false while retreating, target
  (format not decoded). Toolbelt: PROF_MILITIA weapon. Medicine stock: saveinspect.py items
  (CLS_MEDICINE_GAUZE / SLIMEBALM / SHROOMPASTE).
- Regen test: note KV_STATUSBAR_HEALTH of a wounded dwarf, play some game minutes with no
  medicine, compare (unchanged = gain 0; falling while awake = gain = energy gain).

## Test (2026-11-01, user's save, all six dwarves set to 20% KV_STATUSBAR_HEALTH)
Both runs: dwarves first healed with medicine from storage (+350 gauze, +500 slimebalm; one
+1500), identical in A and B, so rank-5 healing still beats work. Rat raid at ~7:04 from load,
cook house destroyed at 7:34 and restored.
- A (vanilla rules): 5 rats killed between 7:43 and 7:54, no dwarf lost.
- B (C1+C2+C3+C4): 1 rat killed at 7:47, then dwarf 2139 (level 9, 303 HP of about 1500, 20%)
  killed at 7:48. Lowering the approach/retreat gates to 10% and ranking heal below combat
  sends weak dwarves into fights they lose; one rat hit is more than 10% of their health.
Shipped: C1 only (attack orders ignore health). Not tested in game.
Open: natural regeneration (D1) is the real driver of the spiral when medicine runs out.

## Fix: mods/natural_healing (2026-11-01)
CLS_DWARF value slot 18 (file offset 0x9b0): STATUSBAR_HEALTH_GAIN, hash, gamefp 3277 (0.05),
is_percent 0. statusbar_system_update applies it per tick and it reaches dwarves in existing saves.
Test: dwarf 2098 set to 950/1900; card read 958 -> 1473 (+500 instant from a meal) -> 1489 over
31 s, i.e. +16 at 0.5/s. Cooked meals restore health instantly (the earlier "medicine" jumps of
350/500 in the A/B runs were meals; the colony owns no medicine, the 45 gauze are market stock).
