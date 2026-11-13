# What removes a block (algae-farm walls, BUGS B15), game.x86_64.dll 1.2.39

Static reading plus one in-game check (copy of KrazJomsglind savegame29, Nov 2026).

- Tile damage: `map_apply_damage` 0x180509e90 is called only by `bt_create_node_mine_drill` (the drill) and by
  `perform_hit` (node_digmine, called from the dig job's tree only). perform_hit hits the dig job's target tile.
- Dig orders (status 2, 0x4000): set only by `command_execute` (Mine tool) and `room_system_write_pattern`
  (0x18016787b / 0x180167904): when a room or infrastructure piece is created, solid tiles its pattern needs open
  become dig orders, and tiles with bits 5-9 set for most pattern characters too. sensor_dig's `update_blocks`
  only flips existing orders between status 3 and 2; `calc_orders_in_reach` sets a bit in a local mask.
- Clearing the solid bit (bit 21) elsewhere: `room_system_write_pattern`, and place-tile completion in
  `default_production_complete_cbck` (kind 5, 0x1802da06a): it writes the order's material (low 5 bits), sets bit
  21 for a block or clears it for a background (flag at [rbp+0x348]), clears order bits, sets the fluid to none
  and refreshes the tile graph, without looking at the tile first.
- A waiting place-tile order marks its tile with order status 1 (0x2000): in an autosave three brick orders at
  (581-583, 993) had 0x2000 set, and the tool then refused those tiles ("Mark at least one background block").
  So a block and a background order can't wait on one tile through the game's tools.
- Placing a block needs a dug tile ("background"), checked by `command_place_tile_is_valid` 0x1802fb420 from map
  bits only.

## Headroom re-carve (BUGS B6, Nov 2026, `mods/keep_placed_blocks`)

- Room patterns: `database/room/room_default.bin`, records of 0x30a0, name at +0, three layers of 64 x 64 chars
  from +0x58 (room, transport, walk; stride 0x1000, rows of 0x40, top row first). Small Scaffold Stair: transport
  `" ", " ", BB, BB, " "`, walk `" ", " ", WW, " ", WW`; Walk Bridges have `WWWW` under two blank rows.
- `room_system_write_pattern` 0x180167560 (rcx system, rdx room record, r8 tile position, r9d mode). Mode 0 is a
  ghost (component +8 set): solid B/C/M/O/X cells get dig orders (0x4000). Mode 1 is a finished room: X, B, C, M
  and O cells lose the solid bit (0x18016799a, 0x180167b4b) and mostly their material, and W sets walk layer 2.
  Modes 2 and 3 remove a ghost or a room. A blank, 0 or `V` cell with a `W` one or two rows below it becomes `C`
  (0x1801676c4); C sets no transport or walk layer bit (0x180167702), so `command_place_tile_is_valid` accepts it.
- Callers: `room_system_finalize_created_components` 0x1801690d2 (mode 1 or 0 by the ghost flag; a load did not
  carve, tested) and `room_system_remove_destroyed_entities` (0x1801693b0 removes the destroyed one; 0x180169507
  re-applies, in mode 1, each finished room within 0x800000 Manhattan (128 tiles) whose column span holds the
  destroyed position's x or whose row span holds its y). That re-apply is what deletes blocks placed in headroom.
- Test (copy of savegame30, `hmtest_head`): tiles (499,1002), (500,1002), (499,1003) set solid in `map/map.bin`
  above entity 3379 (scaffold at 500,1001; rect x 499-500, y 999-1003). Kept through the load and a Lantern Post
  ghost at about (503,1001); gone within 5 s of `order_cancel_single` in vanilla, kept with the mod.
- The fix checks the return address ([rsp+0x138] in write_pattern) to act only in the re-apply, so cave rooms made
  at map generation and a structure's own completion still carve. The earlier guess, a background order deleting
  a block on the same tile, can't be set up (above); the old guard cave was replaced.
