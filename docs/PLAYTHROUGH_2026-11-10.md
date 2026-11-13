# Playthrough 1: Mount Nunlaw (2026-11-10)

This is a new game with default settings, the shipping mods, and `_test_no_achievements`. I played it by
screen and input, with read-only memory and save reads to find out what the screen wouldn't tell me. The
saves are savegame33-36 and `autosave_MountNunlaw_*`. I stopped after about 1 h 45 min of session time
(early in year 2), with the colony starving.

## How far it got
- I followed the tutorial.
- Built: Small Quarry, Small Foundry, and Cave Farm. The Cook House is placed but still waits on Copper Ingots.
- Research: Metallurgy, Foundational Structures, Subterranean Farming, Cooking, and Dwarven Trade Relations.
- Missions:
  - Sounding the Depths, Strike the Earth!, and Stone from Stone are done.
  - Slimes are at 10/10, Water at 5/5, and Toncaps at 3/5.
  - Ymnock has trade level 2.
- Talent points were spent as soon as each one appeared.
- State now:
  - All three dwarves are at 0 Hunger.
  - Hävner is unconscious and needs medicine; Lack of Medicine is also an alert.
  - Morale and Greed are at 0.
  - All three buildings are at 0 Building Health.

## Possible bugs (not yet confirmed)
1. **Buildings sit at 0 health with no attacker in sight.**
   - The log shows 1735 (foundry) and 2364 (quarry) "killed" at 00:48 and 3069 (farm) at 01:08.
   - In the same stretch, the only creatures nearby were 2 green slimes that spawned at 00:48:15.
   - The buildings keep crafting at 0 health.
   - Granite Blocks keep being made and consumed (26 spawned, 24 unspawned by 01:43), but the health bars stay empty.
   - "Our buildings are under attack!" notices stay up.
   - Not investigated: what drains health, and where the blocks go.
2. **A building can be placed where no dwarf can reach it.**
   - The Cave Farm at about x 555-570, y 978-987 was accepted as "valid".
   - The site then showed "No dwarf who is able and allowed to do this job can find their way here."
   - The placement check probably doesn't test reachability; this may be vanilla behaviour.
3. **Cancelling that unbuilt farm left room-layer bits on its whole footprint** (map tiles x 555-570,
   y 978-987, room layer 2, with no farm entity in the save). I did not test whether this blocks new buildings there.
4. **Single clicks with the Cancel (Z) tool did nothing; a drag worked.** This matches the existing CLAUDE.md note about Mine.

## Balance and pacing notes
- **Early food runs out.**
  - The starting food was gone in about an hour.
  - All the wild Toncaps and animals are in unexplored caves.
  - Cave Farm recipes are Water and Bone Ash only; Toncaps need Fertile Soil plus a Toncap to sow.
  - The Cook House needs 4 Copper Ingots and 4 Granite Slabs.
- **Coin can't buy food in practice.**
  - Selling to Ymnock (slime and Copper Ingots) paid out, but the dwarves took it as wages within a minute.
  - They now carry about 10 silver between them, and the vault reads 0.
  - So Lichen (49 copper each) could never be bought. Market notes already describe this drain.
- Many "Destroyed order ent N for producer ent M" log lines are just completed orders, such as Water. They are not bugs.

## Playthrough 2 (restart, savegame38-41)
Small mountain, default overworld. I stopped at the user's request about 42 min of session time in (7th, 1st Forth),
saved as savegame41, with the game paused on its menu.
- Built a Small Quarry, Cave Farm and Small Foundry by about 36 min, roughly twice as fast as run 1. Four missions were done: Stone from Stone,
  Strike the Earth!, The First Pour (the foundry part), and Water 5/5. Research: Foundational Structures, Metallurgy and Subterranean Farming.
  Hired a fourth dwarf (Gully, cook 6) with the starting coin. Spent every talent point except Björnger's and Gully's second ones.
