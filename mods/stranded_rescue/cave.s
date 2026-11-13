# Code cave for stranded_rescue, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# tick: replaces `ucomisd xmm8,xmm6; je 0x1802af400` at 0x1802af3c5 in gamestate::update, which skips
# the frame's work when delta (xmm8) is 0. xmm6 is 0, r12 the gamestate, and volatile registers are
# dead here. Runs check every CHECK_SECONDS of game time, so a paused game doesn't count.
tick:
        ucomisd xmm8, xmm6
        .byte   0x0f, 0x84                      # je SKIP
        .long   SKIP - BASE - (1f - start)
1:      .byte   0x48, 0x8d, 0x05                # lea rax, [rip + timer]
        .long   timer - 2f
2:      movsd   xmm0, qword ptr [rax]
        subsd   xmm0, xmm8
        movsd   qword ptr [rax], xmm0
        comisd  xmm0, xmm6
        ja      3f
        movabs  rcx, CHECK_BITS
        mov     qword ptr [rax], rcx
        mov     rcx, r12
        call    check
3:      .byte   0xe9                            # back to the frame's work
        .long   RESUME - BASE - (4f - start)
4:

# check(gamestate): counts how many checks in a row each dwarf has been stranded, then moves one
# that reached THRESHOLD. Dwarves in the overworld are left out, and a seated rider doesn't count
# up. Nobody moves while more than half are stranded: that is more likely the entrance cut off from
# the colony, and moving them would strand them all away from their food.
# rbx dwarf count, rsi index, rbp dwarf, rdi stranded, r14 dwarves in the cave, r15 counters, r13 mainstate.
check:
        push    rbx
        push    rbp
        push    rsi
        push    rdi
        push    r12
        push    r13
        push    r14
        push    r15
        sub     rsp, 0xc8
        mov     r12, rcx
        mov     r13, qword ptr [rcx + 0x28]
        .byte   0x4c, 0x8d, 0x3d                # lea r15, [rip + counters]
        .long   COUNTERS - BASE - (5f - start)
5:      lea     rcx, [r13 + 0x2498]             # tag ecs
        movabs  rdx, HASH_PLAYER
        lea     r8, [rsp + 0xa8]
        .byte   0xff, 0x15                      # call [rip + tagged entities]
        .long   TAGGED_PTR - BASE - (6f - start)
6:      mov     rbx, rax
        test    rbx, rbx
        jz      done
        xor     esi, esi
        xor     edi, edi
        xor     r14d, r14d

each:
        mov     rax, qword ptr [rsp + 0xa8]
        movzx   ebp, word ptr [rax + rsi*2]
        lea     rcx, [r13 + 0x2498]
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + "CURRENTLY_IN_OVERWORLD"]
        .long   IN_OVERWORLD - BASE - (7f - start)
7:      mov     r8d, ebp
        .byte   0xff, 0x15                      # call [rip + has tag]
        .long   HAS_TAG_PTR - BASE - (8f - start)
8:      test    al, al
        jnz     clear
        inc     r14d
        # ALERT_IS_STRANDED, the game's own test, called with a one-entity property chain input.
        mov     qword ptr [rsp + 0x20], r12     # +0 userdata: gamestate
        mov     dword ptr [rsp + 0x50], 0x10002 # +0x30 u16 type 2 (entity), u16 count 1
        mov     dword ptr [rsp + 0x54], 0x1a486 # +0x34 PC_ENTITY_TAG_GAME
        mov     word ptr [rsp + 0x58], bp       # +0x38 the entity
        lea     rax, [rsp + 0x68]
        mov     qword ptr [rsp + 0x60], rax     # +0x40 out: type, then the value at +8
        mov     qword ptr [rsp + 0x70], 0
        lea     rcx, [rsp + 0x20]
        .byte   0xe8
        .long   IS_STRANDED - BASE - (9f - start)
9:      cmp     byte ptr [rsp + 0x70], 0
.if TEST_FORCE_A
        jne     stranded
        cmp     ebp, TEST_FORCE_A
        je      stranded
        cmp     ebp, TEST_FORCE_B
        je      stranded
        cmp     ebp, TEST_FORCE_C
        je      stranded
        jmp     clear
stranded:
.else
        je      clear
.endif
        inc     edi
        lea     rcx, [r13 + 0xe18]              # family ecs
        xor     edx, edx
        xor     r8d, r8d
        .byte   0xff, 0x15                      # call [rip + family records], 10 bytes each
        .long   FAMILY_PTR - BASE - (10f - start)
10:     lea     rcx, [rbp + rbp*4]
        cmp     word ptr [rax + rcx*2], 0       # a parent: seated in a vehicle
        jne     clear
        cmp     byte ptr [r15 + rbp], THRESHOLD
        jae     next
        inc     byte ptr [r15 + rbp]
        jmp     next
clear:
        mov     byte ptr [r15 + rbp], 0
next:
        inc     rsi
        cmp     rsi, rbx
        jb      each

        lea     eax, [rdi + rdi]
        cmp     eax, r14d
        ja      done
        xor     esi, esi
find:
        mov     rax, qword ptr [rsp + 0xa8]
        movzx   ebp, word ptr [rax + rsi*2]
        cmp     byte ptr [r15 + rbp], THRESHOLD
        jae     rescue
        inc     rsi
        cmp     rsi, rbx
        jb      find
        jmp     done

# One dwarf per check. The steps are bt_fall_enter's: stop him, clear his graph position and his
# query's start. Clearing it also makes the fall sensor start BT_FALL, which lands him on this tile
# and sets both again (the path a dwarf embedded in rock takes). Tile x + 0.5 and whole y are what
# bt_fall_update's landing test wants; his z stays.
rescue:
        mov     byte ptr [r15 + rbp], 0
        mov     word ptr [rsp + 0xa0], 0
        mov     rcx, r12
        lea     rdx, [rsp + 0xa0]
        .byte   0xe8                            # get_entrance_data: u16 entity first
        .long   ENTRANCE_DATA - BASE - (11f - start)
11:     movzx   edi, word ptr [rsp + 0xa0]
        test    edi, edi
        jz      done
        lea     rcx, [r13 + 0x2678]             # transform ecs
        .byte   0xe8                            # fixed_transform_system_get_world_positions
        .long   WORLD_POSITIONS - BASE - (12f - start)
12:     lea     rcx, [rdi + rdi*2]
        mov     edx, dword ptr [rax + rcx*4]
        mov     r8d, dword ptr [rax + rcx*4 + 4]
        lea     rcx, [rbp + rbp*2]
        mov     r9d, dword ptr [rax + rcx*4 + 8]
        and     edx, 0xffff0000
        or      edx, 0x8000
        and     r8d, 0xffff0000
        mov     dword ptr [rsp + 0x78], edx
        mov     dword ptr [rsp + 0x7c], r8d
        mov     dword ptr [rsp + 0x80], r9d
        mov     word ptr [rsp + 0x84], bp
        lea     rcx, [r13 + 0x17f0]             # movement ecs
        lea     rdx, [rsp + 0x84]
        mov     r8d, 1
        .byte   0xe8                            # movement_system_force_stop(ecs, entities, count)
        .long   FORCE_STOP - BASE - (13f - start)
13:     lea     rcx, [r13 + 0x2678]
        mov     edx, ebp
        lea     r8, [rsp + 0x78]
        .byte   0xe8                            # fixed_transform_system_set_world_position
        .long   SET_WORLD - BASE - (14f - start)
14:     lea     rcx, [r13 + 0x17f0]
        mov     edx, ebp
        .byte   0xe8                            # movement_system_get_query_id
        .long   QUERY_ID - BASE - (15f - start)
15:     movzx   ebx, ax
        xorps   xmm0, xmm0
        movups  xmmword ptr [rsp + 0x88], xmm0
        mov     qword ptr [rsp + 0x98], 0
        lea     rcx, [r13 + 0x11d8]             # graph position ecs
        mov     edx, ebp
        lea     r8, [rsp + 0x88]
        .byte   0xe8                            # graph_position_system_update_position
        .long   UPDATE_POSITION - BASE - (16f - start)
16:     lea     rcx, [r13 + 0x18e0]             # navgraph query ecs
        mov     edx, ebx
        lea     r8, [rsp + 0x88]
        mov     r9d, 1
        .byte   0xe8                            # navgraph_query_system_set_start_positions
        .long   SET_START - BASE - (17f - start)
17:
done:
        add     rsp, 0xc8
        pop     r15
        pop     r14
        pop     r13
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbp
        pop     rbx
        ret

        .p2align 3
timer:
        .quad   0
end:
