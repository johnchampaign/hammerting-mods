# Code cave for lava_no_walk, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# lava_gate: replaces `mov rax, [rax+0xb8]` at 0x1802ac280 in the tile graph's edge cost callback.
# rax is the tile graph, rcx the edge id, rdx the query's fluid mask, rdi the edge, rsi the query's
# run context and rbx the cost out pointer. With graph.x86_64.dll patched, every edge of every query
# comes through here. An edge's fluid mask is only updated for tile edges where fluid moves (see
# sweep.s), so on an edge's first visit this reads its tiles the way tile_graph::update_edge_masks
# does, then sets the lava bit if needed and bit 15 to say it has looked.
# Every edge with lava is blocked, except in a creature's own movement query (the only kind whose mask
# has the lava bit) that starts in lava: a dwarf caught by a flow can walk out, at lava's usual cost.
# Edges are stored without a direction, and job and hauling costs are searched backwards from the
# target, so a rule about the step's direction would let a target inside lava look reachable.
lava_gate:
        mov     r9, rax
        mov     rax, qword ptr [rax + 0xb8]
        movzx   r8d, word ptr [rax + 2*rcx]
        test    r8d, 0x8000
        jnz     known
        push    r9
        push    rax
        push    rcx
        push    rdx
        push    rbp
        push    r12
        push    r13
        mov     r8, qword ptr [r9 + 0x28]       # node positions, i16 x, i16 y
        mov     r9, qword ptr [r9 + 8]          # map
        mov     eax, dword ptr [rdi + 4]
        movsx   r10d, word ptr [r8 + 4*rax]     # x0
        movsx   r11d, word ptr [r8 + 4*rax + 2] # y0
        mov     eax, dword ptr [rdi + 8]
        movsx   r12d, word ptr [r8 + 4*rax]
        movsx   r13d, word ptr [r8 + 4*rax + 2]
        sub     r12d, r10d                      # dx
        sub     r13d, r11d                      # dy
        mov     eax, r12d
        cdq
        xor     eax, edx
        sub     eax, edx
        mov     ebp, r13d
        mov     ecx, ebp
        sar     ecx, 31
        xor     ebp, ecx
        sub     ebp, ecx
        cmp     ebp, eax
        cmovl   ebp, eax                        # n = max(|dx|, |dy|)
        xor     r8d, r8d                        # i
sample:
        call    lava_at
        jnz     has_lava
        inc     r8d
        cmp     r8d, ebp
        jbe     sample
        mov     r8d, 0x8000
        jmp     sampled
has_lava:
        mov     r8d, 0x8004
sampled:
        pop     r13
        pop     r12
        pop     rbp
        pop     rdx
        pop     rcx
        pop     rax
        pop     r9
        and     word ptr [rax + 2*rcx], 0x7ffb  # a re-look (see sweep.s) can find the lava gone
        or      word ptr [rax + 2*rcx], r8w
        movzx   r8d, word ptr [rax + 2*rcx]
known:
        test    r8d, 4
        jz      resume
        test    byte ptr [rsi + 0x4c], 4        # the query's own lava bit: a walker's movement query
        jz      blocked
        push    rax
        push    rcx
        push    rdx
        push    rbp
        push    r12
        push    r13
        mov     r8, qword ptr [r9 + 0x28]       # node positions
        mov     r9, qword ptr [r9 + 8]          # map
        mov     r12, qword ptr [rsi]            # _start_nodes
        mov     r13, qword ptr [rsi + 8]        # _start_node_count: a movement query has one or two
        xor     ebp, ebp                        # one tile: lava_at reads no r8, r12, r13
2:      test    r13, r13
        jz      3f                              # no start in lava (ZF set)
        dec     r13
        mov     eax, dword ptr [r12 + 4*r13]
        movsx   r10d, word ptr [r8 + 4*rax]
        movsx   r11d, word ptr [r8 + 4*rax + 2]
        call    lava_at
        jz      2b
3:      pop     r13
        pop     r12
        pop     rbp
        pop     rdx
        pop     rcx
        pop     rax
        jnz     resume
blocked:
        .byte   0xe9
        .long   BLOCKED - BASE - (4f - start)
4:
resume:
        .byte   0xe9
        .long   RESUME - BASE - (5f - start)
5:

# lava_at: ZF clear if tile i of ebp along the edge has lava above its threshold. Keeps r8-r13, ebp.
lava_at:
        xor     ecx, ecx
        test    ebp, ebp
        jz      1f
        mov     eax, r12d
        imul    eax, r8d
        cdq
        idiv    ebp
        mov     ecx, eax
1:      add     ecx, r10d                       # x
        xor     eax, eax
        test    ebp, ebp
        jz      2f
        mov     eax, r13d
        imul    eax, r8d
        cdq
        idiv    ebp
2:      add     eax, r11d                       # y
        mov     edx, dword ptr [r9 + 0x30]      # some nodes lie off the map
        shl     edx, 4
        cmp     ecx, edx
        jae     dry
        mov     edx, dword ptr [r9 + 0x34]      # height in blocks
        shl     edx, 4
        cmp     eax, edx
        jae     dry
        mov     edx, eax
        shr     eax, 4
        imul    eax, dword ptr [r9 + 0x30]      # width in blocks
        push    rcx
        shr     ecx, 4
        add     eax, ecx
        pop     rcx
        shl     eax, 4
        and     edx, 15
        add     eax, edx
        shl     eax, 4
        and     ecx, 15
        add     eax, ecx
        mov     rcx, qword ptr [r9 + 8]         # tiles
        movzx   eax, byte ptr [rcx + 4*rax + 3] # bits 0-2 amount, bits 3-6 fluid type
        mov     ecx, eax
        and     ecx, 0x78
        cmp     ecx, 0x10                       # lava
        jne     dry
        and     eax, 7
        cmp     eax, 1                          # lava's effect threshold
        jbe     dry
        or      eax, 1                          # ZF clear
        ret
dry:
        xor     eax, eax                        # ZF set
        ret
end:
