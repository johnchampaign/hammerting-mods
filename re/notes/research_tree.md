# Research tree (BUGS A17), game.x86_64.dll 1.2.39

## Records
`database/research/research_cdb.bin`: u64 48, u64 218880, then 48 `research_record`s of 4560
bytes (game_entity_types.h:1594). Only the first 0x2a8 bytes are data. The rest are pointer
tables filled at load.
- +0x000 wc_tag name (char[56] + u64 wc_hash).
- +0x040 key_value_cost[4], 0x88 bytes each: i64 cost (16.16), wc_tag tag, wc_tag target
  (always ""). Tags are only KV_MOUNTAIN_LORE and KV_TRADE_LORE.
- +0x260 u64 _dependencies[4] (research tag hashes), +0x280 _tier (0 in the data, set at load).
- +0x2a8 wc_tag _mountainhome_modifiers[4] (MOUNTAINHOME_CENSUS_RECORDS ...).

A research record doesn't list what it unlocks. Every other record type has
`u64 _dependencies[4]`, and the research card's unlock list is built from those:
- recipes: +2440 (0x988) of 3784-byte records;
- talents and hammertings: +0x360 of 904-byte records;
- upgrades: +0x468;
- smart events (missions): +0x90 of 341936-byte records.

A dependency can be any tag (research, item, building, mission, biome).

## Engine rules (unlock_system.cpp, module 30)
- `unlock_system::unlock_system` calls `add_dependencies(tag, deps)` (0x1801ad110) for every
  recipe, research, mission, talent, hammerting and upgrade. A record with deps[0] != 0 goes
  into the HIDDEN list (+0x1e8) and gets a list of the deps it still lacks. There are at most
  1024 dependents.
- Acquiring a tag (0x1801a6180, called "unlock_system_has_seen" in the PDB) removes it from
  every dependent's missing-deps list. A dependent leaves HIDDEN only when that list is empty,
  so all deps are required (AND). This sends TDTD_EVENT_UNLOCK and adds the tag to ACQUIRED
  (+0x1d8).
- Tags are acquired only by these events: PRODUCTION_COMPLETED, OVERWORLD_COMPLETED_MISSION,
  SMART_EVENT_COMPLETED, EXPLORATION_DISCOVERY, DEATH_OF_OBJECT,
  EXPLORATION_DISCOVERY_BIOME, and buying research. Being unlocked doesn't count as acquired.
  Buying on the overworld fires no acquire event.
- `get_unlock_type` (0x1801a9820) checks, in order: in ACQUIRED gives ACQUIRED, in HIDDEN gives
  HIDDEN, can pay `_key_value_costs` (or the "Game/Systems/Unlocks/Allow all" flag at
  +0x18200 is set) gives AFFORDABLE, otherwise AVAILABLE.
- `command_buy_research` is valid only when the status is AFFORDABLE.
  `unlock_system_buy_research` pays the costs and then calls `research_bought` (0x1801a9930).
  That function sends TDTD_EVENT_RESEARCH_BOUGHT, adds the mountainhome modifiers and pushes
  the hash to a PENDING list (+0x1c8). The next `unlock_system_update` turns PENDING into
  acquired. Nothing else consumes lore: no recipe has a lore key_value_cost.
- On load, the constructor rebuilds the HIDDEN and missing-deps lists from the records, and
  LOAD_POST replays the saved ACQUIRED list. Data edits to dependencies therefore apply to
  existing saves.

## Graph check (all 48 research records)
- Every dependency names an existing research record. There are no cycles, the depth is 0-8,
  and no record has more than 3 deps.
- Roots: FOUNDATIONAL_STRUCTURES, METALLURGY, SUBTERRANEAN_FARMING, TRADE_RELATIONS.
- There are no choices that exclude each other. Buying spends lore and never re-hides anything.
- The whole tree costs 1326 Mountain Lore (ML) and 506 Trade Lore (TL). TREASURE_HOARDING
  (needed for BUILDING_VAULT_LARGE, so for the Affluence victory) costs 771 ML / 174 TL with
  all of its prerequisites.
- The data tree has no hard block. The lock-out comes from the lore economy.

## The lock-out: Mountain Lore runs out before it becomes renewable
- TL is renewable: overworld deliveries `OWMIS_*_REPEAT_*` in recipe_mission_cdb.bin give
  LOOT_RESEARCH_TRADE_LORE 1-3, and the one-off OW missions give 53 in total.
- ML is renewable only through `CLS_LAND_SURVEY` (recipe_scriptorium_cdb.bin, record 4): it
  takes a dwarven map, a copper ingot and 2 granite chunks and gives LOOT_RESEARCH_MOUNTAIN_LORE
  1-3. That recipe depends on `RESEARCH_GEOLOGICAL_SURVEYS`, which costs 140 ML / 14 TL with
  its 9 prerequisites:
  - ADVANCED_CASTING, FORMALIZED_LEARNING, METALLURGY, PROBING_THE_DEPTHS, SMITHING;
  - STONEMASONRY (30), SUBTERRANEAN_FARMING, TRADE_RELATIONS, WOODWORKING_TECHNIQUES.
- Before that, ML comes only from one-off sources:
  - cave missions, 242 ML in total (UINT reward chains in smart_event_reward._kv_chain);
  - exploration discoveries (ARG 7 of the log-book entry, finite per map).
- A player who spends ML on cooking, brewing, medicine, smithing branches and so on before
  GEOLOGICAL_SURVEYS can be left with every remaining card AVAILABLE but never AFFORDABLE.
  That fits both the "unable to proceed" and "lock yourself out" reports. Whether QoL4 moved
  Land Survey behind Geological Surveys can't be checked without older data.

## Suspected code bug (needs an in-game check): double charge
The research window pauses the game. Status stays AFFORDABLE until `unlock_system_update`
moves PENDING into ACQUIRED, and neither `buy_research_is_valid` nor
`unlock_system_buy_research` checks PENDING. If commands run while the game is paused but the
ECS update doesn't, each extra click pays again and applies the mountainhome modifiers again.
Test: open research, note the ML, click Buy twice, then compare ML before unpausing.

## Dead unlocks found in passing (not research)
- 0xed18b092e0024acb = `BUILDING_NONE`, never acquired, so these are deliberate disables:
  - recipe_farm: CLS_BERRY_GRAPE_CAVERN, CLS_FOOD_BARLEY_MOUNTAIN, CLS_FOOD_HOPS_DEEP,
    CLS_FOOD_SUGAR_BEET, CLS_SHROOM_TONCAP, CLS_WHEAT_GLOOM (the farms use ORDER_STORE_*);
  - recipe_rooms: MECH_CART, MECH_PLATFORM, MECH_RAILWAY_STATION, MECH_STAIRWAY_SCAFFOLD,
    MECH_STAIRWAY_SCAFFOLD_BIG.
- `CLS_DRINK_CIDER` (recipe_brewers_still) depends on CLS_FOOD_APPLE, which has no item
  record, entity or producer, so it never unlocks.
- Three cave-mission deps don't resolve to any known string: RATS_IN_THE_WALLS
  0x45f07be42ef91fc0, MOPPING_FLOORS 0x8cf93fe3f6ed2735 (JELLY_BAKE follows it), DUST_TO_DUST
  0xef79bc34e2ef48d5. Between them they gate 75 of the 242 mission ML.

## Save format (`unlock_system/*` in the save, header u32 = format version 0x400002)
Each u64 array is `u64 count, u64 bytes, count*u64`. The decoded block holds, in order:
1. +0x178, a sorted hidden set, loaded only;
2. +0x188, a sorted locked set, loaded only;
3. +0x198, unseen tags;
4. +0x1a8, unknown;
5. +0x1d8, ACQUIRED: every acquired tag, research included.

Then (version >= 0x400001) a u16 array (`count, bytes, count*u16`), then u64 n and n
64-byte records. HIDDEN and PENDING aren't saved. The lore values are in the key-value
records of the mountainhome: `key[56], u64 hash, u64 type, value`.

```python
import struct, sys; sys.path.insert(0, 'tools')
from save import Save
s = Save(sys.argv[1]); name = next(n for n in s.raw if n.startswith('unlock_system/'))
ver, d = s.unpack(name); p = 0; L = []
for _ in range(5):
    n, nb = struct.unpack_from('<QQ', d, p); assert nb == 8 * n; p += 16
    L.append(set(struct.unpack_from(f'<{n}Q', d, p))); p += nb
acq = L[4]; db = open('re/extract/database/research/research_cdb.bin', 'rb').read()
n, tot = struct.unpack_from('<QQ', db); R = tot // n
for i in range(n):
    r = db[16 + i * R:16 + (i + 1) * R]; h = struct.unpack_from('<Q', r, 56)[0]
    deps = [x for x in struct.unpack_from('<4Q', r, 0x260) if x]
    cost = {r[0x48 + k * 0x88:0x80 + k * 0x88].split(b'\0')[0].decode():
            struct.unpack_from('<q', r, 0x40 + k * 0x88)[0] / 65536 for k in range(4) if r[0x48 + k * 0x88]}
    st = 'ACQUIRED' if h in acq else 'HIDDEN' if any(x not in acq for x in deps) else 'OPEN'
    print(f'{st:8}', r[:56].split(b'\0')[0].decode(), cost)
for f in s.raw:  # lore balances
    try: _, x = s.unpack(f)
    except Exception: continue
    for k in (b'KV_MOUNTAIN_LORE\0', b'KV_TRADE_LORE\0'):
        i = x.find(k)
        if i >= 0: print(f, k[:-1].decode(), struct.unpack_from('<QQq', x, i + 56))
```
A colony is affected when GEOLOGICAL_SURVEYS isn't ACQUIRED, its own ML balance is below the
ML still missing on the path to GEOLOGICAL_SURVEYS, and its ML-paying cave missions are done.
The value may be raw or 16.16 fixed point: compare it with the top bar.

## Data fix candidates
1. Make Land Survey renewable early. In `database/recipe/recipe_scriptorium_cdb.bin`, record 4
   `CLS_LAND_SURVEY` (record at file offset 0x3b30), change the u64 at file offset 0x44b8
   (record +2440):
   - old: 0x9a7424e51fd3a49a, RESEARCH_GEOLOGICAL_SURVEYS (bytes 9a a4 d3 1f e5 24 74 9a);
   - new: 0x5f7aeac57fd225ff, RESEARCH_FORMALIZED_LEARNING (bytes ff 25 d2 7f c5 ea 7a 5f).

   The scriptorium (BUILDING_ARCANE_WORKSHOP_SMALL), parchment and the dwarven map already
   need FORMALIZED_LEARNING, and copper needs METALLURGY, so the gate becomes 29 ML / 5 TL. It
   applies to existing saves. In a mod, use `ctx.read` and `ctx.write` and find the record by
   name. The card then appears under Formalized Learning automatically.
2. Optional: Land Survey output min/max at file offset 0x4230 (u32 1, u32 3), e.g. 2, 4.
3. If the double charge is confirmed: a DLL patch so `unlock_system_buy_research` returns early
   when the hash is in PENDING (+0x1c8/+0x1d0), or calls `unlock_system_update` (0x1801a8c90,
   rcx = ecs) right after `research_bought` at 0x1801a3360.