- Watering early cleared "Lack of Drink" before it hurt. Food is not yet tested this run: no Toncaps or Cook House yet.
- **Likely cause of run 1's 0-health buildings:** a green slime was seen hitting the Cave Farm (-28 health) with nobody
  fighting it, and "Our buildings are under attack!" appeared at the same time. So bug 1 above is probably wandering slimes
  that no dwarf engages unless ordered to attack, not a bug in health. The missing health refill from Granite Blocks is still unexplained.
- **Mining a pit strands the miners.** Twice, mine orders below the hall floor left Björnger in a pit with no way back up.
  The `stranded_rescue` alert named him at once, and one Small Scaffold Stair fixed it. Recurs whenever digging goes down.
- The pit then took away the floor that the Small Foundry needed ("No suitable spot found"). The site was clear except for
  three missing floor tiles. Placing Bricks to fill them didn't help; I put the foundry elsewhere.
- Dwarves without a pickaxe (two of four at start) sit idle while mining is the only work. The "Dwarves Idle" tooltip says so,
  but only on hover.

## Run 3 (continuing run 2's Kings Uthrund, savegame41 → 44-47)
About 75 minutes of session time. Built a Small Smithy, Cook House and Dwelling (the Dwelling
never finished). Researched Blacksmithing, Cooking, Dwarven Trade Relations and Formalized Learning.
Hired no one, and killed slimes, crabs, rats and a Slime King. **Lost:** all four dwarves went
unconscious from starvation (savegame47). Causes, all play mistakes:
- Raw meat isn't food.
- The Cook House came too late, and one cook was too slow.
- Top speed burned hunger.

`docs/PLAY_STRATEGY.md` has the lessons. No new bugs: the 0-health buildings were rats and slimes
attacking, as run 2 suspected.

## Run 4 (new random game, Norringpool / Zakath, savegame48-52)
About 35 minutes. I applied the run 3 lessons:
- Hired a cook/healer at once.
- Built the Small Quarry, Cave Farm and Small Foundry.
- Researched Foundational Structures, Metallurgy and Subterranean Farming.
- Water 5/5. Harvested wild toncaps (1/5 stored). Mined 14 coal.

Stopped (by choice, not lost) at savegame52, with food fine for now and Cooking not yet researched,
since the sales for trade knowledge were still undelivered. Play mistakes:
- Sold the spare pickaxes, which left two of four dwarves unable to mine.
- Placed copper dig orders up a wall where no one can reach. They were silently accepted and never
  dug; that's vanilla behaviour, not a mod bug.

### Run 4, continued (2026-11-11, savegame52 → 57)
About an hour more of session time. The colony now feeds itself:
- **Food and drink:** a Cook House is up, with Roast Meat maintained at 6. Crab Broth is 1/2 for The
  First Feast. Hunting brings in meat, Water is maintained at 10, and two toncaps are sown on
  fertile soil.
- **Research and buildings:** Blacksmithing and Cooking are researched. The Small Smithy is built and
  making a Blacksmith's Hammer and two pickaxes, so all four dwarves will be able to mine.
- **Missions done:** Strike the Earth!, Water 5/5, Slimes 10/10, and one overworld mission.
- **Trade:** level 2 at Norringpool, after selling slime, ingots and ore.

Not done yet: the Dwelling and Formalized Learning missions. I stopped at a stable point (savegame57).

Lessons are in `PLAY_STRATEGY.md`:
- Ore comes from the background vein, not from the block in front of it.
- The quarry needs a chunk order.
- How the maintain modes work.

No new mod bugs. One tool fix: `tools/uinput.py serve` died when a client was killed mid-command
(BrokenPipeError). It now ignores clients that disconnect early.

## Run 5 (run 4's colony continued, 2026-11-11, savegame57 → run5_a, run5_b)
About 45 minutes of session time. Not won; stopped at a checkpoint, saved as `run5_b`.
- **Done:** bought Dwarven Trade Relations; sold ingots, slime and water to Norringpool (trade level
  2 → 3/6); accepted Expedited Expeditions (a Simple Lantern, queued at the smithy); placed a Dwelling
  (x 487, y 986, left of the smithy); queued Granite Chunks and Blocks.
