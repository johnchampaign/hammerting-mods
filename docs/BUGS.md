# Hammerting: outstanding bugs in the final version (1.2.39.0)

Compiled 2026-10-31 from:
- **Steam forums.** All 286 *Report A Problem* threads and every bug-related *General
  Discussions* thread.
- **Steam reviews.** All 1,572 English reviews, about 565 of them written after the last
  update.
- **Reddit.** All of r/Hammerting: 369 posts and 1,442 comments.
- **Other sources.** The GOG forum and its reviews, ProtonDB, the Steam news and patch
  notes, and the Fandom wiki.

Two items were also found in the game code itself (section A0).

**There is no later build.** 1.2.39.0 is the *Quality of Life 4* update of 7 March 2022.
The public branch has been unchanged since then (Steam app info: build 8272469). The
developers announced the end of development on 17 March 2022. Every report dated after
7 March 2022 is therefore a bug in the version you have.

Status labels:
- **FINAL**: reported after 7 March 2022, so confirmed in 1.2.39.
- **PRE**: only reported before 1.2.39, with no patch note claiming a fix. Probably still
  present.
- **FIXED?**: a patch note claims a fix.

Mod outlook:
- **D**: probably fixable as a data mod (records, `.entity`, localization).
- **C**: needs a code patch to `game.x86_64.dll`.
- **E**: engine limit. Mitigate it, don't expect a fix.
- **X**: outside the game (drivers, platform). Workarounds only.

Source shorthand:
- `S1/<id>` = steamcommunity.com/app/760650/discussions/1/<id>/
- `S0/<id>` = the same under /discussions/0/
- `R/<id>` = reddit.com/r/Hammerting/comments/<id>
- "review (date)" is a Steam user review.

---

## A0. Victory conditions (found in the code)

| # | Problem | Status | Mod |
|---|---|---|---|
| 0.1 | **Affluence victory is effectively unreachable.** Its build part says two Large Vaults, though one completed it in play, and then it needs a Large Vault 100% full: coin fills vaults one at a time in build order, the mission gets the fullness of the vault that just received coin, and a leftover developer `HACK` ignores vaults holding 1,000 gold or less (corrected Nov 12 from `vault_system_add_coin`; earlier notes said total capacity). A Large Vault holds 50,000 gold, while a colony banked 15-30 gold per real hour after wages. | Code | D: **done** (`reachable_affluence`: Large Vault holds 2,000 gold, target 10%, so about 505 gold in the earlier vaults plus 200; `tools/save.py vaultcap` for vaults already built, `tools/save.py affluence` for the target) |
| 0.2 | **Diplomatic ("World Conquest") victory needs all 35 overworld locations to be owned or allied at once.** The player can never own a location other than the mountainhome. Alliances form only through quests, and the AI factions keep fighting each other. Players report conquest quests not registering (review, Jan 2022) and the overworld simulation stopping (review, Aug 2024). | FINAL | D: **done** (`reachable_diplomacy`: 33% of locations, rounded up; see `re/notes/diplomacy.md`) |

## A. Crashes, softlocks and save-breaking bugs

1. **Entity limit: items vanish, then the save breaks.**
   - The engine has a hard limit of 64K entities. Floor items, fluid units, seeds and ore
     all count.
   - Above about 50K entities, the oldest items start silently despawning, including
     gems and Stars of Mara in storage. Going past the limit has broken saves.
   - The developer said the limit "will not change" (Jan 2022).
   - Probably the root cause of several later reports:
     - "8 or more mines/quarries break the game" (Mar 2026);
     - ore vanishing from drill walls;
     - item hoards disappearing.
   - Workaround: sell or use stock, cap seeds and crops, seal fluid sources.
   - **Mod (Nov 2026):** `keep_stored_items` keeps stored items at their normal rot rate between 75% and 90% of the limit, the band where the game rots them 500 times faster. Loose items and the band past 90% are unchanged. Stored items do still rot fast past 90%, and the limit itself stays.
   - FINAL (consequences). **E**. A mod can reduce floor clutter and overproduction.
   - Sources: S0/3200371016617725813, S0/798965853658812692, S1/3200370471673399196.

2. **Crashes that grow with base size, ending in a save that crashes on load.**
   - Mid-to-late game it crashes every 30 minutes or so.
   - One more building past some limit crashes every time.
   - Eventually the save crashes on every load. Players report losing several runs.
   - Probably the same root cause as A1.
   - FINAL: reviews from Apr 2022, Dec 2022, Apr 2026 and Jun 2026; R/1u4m60l (70+
     dwarves, largest map). **E/C**.

3. **Crash in `relation_component_system_change_relation` (entity.x86_64.dll,
   0xc0000005).**
   - It recurs after every reload until the save is dead.
   - Suspected causes: dwarf-relationship conflicts, or the overworld licorice alliance.
   - The poster avoided it by hiring dwarves without relationship-penalty perks.
   - FINAL (Apr and May 2023). **C**. A good first code fix: the faulting function is
     named in the crash.
   - **Code findings (Nov 2026):** the function checks nothing. It reads through NULL
     when the pair has no relation of the given type (0x18007eac0) or the owner's opinion
     key-value is missing (0x18007eba9). The opinion tick runs over every faction pair
     shortly after each load, which fits "recurs after every reload". **Mod:**
     `relation_crash_guard` (entity DLL patch: no relation → no change; missing opinion →
     starts from 0 and is recreated). Not reproduced (no crashing save); tested for
     regressions only: faction opinions and dwarf relationships still change. See
     `re/notes/relation_crash.md`.
   - Source: S1/3827539207871629471.

4. **Crash when completing the Dwarven Licorice / Elves alliance quest.**
   - It crashes every time, which softlocks the diplomacy route.
   - Workaround: lower your standing until the quest drops, raise it again, then
     complete it.
   - FINAL (review, Nov 2024). **C**. Probably related to A3.
   - **Code findings (Nov 2026):** the quest is MISSION_OVERWORLD_ALLIANCE (deliver 10
     Dwarven Licorice while the faction ESTEEMS you). On completion
     `MOUNTAINHOME.JOIN_ALLIANCE(...)` changes the opinion of every faction related to the
     ally without checking that each pair has an opinion relation: the A3 fault. Covered by
     `relation_crash_guard`; not reproduced.

5. **Random "Exception caught 0xc0000005" crashes.**
   - Reported in single-player, when leaving the overworld map, and when starting a new
     game.
   - FINAL (Jul 2022, Apr 2024, Mar 2025). **C**.
   - **Local logs (Nov 2026):** all 246 session logs on this machine were searched. The only exceptions (seven, 0xc0000005)
     are in my test sessions with experimental mods (`pumptest`, `wartest`, five `bcntest` runs of the abandoned
     `buy_coin_notice`, explained in `re/notes/market_buying.md`); none in the user's own play of KrazJomsglind.
   - Sources: R/qx37e6, GOG "Crashes" thread.

6. **Softlock: low-health dwarves refuse to fight ("death panic spiral").**
   - Wounded dwarves retreat and ignore attack orders, even when they're militia with
     weapons. The colony gets chewed through, and one player lost three runs in a row.
   - Workaround: rush medicine (gauze, slime potions).
   - FINAL (Apr 2022). **C/D**: the AI utility data may control the retreat threshold.
   - **Code findings (Nov 2026, `re/notes/panic_spiral.md`):** below 25% health a dwarf
     doesn't approach enemies, ignores attack orders (both score 0) and, if armed and 20+
     tiles from the entrance, retreats there; below about 40% with medicine reachable it
     leaves fights to heal (rank 7, above combat at 6). Health returns only through instant
     items (gauze 350, slimebalm 500, ...); no natural regeneration was found, so without
     medicine a wounded dwarf stays out of combat for good. That is the spiral.
     **Mod:** `steady_fighters` lets attack orders work at any health. Lowering the other
     thresholds to 10% was tried and dropped: with all dwarves at 20% health in the user's
     rat raid, a level-9 dwarf fought on and died, while unpatched she held back and lived.
     The order fix itself is not tested in game (needs a manual attack order).
     **Mod:** `natural_healing` adds STATUSBAR_HEALTH_GAIN 0.05 per tick (0.5 health per
     game second) to CLS_DWARF, so wounded dwarves recover without medicine. Tested: a dwarf
     set to 950/1900 gained 16 health in 31 s with no food or items.
   - Sources: S0/3275815819061302388, S1/3202617741920197937, S1/3202617741912309370,
     S1/3202617741907856253.

