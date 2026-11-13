# Playing Hammerting well: lessons from my playthroughs

Read this before playing a colony, and add to it after each run. The bugs found on the way are in
`PLAYTHROUGH_2026-11-10.md` and `BUGS.md`; this file is only about how to play.

## Opening (first hour)
- Build order that worked in run 2: Small Quarry, Cave Farm, Small Foundry, all in about 36 minutes.
  That was twice as fast as run 1, which followed the tutorial's order.
- Queue Water at the Cave Farm early. It cleared "Lack of Drink" before it hurt.
- **Raw meat is not food.** Crab meat, mystery meat, rat haunches, eggs and gloom wheat give no
  hunger: they only feed a Cook House, which needs Cooking research (10 lore plus 3 trade
  knowledge). Dwarves starve beside a pile of meat (run 3, savegame44: about 20 meats, "Lack of
  Food", Björnger at 0 hunger). Food you can eat raw is listed below, with hunger per item:
  - Toncap mushroom (grow it).
  - Lichen 150, sugar beet 200, algae 350, bacon and cabbage 400, cheese 450.
  - Apples, licorice and fish (Cave Fishing research).
  Each dwarf burns about 0.08 hunger per tick, so 1,500 hunger lasts roughly half an hour at normal
  speed, and one lichen only about 3 minutes.
- Starting food lasts about an hour of play. Plan the food chain before it runs out:
  - Wild Toncaps and animals sit in unexplored caves, so explore early.
  - Growing Toncaps needs Fertile Soil plus one Toncap to sow.
  - The Cook House needs 4 Copper Ingots and 4 Granite Slabs.
- Spend the starting coin before wages drain it. Dwarves take vault coin as wages within minutes,
  so coin sitting in the vault can't buy food later. Run 2 hired a fourth dwarf with it (a cook).
- Two of the four starting dwarves have no pickaxe and sit idle while mining is the only work.
  Give them hauling or building, or make pickaxes early.
- **Never sell the spare starting pickaxes.** The chest holds tools for dwarves who lack them (run 4
  sold two for 16 copper each, leaving two of four dwarves unable to mine). Dwarves equip tools from
  storage on their own.
- **Ore comes from the background vein, not from the block in front of it.** A mine order on a
  solid ore tile only excavates the block (the Excavation job); the ore stays behind in the
  background. A second mine order on the now-open tile (the Mining job) drops the ore items. Exposed
  ore shows as coloured patches on cave walls. Mine those directly: "Strike the Earth!" counted
  nothing until I did.
- Dig orders must be reachable from a floor. A tile up a cave wall above open air (with no floor
  within reach below it) is accepted as an order but never dug. Run 4 lost about 15 game minutes on
  copper orders six tiles above the floor. Order ore at floor level, or build a scaffold stair first.
- Mining is slow with two miners. Use the Job Broker's "+" (wanted workers) on Excavation to pull
  them onto dig orders.
- A new building's footprint carves away the ore under it. Don't place the foundry on the copper
  vein you need for "Strike the Earth!".

## Food is the whole early game (run 3 collapsed from it)
- Run 3 continued run 2's colony (savegame41) for about 75 minutes of session time. All four
  dwarves starved to unconscious (savegame47), even with a Cook House, because nothing produced food
  continuously.
- What sustains food:
  - Cook every raw meat at once: Roast Meat is 1 meat + 25 fuel. Hunt every animal in sight, since
    each one drops meat.
  - Toncaps: right-click a fully grown wild toncap (stage 4/4) to harvest it, then sow more. A toncap
    up a cavern wall (no floor beside it) can't be reached, and the order shows a red "no" icon.
  - Buying lichen needs coin, and wages drain the vault within a minute or two.
- Hunger falls about 0.8 per second at normal speed (about 1,550 per dwarf, so about 30 minutes from
  full). At top speed that's only about 7 real minutes. Don't run at top speed until food comes in
  faster than it's eaten.
- Starvation drains health. At 0 health a dwarf falls unconscious, and the others then have to feed
  and carry them. Two unconscious dwarves out of four is effectively the end.
- One cook at a Small Cook House made only about one Roast Meat per 2 game minutes while hungry and
  tired. That's far too slow to rescue a colony that is already starving. Start cooking early.
- Research order that would have helped: Cooking first (10 lore + 3 trade knowledge; trade
  knowledge comes from selling). Then Dwarven Trade Relations (5 trade) for Dwellings, and Medicine
  for the Infirmary.

## Quarry chain
- Granite Chunk is the base: Crushed Granite takes 1 chunk, a Granite Slab 2, a Block and a Pillar
  more. A quarry with only slab and crushed orders runs dry, and slabs sit at "x0/6" forever.
  Keep a chunk order at the top of the quarry queue.
- Craft queues have three maintain modes (the round button beside Craft):
  - Do not maintain: a one-off amount.
  - Mountainhome: keep this many stored anywhere.
  - Building inventory: count this building's stock only; our `local_maintain_cap` mod caps it at
    4 times the colony total.
  The mode carries over to the next recipe you queue. Use Mountainhome for water and staples.
- A craft queue can show "Craft: Water" under Impossible Orders for a while after loading even though
  it runs. Check the log for spawns before chasing it.

## Fuel
- Fuel comes only from coal ore (500), charcoal (650, made from lumber at the farm) or lava (250).
  The foundry, smithy and Cook House each burn 25-50 per craft.
- Find coal before building the foundry. The map stores ore as content ids (material-record
  index + 2): 3 coal, 4 copper, 9 iron. Coal "piles" on open floor are mined like ore.

## Digging
- Don't dig straight down below a floor. It strands the miners, and it removes floor that buildings
  need ("No suitable spot found"). If you do dig down, put a Small Scaffold Stair in at once.
- Keep the main hall floor intact; place buildings on solid, explored floor.

## Drills
- A Cog Drill (Cogborne Transmission research) works on its own, with no dwarf and no queue. It only mines
  ore inside its own footprint: 6 tiles wide and 7 tall at the bottom, then 4 wide for the top 4 rows.
  - Each cycle it picks a random ore tile in that area and adds one ore to its own inventory.
  - About 1 cycle in 10 wears that tile out.
  - It stops when its inventory is full.
  - It needs fuel.
  - Read from `bt_create_node_mine_drill`'s update, game.x86_64.dll 0x180498890.
- The build tool accepts a spot with no ore at all, and the drill then sits idle with no warning. The
  user's first drill (savegame60, at 739,836) was 5 tiles left of a coal vein. Place it so the vein sits
  inside the bottom 6x7 block.
- Hardness counts against it. The drill's power is reduced by the hardest ore under it divided by 100,
  plus the rock's hardness:
  - Copper 60, coal 100, silver 150, iron 250, diamond 800.
  - A diamond tile among coal slows the coal too.
  - Hover the drill for its Drill Power, Inventory and Cooldown.

## Keeping buildings alive (run 5)
- Buildings lose health two ways:
  - wandering creatures;
  - crafting accidents. A crit failure can be `CRIT_BUILDING_DAMAGE` (-20 to -53).
- A building at 0 health is disabled until a Block of Granite repairs it (+500 each, 2 Granite Chunks).
- **Keep Blocks of Granite in stock from the start.** Set them to Mountainhome maintain at the
  quarry (4-6), with a Granite Chunk order above them. Haulers carry blocks to damaged buildings
  by themselves.
- The quarry must never reach 0 before the others are repaired. If it does, only
  `building_self_repair` brings it back (it regenerates quarries only).
- A door at 0 Building Health is destroyed, and invaders walk through. Repair doors with blocks too.
- Accidents rise when dwarves are unhappy. Keep Greed above 0 (coin in the vault), food coming in
  and morale up; the crit failure values (`tools/modvals.py PROF_*_CRIT`) fall with them.

## Coin
- An empty vault is the root of the spiral: no wages, then Greed 0, unhappy dwarves, accidents and
  broken buildings.
- Plan steady coin before anything else:
  - Sell surplus every few minutes (water sells for 6, Green Slime 10, Copper Ingots 14).
  - Mine `prop/treasure_gold` piles (each adds at least 100 to the vault).
  - Open treasure chests.
- Find gold piles in a save: entities named `prop/treasure_gold` in `debug_name_system/data.bin`, with
  positions in array 2 of `fixed_transform_system/data.bin`.

## Coin and Greed in numbers (run 6)
- Every dwarf shows "Coin Per Greed" (0.17-0.23 in run 6). Wages fill the Greed bar at that rate, so a
  dwarf at 0 Greed takes about 300-430 coin before the next coin stays in the vault. Kane went from
  0 to 1872 Greed after about 500 coin of sales.
- So with four dwarves the vault holds nothing until roughly 1,200 coin has been sold. Buying food
  needs the coin in hand at the moment of the click: plan purchases right after a sale lands.
- Thrifty Outlook (tier 1 talent, +0.02 passive Greed gain) slows the drain. Run 6 took it on three
  dwarves first.
- The Simple Lantern (Expedited Expeditions) sells for 2 silver 99, the best early sale.

## Run 6 opening (worked: stable at 2 hours, all buildings at full health)
1. Hire the recruit with the starting coin at once (a blacksmith/healer).
2. Small Quarry first, Granite Chunks queued. The start chest already holds 9 Blocks of Granite.
3. Metallurgy, then Subterranean Farming, then Foundational Structures. Foundational Structures
   unlocks the quarry's Block of Granite recipe: set it to Mountainhome maintain 5, with chunks at 5.
   A Cook House at 2,200 health got +500 from a block with no order from me.
4. Mine the coal and copper strips in the hall floor twice (block, then background ore).
5. Foundry (maintain 20 Copper Ingots), Cave Farm (maintain 20 Water), harvest every ripe toncap.
6. Blacksmithing, then Dwarven Trade Relations (5 trade lore), then Cooking. Cook House with
   Roast Meat set to 20 and high job priority: four hungry dwarves were fed within one game day.
- Lore came from missions and from discovering rooms, not from walking around: lore sat at 11 for
  the last half hour. `tools/frontier.py <save>` lists explored tiles next to unexplored connected
  cave, for Move To orders.

## Victory is a long research chain
- The Large Vault (Righteous Affluence) needs Granite Pillars, Granite Slabs, Support Beams and Star-cut
  Gems. Star-cut Gems need Lapidary Arts (tier 5, 45 lore + 10 trade lore), and the vault itself is
  further right in the tree. Formalized Learning (15 lore) is the first step toward steady lore.
- Affluence with `reachable_affluence`: coin fills vaults in build order, so the small and medium vaults (about 505 gold)
  fill before the first Large Vault, which then needs 10% of 2,000 gold. Tearing down a vault moves its coin into the
  remaining vaults (`vault_system_remove_destroyed_entities`), so a medium vault demolished after the Large Vaults stand
  sends its coin on to them (read in the code, not tried). The mission only checks when coin is added to a vault, so a save
  rewritten by `tools/save.py vaultcap` needs one more deposit (a sale) after loading. Load it from the Load menu: Continue
  opens `lastsave`, which is the unedited save. One Large Vault completed the "build 2" part in
  play, so tearing down the medium vault (its coin tops up the small one, the rest goes to the Large Vault) is the finish. No market buys gems or the Star of Mara.
- A dwarf can only eat food that he, or a dwarf who can reach both him and the food, can walk to. A stranded dwarf
  goes for the only food in his pocket, even beside a lair, and bought food stays at the settlement until fetched.
  Far build orders (a shaft 600 tiles below the colony, SouthXanforge savegame73) lose to the near ones in a long
  builder queue (`re/notes/job_broker.md`), so give a rescue route High priority or clear the queue.
- The cut gems (Rough, Cabochon, Trilliant, Brilliant) are not gems found in the ground: the White Anvil cuts them
  in turn from any raw gem. In vanilla every step takes 3 identical items, so one Star of Mara costs 243 raw gems of
  one kind (`re/notes/material_subtypes.md`); with `gem_cut_rebalance` it costs 9 of any kind. Gems come from gem
  veins in most biomes and as rare drops from ore. Crafting a Star unlocks the Star of Mara achievement.
- Sulphur Sprouts (Dwarven Licorice) grow wild only in the Underworld, and no market sells them. On SouthXanforge
  (savegame70) the Underworld is one region along the bottom of the map, y 0 to 175-255 across the whole width, with
  the colony at y 988 and no Underworld tile explored yet; the nearest dig is about 150 tiles straight down from y 391, x 384. After the first sprouts, farm them (`re/notes/lava.md`, licorice chain).
- A Dwelling needs Lumber, a Granite Pillar and a Block of Granite. Lumber only comes from the market
  (59-94 coin), so it waits on the Greed bars filling.

## Threats
- Wandering slimes damage buildings, and nobody fights them unless ordered. When "Our buildings are
  under attack!" shows, find the slime and order an attack. This was probably run 1's 0-health
  buildings.
- In run 6, green slimes spawned three times in the same spot beside the foundry (about 574, 971),
  plus rats, a fox and crabs. Each attack order killed its target within seconds. A mole sat inside
  solid rock next to the foundry all game and could not be targeted; buildings stayed at full health.

## Economy and overworld
- Lumber from the overworld (lumber mill, driftwood, reclaimed) is enough; no need to grow every
  plant. Rails are optional, and so is the God of the Forge (its mission pays 50 Mountain Lore).
- Bought goods wait in the settlement until a hauler fetches them, and the starting chest needs its
  overworld source enabled (the default).

## Driving the game (tooling)
- Use Windowed mode: in borderless fullscreen, screenshots lag 15-60 s. Switch back afterwards.
- Spend talent points as soon as the yellow plus shows, and check "Dwarves Idle" at every check-in.
- Use the Alerts and Cave Missions panels as the to-do list, red alerts first.
- Talents:
  - Tier 2 talents have personal requirements (a specific Tier 1 talent) and sometimes a colony
    research. Hover a talent before choosing it.
  - Double-click selects a talent, then Acquire buys it.
- Research: one click buys a topic when you can afford it. Check the prerequisites in the left
  panel (Medicine needs Dwarven Trade Relations).
- Craft panels:
  - Shift-click Craft queues 5.
  - Recipe positions shift as new recipes unlock, so read the recipe card before queueing (I queued
    Crushed Granite instead of blocks once).
- Job Broker cells: blue = allowed, yellow = favourite, red = forbidden. A click cycles them, so
  don't click to "enable".
- Escape opens the pause menu when no tool is active, so don't press it after a placement (build
  tools close themselves).
- Attack (hotkey `;`) only registers as a single click on the creature's sprite, about a tile above
  its stored position. Drags and clicks on the stored tile did nothing.
- Move To needs an explored target tile; an unexplored one shows "not valid".
- F1 switches between cave and overworld, F7 opens the trade list. Zooming the cave far out also
  switches to the overworld. Once the overworld camera showed only cloud and neither panning nor the
  Locations list brought the map back; saving and loading fixed it.
- Mission items: the Missions tab of a settlement accepts a mission with the small checkbox beside its
  name.