- **Bug found and fixed: a broken quarry soft-locks the colony** (BUGS.md, `mods/building_self_repair`).
  On load the quarry, foundry and smithy were at 0 Building Health, and the Cook House reached 0 during
  play. Buildings at 0 are disabled, only a quarry makes the Granite Blocks that repair them, and every
  dwarf stood idle. With the mod the quarry and foundry recovered to 374 in one autosave interval.
- **How the colony failed (play lessons in PLAY_STRATEGY.md):**
  1. The vault was empty, so wages stopped. Every dwarf's Greed hit 0 (angry face), and their
     morale fell.
  2. Crafting crit failures ran 0.11-0.34 (1-3% per crafting hit); one effect is
     `CRIT_BUILDING_DAMAGE` (-20 to -53 a hit).
  3. Rats, slimes, a Slime King and a goblin also hit the buildings.
  4. Nothing kept Granite Blocks in stock, so nothing was repaired.
- **Unused coin:** three `prop/treasure_gold` piles and a treasure chest at x 426-432, y 986, in
  unexplored cave beyond the west corridor. Run 4's dig orders toward them (x 474-476, y 984) were
  behind a solid tile with no order, so they could never be dug.
- **Tooling:** `tools/camera.py` reads the camera rectangle and converts tile coordinates to screen
  points. Clicking a dwarf row made the camera follow that dwarf, which undid panning; dig orders
  placed then landed in the wrong place.

## Run 6 (new random game, King's Vorpool / Deadwoods, 2026-11-12, saves run6a, runsix, runsixb, runsixc)
About 2 hours 25 minutes of session time. Not won, stopped at a stable checkpoint (`runsixc`).
- **Built:** Small Quarry, Small Foundry, Cave Farm, Small Smithy and Cook House. All five were at
  full Building Health at the stop; blocks repaired damage automatically.
- **Research:** Metallurgy, Subterranean Farming, Foundational Structures, Blacksmithing, Dwarven
  Trade Relations and Cooking.
- **Missions done:** Stone from Stone, Sounding the Depths, Strike the Earth!, The First Pour, Roar
  of the Furnace, Slimes 10/10, Crab Broth 2/2, an overworld mission, Expedited Expeditions accepted
  and its lantern crafted. Trade level 2 at King's Vorpool.
- **Colony:** four dwarves (hired Lobus with the starting coin), fed by Roast Meat and toncaps, Water
  maintained. Lore stuck at 11 for the last half hour; vault at 0 because wages absorb every sale until
  the Greed bars fill (`PLAY_STRATEGY.md`, "Coin and Greed in numbers").
- **No new mod bugs seen in play.** Buildings never broke, which I credited to the block stock. It was
  also `building_self_repair`: its regen on every building kept any from reaching the death step, which
  later showed up as doors that never break (fixed to quarries only, Nov 12).
- **Next steps for this colony:** Formalized Learning at 15 lore, sell until all Greed bars are full,
  then buy Lumber for the Dwelling; send explorers to the frontiers `tools/frontier.py` lists.
- **Tooling:** `tools/uinput.py` now sends `semicolon` (Attack hotkey) and `minus`;
  `tools/frontier.py` lists exploration targets.

## Tooling found along the way (scratchpad scripts, not yet in tools/)
- **Use Windowed mode.**
  - In borderless fullscreen, `tools/shot.sh` images lag the game by 15-60 s.
  - In Windowed mode (Options > Graphics, saved by the game; 1280x1024 at +67+32) they are current.
  - Put it back to borderless when done.
- **Camera rectangle in game memory.**
  - It is float32 at about 0x6d6f000 in this process: four corner (x, y, z) triples, with the tile plane at z = 4 from +0x30.
  - It turns tile coordinates into window pixels, so no blind panning is needed. Verify the address per launch.
- **Live entity positions.** Search memory for two building positions, as `tools/memtrack.py` does. Save positions go stale within minutes.
- **`saveinspect.py` gets the wrong parent on this map.** Every item reports parent 1 (`logic/biome_region`), including food that is
  plainly stored, so its "held" and "loose" split is not reliable here.
