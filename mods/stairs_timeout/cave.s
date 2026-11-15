# Code cave for stairs_timeout, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# watch: replaces `mov r11,rsp; mov [r11+8],rbx` at the entry of bt_walk_stairs_update (0x1804dda70),
# update(node rcx, context rdx, delta r8) -> bt_result. The behaviour plays one step animation at a
# time and finishes only when that animation's done event arrives; it has no timeout. A dwarf whose
# event never comes stands on the step point for good with his job still running. This keeps, per
# dwarf, his position and how long it has not changed while the behaviour runs; after LIMIT game
# seconds it returns BT_FAILURE (the behaviour's exit then unlocks him) instead of running the update.
# TABLE: SLOTS 16-byte slots by entity & (SLOTS-1): u16 entity, u16, i32 x, i32 y, i32 still time
# (16.16 s). Two dwarves in one slot just keep resetting each other. COUNT: u32 timeouts so far, u32 last entity freed, i32 x, i32 y.
watch:
        push    rbx
        push    rsi
        push    rdi
        sub     rsp, 0x20
        mov     rbx, rcx                        # node
        mov     rsi, rdx                        # context
        mov     rdi, r8                         # delta
        mov     rcx, qword ptr [rdx]            # gamestate
        mov     rcx, qword ptr [rcx + 0x28]     # mainstate
        add     rcx, 0x2678                     # transform ecs
        .byte   0xe8                            # fixed_transform_system_get_world_positions
        .long   WORLD_POSITIONS - BASE - (1f - start)
1:      movzx   ecx, word ptr [rsi + 0xec8]     # entity
        lea     rdx, [rcx + rcx*2]
        mov     r8d, dword ptr [rax + rdx*4]    # x
        mov     r9d, dword ptr [rax + rdx*4 + 4]  # y
        mov     edx, ecx
        and     edx, SLOTS - 1
        shl     edx, 4
        .byte   0x4c, 0x8d, 0x15                # lea r10, [rip + TABLE]
        .long   TABLE - BASE - (2f - start)
2:      add     r10, rdx
        cmp     word ptr [r10], cx
        jne     reset
        cmp     dword ptr [r10 + 4], r8d
        jne     reset
        cmp     dword ptr [r10 + 8], r9d
        jne     reset
        add     dword ptr [r10 + 12], edi       # still: add this update's time
        cmp     dword ptr [r10 + 12], LIMIT
        jl      run
        mov     dword ptr [r10 + 12], 0
        .byte   0x4c, 0x8d, 0x15                # lea r10, [rip + COUNT]: for tests, the timeouts so far and
        .long   COUNT - BASE - (4f - start)     # the last dwarf freed and where
4:      inc     dword ptr [r10]
        mov     dword ptr [r10 + 4], ecx
        mov     dword ptr [r10 + 8], r8d
        mov     dword ptr [r10 + 12], r9d
        mov     eax, 2                          # BT_FAILURE
        add     rsp, 0x20
        pop     rdi
        pop     rsi
        pop     rbx
        ret
reset:
        mov     word ptr [r10], cx
        mov     dword ptr [r10 + 4], r8d
        mov     dword ptr [r10 + 8], r9d
        mov     dword ptr [r10 + 12], 0
run:
        mov     rcx, rbx
        mov     rdx, rsi
        mov     r8, rdi
        add     rsp, 0x20
        pop     rdi
        pop     rsi
        pop     rbx
        mov     r11, rsp                        # the replaced instructions
        mov     qword ptr [r11 + 8], rbx
        .byte   0xe9                            # back into the update
        .long   RESUME - BASE - (3f - start)
3:
end:
