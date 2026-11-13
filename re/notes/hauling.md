# Hauling: why carried items end up on the floor (BUGS B5)

## Code
- `bt_haul_exit` 0x1804eeb30 runs whenever a dwarf leaves BT_HAUL. It releases every claim the trip made
  (one "unclaimed" log line per item) and then calls `try_drop_item_on_ground` 0x1804ee360 for every item
  still in the hauler's inventory (call at 0x1804eec4f) [S]. After a normal delivery that inventory is empty.
- `try_drop_item_on_ground` skips the drop while `CURRENTLY_IN_OVERWORLD` is set, and otherwise moves the
  item to the ground with `inventory_system_drop_items` 0x180117cd0 [S].
- `bt_haul_enter` also calls it (0x1804eeaa3) for a held item whose claim belongs to something else [S].
- The behaviour switch that triggers the exit is `ai_behavior_system_update` 0x18035919a (calls the old
  tree's exit through its vtable). A second exit path is at +0x2aaa (0x18035a54a) [S, stacks captured in game].
- `BT_CLEAN_INVENTORY` (sensor `sensor_create_clean_inventory`, tree `bt_create_tree_clean_inventory`) takes a
  dwarf's unclaimed held items to a haul destination (storage) through an interact [S, I for the details].

## Debug logs
- `g_debuginator_gamestate_settings` 0x1805a77f0 points at a static flag array at 0x1805a56e0, set in
  `gamestate::gamestate` (0x1802aecb0). One byte per log group, all 0 in release [S]: +5 claims, +7 waves and
  spawners, +8 GAMESTATE-HAUL (haul node, pick up, claims for hauls), +9 inventory moves and toolbelt, +10
  GAMESTATE-MOVE (movement, idle, stations; very verbose), +11 overworld, +12 equip sensor, +13 smart events,
  +14 GAMESTATE-TALK, +15 vault.
- Behaviour switches ("Entity %hu switching from %s to %s", GAMESTATE-BT) are gated separately by byte +0xda
  of the ai_behavior system (`je` at 0x180359048) [S].
- `mods/_test_drop_log` sets +8, +10, +12 and +14, removes the +0xda gate, and copies the stack at each drop
  into `.hmod` data (read with a /proc mem reader; the DLL loads at a different base under Wine).
- From the same save the sim is deterministic: the first 12-item drop came at tick 254601 in every run.

## Test (2026-11-06, copies of KrazJomsglind savegame30, `_test_quiet`, key 3)
- Without the fix, about 3 minutes of play: 81 items dropped, 102 deliveries. A hauler collecting 12 loose
  items for chest_start dropped all 12 halfway when his AI switched; he walked on to the entrance empty and
  took a new haul there. Behaviours that replaced a loaded haul, counted per dropped item: BT_EAT 25,
  BT_MOVE_TO_JOB 24 (the Job Broker moved him to another job), BT_SLEEP_IN_ROOM 20, BT_PICKUP 5.
- The same item was often picked up and dropped by several haulers in turn. With `ground_pickup`, most
  dropped items were stored again within 30-90 s; 46 of 114 were still loose at the next autosave.
- With `haulers_keep_load` (the call at 0x1804eec4f replaced by a nop), about 7.3 minutes of play: 16 drops,
  all from `bt_haul_enter`, and 295 deliveries. After an interrupted trip the dwarf ran BT_CLEAN_INVENTORY
  soon after, usually once he had eaten or picked up (43 clean-inventory runs). Items held by dwarves
  peaked at 41 and were 3 in the last autosave (the unfixed run: 76 and 42). Loose items went 209 to 26,
  as in the unfixed run. No exceptions. One dwarf holding 12 kept items alternated BT_PICKUP and BT_FALL
  three times, then cleaned his inventory and went back to hauling; falls were rarer than without the fix
  (5 against 40).
- Not tested: long play, carts (the Steam report also has carts dropping ore), a dwarf whose kept load blocks
  him from eating or equipping, and the rot of items held in a dwarf's inventory.

## Storage to storage (2026-11-12, code only, not tested in game)
- `add_haulable_items` (VA 0x1801dc1b1..0x1801dc2b7) decides, per item and destination, whether the item's holder
  is a valid source. Source mask bits (destination +0x58): 0x01 Take from ground, 0x02 Take from Inventories,
  0x04 Take from Overworld (the storage panel's order). Overworld holders need 0x04; holders of one entity type
  need 0x02. Then, whatever the bits, an item whose holder is itself a haul destination with type bit 0x02
  (+0x4 of the 0x78-byte record; general storages and Stone Chests, save record byte +2) is skipped.
- So **no haul job ever moves items from one storage to another**, and a Cart between two storages has nothing
  to carry. Carts and haulers move ground items, building outputs and overworld goods into storage, and
  production demand pulls inputs out of storage into buildings. The start chest (type 0x01) is not skipped, so
  storages do empty it.