7. **Greed loop: dwarves stuck at the entrance chest trying to get paid.**
   - Low-greed dwarves camp at the starting chest or jog in place by the entrance, even
     with full vaults. It survives reloads; one player "bricked 4 games".
   - A variant: a dwarf with a full purse loops between "Stashing coins" and "Going to
     work".
   - Likely trigger: QoL4's greed scaling, under which higher-level dwarves need much
     more coin.
   - FINAL (Mar 2022 to Mar 2025). **D/C**: greed rates are data; the pay behaviour is
     `BT_TAKE_GOLD_FOR_GREED`.
   - **Code findings (Nov 2026, `re/notes/greed_loop.md`):** wages are paid only at
     `building/chest_start` (from the whole hoard), only below 75% greed, and the take node
     reports success even when it moves no coin; a failed or empty wage trip is recreated at
     once (the 5 s cooldown is set on the deleted instance). A dwarf carrying more than its
     purse holds (10 + 50 x level) scores the wage trip as worthwhile through an unsigned
     wrap (0x1802de54e, 0x1802de561), so it can repeat empty trips. Purses empty only into
     the dwarf's own dwelling, and the dwelling menu wants more than 99 carried coin.
     **Not reproduced:** a test dwarf with 2000 coin in a 1310 purse kept working and
     levelling for several game hours (the wage trip loses to real work). Candidate fix:
     signed compares at those two sites (`48 0f 42 c1` -> `48 0f 4c c1`, `4c 0f 42 c9` ->
     `4c 0f 4c c9`). **Mod:** `greed_purse_guard` applies them (preventive; the loop
     itself was not reproduced).
   - Sources: S0/4658416565932110849, S0/4633736978453562683, S1/4358997268256592010,
     S1/3187992943275564519, S0/3274687384235600297.

8. **Overworld invaders freeze outside the entrance and multiply without limit.**
   - Comes with QoL4's "War on the Mountainhome" option.
   - Workaround: disable war on the Mountainhome and enemy waves at map generation.
   - **Findings (Nov 2026, `re/notes/overworld_invaders.md`):** nothing in the overworld attack
     or generic wave code caps or checks living invaders, which explains unlimited growth if
     they do not die. The freeze is not reproduced: attacks fired directly in a test build were
     all killed, and edited wars revert to peace, so the real army path was not exercised.
     **Mod:** `invader_cap` stops new attacks and generic waves at 24 living invaders (tested: 24
     instead of 35 in a burst, resumes after kills). It bounds the pile-up but does not cure a freeze.
   - FINAL (2025, also on the latest GOG build). **C**.
   - Sources: S0/720115994490568717, S0/596271645583230881.

9. **Late-game breakdown of dwarf jobs (effectively a softlock).**
   - After many hours, dwarves stop collecting, cooking, eating, building or crafting,
     even with thousands of materials on hand. Many players restarted runs because of it.
   - Contributors:
     - seed overstock (B1);
     - full building inventories (B2);
     - floor clutter;
     - impossible orders;
     - Restoration priority turned down.
   - Large maps or 30+ dwarves make it worse: they stop building scaffolds, rails or
     elevators far from base.
   - FINAL (Mar 2022 to Aug 2026). **C/D**.
   - Sources: R/1cgsyb7, R/1u4m60l, R/1br0xf5, S1/2960544821836036734,
     S0/3819655917507239893, S0/6126615404777760415.

10. **Dwarves stuck floating mid-air or embedded in terrain.**
    - After digging, or when the block under them is removed, dwarves hover and can't be
      moved. They may starve.
    - One player found "90% of my dwarves stranded" after a reload (Mar 2026).
    - Other variants:
      - endless movement or jump loops;
      - digging themselves into pits;
      - a new recruit stuck on a ledge who dies repeatedly.
    - Workaround: build a block or scaffold under them, or dig them out.
    - **Code findings (Nov 2026, `re/notes/stuck_dwarves.md`):** the only recovery is the
      fall sensor (BT_FALL lands the dwarf and snaps him to the nearest edge). For a dwarf
      with a valid graph position it checks support only when his MOVEMENT_STATE key is
      missing or STAND, but walking never writes the key and vertical jumps leave JUMP or
      CLIMB behind (two of six dwarves in the user's save had a stale JUMP), so such a dwarf
      hovers when the block under him is dug. A dwarf with no graph position is never
      re-snapped when nodes are added, so building under him does nothing by itself; and the
      fall/land cycle repeats forever when no edge is within 96 tiles. **Mod:**
      `fall_when_idle` (runs the support check for every dwarf with no movement behaviour
      running). Regression-tested on the user's save over two autosave intervals: no
      spurious falls or injuries, dwarves kept working and levelling, stale JUMP states
      cleared. The hovering itself was not reproduced.
    - **Dwarf cut off by a finished stair (Nov 2026, end of `re/notes/stuck_dwarves.md`):** on East Tharnlaw, finishing a scaffold stair piece turned one open tile of another stair's bottom landing into walkway. That closed the only route between a cavern and the colony, and the dwarf inside then idles and starves, in all 8 runs from savegame16, with or without mods. Reloading doesn't help, because the tile is saved. Found live with `tools/navreach.py`. Why that tile changed at that moment is unknown. This may be behind some "stranded" reports. **Fix in play:** a stair piece that gives the route a real link. On that colony, a Small Scaffold Stair directly under the stairs at 626, 953 reconnected the cavern and the dwarf recovered (2 runs; the first survived a reload, the second started from a save with a pending tear-down of the stair above, cancelled first). Tearing that stair down also freed the dwarf (1 run), at the cost of the stair. The game's Stranded Dwarves alert shows this state. **Mod:** `stranded_rescue` moves a dwarf stranded for 10 game minutes in a row back to the Entrance, unless more than half are stranded. The route stays closed, so he can be cut off again if his next job takes him back in. Tested on this colony (real rescue once at a 1-minute timer, the 10-minute value with the check forced, no fall damage, no exceptions); not in long play. It doesn't cover hovering dwarves with no graph position, whom the alert doesn't count either.
    - FINAL (Mar 2022 to Mar 2026). **C**.
    - Sources: S1/4658416565924987030, S0/3274687384235600297, S0/3873717500286475400,
      S0/3091137796306332301, R/td78tb.

11. **Hammerting meeting softlock.**
    - Calling a meeting while any dwarf is stuck freezes the colony. Everyone waits
      forever, so nobody can rescue the stuck dwarf.
    - The developer acknowledged it (Jan 2022).
    - **Code findings (Nov 2026, `re/notes/hammerting_meeting.md`):** a Hammerting is the
      talk system's global conversation at the Great Hall. Every free dwarf who can reach it
      is summoned; attendees can't work and their talk action outranks work, food and sleep.
      The session starts only when every participant is seated, with no timeout and no
      cancel, so a dwarf who can't reach his seat holds everyone. **Mod:**
      `hammerting_deadline` (the session starts at most 120 s after the call). Not tested
      in game: the user's colony has no Great Hall.
    - PRE. **C**.
    - Source: S1/3200371016631574279.

12. **Starvation next to food.**
    - Dwarves never eat food from the floor. This is intended, but it starves colonies,
      and the help text barely mentions it.
    - They skip food reserved by big cooking or tavern queues.
    - Some colonies eat only raw food and ignore hundreds of cooked meals.
    - Cooks sometimes stop cooking.
    - Dwarves chase lichen into slime lairs.
    - Workaround: build a food storage chest early, and keep crafting queues small.
    - **Code findings (Nov 2026):** the eating code does not reject floor food. It
      rejects food reserved by anything else (a cooking or tavern queue, a hauler on the
      way, a sale), food on unexplored tiles, and food no dwarf can reach. Storages never
      collect loose items by default (see B1), so harvests and dropped food stay on the
      floor and rot in about 2.8 game hours. **Mod:** `ground_pickup`. Not yet fixed:
      food a queue has hauled into its building stays reserved, and a stalled cook house
      keeps it reserved indefinitely (one held 28 items all day). `mods/eat_reserved_food`
      (code cave) lets dwarves eat reserved food that is still outside the building, but
      that case did not come up in testing, so it is not in the recommended set. See
      `re/notes/food_ai.md`.
    - **Why cooks stop cooking (Nov 2026):** an item that arrives at a production
      building is reserved by the first queue entry that wants it, up to that entry's whole
      queued amount, and stays reserved until the entry completes. Entries missing one input
      therefore keep the inputs they have forever. In the user's colony seven cook-house
      entries each held part of a recipe (21 water, 3 algae, flowers, lichen, gloom wheat)
      and none could start, while the colony lacked drink. See
      `re/notes/production_stall.md`. **Mod:** `whole_batch_inputs` (an entry reserves
      one craft's worth). An earlier version also required every input to be available
      at once, and that caused stalls of its own: floor items don't count as available,
      so a foundry with 425 ore on the floor stopped. That part was removed on Nov 3. The
      earlier test (a one-time amount change let the cook house release 22 items) was on
      the removed version and has not been repeated.
    - FINAL (2022 to 2026). **D/C**.
    - Sources: S0/839500962846512385, S0/3461597549827575768, S0/6077070109432826801,
      S0/4287991687311369285, R/sw1n4z, R/s02c5y.

13. **Cargo carts and minecarts get stuck.**
    - Carts stall at stations without unloading.
    - Minecarts freeze after several reloads and can't be removed (2025).
    - Carts float after their rail is removed, and tearing one down crashed the game.
    - **Findings (Nov 2026, `re/notes/carts_elevators.md`):** vehicle queues aren't saved, which fits "save and
      reload fixes it", and the code has no-timeout states for riders (a dead rider's queue entry parks the
      Handcar for good). **Mod:** `rail_fixes` removes dead riders from queues and frees every rider when a Handcar
      is torn down; regression-tested, neither bug reproduced. Tearing down a floating Handcar worked with no crash.
      **The cargo cart stall did not reproduce (Nov 2026):** Carts delivered 30 items to a chest and ended empty, in 3 runs, including after
      three reloads in a row. Trips were few and short, and a save during a trip was not tested. The detailed reports predate 1.2.39; the
      2025 ones are one line each.
    - **New report (Steam, 2026-11-20):** about 20 Handcars, 5-10 Carts and 6 ore grinders; now and then a Cart takes ore for a smelter
      and never delivers, and the smelter waits until its production is paused and unpaused. **Mod:** `cart_timeout` fails a Cart's
      haul once it has stood still for 30 game seconds during it, dropping its own route entry, so the job is offered again (the same
      exit pausing takes). Tested 2026-11-22 on a copy of SouthXanforge savegame75 (one Cart, 3679): at a 1-second limit it never fired
      in 3 minutes of the Cart hauling (a hauling Cart never stood still; it stood still only between jobs); at 0.05 s it failed the
      Cart's haul on every tick, about 1,700 times, and the Cart took the job straight back each time, with no exceptions. The stall
      itself was not reproduced.
    - FINAL (Oct 2023, 2025). **C**.
    - Sources: S1/2958292387827395207, S0/3887226763718533547, S1/4241812037675269814.

14. **Elevators.**
    - No platform appears, so elevators "don't work" (Dec 2022, on 1.2.39).
    - "Dwarves can't reach next elevator section" when building downward (Mar 2022).
    - 20+ carts stuck on elevator rails.
    - A fan is testing their own elevator fix (R/1uz1lea, S0/576047359821315412,
      Jul 2026).
    - **Findings (Nov 2026, `re/notes/carts_elevators.md`, tested on colony copies):** the "platform" can't be built
      (its recipe depends on BUILDING_NONE), and only a **Handcar** carries dwarves, while the game's help says "a Cart to
      ride in". With a Handcar and a complete line, elevators work, also after a reload. "Can't reach the next section"
      reproduced: an Elevator Rail order stayed unreachable for 7.7 minutes with only a Cart on the line and was built
      within a second of adding a Handcar. Building down two sections with a Handcar worked. A missing piece shows no error.
      **Mod:** `rail_help` corrects the tooltips and help pages. No code bug was found behind this report.
    - FINAL. **C** (mostly misleading text).
    - Sources: R/zpr38d, R/tlgfdl.

15. **Scaffolds and 4x4 ladders can't be demolished.**
    - The remove order is refused. One bugged scaffold marks every connected scaffold
      "not reachable".
    - **Code findings (Nov 2026, `re/notes/scaffold_removal.md`):** Tear down creates a
      builder order at the piece; it is refused (":cross:") for no valid target or an
      existing order on that piece (cancel by dragging Cancel over its pivot tile). The
      order keeps only the one work position nearest the entrance, and the far end of a
      connected run goes first. "Not reachable" means no builder's path reaches that one
      position; mid-column pieces may have no valid position at all. Which link fails in
      practice is not confirmed. Candidate patches (all positions count; stair paths
      count) are in the notes; not built. The user's colony (17 small scaffold stairs, 8
      stone bridges) had no pending tear-down orders.
    - **In-game test (2026-11-02, copy of the user's colony, 16 mods installed):** not
      reproduced so far. The top and a middle piece of one column were both removed by a
      builder, 1-2 minutes after ordering, so the "mid-column pieces have no position"
      theory is wrong for that piece. After those two removals one dwarf was reported
      stranded, and a later order, probably on a piece of another column, sat at 0% for six
      minutes with no "not reachable" text and no listing under Impossible Orders; why is
      not known, and its target was not confirmed. Bottom pieces, the other two columns,
      bridges and 4x4 ladders are untested. No patch is justified yet.
    - **"It won't let me" (Nov 2026, the user's colony, `re/notes/scaffold_removal.md`):** the user's order on a stair sat at 0% and a second try was refused. Left alone at speed, all three of their pending tear-downs ran within about 1.5 real minutes (1 run). So the order was waiting its turn (about 7 game minutes there), and the refusal is the existing order: the tool's hover says "There's already an order here." **Mod:** `teardown_hint` explains both in the tooltips; seen in game. A stuck order or a refused piece with no order has still not been reproduced.
    - FINAL (Feb 2023, 2024, 2025). **C**.
    - Sources: S0/3781371514573992048, S1/2958292387843641428.

16. **Single-report crashes:**
    - equipping a crafted Mining Pickaxe (Dec 2022, S0/3717188878659202520);
    - building scaffolding (Apr 2022, S1/3274687384245553562);
    - saving (Mar 2024, S1/7056650139346027709);
    - clicking quickly in the dwarf list, or an alert that jumps to a dwarf (reviews,
      Jun and Nov 2024).
      Not reproduced (Nov 2026, copy of KrazJomsglind savegame32, shipping mods, 1 run): about 550 clicks on dwarf
      rows 5-30 ms apart at normal speed and at top speed, double-clicks, 80 fast clicks on the dwarf panel's
      previous and next arrows, and the Outdated Equipment and Impossible Orders alerts clicked between dwarf rows
      caused no crash or exception;
    - deleting a structure still waiting to be built (GOG review, Dec 2024).
      Not reproduced (Nov 2026, copy of KrazJomsglind savegame32, `_test_rails` with real track costs, 1 run):
      Railway pieces cancelled with the Cancel tool while set in rock with no route (dig orders added, track not
      yet delivered) and 55 s after placement on open floor (a piece there took 68 s to build) caused no crash
      or exception. Cancelling leaves the dig orders the placement added. Buildings and Tear down were not tried.

    All FINAL. **C**.

17. **Research tree blocked.**
    - "Unable to proceed in research tree due to a bug" (Aug 2023). You can also lock
      yourself out of tech.
    - Probably from QoL4 rearranging the tree.
    - **Data findings (Nov 2026, `re/notes/research_tree.md`):** no missing prerequisites,
      cycles or either/or choices. The lock-out is Mountain Lore: the tree costs 1326 ML and
      ML is renewable only through Land Survey, which needed Geological Surveys (about 140
      ML into the tree); before that ML comes only from one-off missions and discoveries.
      The West Hirdness colony had 3 ML and no Geological Surveys. **Mod:**
      `early_land_survey` (Land Survey unlocks with Formalized Learning; verified in game: the
      recipe appears in the Arcane Workshop). Unchecked: a possible double charge when Buy is
      clicked twice while the research screen has the game paused.
    - FINAL. **D**.

18. **Autosave freezes the game for up to a minute, and can't be turned off.**
    - FINAL (Jun 2024). **D/C**: there may be an autosave option (`gamestate-autosave`).
    - **Findings (Nov 2026):** autosave runs after 300 s of unpaused game time, but that value
      is overridden by a developer debug-menu setting (gamemedia.x86_64.dll "Game/Gamestate/
      Autosave interval"). The launch option `--gamestate-autosave false` turns autosaves
      off (tested: no autosave in 4 minutes). **Mod:** `autosave_interval` (default every 15
      game minutes; tested with a 1-minute build: autosaves came exactly 60 s apart).
    - Sources: S1/3121550424349869737, S0/4658416565928103725.

19. **Multiplayer.**
    - Co-op joins hang in the lobby.
    - Desync crashes every 3–5 minutes.
    - GOG co-op needs Galaxy.
    - FINAL (2023–2025). **C**: low priority for single-player completion.

## B. Broken mechanics that stall progress

1. **Overproduction and floor litter from "Maintain" orders and farms.**
   - When a building's inventory fills, it spews items onto the floor, where dwarves
     ignore them, and the cycle repeats.
   - Farms stockpile seeds past their limit: "thousands of barley seeds".
   - A Maintain order combined with a take-from-inventory storage crafts forever.
   - Feeds A1 and A9.
   - **Code findings (Nov 2026):**
     - New storages default to "take from overworld" only (`haul_system_create_components`
       sets the source mask to 0x04), so mining, harvests, fishing piers and spills stay
       loose until they rot (about 2.8 game hours; the colony tested had 657 loose items).
       **Mod:** `ground_pickup` makes the default "ground + overworld". Tested on the
       West Hirdness save: loose items 657 → 384 and stored 239 → 510 in five game minutes.
     - Local Maintain counts only the building's own inventory, so once haulers move the
       output it crafts forever. Global Maintain counts every item, loose or stored.
       **Mod:** `maintain_hint` explains this in the tooltips, and `local_maintain_cap` stops a Local
       Maintain order once the colony holds 4 times its level (tested with the factor at 1, one colony).
     - No code path was found that makes extra seeds: a harvest throws one crop and one
       seed on the floor, and sowing takes one seed.
     - Every item rots; past 75% and 90% of the 64K entity limit, stored items rot too
       (in hours, then minutes). This is the "items vanish in big colonies" report (A1).
   - FINAL (to Aug 2025, Jun 2026). **C/D**.
   - Sources: S0/4658416565937643457, S1/3187988461096478677, S0/4293692546845361055,
     R/1ub5qhh, R/tprjoy.

2. **Deadlocks from reserved or full inventory slots.**
   - Queuing every dwelling upgrade fills all 18 slots.
   - A factory's storage full of reserved inputs leaves no slot for water.
   - A cookhouse fills with water and stops.
   - **Code findings (Nov 2026):** a queue entry reserved each arriving input up to its
     whole queued amount and kept partial sets until it crafted, so entries each holding
     part of a recipe blocked one another (see A12, `re/notes/production_stall.md`).
     **Mod:** `whole_batch_inputs`.
   - **Full slots (Nov 2026, `re/notes/production_stall.md`):** small buildings have 120 slots, and that mod limits what an entry reserves (one craft, or 5 for one-input recipes), so normal queues
     don't fill up; nearly every smithy recipe queued at once could (156). Reproduced with slots cut to about the current count on a colony copy: without the mod the cook house froze with 30 items claimed and cooked nothing at the end; with it,
     it kept cooking (1 run each). No further mod. The dwelling report (18 slots, Jan 2022) predates 1.2.39, and upgrade units have 64 slots now. Many duplicate entries and mission deliveries are not excluded.
   - FINAL. **C**.
   - Sources: S1/3200370471682063490, S0/3887227420039649316, R/tkppg6.

3. **Orders lock onto one material subtype.**
   - One gem, bone or timber of the wrong subtype blocks an order, even with dozens of
     the generic material available.
   - Smiths use the cheapest (or the most expensive) metal unless you pick it.
   - Stations forget material choices.
   - **Code findings (Nov 2026, `re/notes/material_subtypes.md`):** a slot needing more
     than one item is ready only with that many identical items (same type and full
     material modifiers), because crafted outputs inherit the input's material; yet while
     short it accepts any item of the class and never lets a mismatch go. Material choice is
     kept only on the station's template, and every recipe click reset it. **Mod:**
     `class_matched_inputs` (slots whose material isn't passed on, and building recipes,
     count every claimed item; clicking the current recipe keeps the choice). Tested: the
     user's Cave Farm held 1 sturdy + 1 restless bone for Bone Ash (2 bones, material not
     inherited) forever; with the mod it crafted. The template fix is not tested in game.
     **Mixed holds in crafts that inherit material (Nov 2026):** `one_kind_inputs`. A slot holding
     part of a craft takes only more of the same kind, and an entry already holding a mix gives
     it back and takes one kind. On a copy of the user's savegame32 (about 50 game minutes at speed 3,
     1 run each), without it a Whitesmith's Rough Cut took a ruby on top of its 2 sapphires while
     the other Whitesmith held the colony's second ruby, locking all four gems, and the Arcane
     Workshop's Runic Bone held 2 sturdy + 1 restless bone (one of each since savegame30). With
     it the Runic Bone held 2 restless bones, the Rough Cut 3 sapphires (ready) and no ruby, and
     the rubies stayed free. No change in game speed. An entry locked on a kind the colony can't
     complete waits, as before; there is deliberately no availability check, since floor items
     don't count as available (`re/notes/material_subtypes.md`).
   - FINAL (to Nov 2022). **C**.
   - Sources: S1/3202617741907422869, S1/3053986162873998715, R/si4c1a.

4. **Construction materials eaten or not counted.**
   - A foundry ate six beams, though it needs three.
   - A Large Vault only accepts Iron or Citadel-wood pillars. This matters for the
     Affluence victory.
   - **Code findings (Nov 2026):** building, upgrade and delivery recipes set
     use_classification_matching, but readiness ignored it, so a building counted only its
     largest identical group of parts, kept taking mismatched ones and dropped the extras
     when it completed. The Large Vault's 10 Support Beams had to share one wood and metal.
     **Mod:** `class_matched_inputs` counts every claimed part for those recipes; construction
     kept its pace in testing.
   - FINAL (Apr 2022). **C**.
   - Sources: S1/3280317523017592298, S1/3200369647708032373.

5. **Items, tools and loads vanish or get dumped.**
   - Dwarves throw away rings, gold or gems mid-route.
   - New tools disappear, and "reserved" tools can't be found.
   - Bought goods sit in the entrance chest.
   - Partly caused by auto-sell reserving items.
   - **Cause of the drops (Nov 2026, `re/notes/hauling.md`):** when the AI switches a loaded hauler to something
     else (eating, sleeping, a pickup, or another job from the Job Broker), `bt_haul_exit` releases the trip's
     claims and drops everything he carries on the spot, up to 12 items at once. The items then wait for a
     production building or a storage that takes from the ground, and otherwise rot in about 2.8 game hours: the
     "picking up stuff and throwing them everywhere" thread. Found with the game's own haul and behaviour logs,
     switched on by a test mod, on copies of KrazJomsglind savegame30: 81 items dropped in about 3 minutes of play.
     **Mod:** `haulers_keep_load`: the hauler keeps the items, and the game's clean-inventory behaviour takes
     them to storage. With it, 16 drops in about 7 minutes (only held items claimed by something else, dropped
     when the next haul starts), deliveries up from about 34 to 40 a minute, and dwarf-held items back to 3 at the
     end (1 run each). Carts, long play, and the reports of goods left in the entrance chest were not looked into.
     The thread's cart drops are dwarves riding Handcars while hauling, so they likely end the same way (not tested).
   - **Reserved tools that are never equipped (Nov 2026, `re/notes/tool_upgrade.md`):** when an automatic tool
     upgrade fails, the equip sensor keeps the dwarf marked busy and the tool claimed for him until a reload, so
     he is never upgraded again and nobody else can take the tool. Seen in the user's colony: dwarf 5518's
     claim on a tool held for 31 minutes of play, from the 16:29 autosave to savegame30, with no load between.
     **Mod:** `failed_equip_release` clears both after a failed automatic equip. On copies of savegame30 with
     two equips forced to fail (`_test_equip_fail`): without it neither dwarf equipped again in 30 game minutes
     while 25 other equips happened; with it both took their tool within 30 game seconds (1 run each). A Reddit reply explains the "reserved for selling" case: the queue entry's coin
     toggle is auto-sell.
   - FINAL (to Jun 2022). **C**.
   - Sources: S1/3187992943272016665, S0/3187992458103779388, R/tnpbs4, R/ugupq7.

6. **Player-placed blocks disappear.**
   - Reservoir walls vanish and cause floods.
   - Bricks vanish inside invisible no-build zones.
   - **Cause (Nov 2026, `re/notes/tile_placement.md`):** a structure's pattern turns the one or two blank cells
     above a walkway into headroom (`C`). Headroom sets no layer bit, so Place Block accepts it. When any room or
     infrastructure piece is destroyed (a ghost cancelled or finished, a teardown),
     `room_system_remove_destroyed_entities` re-carves every finished structure within 128 tiles that shares its
     rows or columns, and the carve clears solid headroom tiles outright: no dig order, no refund. So a block
     above a scaffold or walk bridge vanishes whenever something nearby is built or removed, which matches the
     Steam thread's "two spaces above scaffolding" and its "random delay". **Reproduced** on a copy of
     KrazJomsglind savegame30: three blocks above the top Small Scaffold Stair at (500, 1001) survived the load and
     placing a Lantern Post ghost in its rows, and were gone in the first autosave after the ghost was cancelled.
     **Mod:** `keep_placed_blocks` leaves solid headroom alone in that re-carve; with it the same three blocks
     stayed (1 run each). A structure's own completion still carves its headroom, so a block placed there while it
     is a ghost is still removed when it finishes (not tested). The reservoir report wasn't readable and may have
     another cause.
   - FINAL (Apr–May 2022). **C**.
   - Sources: R/u9emye, R/urpwzr, S1/4241812037687177600.

7. **Rails not laid, or excavated the wrong way.**
   - Rails aren't laid despite 100+ in stock.
   - Upward track gets stuck because digging is always planned downward.
   - **Findings (Nov 2026):** the dig scan does try the highest tiles first (`re/notes/carts_elevators.md`), but the stuck
     branch was not found. Why stored rails were ignored is not known. No mod.
   - **Tested 2026-11-08 (copies of savegame32, all mods):** neither symptom reproduced.
     - Stock, one order: 105 Track Sections made at the foundry, then one Railway ordered in the hall. Built 27 s later.
     - Stock, many orders (same day): 16 Railways on the hall floor with 89 free (metal-less, test-recipe) tracks held in
       storage, none in the foundry: all 16 built, each 20-60 s after it was placed. Then 25 real tracks (copper and iron
       ingots plus slabs, as the reporter made them) and 16 more orders: 6 built at once. The other 10 had landed in the
       ground below the cave entrance floor (the screen lagged behind the camera). Placing them there made dig orders that
       no dwarf could reach, and they showed red no-path markers. Each still had its track delivered ("x1"), so the stock
       was used; the digging held them up.
     - So stored rails are used, with or without metal. Not explained: why the reporter's pieces moved once the rails were
       dumped on the floor. Their pieces showed blue icons, which a reply says means "build the previous piece first",
       and pieces that need digging or a previous piece look the same as a stock problem.
     - Upward digging: a 1-wide column and a 3-wide block of dig orders above a small pocket. Dwarves dug every tile they
       could reach from a standing spot within a few minutes, then left the rest. No dwarf was stuck at it. The dig target
       (`get_next_dig_pos`) is only ever a dig-ordered tile inside the dwarf's reach from where he stands, so it can't
       pick a tile he can't reach. Tiles out of reach wait for a scaffold stair, which is normal play, not this bug.
   - FINAL. **C**.
   - Sources: S0/3887227420039649316, S0/3781371514574012810.

8. **Lava problems.**
   - Dwarves burn lava as fuel instead of coal, and there's no way to forbid it.
   - They walk into lava and die.
   - The hand pump counts water toward a lava target.
   - Together these make the licorice (diplomacy) chain hard.
   - **Findings (Nov 2026, `re/notes/lava.md`), all three reproduced in play on colony copies:**
     - **Fuel:** a bar with 300 room took one lava (exactly +250) with lava beside it, in 2 runs of 2.
       With a bar at 0, coal was used, since coal is worth double when there is room. **Mod:**
       `lava_not_fuel` removes the value; the same test then stayed at 700 for about 7 minutes (1 run).
     - **Pump:** the Mountainhome count sums water and lava, so a lava pump showed `x15 / 5` with no lava
       and did not run. **Mod:** `pump_fluid_count` counts only the pump's own fluid, tested on lava and
       water, in the install line since 2026-11-09. Without it, Local
       maintain or a fixed amount also works; Local counts total fluid held in that pump.
     - **Deaths:** with lava on the whole floor of the cook house block, all six dwarves died within about
       5 game minutes (Defeat, test copy), with no refusal to enter. With a 6-tile strip across the main
       hall, dwarves crossed repeatedly at about 300 HP each. **Partial mod:** `lava_no_walk` stopped all
       crossing (1 run, no speed loss), and is in the install line since 2026-11-03. It cuts off whatever lies past the strip
       until a bridge is built; with 3 Small Stone Bridges dwarves crossed on the deck again (12
       crossings, none in lava, 1 run). The flood still ended in Defeat with `lava_no_walk`, `lava_escape`
       and `lava_burn` together, so lava on workplaces was not fixed.
     - **Lava on workplaces: cause found and fixed (Nov 2026).** On a copy of KrazJomsglind savegame32, lava poured on the
       Cave Farm floor flowed downhill and pooled under a storage that is the walkway between two parts of the colony. All 13
       dwarves kept walking through it, and one died with normal lava damage. Three gaps let them:
       - Path edges are stored without a direction, and `lava_no_walk` only checked the edge's first node, so a dwarf could
         step in from the other end (seen in the movement log), and one caught in lava could find his exits blocked.
       - The path search (graph.x86_64.dll) calls the game's edge cost callback only for edges with flag data. The game
         flags fluid only on tile edges where fluid moves: after a load lava at rest had no flag, and a building's own
         walkway edges never get one. So the storage floor was walked as dry ground, without even lava's normal x50 path
         cost.
       - Job and hauling costs are searched backwards from the target, so a target inside lava looked reachable and dwarves
         looped on it (377 haul restarts by one dwarf in 4 minutes).

       **Mod:** `lava_no_walk` now has the path search call the callback for every edge. It blocks every edge touching lava
       except in a creature's own movement search that starts in lava. It marks lava blocks for an edge update after each
       load, and re-reads edges every 128 edge updates. `lava_escape` (now in the install line) reacts only to lava deep
       enough to burn. Same copy, normal damage:
       - With pooled lava, no dwarf entered it in 4 game minutes (2 runs), and the two who started in it walked out.
       - In the final form's run there was no haul loop and top speed was 4.8x, against about 4.6x before.
       - With fresh lava flowing over the Cave Farm, the dwarf working there got out in about 10 game seconds and nobody
         died (1 run).

       Not tested: lava creatures (they can no longer enter lava from dry ground either) and a lava lake reached by digging.
       Regression check (2026-11-09): a copy of savegame32 without lava, with the install line and invaders on, ran about
       60 game minutes at top speed (about 4.45x, against 4.6x in the earlier soak). All 13 dwarves stayed alive and moving,
       18 attackers and creatures were killed, queue entries fell from 93 to 55, and there were no exceptions (1 run).

9. **Plants stop growing after a load.**
   - Citadel mushrooms, Citadel wood and gloom wheat stall at stage 2/4.
   - Workaround: delete the plants and replant.
   - **Code findings (Nov 2026, `re/notes/plant_growth.md`):** stage, timer and tile are
     saved and restored exactly; nothing is lost on load. Citadel's "2/4" is its watering
     stage (ORDER_SOW_WATER_PLANT needs a Water item, which is also the dwarves' drink), so it
     stalls when no Water reaches it. Timed stages advance only when the timer equals the
     current second exactly, so an overdue timer never fires. **Mod:** `plant_timer_fix`
     (fire when due or overdue; tested: a Citadel with an overdue timer advanced at once,
     one with a future timer waited). Wild plants (not player-sown) are harvested only on a
     harvest order and then removed; the user's colony had 28 ripe wild plants waiting.
   - FINAL. **C**.
   - Source: S1/4658416565930577907.

10. **Fishing pier drops fish on the floor, so its counts never register.**
    - Workaround: build a storage next to the pier.
    - **Cause (Nov 2026):** the craft completion code checks for the pier's loot table by name and throws that loot out
      with a random velocity instead of adding it to the pier's inventory, as other loot is.
      **Mod:** `pier_keeps_catch` (one byte; `re/notes/clutter.md`).
    - FINAL. **C**.
    - Source: S1/3274687384238467901.

11. **Quests that never complete.**
    - "Discover sacred well" never completes if the well was found earlier.
    - The rathole count drops on load.
    - A delivery mission only completed after a restart.
    - **Code findings (Nov 2026, `re/notes/discovery_quests.md`):** discovery quests count
      only rooms discovered while the quest is active (one event per room, ever). Sacred Well
      starts after Medicine and God of the Forge after Formalized Learning, so a room found
      earlier never counts; the forge god is unique, so that quest can stall for good. West Hirdness had found neither. East Tharnlaw is affected: it found a
      well (entity 230) by savegame9, before the quest started by savegame10, and the quest
      stayed at 0 / 1 through savegame15. **Mod:** `discovery_counts_found_rooms` credits an already found room at mission start and on load (tested on
      East Tharnlaw saves, and confirmed by the user in play: 2026-11-04, lore 4 to 9). It also counts old finds towards the Spelunker achievement. The rathole "count drops on load" is not explained
      by the 1.2.39 code.
    - FINAL (Oct 2022, May 2023). **D/C**.
    - Sources: S0/3001046778340817388, S1/3200367137211804481.

12. **Tool auto-upgrade.**
    - Dwarves equip duplicate tools, and the "Outdated Equipment" alert never clears.
    - **Findings (Nov 2026, `re/notes/tool_upgrade.md`):** the alert fires while any dwarf
      has a starter tool (CLS_NOOB_TOOL: grandfather pickaxe, hammer, axe, ladle, grandmother
      lantern) anywhere on the toolbelt, whether or not a better one exists or the tool is
      used. Auto-upgrade swaps only for a strictly better unclaimed tool and never removes a
      redundant one. In the user's colony every dwarf's only weapon is the starter axe and no
      better weapon exists (Blade Forging / Spear Making not researched), so the alert is
      accurate there. Code-level candidates (failed auto-equip leaving the dwarf's equip
      sensor busy and the tool reserved until a reload, stale empty slots refilling) are
      designed in the notes but not built: no case in the user's save, and one risks a
      retry loop. No mod for the alert. The failed auto-equip case is now fixed by `failed_equip_release`
      (see B5). A tool whose equip keeps failing may now be retried again and again; that was not tested.
    - **Mod (Nov 2026):** `equip_missing_tools` covers a related gap: a slot is only offered
      professions its current tool has, so the first tool for a new profession (a Cook's Ladle,
      needed before anyone can cook) was never equipped on its own.
    - FINAL (Nov 2025). **C**.

13. **Doors.**
    - Dwarves won't dig next to a door.
    - You can't build under a door placed first.
    - **Findings (Nov 2026), not fixed:**
      - **Dig beside a door: not reproduced.** On a copy of West Hirdness with its Brickwall Door (x 625-627, y 980-983,
        placed in a dug diagonal tunnel), dig orders written into the map on the wall tiles beside its top rows (628,983),
        (628,982) and (624,983) were all dug within about 90 s, as fast as two controls in the tunnel (1 run). A dig order
        is only the map's order bits (`command_execute` 0x1802f85d0 sets status 2 and marks the block dirty), so the edit is
        a real order. The door marks its two side columns (top two rows) and its centre column as walk layer 3 (obstructed).
        The report's trigger, a door placed before the hole is dug, and its exact layout were not tested.
      - **Building under a door:** placement (`room_system_is_valid_pattern` 0x180167000) refuses a pattern cell on a tile
        whose room, transport or walk layer is already set (transport and walk cells marked `C` or `W` are exempt). A door
        sets the walk layer over its frame, so anything whose pattern needs those tiles is refused. That is the general
        overlap rule, not a door-specific bug; patterns come from the model data, which wasn't decoded.
    - **Cause found and fixed (Nov 2026), `mods/door_dig_reach`:** the thread's condition (son-goku, Mar 2022) is a door with no
      free tile beside its 3x4 frame. `tile_graph::add_block_ctx_to_graph` disables (EDGE_DISABLED, `bts ecx, 8` at 0x180335462)
      every edge from a gamepath to a tile node that has no edge to another tile node. A brick door's walkable cells are its lower
      side tiles (walk layer `C O C` in the bottom two rows, `OOO` above, centre column on the door path); each connects only to
      the door path and to the tile outside it, so with rock outside, its edge is disabled and no one can stand there. Rock
      touching only that cell then can't be dug. Test on a copy of KrazJomsglind savegame32: rock filled into the two open
      columns left of the Brickwall Door at x 452-454, y 958-961, dig orders on the column touching the door, control orders
      on three ordinary tunnel walls. Without the mod the controls were dug and the four door orders were untouched after about
      55 game minutes; the door's left inner tile was reached by no dwarf's query, the door path by 14. With the mod (the edge
      stays enabled while one of the tile's 8 neighbours has a dig order) the inner tile was reached and all four were dug within
      about 18 game minutes, no exceptions (1 run each). The colony's 81 other disabled edges, mostly tiles inside buildings
      reached through the building's path, were unchanged.
    - FINAL. **C**.
    - Source: S1/4658416565935612822.

14. **Handcars through monster lairs.**
    - Riders can't attack but can be hit, and they bounce back and forth.
    - **Cause found and fixed (Nov 2026), `mods/ride_then_fight`:** a seated rider can start a melee attack (rank 6 beats his
      job). The attack stops his movement, which ends his wait in the Handcar and takes him out of its queue while he stays
      seated, so the Handcar drives off to a station with him and the swing lands up to 19 tiles from the enemy. When it ends,
      his job or bed queues the Handcar back past the enemy, and the next swing starts the same way. Test on copies of
      KrazJomsglind savegame32: a corridor carved east of the big room (x 572-678, y 973-979), a Handcar line with Rail
      Stations at 590, 622 and 670, and the Killer Plant moved beside the rail at x 646, 24 tiles from the nearest stations
      (monsters and dwarves look for targets within 20 tiles). Without the fix riders swung 44 and 104 times from the seat
      while the Handcar shuttled between about x 610 and 644, and the plant lived 162 and 231 game seconds, until a dwarf
      walked up and killed it in 3 swings (2 runs). With the fix (melee scores 0 for a combateer with a family parent, which
      only seated riders have), the rider had the Handcar take him to the station at 622, walked back and killed it in 3
      swings, 2.8 game seconds after its first attack, with no swings from the seat; rides and the digging past the line
      carried on, no exceptions (1 run). Whether the plant's hits hurt the riders was not checked. With the plant 16 tiles
      from a station, the fight started before the rider left and he walked over, so the loop needs an enemy more than 20
      tiles from the stations. A goblin moved beside the rail left it and was killed in the colony.
    - FINAL. **C**.
    - Source: S1/3193621324037871655.

15. **Smaller mechanics bugs:**

    | Bug | Status |
    |---|---|
    | Dwarves ignore elevators and handcars | FINAL. Not a code bug found (Nov 2026, `re/notes/carts_elevators.md`): on a complete line dwarves rode a Handcar; with one piece missing the Handcar parks at a station it can reach and nobody rides, with no message, which looks exactly like this report. Pieces need exact alignment. In the tests only a Handcar carried dwarves; Carts never did |
    | Conversation partner freezes | FINAL. **Cause (Nov 2026):** a chat starts only when its last participant sits down and finds everyone seated. When one leaves, `talk_system_leave_conversation` removes a chat with at most one participant left unless its place is the Hammerting's, which is 0 when none is held, the same as a chat between nearby dwarves. So a partner already seated keeps a chat that never starts, and Talk outranks work, food and sleep. Any end of the talk action does it (move order, fall, fight). **Mod:** `chat_partner_release`; on a copy of KrazJomsglind savegame29 with a test patch making dwarves walk off at their seat, lone partners waited 400-866+ game seconds in vanilla and were released within 5 s with the mod (1 run each) |
    | Builds abandoned when nearly finished | FINAL. **Cause (Nov 2026, from the code):** the Job Broker's bonus for a dwarf's current job fades over his first 300 s on it (x5 to x1, +1500 to 0); hauling adds a fixed +10000, crafting and building nothing. A building is 5 units of work against 1 for a craft (about 33 s per unit at normal speed), so with the walk a builder passes 300 s near the end and any same-priority job can take him. **Mod:** `builders_finish` (builders keep +900 on their current build); checked in game memory and a smoke run, the abandonment itself not reproduced (`re/notes/job_broker.md`) |
    | A cancelled town upgrade can't be re-queued | FINAL. Not reproduced (Nov 2026): on a copy of KrazJomsglind savegame29, Dwarven Milestone at Gramnock was queued, cancelled with the queue entry's X (`order_remove_craft_queue_entry`) and queued again; the new order appeared in the queue (1 run). Not tried: cancelling after materials were delivered. Queue validity is `check_upgrade_is_valid` 0x1802dc040 (free upgrade slot, unlock status 3); the upgrade's unlock is acquired only on completion (`default_production_complete_cbck`) |
    | Critical-success traits do nothing | FINAL. **Cause (Nov 2026):** traits, morale, energy, food, gold statuses, rings and armour grant four "all professions" entries (crit success, crit failure, speed, level) that no profession entry reads. **Mod:** `all_profession_bonuses` adds them to every profession's speed, crit and production entries and to the explorer-level stats; seen in game memory on a copy of KrazJomsglind savegame25 (`re/notes/modifiers.md`) |
    | Stairs move dwarves at half speed (developer won't fix) | FINAL. **Cause (Nov 2026):** every one-tile step runs the walk_stairs behaviour, which plays the skip_up/skip_down animation at a fixed 1.0 and moves the dwarf with it (`bt_walk_stairs_enter` 0x1804dd655, `event_callback_stairs_anim_done` 0x1804dd041); walking plays at the dwarf's STAT_MOVE_SPEED and climbing reads STAT_CLIMB_SPEED. On a copy of KrazJomsglind savegame32, stepped slopes were crossed at 4.1-5.0 tiles/s against 4.6-7.6 on the flat; a step took about 0.3 s per tile across, walking 0.14 s. Small Scaffold Stair columns already run at about 6.7 tiles/s. **Mod:** `step_pace` plays steps at 2 x STAT_MOVE_SPEED (capped at 2.5x): slopes then ran at 5.8-7.8 tiles/s, no stuck dwarves or errors in 3 game minutes (1 run). Not seen: whether Stone Stairways use the same behaviour (nobody crossed one in 11 minutes); the developers' header comment on `movement_state` says walk_stairs "might be supposed to walk the whole length" of a staircase, so it probably does [inferred]. Source: S0/3112519747616498954 (Feb 2021, no developer reply found). |
    | Algae-farm walls broken by dwarves | FINAL. Not reproduced (Nov 2026; one post, no replies). In the code only dig jobs (`perform_hit` in node_digmine) and the mine drill damage tiles, and dig orders come only from the Mine tool and from placing a building or infrastructure piece, which marks solid tiles inside its own footprint (`room_system_write_pattern`; a ladder added against the wall would do that). Completing a background tile order clears the solid bit without checking the tile, but a waiting place order marks its tile (order status 1, seen on a copy of savegame29), so a block and a background order can't share a tile (`re/notes/tile_placement.md`). Later found (B6): blocks in the headroom over a scaffold or walk bridge walkway are deleted whenever something nearby is built or removed, with no dig order; walls built there would "randomly break" the same way, and `keep_placed_blocks` covers that |
    | Hauler won't deliver water to the infirmary | FINAL. Not reproduced (Nov 2026): in KrazJomsglind savegame27 the queued Balm of Ooze already held its Water 1/1 and Green Slime 1/1. Water is an ordinary item (`fluid_water.entity` is laid out like `slime_green.entity`), made at the Cave Farm. What does stop balm: a building crafts the first ready entry in queue order (`calc_best_production_queue_entry` 0x1802db610), and Gauze at the top was made 39 times and used 22 times in 25 game minutes, so lower entries never ran (copy of savegame27, key 3, 1 run). Workaround: move the wanted entry up |
    | Attributes randomly decrease | FINAL. **Not a bug in the stored values (Nov 2026):** across 42 saves of three colonies (202 before/after comparisons) no KV_ATTRIBUTE_* ever fell. The shown value adds modifiers: 26 statuses from the energy, morale, greed and hunger bars lower an attribute by 1-3 while they last, and 19 traits lower one from the start, and no tooltip says so. **Mod:** `attribute_hint` (text) |
    | God of the Forge missing although its biome was revealed | FINAL. Not reproduced (Nov 2026): each of the three colonies (West Hirdness, East Tharnlaw, KrazJomsglind) has exactly one forge god from the start, deep in the bottom biome at y 77-88 and varying x (not below the entrance, as a forum reply claims); none has explored near it yet. A room is discovered only when one of the 9 blocks around it is first explored while its anchor tile is explored, or after 9 such checks, so a room seen only after all its neighbour blocks were explored can stay undiscovered. No room in any save is in that state: every partly explored room's check count equals its explored neighbour blocks (`re/notes/discovery_quests.md`) |
    | Fertile soil over bridges vanishes | PRE. Not reproduced (Nov 2026): on a copy of KrazJomsglind savegame24, two sown soil tiles right on top of a Small Stone Bridge deck stayed, with no dig order, for about 13 minutes at speed 3 (1 run). Only mining (`map_apply_damage`), cave-room patterns and the place-tile order clear a block in the code; not checked: harvest, tearing the bridge down, long play |
    | Building priority resets after each phase | PRE. Not reproduced (Nov 2026, from the code): the priority dropdown (`command_workplace_jobs_prio_execute` 0x1802f41c0) stores the priority on the building's producer (+0x568) and its haul destination and sets every current job, and sensor_craft_update copies the producer's priority into its record each update (0x1803c7110), from which new craft jobs take theirs (job def +0x44). So a later job of the same building keeps the setting. A phase that hands the work to another entity would not; not tested in play |
    | Mass Nemesis relations after a meeting | FINAL in the user's colony (Nov 2026, `re/notes/hammerting_meeting.md`): one Hammerting before savegame29 turned 35 of 72 relation sides Spiteful and 17 Cold (none before) and changed all 72 values (median -240 of 1000, 21 to 0); 24 were still Spiteful in savegame32. When any chat ends, every pair of participants gets a random change scaled by the chat's tone, which each talk turn moves up or down and nothing caps or averages, so a meeting hits every pair at once with one large tone. **Mod:** `meeting_tone_scale` divides the tone by (participants - 1) for that change, so a meeting changes each pair about as much as one chat and two-dwarf chats are unchanged; tested on a natural 3-dwarf chat (tone -246 to -123, 1 run), not on a meeting. Relations already soured stay as they are. Morale was not hit: it rose for most dwarves from savegame28 to savegame29, so the morale step (which still uses the full tone) was left alone |
    | Auto talents stop at tier 2 | PRE. Not reproduced (Nov 2026, from the code): toggling auto-buy queues every missing prerequisite first, recursively (`unlock_system_toggle_auto_buy`), and the queue is tried on every XP gain (mining hits, crafts, hauls, combat, exploring) and buys the first queued talent that is affordable with all prerequisites owned. No talent has a tier or level gate beyond its prerequisites and 1 talent point. None of the user's dwarves had anything queued in savegame30 (they own 6-8 talents each), so it was not tested in play |
    | Ring and armour bonuses lost on load | PRE. Not reproduced (Nov 2026): items in a dwarf's 15 equipment slots (inventory type 1; slot 6 holds the wielded tool, the others rings and armour) give their modifiers through the modifier system's affected-by links, which mainstate's inventory_moved_cb (0x1802ab110) adds and removes as items enter and leave those slots. The links are saved (`modifier_system/modifier.bin` ends with (entity, source) u16 pairs, slot items included), and in a loaded copy of KrazJomsglind savegame32 all 16 dwarves had them for their slot items. No dwarf there wore a ring or armour, so a ring itself was not checked. Rings and armour are equipped only by hand, from the dwarf's Equipment panel; nothing auto-equips them |
    | Destroying a chest overfills the entrance chest with coins | PRE. **By design (Nov 2026, from the code):** when a vault is removed, `vault_system_remove_destroyed_entities` (0x18026cd80) takes its coin and capacity off the totals and adds the coin back through `vault_system_add_coin`, which fills the remaining vaults and puts what does not fit into the Mountainhome entrance chest over its cap ("Overflowed %lu coin ... mh now has %lu"). While total coin exceeds total capacity, `update_overflow_waste` destroys 0.5% x (coin / capacity) of all coin every 10 game seconds until it fits, so an overfilled chest drains back to capacity within minutes. Nothing is lost on demolition itself. To keep the coin, build the new vault before tearing the old one down. No mod |

**Buying with too little coin does nothing.** A buy the vault can't pay for is dropped silently: no message, nothing logged. Found in play, Nov 2026. **Mods:** `buy_coin_warning` (red tooltip line) and `low_vault_alert` (red alert under 100 coin); a per-click notice wasn't achieved (`re/notes/market_buying.md`).

**Overworld missions offered at hidden locations.** The game announces Dwarven Subversion, but its capital is usually still in the fog, where its panel can't be opened. Reveals come only from sales and get dearer as nearby hexes run out, and a road hex must wait for its neighbour along the road. Found in play, Nov 2026. **Mod:** `known_capital_missions` only offers it at revealed capitals, and offers it when a capital is revealed later. Reveal prices and the road rule are unchanged (`re/notes/diplomacy.md`).

**A broken quarry soft-locks the colony.** Found in play, run 4 continued (Nov 2026, from savegame57). The game's help says a building is "disabled, pending repairs, if its Building Health runs out", and the Damaged Building alert says to craft Blocks of Granite (the only item with STATUSBAR_BUILDING_HEALTH_INSTANT). Only the quarry makes blocks. The quarry, foundry and smithy all sat at 0 (the Cook House was "killed" at 0 during play too), every queue was impossible, and all four dwarves stood idle with no way to make a block. The damage came from two sources: wandering creatures (rats, slimes, a Slime King) and crafting accidents. `CRIT_BUILDING_DAMAGE` is one of the crit failure effects in `event_callback_anim` (0x1804d31f1, resolved by `resolve_building_damage`); this colony's crit failure values were 0.11-0.34 (`tools/modvals.py PROF_*_CRIT`), about a 1-3% chance per crafting hit, and dozens of -20 to -53 hits landed on the foundry in a few minutes at top speed. No building has a health gain in `room_modifiers_cdb.bin`. **Mod:** `building_self_repair` gives the quarry records `STATUSBAR_HEALTH_GAIN` 0.05 per tick (the Building Health bar's record in `statusbar/statusbar.bin` names that tag as its gain; `STATUSBAR_BUILDING_HEALTH_GAIN` did nothing). Tested on a copy of that colony: quarry and foundry 0 to 374 in one autosave interval, smithy rising. The first version gave every building and mech the gain; then no building ever reached the death step (none was "killed" in any session after the install, against many before), and that step is what destroys a door at 0 (`death_util::init_death_effects`, lambda 0x1803ffad0, `KV_IS_DOOR` → `entity_entity_manager_destroy_entities`). Invaders kept hitting an empty door that never opened (user report, Nov 12 2026), so the gain is now on quarries only. Play advice: keep Blocks of Granite maintained in the Mountainhome so haulers repair before anything breaks.

**Only the up-right incline rail can be built.** The user found no way to lay an incline that rises to the left (Nov 2026). The game ships `MECH_RAILWAY_LEFT_INCLINE`: entity, model, mirrored path (rail0 at 1,0, rail1 at -1,1 in `all.gamemodelblob`), mirrored footprint (`B `/`BB`/`BB`) and recipe, and the right incline's room record names it as its `_mirror_tag`. But it was left unfinished: it's missing from the Railway list in `category_mech_window_generate.entity`, its recipe has no unlock dependency and a menu weight of -1, it has no icon, and both pieces are called "Incline Railway". There is no flip key (none in the keybinding options or UI text). **Mod:** `left_incline_rail` lists it after the right incline, unlocks it with Cogborne Transmission like the right one, adds a mirrored icon and names the two "(Up Right)" and "(Up Left)". Tested on copies of savegame61: both showed in the menu with Cogborne researched, the ghost and the built piece rise to the left, and with `_test_rails` (free pieces) a dwarf built it in a tunnel by the colony in 8 seconds. Not ridden with a Handcar. Without `_test_rails` the order waited: that colony had no Track Sections, and its own rail orders 200 tiles below the colony were unreachable too.

**Dwarf alerts jump to an empty map corner.** Clicking Wrong Tools Equipped moved the camera to the unexplored bottom-left corner of the cave. Found in play by the user, Nov 2026 (savegame58). The dwarf it listed (Gudvi, entity 2346) was carrying goods to a settlement: he was tagged CURRENTLY_IN_OVERWORLD, and his position was in overworld coordinates (-3.5, 2.0, -2.23; overworld hexes sit at values like these). The click action, `CAMERA_MOVE_TO_POSITION(DATA.GET_AT(NEXT_CLICK_INDEX).POS)`, used it as a cave position. Seven alerts list dwarves this way (Missing Dwelling, Low Health, Outdated Equipment, Unmanaged Professions, Idle, Wrong Tools, Stranded). **Mod:** `away_dwarf_alerts` leaves dwarves tagged as in the overworld out of those lists. Tested on a copy of savegame58: on load the alert was gone; about a minute later Gudvi was back, the alert listed him, and a click centred the camera on him at the entrance (1 run).

**A stranded dwarf with a home neither sleeps nor eats.** Found in play (Nov 12 2026, SouthXanforge, Runa, entity 2166, cut off below an unfinished elevator shaft): she ignored two raw Rime Beets 4 tiles away. Replayed on a copy of savegame73 with `_test_drop_log` (1 run): she was more tired (energy 547/2525, 22%) than hungry (1610/2800, 57%), so ACTION_SLEEP outranked eating. `sleep_action_begin_func` (0x1803bcab0) picks BT_SLEEP_IN_ROOM whenever `dwelling_system_get_dwelling` returns a home, else BT_SLEEP_ON_FLOOR, with no reachability check, so with her home out of reach every attempt failed within 0.2 s, she idled 5 s and chose sleep again (43 times in about 5 minutes, no eat attempt after the first minute). Her first eat attempts went for Lichen about 56 tiles east in a slime pool (150 hunger, one carried by a live slime) instead of the beets (300 hunger); why the beets lost is not established (depth, claims and reachability ruled out: haulers took them once the shaft was done). Workaround: unassign the stranded dwarf's dwelling, if the game allows it, so she sleeps on the floor. **Mod:** not written yet; candidate fix in `re/notes/food_ai.md`.

**Soak test, Nov 2026.** A copy of KrazJomsglind savegame32 with the shipping mods (invaders on) ran 35 real minutes at speed 3, about 2.7 game hours, with 11 attack pauses. No dwarf died or stood still across snapshots, no exceptions, loose items fell from 213 to 19 and stored food rose from 432 to 528. 34 queue entries made no progress; all lack an ingredient (fish, eggs, gold ore, hides, lichen, a second matching gem or bone) or wait on another stalled entry, and the crab, rat, spider and skeleton drops that look stocked are carried by live creatures. The Cave Farm's store-Toncap order also stays at x5, but it is a local stock order and Toncaps were grown and used throughout (306, 341, 308).

## C. Performance (the most-cited end-game blocker)

- **Symptoms:**
  - The simulation drops to single-digit FPS beyond about 20–40 dwarves, many
    carts or drills, or a large map.
  - "Fastest" speed is no faster than normal.
  - Autosaves and overworld transitions freeze the game for 10–45 seconds.
- **Drivers:** fluids, floor items and big queues (see A1, B1).
- FINAL (to Nov 2025, 2026). **C/E**.
- **Workarounds:**
  - small map;
  - 20–30 dwarves at most;
  - store or sell everything on the floor;
  - seal fluid sources;
  - limit carts and drills;
  - cancel impossible orders.

## D. Graphics and startup (mostly drivers or platform: X)

1. **Will not start, or crashes in Vulkan.**
   - The variants:
     - black screen, then the game exits;
     - `VK_ERROR_DEVICE_LOST`;
     - "Vulkan 1.1 system call failed";
     - laptops that pick the integrated GPU;
     - `VK_ERROR_OUT_OF_DEVICE_MEMORY`;
     - `SteamAPI_Init failed`.
   - Workarounds:
     - update both GPU drivers;
     - launch with `--render-device 0` or `--render-device 1`;
     - remove overlay or hook software (ReShade, Overwolf, FPS Monitor, and so on);
     - rename `SteamOverlayVulkanLayer64.dll`;
     - delete `Documents\My Games\Warpzone Studios\tdtd\settings.txt`;
     - launch with `--texture-skip-mip true`;
     - resolution scaling 50%;
     - windowed mode.
   - FINAL (to 2025).
   - Sources: pinned S1/2972897380410805372 and others.
2. **Full-screen green, red or pink colour corruption with gibberish text.**
   - Often triggered by selecting a large building or by an autosave.
   - Workaround: low-res textures and bloom off.
   - FINAL (to Aug 2023).
   - Source: S1/4677521348349933854.
3. **UI scale at 4K or ultrawide.**
   - 200% does nothing or pushes the Apply button off-screen.
   - Resolution changes can leave a black screen.
   - Workarounds: press Apply and restart, or delete or edit `settings.txt`.
   - FINAL (to Jul 2026). **D**: the UI could be modded.
4. **Streaming** (Remote Play, Discord) shows black.
   - Workaround: true windowed mode.
   - FINAL.
5. **Smaller UI bugs, all FINAL:**
   - dragging an order while the camera auto-pans stretches it;
   - dwarf name labels block clicks;
   - Cave Farm selection is off by two columns;
   - Exit buttons overlap;
   - the tech tree hides one tech on widescreen;
   - empty dwellings stay lit;
   - fog-of-war glitches;
   - statues spawn on top of buildings.
6. **Linux and Steam Deck.**
   - Fine on Proton 9–10 and GE-Proton 9 (ProtonDB, 2024–2025). It runs here on Proton
     Experimental.
   - Older AMD artifacts were fixed with `RADV_DEBUG=zerovram`.

## E. Fixed by patch notes (don't count against 1.2.39)

**QoL4:**
- female dwarves turning male;
- Citadel mushrooms couldn't be stored;
- rail tracks not crafted;
- long overworld upgrade queues not built;
- lair guards not saved;
- non-militia dwarves following attack orders (now intended);
- conquered towns still giving bonuses;
- stacked brick doors;
- single-type enemy waves;
- statues and world loot not spawning;
- hand pump giving no XP;
- dying dwarves floating;
- tear-down orders destroying random entities;
- several overworld, hauling and autosell crashes;
- corrupt-save detection.

**QoL3:**
- missions resetting on load;
- the licorice quest;
- mushroom stew;
- dwelling lights;
- crashes with 32+ attacking dwarves;
- Vulkan validation errors;
- 0-byte saves.

## F. Design complaints (not bugs, but relevant to "playable to completion")

- **Endgame and progress:**
  - no real endgame;
  - God of the Forge does nothing;
  - victory conditions unreachable (A0);
  - the overworld is shallow, and you can't join wars.
- **Balance:**
  - enemy waves much harsher since QoL4;
  - wood, hide, slime and bone not renewable;
  - higher-tier materials no better than lower ones;
  - gold over vault capacity is lost;
  - money stops mattering mid-game.
- **Controls and tutorial:**
  - coarse job control: you can't pin a dwarf to a building;
  - slow one-item hauling;
  - the tutorial explains little;
  - food on the floor isn't eaten (intended).
- **Structural:**
  - alliances permanent;
  - only the licorice quest leads to alliances;
  - support beams deep in the tech tree;
  - promised mod and Workshop support never arrived;
  - Vulkan only, Windows 10+.

## What this means for the mod plan

These look most valuable for finishing a game, roughly in order of payoff for effort:

1. **Victory reachability.** Affluence is done. Diplomatic (A0.2) still needs work.
2. **Starvation and food access.** Dwarves eat from nearby floor stacks, or food gets
   auto-stored (A12). Data first, code if needed.
3. **Floor clutter and overproduction.** Enforce Maintain and seed limits, auto-store
   (B1, B2). This also eases A1, A9 and C.
4. **Crash fixes with a named function.** `relation_component_system_change_relation`
   (A3) and the licorice-quest crash (A4).
5. **Stuck dwarves and carts**, the invader freeze, and greed loops (A7, A8, A10, A13).
6. **Panic spiral** (A6): retreat threshold or militia override.
