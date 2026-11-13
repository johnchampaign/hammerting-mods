# Code cave for lava_no_walk's load sweep, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# rebuilt: replaces `mov [rsp+8], rcx` (5 bytes) at the top of tile_graph::initialize (0x180330e20),
# which builds a new graph with no fluid on its edges (a load or a new game).
rebuilt:
        .byte   0xc6, 0x05                      # mov byte ptr [rip + pending], 1
        .long   pending - 1f
        .byte   1
1:      mov     qword ptr [rsp + 8], rcx
        .byte   0xe9
        .long   INIT_RESUME - BASE - (2f - start)
2:

# sweep: replaces `mov [rsp+8], rcx` (5 bytes) at the top of tile_graph::update_edge_masks
# (0x180332d50); rcx is the tile graph, [rcx+8] its map. update_edge_masks only visits blocks marked
# dirty (front, fluid or layer), and lava at rest after a load marks none, so its edges carry no lava
# bit and no EDGE_HAS_FLUID, and the path search never calls the edge cost callback for them: the
# lava cost and lava_gate never apply. The first run after a new graph marks every block holding
# lava deep enough to burn as fluid-dirty (MAP_DIRTY_FLUID_BIT, map.h), so this run flags its edges.
sweep:
        .byte   0x80, 0x3d                      # cmp byte ptr [rip + pending], 0
        .long   pending - 3f
        .byte   0
3:      je      refresh
        .byte   0xc6, 0x05                      # mov byte ptr [rip + pending], 0
        .long   pending - 4f
        .byte   0
4:      push    rax
        push    rcx
        push    rdx
        push    r8
        push    r9
        push    r10
        mov     rax, qword ptr [rcx + 8]        # map
        mov     r8d, dword ptr [rax + 0x38]     # blocks
        mov     r9, qword ptr [rax + 8]         # tiles, 256 per block
        mov     r10, qword ptr [rax + 0x18]     # block dirty bits
        xor     ecx, ecx
block:
        cmp     ecx, r8d
        jae     swept
        mov     edx, ecx
        shl     rdx, 10                         # 256 tiles x 4 bytes
        lea     rdx, [r9 + rdx + 3]             # fluid byte of the block's first tile
        mov     eax, 256
tile:
        movzx   r11d, byte ptr [rdx]            # bits 0-2 amount, bits 3-6 fluid type
        and     r11d, 0x7e                      # lava (0x10) with amount 2 or more
        cmp     r11d, 0x12
        jae     5f
6:      add     rdx, 4
        dec     eax
        jnz     tile
        jmp     7f
5:      cmp     r11d, 0x17
        ja      6b
        or      byte ptr [r10 + rcx], 0x10      # MAP_DIRTY_FLUID_BIT
7:      inc     ecx
        jmp     block
swept:
        pop     r10
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
        pop     rax
# refresh: building walkway edges are not tile edges, so update_edge_masks never updates their masks, and
# lava_gate's answer for them would never change. Every 128th run clears every edge's looked bit, so
# lava_gate reads each edge's tiles again on its next visit.
refresh:
        .byte   0xfe, 0x05                      # inc byte ptr [rip + runs]
        .long   runs - 9f
9:      .byte   0xf6, 0x05                      # test byte ptr [rip + runs], 0x7f
        .long   runs - 10f
        .byte   0x7f
10:     jnz     done
        push    rax
        push    rdx
        mov     rax, qword ptr [rcx + 0xb8]     # edge fluid masks
        mov     edx, dword ptr [rcx + 0xc0]     # count
11:     test    edx, edx
        jz      12f
        dec     edx
        and     byte ptr [rax + 2*rdx + 1], 0x7f
        jmp     11b
12:     pop     rdx
        pop     rax
done:
        mov     qword ptr [rsp + 8], rcx        # as before
        .byte   0xe9
        .long   UEM_RESUME - BASE - (8f - start)
8:
pending:
        .byte   0
runs:
        .byte   0
end:
