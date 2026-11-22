# Code cave for cart_timeout, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# watch: replaces `mov [rsp+0x18],rbx; mov [rsp+0x10],rdx` at the entry of bt_haul_update (0x1804ef230),
# update(node rcx, context rdx, delta r8) -> bt_result. A Cart delivers through the same haul behaviour as a
# dwarf, and its movement is a queue entry in station_system. A Cart whose trip stops (no reachable target,
# or a vanished entry) waits in this behaviour for good, and the building it serves waits with it. For
# vehicles only (station_system_is_vehicle), this keeps the Cart's position and how long it has not changed
# while the behaviour runs; after LIMIT game seconds it drops the Cart's own route entry
# (station_system_dequeue) and returns BT_FAILURE, so the haul's exit releases its claims and the job is
# offered again, as pausing the building does. Dwarves run the update unchanged.
# TABLE: SLOTS 16-byte slots by entity & (SLOTS-1): u16 entity, u16, i32 x, i32 y, i32 still time (16.16 s).
# COUNT: u32 timeouts so far, u32 last Cart freed, i32 x, i32 y (read from memory in tests).
watch:
        push    rbx
        push    rsi
        push    rdi
        sub     rsp, 0x20
        mov     rbx, rcx                        # node
        mov     rsi, rdx                        # context
        mov     rdi, r8                         # delta
        movzx   edx, word ptr [rsi + 0xec8]     # entity
        mov     rcx, qword ptr [rsi]            # gamestate
        mov     rcx, qword ptr [rcx + 0x28]     # mainstate
        add     rcx, 0x2330                     # station system
        .byte   0xe8                            # station_system_is_vehicle
        .long   IS_VEHICLE - BASE - (1f - start)
1:      test    al, al
        jz      run
        mov     rcx, qword ptr [rsi]
        mov     rcx, qword ptr [rcx + 0x28]
        add     rcx, 0x2678                     # transform ecs
        .byte   0xe8                            # fixed_transform_system_get_world_positions
        .long   WORLD_POSITIONS - BASE - (2f - start)
2:      movzx   ecx, word ptr [rsi + 0xec8]
        lea     rdx, [rcx + rcx*2]
        mov     r8d, dword ptr [rax + rdx*4]    # x
        mov     r9d, dword ptr [rax + rdx*4 + 4]  # y
        mov     edx, ecx
        and     edx, SLOTS - 1
        shl     edx, 4
        .byte   0x4c, 0x8d, 0x15                # lea r10, [rip + TABLE]
        .long   TABLE - BASE - (3f - start)
3:      add     r10, rdx
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
        .byte   0x4c, 0x8d, 0x15                # lea r10, [rip + COUNT]
        .long   COUNT - BASE - (4f - start)
4:      inc     dword ptr [r10]
        mov     dword ptr [r10 + 4], ecx
        mov     dword ptr [r10 + 8], r8d
        mov     dword ptr [r10 + 12], r9d
        mov     edx, ecx                        # the Cart is its own rider in its queue
        mov     rcx, qword ptr [rsi]
        mov     rcx, qword ptr [rcx + 0x28]
        add     rcx, 0x2330
        .byte   0xe8                            # station_system_dequeue
        .long   DEQUEUE - BASE - (5f - start)
5:      mov     eax, 2                          # BT_FAILURE
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
        mov     qword ptr [rsp + 0x18], rbx     # the replaced instructions
        mov     qword ptr [rsp + 0x10], rdx
        .byte   0xe9                            # back into the update
        .long   RESUME - BASE - (6f - start)
6:
end:
