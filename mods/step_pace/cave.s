# Code cave for step_pace, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# step_enter: replaces `mov qword ptr [rbp+0x1a0], 0x10000` (11 bytes) at 0x1804dd655 in bt_walk_stairs_enter,
# the playback multiplier of the first skip_up/skip_down animation. rax (animation tag), rdx (&entity), r8 (&info)
# and r9 (count) are live; rdi = the behaviour context, [rdi+0x28] the gamestate.
step_enter:
        push    rax
        push    rdx
        push    r8
        push    r9
        mov     rcx, qword ptr [rdi + 0x28]
        movzx   edx, word ptr [rbp + 0x1318]
        call    rate
        mov     qword ptr [rbp + 0x1a0], rax
        pop     r9
        pop     r8
        pop     rdx
        pop     rax
        .byte   0xe9
        .long   ENTER_RESUME - BASE - (1f - start)
1:

# step_next: replaces the same store, `mov qword ptr [rbp+0x190], 0x10000` at 0x1804dd041, in
# event_callback_stairs_anim_done, which plays the next step. Only rax (0) is live; r14 = the context.
step_next:
        mov     rcx, qword ptr [r14 + 0x28]
        movzx   edx, word ptr [rbp + 0x1270]
        call    rate
        mov     qword ptr [rbp + 0x190], rax
        xor     eax, eax
        .byte   0xe9
        .long   NEXT_RESUME - BASE - (1f - start)
1:

# rate(rcx = gamestate, dx = entity) -> rax = FACTOR * STAT_MOVE_SPEED (16.16), clamped to MIN..MAX. Walking plays
# its animation at STAT_MOVE_SPEED (bt_walk_enter); steps played at 1.0 whatever the dwarf's speed.
rate:
        sub     rsp, 0x58
        mov     word ptr [rsp + 0x38], dx
        add     rcx, 0x1778                     # modifier system
        lea     rdx, [rsp + 0x38]
        mov     r8d, 1
        lea     rax, [rip + name]
        mov     qword ptr [rsp + 0x40], rax
        lea     r9, [rsp + 0x40]
        mov     qword ptr [rsp + 0x20], r8
        lea     rax, [rsp + 0x48]
        mov     dword ptr [rax], 0x10000
        mov     qword ptr [rsp + 0x28], rax
        add     rax, 4
        mov     qword ptr [rsp + 0x30], rax
        .byte   0xff, 0x15                      # call [modifier_system_get_by_name]
        .long   GET_BY_NAME - BASE - (1f - start)
1:
        movsxd  rax, dword ptr [rsp + 0x48]
        imul    rax, rax, FACTOR
        sar     rax, 16
        mov     ecx, MIN
        cmp     rax, rcx
        cmovl   rax, rcx
        mov     ecx, MAX
        cmp     rax, rcx
        cmovg   rax, rcx
        add     rsp, 0x58
        ret

name:   .asciz  "STAT_MOVE_SPEED"
end:
