Title: I fixed 53 bugs in Hammerting so it can actually be finished: free mod pack with reachable victories and a new research victory

---

Hammerting stopped getting updates after 1.0, and it still has crashes, soft-locks, dwarves who wander into lava, hauling loops and two victory conditions that are practically out of reach. I played it through to the end and fixed what I hit along the way. The result is a free, open-source set of 53 mods.

**Download:** [github.com/johnchampaign/hammerting-mods](https://github.com/johnchampaign/hammerting-mods/releases/latest) (choose "Source code (zip)"). Latest version: 1.6.3.

No game files are included. The installer reads your own copy of the game and patches it on your PC, keeping the original files as a backup. Existing saves keep working.

# What it changes

**Winning**

* **Righteous Affluence is reachable.** A Large Vault holds 2,000 gold and needs to be 10% full, instead of 100% of 50,000 gold.
* **World Conquest** needs a third of the overworld owned or allied instead of all of it.
* **New victory, Mountainking of Lore:** finish the whole research tree and hold 100 Mountain Lore and 100 Trade Lore. Your progress shows under Victory Conditions.
* A Star of Mara costs 9 gems of any kind instead of 243 gems of one kind.
* The Victory Conditions panel shows how full your vaults are against the target.

**Crashes and soft-locks**

* No more crash when completing faction alliance quests such as Dwarven Licorice.
* A Hammerting meeting starts within 2 minutes even if someone can't reach their seat.
* Plants no longer freeze at a growth stage.
* Quarries repair themselves, so a broken quarry can't lock up the colony.
* Dwarves cut off by a closed route are sent back to the entrance.
* Invader pile-ups are capped, and autosaves come every 15 minutes instead of 5.

**Hauling, storage and crafting**

* Storages pick up loose items, so mined ore, harvests and food stop rotting on the floor.
* Haulers keep their load when interrupted instead of dropping it, and goods you buy at a settlement actually get fetched.
* Stored items no longer suddenly rot in large colonies.
* Production queues stop locking up the colony's food and water, and Local Maintain stops at a sensible stock level instead of crafting forever.
* Buildings accept mixed materials, craft slots don't get stuck holding mixed gems, and the fishing pier stores its catch.

**Dwarves**

* Fairer job choice: far jobs no longer starve, and builders finish what they start.
* Ripe crops are harvested promptly instead of standing until you press Harvest on each plant.
* First tools are equipped automatically, and failed tool upgrades no longer reserve the tool for good.
* Dwarves heal slowly on their own, and wounded dwarves follow attack orders.
* Trait, gear and status bonuses to "all professions" now actually apply.
* One meeting no longer turns the whole colony into Nemeses.
* No more dwarves frozen waiting for a chat partner, hovering in mid-air or camping at the starting chest.
* Stepped tunnels are walked at normal speed, and rock behind a door gets dug.

**Lava, rails and missions**

* Dwarves don't walk into lava and walk out if it reaches them. Furnaces don't burn the lava you need for Sulphur Sprouts, and a lava pump isn't stopped by stored water.
* Handcar fixes: riders don't get stuck in queues, don't fight from a moving cart, and keep their place in line. The unfinished left-rising incline rail is added to the build menu.
* Land Survey unlocks early, so you can't lock yourself out of Mountain Lore. Discovery missions count rooms you found before the mission started. Dwarven Subversion is only offered at capitals you have found.
* Warnings when the vault can't pay for a purchase or is nearly empty, plus clearer tooltips.

You can leave out any mod you don't want. The GitHub page describes each one in detail, including how it was tested.

# How to install

You need [Python 3](https://www.python.org/downloads/) (3.10 or newer). On Windows, tick "Add python.exe to PATH" when installing it.

1. Download the zip from the [releases page](https://github.com/johnchampaign/hammerting-mods/releases/latest) and unzip it anywhere.
2. Close Hammerting.
3. Windows: double-click `install.bat`. Linux: run `./install.sh` in the unzipped folder (see below).
4. In Steam, right-click Hammerting > Properties > General > Launch Options, and paste:
   `%command% --game-extra-archives danger_zone/hammerting_mods.wkz`
5. Play!

The installer finds the game through Steam. If it can't, set the `HAMMERTING_DIR` environment variable to the game folder (the one containing `game.wkz`).

* **Choosing mods:** `mods/recommended.txt` lists what gets installed. Delete a line and run the installer again to leave that mod out.
* **Smaller map:** to have the Underworld closer, pick Mountain Size: Small when you start a new game (800 x 800 tiles instead of the default 1088 x 1088).
* **Updating:** download the new zip and run the installer again. It always patches from your original game files.
* **Uninstall:** double-click `uninstall.bat` (Linux: `./uninstall.sh`), then clear the Launch Options. Steam's "Verify integrity of game files" also restores the original game files.

# Playing on Linux

Hammerting has no Linux build, but it runs well under Proton, and the mods were developed and tested there.

1. In Steam, right-click Hammerting > Properties > Compatibility, tick "Force the use of a specific Steam Play compatibility tool" and pick **Proton Experimental**. Start the game once without mods, then quit.
2. Check you have Python 3 (`python3 --version`); most distributions include it.
3. Unzip the release and run `./install.sh` in that folder.
4. Set the Launch Options as above.

If your game is in an unusual place, run `HAMMERTING_DIR=/path/to/Hammerting ./install.sh`. Steam Deck Desktop Mode should work the same way, but I haven't tried it.

# Good to know

* Made for the current Steam version (1.2.39), on Windows or Linux with Proton.
* To check the mods are loaded, look for "+ Fix-Up Mods" after the version number in the main menu's corner. The Mods button there lists every installed mod.
* Steam achievements still unlock normally. The new research victory has no achievement of its own.
* Mountainking of Lore shows up under Victory Conditions once you research Metallurgy, together with Righteous Affluence. A game that already had Metallurgy before you installed won't list it, but you can still win it there.
* A Large Vault you built before installing keeps its old 50,000-gold size. The GitHub page explains how to resize it in a copy of your save.
* Unofficial and not affiliated with Warpzone Studios or Team17.

Bug reports and suggestions are welcome here or on [GitHub](https://github.com/johnchampaign/hammerting-mods/issues).
