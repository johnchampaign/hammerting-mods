# Code cave for local_maintain_cap, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# count: replaces the call to production_system_get_matching_output_entities(ecs, producer, entry, 2, 0, 0)
# in refresh_maintain_locally. It returns the building's own count, or a huge one once the colony
# holds FACTOR times the entry's high mark, so the caller sets the amount to 0. The colony count is
# refresh_maintain_globally's. rcx ecs, dx producer, r8 entry.
count:
        push    rbx
        push    rsi
        push    rdi
        sub     rsp, 0x40
        mov     rdi, rcx
        mov     rbx, r8
        mov     qword ptr [rsp + 0x20], 0
        mov     qword ptr [rsp + 0x28], 0
        mov     r9d, 2
        .byte   0xe8                            # production_system_get_matching_output_entities
        .long   MATCHING - BASE - (1f - start)
1:      mov     rsi, rax
        mov     rax, qword ptr [rbx + 0x10]     # recipe
        cmp     byte ptr [rax + 0xec0], 0       # deliver_only: not stock, leave it alone
        jne     local
        mov     rdi, qword ptr [rdi + 0x40]     # production_system data
        mov     dword ptr [rsp + 0x30], 0       # UNCLAIMED
        mov     dword ptr [rsp + 0x34], 2
        mov     dword ptr [rsp + 0x38], 3
        lea     rcx, [rdi + 0x478]
        mov     rdx, rbx
        lea     r8, [rsp + 0x30]
        mov     r9d, 3
        .byte   0xe8                            # global_inventory_system_get_matching_inventory
        .long   GLOBAL - BASE - (2f - start)
2:      movzx   ecx, word ptr [rbx]
        imul    rcx, rcx, 0x68
        add     rcx, qword ptr [rdi + 0x90]     # entry extras
        mov     ecx, dword ptr [rcx + 4]        # high mark
.if TEST_DIAG
        .byte   0x4c, 0x8d, 0x15                # lea r10, [rip + diag]
        .long   diag - 6f
6:      mov     qword ptr [r10], rax
        mov     qword ptr [r10 + 8], rsi
        mov     qword ptr [r10 + 16], rcx
        mov     rdx, qword ptr [rbx + 0x538]
        mov     qword ptr [r10 + 24], rdx
        inc     qword ptr [r10 + 32]
.endif
        imul    rcx, rcx, FACTOR
        cmp     rax, rcx
        jb      local
        mov     rsi, 0x7fffffff
local:
        mov     rax, rsi
        add     rsp, 0x40
        pop     rdi
        pop     rsi
        pop     rbx
        ret

# tick: replaces `cmp dword ptr [rbx+0x548], 4; jne next` in production_system_update's loop over
# every entry, which refreshes only Global Maintain. Local Maintain refreshes on inventory events, and
# none fires here when the colony's stock falls, so the cap needs this to lift. Registers there: rbx
# entry, rsi ecs, bpl the building's inventory is full (left to the event path). RATE is the code after
# the global count call, which compares rax to the marks and sets the amount with the entry's own type.
tick:
        mov     eax, dword ptr [rbx + 0x548]
        cmp     eax, 4
        .byte   0x0f, 0x84                      # je: Global Maintain, as before
        .long   GLOBAL_PATH - BASE - (3f - start)
3:      cmp     eax, 2
        jne     skip
        test    bpl, bpl
        jnz     skip
        sub     rsp, 0x38
        mov     rcx, rsi
        movzx   edx, word ptr [rbx + 2]         # producer
        mov     r8, rbx
        call    count
        add     rsp, 0x38
        .byte   0xe9
        .long   RATE - BASE - (4f - start)
4:
skip:
        .byte   0xe9
        .long   NEXT - BASE - (5f - start)
5:
.if TEST_DIAG
diag:
        .fill   40, 1, 0
.endif
end:
