# Code cave for known_capital_missions, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# tick: replaces `movd xmm0,[r12+0xc4]` at 0x1802af400 in gamestate::update, reached on every frame,
# paused or not. r12 is the gamestate, and volatile registers are dead here.
tick:
        .byte   0xff, 0x05                      # inc dword ptr [rip + frames]
        .long   frames - 1f
1:      mov     rcx, r12
        call    step
        movd    xmm0, dword ptr [r12 + 0xc4]
        .byte   0xe9                            # back to the frame's work
        .long   RESUME - BASE - (2f - start)
2:

# step(gamestate): looks at one hex per frame. A mission still on offer at a hidden hex fails; only saves from
# before this mod have any. A known capital whose faction esteems you, and that has no Dwarven Subversion, gets
# one, so revealing a capital later isn't a missed chance. The child walk is HAS_LOCAL_MISSION's (0x1800ce300).
# rsi hex, ebx its entity, r13 mainstate, r15 family records, ebp child, r12d first child, rdi condition.
step:
        push    rbx
        push    rbp
        push    rsi
        push    rdi
        push    r12
        push    r13
        push    r14
        push    r15
        sub     rsp, 0x28
        mov     r13, qword ptr [rcx + 0x28]
        mov     r14, qword ptr [r13 + 0x1b78]   # overworld map ecs (0x1b38) + 0x40
        test    r14, r14
        jz      done
        mov     ecx, dword ptr [r14 + 0x10]     # hexes
        test    ecx, ecx
        jz      done
        .byte   0x8b, 0x05                      # mov eax, dword ptr [rip + frames]
        .long   frames - 3f
3:      xor     edx, edx
        div     ecx
        imul    rdx, rdx, 0x158
        mov     rsi, qword ptr [r14 + 8]
        add     rsi, rdx
        movzx   ebx, word ptr [rsi]
        cmp     byte ptr [rsi + 0xf7], 0        # explored
        jne     known

        cmp     ebx, TEST_REVEAL
        jne     4f
        .byte   0x81, 0x3d                      # cmp dword ptr [rip + frames], 0x800: test only, after the failures
        .long   frames - 31f
        .long   0x800
31:     jae     reveal
4:      call    first_child
fail_each:
        test    ebp, ebp
        jz      done
        lea     rcx, [r13 + 0x19d0]             # objective ecs
        mov     edx, ebp
        .byte   0xe8                            # call objective_system_get_status
        .long   GET_STATUS - BASE - (5f - start)
5:      test    rax, rax
        jz      6f
        movabs  rcx, 0x4556495443414e49         # "INACTIVE": offered, not accepted
        cmp     qword ptr [rax], rcx
        jne     6f
        cmp     byte ptr [rax + 8], 0
        jne     6f
        lea     rcx, [r13 + 0x19d0]
        mov     edx, ebp
        mov     r8d, STATE_FAILED
        .byte   0xe8                            # call objective_system_set_state
        .long   SET_STATE - BASE - (7f - start)
7:      jmp     done
6:      call    next_child
        jmp     fail_each

known:
        cmp     byte ptr [rsi + 0xf6], 0        # every location is on a road
        je      done
        .byte   0x48, 0x8d, 0x3d                # lea rdi, [rip + conditions]
        .long   conditions - 8f
8:      cmp     byte ptr [rdi], 0
        je      9f
        mov     rdx, rdi
        call    eval
        test    al, al
        jz      done
10:     inc     rdi
        cmp     byte ptr [rdi - 1], 0
        jne     10b
        jmp     8b
9:      call    first_child
offered_each:
        test    ebp, ebp
        jz      offer
        lea     rcx, [r13 + 0x19d0]
        mov     edx, ebp
        .byte   0xe8                            # call objective_system_get_status
        .long   GET_STATUS - BASE - (11f - start)
11:     test    rax, rax
        jz      12f
        cmp     byte ptr [rax], 0x46            # 'F': FAILED, FAILED_WAITING
        je      12f
        cmp     word ptr [rax], 0x4143          # "CA": CANCELLED
        je      12f
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + is_subversion]
        .long   is_subversion - 13f
13:     mov     r8d, ebp
        call    eval_ent
        test    al, al
        jnz     done
12:     call    next_child
        jmp     offered_each
offer:
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + add_offer]
        .long   add_offer - 14f
14:     call    eval
        jmp     done

# reveal: test only (HMOD_KCM_TEST_REVEAL=<hex entity>), the end of overworld_map_system_explore_hex_near_entity.
reveal:
        sub     rsp, 0x40
        mov     byte ptr [rsi + 0xf7], 1
        mov     byte ptr [r14 + 0xc8], 1        # visibility needs updating
        mov     dword ptr [rsp + 0x20], 0x1000a # two pointer arguments: origin hex, explored hex
        mov     dword ptr [rsp + 0x24], 0xd9027f38
        mov     qword ptr [rsp + 0x28], rsi
        mov     dword ptr [rsp + 0x30], 0x1000a
        mov     dword ptr [rsp + 0x34], 0xd9027f38
        mov     qword ptr [rsp + 0x38], rsi
        .byte   0x48, 0x8d, 0x0d                # lea rcx, [rip + "TDTD_EVENT_OVERWORLD_HEX_EXPLORED"]
        .long   EVENT_NAME - BASE - (15f - start)
15:     mov     edx, 0x21
        .byte   0xff, 0x15                      # call [rip + string hash]
        .long   HASH_PTR - BASE - (16f - start)
16:     mov     rcx, qword ptr [r14 + 0x58]
        mov     rcx, qword ptr [rcx + 0x28]
        add     rcx, 0xcb0
        mov     rdx, rax
        lea     r8, [rsp + 0x20]
        mov     r9d, 2
        .byte   0xff, 0x15                      # call [rip + send event]
        .long   SEND_PTR - BASE - (17f - start)
17:     add     rsp, 0x40

done:
        add     rsp, 0x28
        pop     r15
        pop     r14
        pop     r13
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbp
        pop     rbx
        ret

# first_child: ebp, r12d = the first child of the hex in ebx. Keeps r15 = family records.
first_child:
        sub     rsp, 0x28
        lea     rcx, [r13 + 0xe18]              # family ecs
        xor     edx, edx
        xor     r8d, r8d
        .byte   0xff, 0x15                      # call [rip + family records]
        .long   FAMILY_PTR - BASE - (18f - start)
18:     mov     r15, rax
        add     rsp, 0x28
        mov     eax, ebx
        lea     rax, [rax + rax * 4]
        movzx   ebp, word ptr [r15 + rax * 2 + 2]
        mov     r12d, ebp
        ret

# next_child: ebp = the next sibling, or 0 back at the first.
next_child:
        lea     rax, [rbp + rbp * 4]
        movzx   ebp, word ptr [r15 + rax * 2 + 6]
        cmp     ebp, r12d
        jne     19f
        xor     ebp, ebp
19:     ret

# eval(rdx chain) with the hex as context and ARG('0'), eval_ent(rdx chain, r8d entity). Returns al = out's bool.
eval:
        mov     r8d, ebx
eval_ent:
        sub     rsp, 0x878
        mov     dword ptr [rsp + 0x40], 0x00010002      # PCT_ENTITY, one
        mov     dword ptr [rsp + 0x44], 0x1a486         # PC_ENTITY_TAG_GAME
        mov     qword ptr [rsp + 0x48], r8
        mov     dword ptr [rsp + 0x50], 0x00010002
        mov     dword ptr [rsp + 0x54], 0x1a486
        mov     qword ptr [rsp + 0x58], r8
        xor     eax, eax
        mov     qword ptr [rsp + 0x60], rax
        mov     qword ptr [rsp + 0x68], rax
        lea     rcx, [r13 + 0x1e80]             # property ecs
        lea     r8, [rsp + 0x40]
        lea     r9, [rsp + 0x60]
        lea     rax, [rsp + 0x50]
        mov     qword ptr [rsp + 0x20], rax
        mov     qword ptr [rsp + 0x28], 1
        lea     rax, [rsp + 0x70]
        mov     qword ptr [rsp + 0x30], rax
        mov     qword ptr [rsp + 0x38], 0x800
        .byte   0xff, 0x15                      # call [rip + evaluate_chain_string_args]
        .long   EVAL_PTR - BASE - (20f - start)
20:     movzx   eax, byte ptr [rsp + 0x68]
        add     rsp, 0x878
        ret

conditions:
        .asciz  "HAS_LOCATION"
        .asciz  "NOT(FACTION_ENTITY.EQUALS(MOUNTAINHOME))"
        .asciz  "OVERWORLD_MAP_HEX.CAPITAL.STRING.EQUALS(FACTION_ENTITY.FACTION.TAG.STRING)"
        .asciz  "FACTION_ENTITY.RELATION('RELATION_FACTION_OPINION', MOUNTAINHOME).STATE.TAG.STRING.EQUALS('RELATION_FACTION_OPINION_ESTEEMED')"
        .asciz  "NOT(FACTION_ENTITY.RELATION('RELATION_FACTION', MOUNTAINHOME).STATE.TAG.STRING.EQUALS('RELATION_FACTION_ALLIANCE'))"
        .byte   0
is_subversion:
        .asciz  "SMART_EVENT_RECORD.TAG.STRING.EQUALS('MISSION_OVERWORLD_ALLIANCE')"
add_offer:
        .asciz  "ADD_SMART_EVENT_FROM_TRIGGER( 'MISSION_OVERWORLD_ALLIANCE', 'MISSION_PARENT', ARG('0'), 'MISSION_SOURCE_FACTION', ARG('0').FACTION_ENTITY.FACTION)"

        .p2align 3
frames: .long   0
        .long   0
end:
