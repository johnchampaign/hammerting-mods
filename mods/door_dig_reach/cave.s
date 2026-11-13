# Code cave for door_dig_reach, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# dead_end: replaces `mov ecx, [rbx]; and ecx, 0x7ffffe00; bts ecx, 8` (12 bytes) at 0x18033545a in
# tile_graph::add_block_ctx_to_graph. That path runs for an edge between a gamepath (door, stairs, rails, building)
# and a tile node that has no edge to another tile node, and marks the edge EDGE_DISABLED. Here the edge stays
# enabled when one of the tile's 8 neighbours holds a dig order, so a dwarf can stand there and dig on. rbx = the
# edge, r10d = its tile node, [rbp+0x4050] = the tile_graph (+8 map, +0x28 node positions: i16 x, y). r9 and r13
# are live; rax, rcx, rdx, r8, r10 and r11 are free.
dead_end:
        push    r9
        push    r12
        mov     rax, qword ptr [rbp + 0x4050]
        mov     rdx, qword ptr [rax + 0x28]
        movsx   r8d, word ptr [rdx + r10*4]     # x
        movsx   r11d, word ptr [rdx + r10*4 + 2] # y
        mov     rax, qword ptr [rax + 8]        # map: +8 tiles, +0x28 width, +0x2c height, +0x30 block width
        lea     rdx, [rip + offsets]
next:
        movsx   ecx, byte ptr [rdx]
        add     ecx, r8d                        # x'
        movsx   r10d, byte ptr [rdx + 1]
        add     r10d, r11d                      # y'
        cmp     ecx, dword ptr [rax + 0x28]
        jae     skip
        cmp     r10d, dword ptr [rax + 0x2c]
        jae     skip
        mov     r9d, r10d                       # ((y>>4) * block width + (x>>4)) << 8 | (y&15) << 4 | x&15
        shr     r9d, 4
        imul    r9d, dword ptr [rax + 0x30]
        mov     r12d, ecx
        shr     r12d, 4
        add     r9d, r12d
        shl     r9d, 8
        and     r10d, 15
        shl     r10d, 4
        or      r9d, r10d
        and     ecx, 15
        or      r9d, ecx
        mov     r12, qword ptr [rax + 8]
        test    dword ptr [r12 + r9*4], 0x4000  # order status 2 or 3: dig
        jnz     keep
skip:
        add     rdx, 2
        cmp     byte ptr [rdx], 0x7f
        jne     next
        pop     r12
        pop     r9
        mov     ecx, dword ptr [rbx]            # as before: disable
        and     ecx, 0x7ffffe00
        bts     ecx, 8
        .byte   0xe9
        .long   DISABLE_RESUME - BASE - (1f - start)
1:
keep:
        pop     r12
        pop     r9
        mov     ecx, dword ptr [rbx]            # as the enabled branch at 0x180335595
        shr     ecx, 8
        and     ecx, 0x7ffffe
        .byte   0xe9
        .long   ENABLE_RESUME - BASE - (1f - start)
1:

offsets:
        .byte   -1, 0,  1, 0,  0, 1,  0, -1,  -1, 1,  1, 1,  -1, -1,  1, -1,  0x7f
end:
