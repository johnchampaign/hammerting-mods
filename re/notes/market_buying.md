# Buying from settlements (2026-11-04)

Tests used copies of savegame14 (colony East Tharnlaw, 524 coin) with the installed 23 mods. One run of each case.

## Too little coin: the click silently does nothing
- `buy_items_is_valid` needs the price of one to be <= vault coin (read in the disassembly, 0x1802eb760).
- `trade_offer.entity` has no coin check on the button, and the tooltip still says "Click to buy".
- Test: Animal Bone (97) with coin 820 logged `Executing command buy_items`, coin went to 723, stock 9 to 8. Beaver Hide (881)
  with coin 723 logged nothing and nothing changed.
- So failed clicks leave no trace in session logs, and the logs can't count them.
- Coin moves fast: 524, 820, 723, then 438 within about 14 minutes of log time, and 0 at the end of the second run. Wages through
  the Greed bar are the likely drain (not measured).

## Paid-for goods never come home while the only storage also takes from the ground
- Bought items stay in the settlement's backpack, unclaimed. The market popup lists them under "Buy"
  (`GAME_CTX.BACKPACK.FILTER("NOT(IS_CLAIMED)")`). They need an overworld-enabled haul destination and a dwarf to fetch them.
- `add_haulable_items` accepts an overworld item only if the destination has source bit 0x04 (0x1801dc265). The colony has one
  storage, `building/chest_start`, with source mask 0x05 (ground + overworld).
- The user's one purchase (10 gauze, log 00:34:59, about 20:37) was still at Suthnock in savegame14, about 27 real minutes later.

| Chest mask | Result |
|---|---|
| 0x05 (as saved) | Gauze and a bought bone stayed in the list, log t 6:32 to 14:50 (normal speed, then key 3) |
| 0x04 (save edit, nothing else changed) | Dwarf 2080 had all 10 gauze by log t 4:36 (play from 2:07). By the 7:15 manual save the claim was gone and they were not loose |

Why [inferred, not traced]: haul eta takes the nearest eligible item (`job_broker.md`), and the colony has about 1400 loose items, so a chest
that also takes from the ground always has something nearer than a settlement.
Not checked: that the gauze is in the chest (no direct read of its contents, only claim released and not loose); the in-game toggle (the
test edited the save); a second storage set to overworld only; whether the mask came from `ground_pickup` or `tools/save.py ground`.

## Trap in tools/saveinspect.py
`where()` says "held" for anything with a parent and no ow_ claim, and that includes bought goods still at a settlement. Reading that as "in a
colony inventory" made me wrongly report that no goods were stranded. Item parents are region entities, so `parent` doesn't separate them.
Use the market popup or the claim history.

## Fixes (2026-11-04)
Tested on an unmodified copy of savegame14, chest mask still 0x05, with all 25 mods. No exceptions or unlocks.

`mods/overworld_goods_first`: bt_haul_update's item loop (0x1804f85c0) takes the smallest distance. For an item inside a container the distance is
cached per root at [r14+8], filled by `station_system_are_positions_accessible` (call at 0x1804f8b60). The cave at 0x1804f8b65 tests the item's
parent for CURRENTLY_IN_OVERWORLD, the same test as `add_haulable_items`, and shifts a reachable distance right by 12. Only the choice reads that
value. A hauler already carrying items also goes for the town goods instead of delivering first (the check at 0x1804f8d88) [read, not seen in game].
- Result: the Buy list looked empty on screen at 7:36:52, about 5 minutes after unpausing (normal speed, then key 3 from 7:33:43). The picture lags, so the real time
  was shorter. In a save at 7:39 the 5 remaining gauze had no claim and were not loose. Without the mod nothing moved in about 8 minutes. In a second run a dwarf
  had claimed a bought bone in the first autosave, about 80 s of log time after the purchase.
- 5 of the 10 gauze were unspawned at log t 3:21-3:41. Health refill using them as medicine is the likely reason, not confirmed
  (`food_ai.md`). The screen kept showing them for 2-3 minutes, so don't time deliveries from the picture.
- Not tested: long play, more than one settlement with goods, a town under attack, walking time lost to loose items waiting.

### Steal loop it caused (found and fixed 2026-11-10)
- Seen in the user's South Xanforge colony (savegame43): two dwarves stood still by the hand pump showing a haul task, and two more stood
  still elsewhere. `_test_drop_log` showed four of them taking one bought lumber_reclaimed (3553, for chest_start) from each other every
  tick: "stealing haul of 3553", 1487 times in 30 s, and none walked. Their nav reach was the whole colony; behaviours are not saved, so
  the loop restarted at once after a load.
- Cause: the scaled distance doesn't stay in the choice. bt_haul_update passes it (as 0x2e8 and 0x1a0 of its frame) to
  `should_haul_item` (0x1804edf80), whose steal test (0x1804ee326) takes over a claim when `mine + 10 tiles <= claimant's`, and the
  claimant's distance is computed there fresh, unscaled. A scaled settlement distance is tiny, so every hauler beat every claimant.
- Fix: cave `no_steal` (.hmod 0x2580) at that test. For an item whose parent has CURRENTLY_IN_OVERWORLD it makes the test fail, so a claim
  on settlement goods is never taken over by distance. Unscaling instead isn't safe: `should_haul_item` computes its own (unscaled) distance
  when passed a negative one, so it can't tell which kind it got.
- The other steal path is untouched: when bit +0x350 of the hauler's node state is set and the claimant's isn't (it looked like "already
  in the overworld"), `should_haul_item` steals without a distance test. That happened once per item in the test, as in vanilla.
- Test: copy of savegame43, shipping mods minus `stranded_rescue`, plus `_test_drop_log`. 5 steals in about 100 s, none repeated; all five
  dwarves moved, and 2053 delivered six settlement items, 3553 among them, to chest_start 75 s after unpausing.

`mods/buy_coin_warning`: extra `%O` chain in `UI_MARKET_BUY_X_DESC` and `UI_MARKET_BUY_ALL_DESC`, built with `evalchain.compile_chain`. Seen at 820 coin:
Bone x1 no line, Bone all (873) "only some", Beaver Hide x1 (881) and all (3524) "do nothing". Buy All on 9 bones then bought 8 for 776, leaving 44, so
the partial buy is real. The button can't be greyed yet: that needs a new or larger chain in `trade_offer.entity`, whose record layout isn't worked out.

## Notice on a refused buy: attempts (2026-11-05), not shipped
`mods/buy_coin_notice` (not in the install line) hooks the coin check in `buy_items_is_valid` (0x1802eb833, `cmp [rbx+8],rax; ja`).
The cave is reached once per refused click (counter read from memory). Tried on copies of savegame20 (vault 0):
- A new log book entry record (appended to log_book_entries.bin) crashes every startup in gamemedia's
  `gamegfx_base::register_settings` (`command_option::set_string_if_set`), probably the per-entry OPTION_LB_ENT_* setting. A new
  category alone wasn't tested; entry + category and entry alone both crashed; without the entry it starts.
- Borrowing LB_ENT_RESEARCH_BOUGHT with `log_book_system_update_entry` (0x1802158c0) from the hook: no crash, but no notification
  and no log book entry.
- Posting through `LOG_BOOK_UPDATE_ENTRY(...)` with `property_component_system_evaluate_chain_string_args` from the hook crashed
  in `property_component_system_evaluate_chain_args` (entity DLL), with an empty context and with a U64 context and argument.
Inferred, not checked: the validity check runs against a gamestate other than the simulation's (the UI's copy), so state changed
there isn't the game's. The next try should post from the simulation side, or from the button's own click chain in trade_offer.entity.

Later the same day:
- Splitting it (the check only counts refusals in `.hmod`; a hook at 0x1802af40a in gamestate::update posts) fixed the "which gamestate"
  question: `log_book_system_update_entry` from the update put the value into the live game's memory, yet nothing appeared in the
  log book or as a notification. Not explained.
- `MOUNTAINHOME.SET_KEY_VALUE(...)` evaluated from that update hook froze the sim (frame counter stopped, no exception), like the
  second reward slot in diplomacy.md. Chains that only read or add smart events worked from a hook (known_capital_missions).
- Shipped instead: `mods/low_vault_alert`, data only. The unused ALERT_NO_ENERGY_ITEM (condition FALSE) now has the condition
  `VAULT_COIN_CURRENT.LESS('100')` and its texts say why. Seen at 0 coin with the tooltip, absent at 806 (copies of savegame20, 21).
  It warns ahead of a click rather than on it. `mods/buy_coin_notice` stays in the repo, not installed.
