# Code cave for keep_placed_blocks, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# keep_check: replaces `cmp esi, 1; jne MODE_OTHER` (9 bytes) at 0x180167958 in room_system_write_pattern, where a
# pattern cell is about to be applied in mode 1 (a finished room: carve its cells). esi is the mode, r11d the
# cell's character, rbx the map (tile array at +8) and r15 the tile index. The return address of the call sits at
# [rsp+0x138] (seven pushes and 0x100 of locals).
#
# room_system_remove_destroyed_entities re-applies every finished room in the rows or columns of a destroyed one
# (a cancelled or finished ghost, a teardown) in mode 1. A 'C' cell, the headroom over a 'W' walkway, sets no layer
# bit, so Place Block accepts it, and mode 1 then clears its solid bit and material. Only in that re-apply, a C
# cell whose tile is solid is now left alone; a room's own creation still carves as before.
keep_check:
        cmp     esi, 1
        je      1f
        .byte   0xe9
        .long   MODE_OTHER - BASE - (2f - start)
2:
1:      cmp     r11d, 0x43                      # 'C'
        jne     3f
        mov     rax, qword ptr [rbx + 8]
        test    dword ptr [rax + r15*4], 0x200000
        jz      3f                              # open tile: as before
        .byte   0x48, 0x8d, 0x05                # lea rax, [rip + REFRESH_RET]
        .long   REFRESH_RET - BASE - (4f - start)
4:
        cmp     qword ptr [rsp + 0x138], rax
        jne     3f                              # not the re-apply: as before
        .byte   0xe9                            # next layer or cell (reloads r9)
        .long   SKIP - BASE - (5f - start)
5:
3:      .byte   0xe9
        .long   MODE1 - BASE - (6f - start)
6:
end:
