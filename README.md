# Hammerting Fix-Up Mods

Unofficial mods that fix bugs in **Hammerting** (Warpzone Studios / Team17, Steam version 1.2.39)
and make it possible to finish. The game stopped getting updates after its 1.0 release in 2021 and
still has crashes, stuck dwarves, hauling loops and victory conditions that are out of reach in
practice. These 53 mods fix or work around them. The problems were found during full
playthroughs, and [`mods/README.md`](mods/README.md) says how each fix was tested.

Not affiliated with Warpzone Studios or Team17. The mods ship no game files: the installer reads
your own copy of the game and patches it on your machine.

## Requirements

- Hammerting on Steam, current version (1.2.39). Windows, or Linux with Proton.
- [Python 3](https://www.python.org/downloads/) (3.10 or newer; tested with 3.14). On Windows, tick
  "Add python.exe to PATH" in the installer.

## Install

1. Download the latest release from the
   [Releases page](https://github.com/johnchampaign/hammerting-mods/releases) (Source code, zip)
   and unzip it anywhere.
2. Close Hammerting.
3. Install:
   - **Windows:** double-click `install.bat`.
   - **Linux:** run `python3 tools/hmod.py install recommended` in the unzipped folder.

   The installer finds the game through Steam. If your game is somewhere unusual, set the
   `HAMMERTING_DIR` environment variable to the game folder (the one with `game.wkz`).
4. In Steam, right-click Hammerting → Properties → General → Launch Options, and enter:

   ```
   %command% --game-extra-archives danger_zone/hammerting_mods.wkz
   ```

5. Play. Your existing saves keep working.

Installing writes `danger_zone/hammerting_mods.wkz` into the game folder and patches three game
DLLs. The untouched DLLs are kept next to them as `*.hmod-orig`, and the installer always patches
from those originals, so installing again (after an update to these mods, or with a different set)
is safe.

## Uninstall

- **Windows:** double-click `uninstall.bat`. **Linux:** `python3 tools/hmod.py uninstall`.
- Then clear the Launch Options.

Steam's "Verify integrity of game files" also restores the original DLLs.

## Choosing mods

`mods/recommended.txt` lists what `install recommended` installs. Delete a line to leave a mod out.
Or name mods yourself: `python tools/hmod.py install natural_healing ground_pickup ...`.
`python tools/hmod.py list` shows them all. [`mods/README.md`](mods/README.md) describes every mod
in detail, with how each was tested.

Some mods have a setting at the top of their `mod.py` (for example `TARGET_PERCENT` in
`reachable_affluence`). Change it and install again.

## What the recommended set changes

**Winning**
- **Righteous Affluence** is reachable. A Large Vault holds 2,000 gold, and it must be 10% full
  instead of 100% of 50,000 gold. (`reachable_affluence`, `victory_tracker`)
- **World Conquest** needs a third of the overworld owned or allied, not all of it.
  (`reachable_diplomacy`)
- **New victory, Mountainking of Lore:** finish the research tree and hold 100 Mountain Lore and
  100 Trade Lore. (`research_victory`)
- A Star of Mara costs 9 gems of any kind instead of 243 gems of one kind. (`gem_cut_rebalance`)

**Crashes and soft-locks**
- No crash when completing faction alliance quests such as Dwarven Licorice. (`relation_crash_guard`)
- A Hammerting meeting starts within 2 minutes even if someone can't reach their seat.
  (`hammerting_deadline`)
- Plants no longer freeze at a growth stage. (`plant_timer_fix`)
- Quarries repair themselves, so a broken quarry can't lock up the colony. (`building_self_repair`)
- Invader pile-ups are capped at 24. (`invader_cap`)
- Dwarves cut off by a closed route are sent back to the entrance after 10 game minutes.
  (`stranded_rescue`)
- Autosaves every 15 minutes instead of 5, since each one can stall a big colony.
  (`autosave_interval`)

**Hauling, storage and crafting**
- New storages pick up loose items from the floor, so ore, harvests and food stop rotting there.
  (`ground_pickup`)
- Haulers keep their load when interrupted instead of dropping it. (`haulers_keep_load`)
- Goods you buy at a settlement are actually fetched. (`overworld_goods_first`)
- Stored items don't suddenly rot in large colonies. (`keep_stored_items`)
- Queues reserve inputs one batch at a time instead of locking up the colony's supply.
  (`whole_batch_inputs`)
- Buildings accept mixed materials, and craft slots don't get stuck holding mixed gems.
  (`class_matched_inputs`, `one_kind_inputs`)
- Local Maintain stops at a sensible stock level instead of crafting forever.
  (`local_maintain_cap`, `maintain_hint`)
- The fishing pier stores its catch. (`pier_keeps_catch`)

**Dwarves and jobs**
- Fairer job choice: far hauling jobs no longer starve, and builders finish what they start.
  (`fair_jobs`, `builders_finish`)
- First tools get equipped automatically, and a failed tool upgrade no longer reserves the tool
  for good. (`equip_missing_tools`, `failed_equip_release`)
- Dwarves heal slowly on their own. (`natural_healing`)
- Wounded dwarves obey attack orders. (`steady_fighters`)
- Bonuses to "all professions" from traits, gear and statuses now apply. (`all_profession_bonuses`)
- One meeting no longer turns the whole colony into enemies. (`meeting_tone_scale`)
- Dwarves no longer freeze waiting for a chat partner, hover in mid-air, or camp at the starting
  chest. (`chat_partner_release`, `fall_when_idle`, `greed_purse_guard`)
- Stepped tunnels are walked at normal speed, and rock behind a door gets dug.
  (`step_pace`, `door_dig_reach`)

**Lava**
- Dwarves don't walk into lava, and walk out if it reaches them. (`lava_no_walk`, `lava_escape`)
- Furnaces don't burn the lava you need for Sulphur Sprouts. (`lava_not_fuel`)
- A lava pump isn't stopped by stored water. (`pump_fluid_count`)

**Rails**
- Riders don't get stuck in Handcar queues, fight from a moving Handcar, or lose their place in
  line. (`rail_fixes`, `ride_then_fight`, `rail_queue_keep`)
- The unfinished left-rising incline is added to the build menu. (`left_incline_rail`)
- Rail help text explains Handcars. (`rail_help`)

**Missions and research**
- Land Survey unlocks early, so you can't lock yourself out of Mountain Lore. (`early_land_survey`)
- Discovery missions count rooms found before the mission started. (`discovery_counts_found_rooms`)
- Dwarven Subversion is only offered at capitals you have found. (`known_capital_missions`)

**Information**
- Warnings when the vault can't pay for a purchase, and when it is nearly empty.
  (`buy_coin_warning`, `low_vault_alert`)
- Clearer tooltips for tear-down orders, attributes, and alerts about dwarves away on the
  overworld. (`teardown_hint`, `attribute_hint`, `away_dwarf_alerts`)
- Blocks you place above walkways stay put. (`keep_placed_blocks`)

## Notes

- Steam achievements still unlock normally, including the victory ones. The new research victory
  has no achievement of its own.
- A Large Vault built before installing keeps its 50,000-gold size. `tools/save.py vaultcap` can
  rewrite one in a copy of a save: see [`mods/README.md`](mods/README.md).
- `docs/PLAY_STRATEGY.md` has strategy notes from a full playthrough, and `docs/BUGS.md` lists the
  bugs found, fixed and still open. `re/notes/` holds reverse-engineering notes for modders.
- Mods whose names start with `_test` are for testing only. Don't install them for play.

## License

MIT. See [LICENSE](LICENSE). Hammerting is © Warpzone Studios and Team17.
