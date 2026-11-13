# Code cave for discovery_counts_found_rooms, in the .hmod section (see tools/cave.py).
# Entered by `jmp` from 0x180086219 in MISSION_GEN_DISCOVER, replacing `cmp r14b,4; jne 0x180086282`.
# Live: r15 the part instance, rdi args (16-byte property_comps), r14b arg_count, r12 &mainstate+0x1e80.
# rbx, rsi, r14 and volatiles are dead at RESUME (0x180086282). [rsp+0x60] is the chain buffer, written later.
        .intel_syntax noprefix
        .text
start:
floor:
        xor     ebx, ebx                        # floor = 0
        cmp     r14b, 4
        jne     1f
        lea     rcx, [rdi + 0x30]               # args[3]
        .byte   0xe8                            # property_comp::to_i64
        .long   TO_I64 - BASE - (0f - start)
0:      mov     rbx, rax
1:      lea     rcx, [rsp + 0x60]               # scratch (the chain buffer, unused yet)
        mov     edx, 0x100
        .byte   0x4c, 0x8d, 0x05                # lea r8, [rip + "%s_EXPLORED"]
        .long   FMT - BASE - (2f - start)
2:      lea     r9, [r15 + 0x120]               # TYPE tag string, e.g. CAVE_ROOM_FOUNTAIN_GOD
        .byte   0xff, 0x15                      # call [sys_snprintf]
        .long   SNPRINTF - BASE - (3f - start)
3:      lea     rcx, [rsp + 0x60]
        mov     rdx, -1
4:      inc     rdx
        cmp     byte ptr [rcx + rdx], 0
        jne     4b
        .byte   0xff, 0x15                      # call [wc_hash] (ptr, len)
        .long   WC_HASH - BASE - (5f - start)
5:      mov     rdx, rax
        lea     rcx, [r12 + 0x870]              # &mainstate->_unlock_system (mainstate+0x26f0)
        .byte   0xe8                            # unlock_system_is_known(ecs, hash)
        .long   IS_KNOWN - BASE - (6f - start)
6:      test    al, al
        je      7f
        test    rbx, rbx
        jg      7f
        mov     ebx, 1                          # a room of this type was discovered at some point
7:      cmp     dword ptr [r15 + 0x230], 0x10004 # AMOUNT_DONE is an inline i64?
        jne     8f
        cmp     qword ptr [r15 + 0x238], rbx
        jge     9f
8:      mov     qword ptr [r15 + 0x230], 0x10004
        mov     qword ptr [r15 + 0x238], rbx
9:      cmp     dword ptr [r15 + 0x1a0], 0x10004 # AMOUNT_WANTED inline i64?
        jne     10f
        mov     rax, qword ptr [r15 + 0x238]
        cmp     rax, qword ptr [r15 + 0x1a8]
        jl      10f
        cmp     byte ptr [r15 + 0x550], 0       # the part is met: queue it for drain (cave_drain.s)
        jne     10f
        .byte   0x8b, 0x05                      # mov eax, [rip + COUNT]
        .long   COUNT - BASE - (12f - start)
12:     cmp     eax, 16
        jae     10f
        .byte   0x48, 0x8d, 0x0d                # lea rcx, [rip + LIST]
        .long   LIST - BASE - (13f - start)
13:     mov     qword ptr [rcx + rax*8], r15
        inc     eax
        .byte   0x89, 0x05                      # mov [rip + COUNT], eax
        .long   COUNT - BASE - (10f - start)
10:     .byte   0xe9
        .long   RESUME - BASE - (11f - start)
11:
end:
