# Hammerting completion mods: findings and plan

Status 2026-10-31. Findings are from the shipped game data (`game.wkz`), the public
headers bundled inside it, and disassembly of `game.x86_64.dll` with its PDB symbols.
Items marked *unverified* have not been checked in a running game.

## How the game is meant to end

`database/game_overs/game_over_conditions.bin` defines the game over conditions:

| Condition | Trigger |
|---|---|
| `WIN_AFFLUENCE` | mountainhome key `KV_WIN_AFFLUENCE` is true |
| `WIN_DIPLOMATIC` | mountainhome key `KV_WIN_DIPLOMATIC` is true |
| `LOSS_ALL_DORFS_DEAD` | no player dwarf has health left |
| `WIN_DEMO_TIME` | demo builds only (one hour played) |

Two victory-condition missions set those keys. Both are in the standard mission set and
appear in the outliner's Victory Conditions panel.

### Affluence (cave mission `MISSION_AFFLUENCE`)

The mission has two parts:
1. `MISSION_GEN_BUILD('BUILDING_VAULT_LARGE', '2', '2', 'PRE_EVAL')`: build two Large Vaults.
2. `MISSION_GEN_ACQUIRE_VAULT_FULLNESS('DUMMY', '100', '100')`: total vault fullness reaches 100%.

The fullness generator in `property/smart_event_generation.h` starts with a
developer placeholder:

```
//! HACK: Making this simple because I'm guessing we might want to redo the logic.
"ARG('1').GREATER('10000000')"
```

`vault_system_add_coin` (disassembled) sends `TDTD_EVENT_VAULT_CHANGED` with
ARG0 = fullness % (integer) and ARG1 = `KV_GOLD_MAX`, the total vault capacity. It
only sends the event when the integer percentage changes.

Vault capacity comes from `KV_GOLD_MAX` in each vault entity. Money is stored in copper,
with 10,000 copper to the gold (the currency formatter divides by `0x2710`).

| Vault | Capacity (copper) | On screen |
|---|---|---|
| Small | 50,000 | 5 gold |
| Medium | 5,000,000 | 500 gold |
| Large | 500,000,000 | 50,000 gold |

The 10,000,000 check passes as soon as you own one Large Vault. Fullness is total
gold divided by total capacity, so the win needs at least two Large Vaults filled:
**at least 100,000 gold banked**, plus the capacity of any other vaults. Meanwhile
dwarves draw wages from the vault through Greed. A cave gold pile gives
`gold/500 + 100` copper, about 1 silver. *Unverified:* how fast a developed fortress
earns from market sales. If it is anywhere near what players report, this victory is
out of reach in practice.

### Diplomatic (overworld mission `MISSION_OVERWORLD_CONQUEST`)

`MISSION_GEN_OW_CONQUEST` counts overworld locations. The goal is
`OW_LOCATIONS.COUNT`. Progress is the number of locations owned by the mountainhome
plus the number owned by factions whose relation to the mountainhome is
`RELATION_FACTION_ALLIANCE`.

- There is no player command to capture a location. The player commands are build,
  buy_items, buy_research, buy_talent, craft, diplomatic_action, sell, recruit, and so
  on. You own only your mountainhome, so every other location must belong to a faction
  allied with you.
- The nine AI factions (Baraz, Deadwoods, Froia, Loogun, Marunia, Ogor, Sylver, Vendar,
  Zakath) form, join, leave and disband alliances among themselves (`ALLIANCE_A`–`E`,
  logged as "Fac %hu joining %hu in alliance"). The player joins one alliance through the
  `MISSION_OVERWORLD_ALLIANCE` reward `MOUNTAINHOME.JOIN_ALLIANCE(...)`.
- So the win needs every location-owning faction in your one alliance at the same
  time, with no faction at war tearing it apart. *Unverified:* whether the AI ever
  converges on that, and whether `FACTION_ENEMY` or `FACTION_NEUTRAL` own any location.
  If they do, the victory is impossible.

## Reported blocking bugs (Steam discussions, not yet reproduced)

- With invasions enabled, invaders freeze on the world map near the entrance and their
  number grows without limit.
- Minecarts freeze after several save/reload cycles.
- 4x4 ladders sometimes can't be demolished, also after reloads.
- Severe late-game slowdown.
- Farms can't be restocked once seeds or mushroom spawn are consumed. There are no
  production caps, so storage overflows.
- The wave-based siege option never triggers. Faction upgrades have no visible effect.

## Proposed mod set

Each mod is a separate archive, loaded with `--game-extra-archives` and individually
optional. A small launcher will pick which ones load.

1. **Reachable Affluence** (data). Rebalance the victory to a sensible scale of income.
   The options are to edit the mission arguments in
   `cave_mission_records_cdb.bin` (vault count, fullness target) and/or the Large Vault
   `KV_GOLD_MAX`. First measure real income in a mid-game save to pick the numbers.
   Same-length string patches (`'100'` → `'060'`) avoid needing the full record format.
2. **Reachable Diplomacy** (data). Count locations of allied or *friendly* factions,
   or require alliances with a majority of factions rather than every location. This
   depends on confirming how the alliance AI behaves.
3. **Victory tracker** (UI data). Show both victories' progress in the outliner: banked
   gold against the target, and locations allied against the total.
4. **Economy and Greed balance** (data). Tune wages, vault capacities and gold piles so
   money matters early and doesn't trivialise late. Players report that gold becomes
   meaningless mid-game.
5. **Farming fixes** (data or code). Allow replanting stock and production caps.
6. **Bug fixes** (code). Invasion freeze and unbounded invaders, minecart freeze after
   reload, ladder demolition, and late-game performance. These need DLL patching. The
   PDB gives full symbols and the headers give data layouts, so targeted patches (or a
   proxy DLL that hooks named functions) are feasible.

## Next steps

1. Decode the smart-event record layout in `database/smart_event/*.bin` (PDB types are
   queued) so missions can be edited properly, not just with same-length patches.
2. Measure income: read sale prices and gold over time from a save, or from the user's
   playthrough.
3. Check the Diplomatic victory in a running game: log alliance changes
   and see whether any enemy- or neutral-owned locations exist.
4. Build mods 1 and 3 first, then test with a late-game save. The debug console
   (`debuginator`) or a test scenario can be used to fast-forward.
