# Code cave for rail_fixes, in the .hmod section (see tools/cave.py for the convention).

        .intel_syntax noprefix
        .text
start:

# rider_cleanup: replaces the stub `mov rcx,[rcx+0x40]; jmp destroy_entities` at 0x18035f060,
# station_system_remove_destroyed_entities(ecs, u16 *ids, count). Queue entries of destroyed
# riders are never removed otherwise, and the vehicle serves the first entry for good.
rider_cleanup:
        push    rbx
        push    rsi
        push    rdi
        push    r12
        sub     rsp, 0x28
        mov     rbx, rcx
        mov     rsi, rdx
        mov     rdi, r8
        xor     r12d, r12d
next_id:
        cmp     r12, rdi
        jae     ids_done
        movzx   edx, word ptr [rsi + 2*r12]
        mov     rcx, rbx
        .byte   0xe8                            # station_system_dequeue
        .long   DEQUEUE - BASE - (1f - start)
1:      inc     r12
        jmp     next_id
ids_done:
        mov     rcx, qword ptr [rbx + 0x40]
        mov     rdx, rsi
        mov     r8, rdi
        add     rsp, 0x28
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbx
        .byte   0xe9                            # destroy_entities
        .long   DESTROY - BASE - (2f - start)
2:

# teardown_next: replaces the end of the rider loop in on_event_teardown at 0x18035eb3a. The rider
# just detached is in [rsp+0xe0], and di holds the next one, read before the detach. The original
# never stores di back, so a rider list of two or more stops after the first. The list is circular
# and a detached node links to itself, so di == current on the last rider.
teardown_next:
        movzx   edx, word ptr [rsp + 0xe0]
        cmp     di, dx
        je      teardown_done
        mov     word ptr [rsp + 0xe0], di
        movzx   edx, di
        test    dx, dx
        .byte   0x0f, 0x85                      # jnz the top of the loop
        .long   TEARDOWN_TOP - BASE - (3f - start)
3:
teardown_done:
        .byte   0xe9
        .long   TEARDOWN_END - BASE - (4f - start)
4:
end:
