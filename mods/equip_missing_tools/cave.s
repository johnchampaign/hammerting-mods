# Code cave for equip_missing_tools, placed in the .hmod section that tools/dllpatch.py appends.
# Assembled by mod.py through tools/cave.py; BASE and the absolute addresses come in as --defsym.
# Windows x64 calling convention: args rcx, rdx, r8, r9, then the stack above 32 bytes of
# home space; rbx, rsi, rdi, rbp, r12-r15 are callee-saved; rsp is 16-byte aligned at calls.

        .intel_syntax noprefix
        .text
start:

# score_slot: replaces `cmp r9d, ebx; jle +0x42` at 0x1803efe80 in sensor_equip_try_equip_upgrade,
# after it has scored one (candidate tool kind, belt slot) pair. r9d is the score, ebx the dwarf's
# best so far, r13 the slot, r14 the profession whose level decides between dwarves. rbp is the
# function's frame, and rsp there is rbp - 0x100. rax, rcx, rdx, r8, r10, r11 are free.
# Frame: -0xc0 sensor, -0xb0 profession count, -0x50 slot * profession count, -0x38 modifier system,
# -0x28 profession records, -0x20 candidate's values, -0x18 candidate's professions {ptr, u32 n},
# -0x10 the slot's setting + 3, +0x570 belt values, +0x970 its inline marker, +0x9e8 the dwarf.
#
# The original only scores professions the slot is already assigned, so a tool for a profession
# nobody has a tool for scores at most 0 and is never taken. Here such a pair gets a large bonus if:
# the slot is in recommended mode and not the dwarf's weapon; every profession its current tool offers is also offered by
# another tool on a belt, so what it replaces stays covered and the dwarves can't trade it back;
# no belt has a tool for the profession; and this dwarf may do it and has a level in it.
# The original score stays in the sum, so the slot whose tool is used least goes first.
score_slot:
        push    rbx
        push    rsi
        push    rdi
        push    r12
        push    r15
        sub     rsp, 0x60
        mov     r15d, r9d
        mov     rdi, qword ptr [rbp - 0xc0]
        mov     rax, qword ptr [rbp - 0x10]
        cmp     byte ptr [rax - 1], 0           # _upgrade_to_recommended
        je      finish
        cmp     byte ptr [rax + 8], 0           # _allowed_professions[8], MILITIA: keep the weapon
        jne     finish

        lea     rax, [rbp + 0x570]
        cmp     word ptr [rbp + 0x970], 0xffff
        cmove   rax, qword ptr [rbp + 0x570]
        mov     rcx, qword ptr [rbp - 0x50]
        lea     r12, [rax + rcx*4]              # the slot's current tool: value per profession
        xor     ebx, ebx
keep_covered:
        cmp     rbx, qword ptr [rbp - 0xb0]
        jae     find_missing
        cmp     dword ptr [r12 + rbx*4], 0
        jle     keep_next
        mov     rax, qword ptr [rbp - 0x28]
        mov     rcx, qword ptr [rax + rbx*8]
        call    on_belts
        cmp     rax, 2
        jb      finish
keep_next:
        inc     rbx
        jmp     keep_covered

find_missing:
        mov     rsi, qword ptr [rbp - 0x18]
        xor     ebx, ebx
missing_loop:
        cmp     ebx, dword ptr [rsi + 8]
        jae     finish
        mov     rax, qword ptr [rbp - 0x20]
        mov     rax, qword ptr [rax]
        cmp     dword ptr [rax + rbx*4], 0
        jle     missing_next
        mov     rax, qword ptr [rsi]
        mov     r12, qword ptr [rax + rbx*8]    # profession record
        mov     rcx, r12
        call    on_belts
        test    rax, rax
        jnz     missing_next

        mov     qword ptr [rsp + 0x40], 0       # KV PROF_X_ALLOWED, as refresh_autoupgrade reads it
        mov     qword ptr [rsp + 0x48], 0
        mov     rcx, qword ptr [rbp - 0x38]
        sub     rcx, 0x258                      # key_value system: mainstate+0x1520, modifier +0x1778
        movzx   edx, word ptr [rbp + 0x9e8]
        mov     r8, qword ptr [r12 + 0xb8]
        lea     r9, [rsp + 0x40]
        .byte   0xff, 0x15
        .long   KV_GET_PTR - BASE - (1f - start)
1:
        movzx   eax, word ptr [rsp + 0x40]
        test    ax, ax
        jz      check_level                     # no key: allowed
        cmp     ax, 3
        jne     missing_next
        cmp     dword ptr [rsp + 0x44], 0
        jne     missing_next
        movzx   ecx, word ptr [rsp + 0x42]
        test    cx, cx
        jz      missing_next
        lea     rax, [rsp + 0x48]
        cmp     cx, 1
        cmovne  rax, qword ptr [rsp + 0x48]
        cmp     qword ptr [rax], 0
        je      missing_next

check_level:
        mov     dword ptr [rsp + 0x50], 0
        mov     byte ptr [rsp + 0x54], 0
        lea     rax, [rsp + 0x54]
        mov     qword ptr [rsp + 0x30], rax
        lea     rax, [rsp + 0x50]
        mov     qword ptr [rsp + 0x28], rax
        mov     qword ptr [rsp + 0x20], 1
        mov     rcx, qword ptr [rbp - 0x38]
        lea     rdx, [rbp + 0x9e8]
        mov     r8d, 1
        lea     r9, [r12 + 0x360]               # _modifier_level
        .byte   0xff, 0x15
        .long   MOD_GET_PTR - BASE - (2f - start)
2:
        cmp     dword ptr [rsp + 0x50], 0
        jle     missing_next
        mov     r14, r12
        add     r15d, 0x40000000
        jmp     finish
missing_next:
        inc     ebx
        jmp     missing_loop

finish:
        mov     r9d, r15d
        add     rsp, 0x60
        pop     r15
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbx
        cmp     r9d, ebx
        jg      better
        add     qword ptr [rsp], 0x42           # the original jle
better:
        ret

# unused_slot_first: replaces `mov eax, [rsp+0x48]; mov [rbp-0x76], bx` at 0x1803efff3, where the
# winning pair becomes an equip entry. eax is the value that decides between dwarves wanting the same
# item. rcx and rdx are live. The winning score is at rbp+0x9d0, except that its low byte has been
# overwritten. A score of exactly the bonus means the slot's tool does nothing for its dwarf, so
# that dwarf goes ahead of any who would give up a tool they use.
unused_slot_first:
        mov     word ptr [rbp - 0x76], bx
        mov     eax, dword ptr [rbp + 0x9d0]
        shr     eax, 8
        cmp     eax, 0x400000
        mov     eax, dword ptr [rsp + 0x50]     # +8 for the return address
        jne     level_only
        add     eax, 0x10000000
level_only:
        ret

# on_belts: rcx = profession record; rax = how many tools offering it have a claim other than sale,
# haul or trade, which is what a belt holds (_claimed_count[4], gie +0x28), summed over the sensor's
# tool kinds. rdi = sensor. Uses rax, rdx, r8-r10.
on_belts:
        xor     eax, eax
        xor     edx, edx
kind_loop:
        cmp     edx, dword ptr [rdi + 0x28]
        jae     kinds_done
        mov     r8, rdx
        shl     r8, 4
        mov     r9, qword ptr [rdi + 0x30]
        add     r9, r8
        mov     r10, qword ptr [rdi + 0x40]
        mov     r10, qword ptr [r10 + r8]
        mov     r8d, dword ptr [r9 + 8]
        mov     r9, qword ptr [r9]
prof_loop:
        test    r8d, r8d
        jz      kind_next
        dec     r8d
        cmp     qword ptr [r9 + r8*8], rcx
        jne     prof_loop
        cmp     dword ptr [r10 + r8*4], 0
        jle     prof_loop
        mov     r8, qword ptr [rdi + 0x20]
        mov     r8, qword ptr [r8 + rdx*8]
        add     rax, qword ptr [r8 + 0x28]
kind_next:
        inc     edx
        jmp     kind_loop
kinds_done:
        ret
end:
