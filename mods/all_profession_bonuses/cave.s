# Code cave for all_profession_bonuses, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# add_all_bonus: replaces `cmp byte ptr [rbp + 0x77d0], 0` at 0x1802976e8 in mainstate::mainstate, where each
# generated profession modifier entry is committed. The je after the call still reads the flags of that compare.
# There r13 is the generated kind (0 %s_LEVEL, 1 %s_SPEED, 2 %s_CRIT_SUCCESS, 3 %s_CRIT_FAILURE, 4 %s_XP_GAIN,
# 5 %s_PRODUCTION, 6 %s_DPS), [rbp + 0x77d0] the entry's name (empty when the profession has no such entry),
# rdi the generated entries (0x23c8 bytes each) and r12 the index of this profession's %s_LEVEL entry.
# The entry being built is at [rbp + 0x7b70]; its funcs start at +0xc8, 0x8c0 bytes each: source tag +0, compute
# tag +0x40, dependency tags +0x80 (16, 0x40 each), dependency weights +0x880 (16.16). A tag is name[0x38] then
# wc_hash(name), and a dependency list ends at the first zero hash.
#
# The game evaluates one func per source, so a second FROM_DWARF func is ignored. Instead this extends func 0
# (FROM_DWARF dependencies_multiply_and_sum) of speed, crit success, crit failure and production:
# - next to %s_LEVEL, PROF_ALL_LEVELS with the same weight, so level grants count wherever the level does;
# - for speed and the crits, PROF_ALL_SPEEDS, _CRIT_SUCCESSES or _CRIT_FAILURES with weight 1.
add_all_bonus:
        cmp     byte ptr [rbp + 0x77d0], 0
        je      check
        cmp     r13, 5
        ja      check
        cmp     r13, 4
        je      check
        test    r13, r13
        jz      check
        push    rax
        push    rcx
        push    rdx
        push    rsi
        push    rdi
        push    r8
        push    r9
        imul    rax, r12, 0x23c8
        mov     r9, qword ptr [rdi + rax + 0x38]        # this profession's %s_LEVEL hash
        lea     r8, [rbp + 0x7c38]                      # func 0
        movabs  rax, H_COMPUTE
        cmp     qword ptr [r8 + 0x78], rax
        jne     restore
        xor     ecx, ecx
1:      mov     edx, ecx
        shl     edx, 6
        cmp     qword ptr [r8 + rdx + 0xb8], 0
        je      2f
        inc     ecx
        cmp     ecx, 16
        jb      1b
        jmp     restore                                 # no free slot
2:      test    ecx, ecx
        jz      restore
        lea     edx, [rcx - 1]
        mov     eax, dword ptr [r8 + 4*rdx + 0x880]     # the last dependency's weight
        shl     edx, 6
        cmp     qword ptr [r8 + rdx + 0xb8], r9
        jne     3f
        .byte   0x48, 0x8d, 0x35                        # lea rsi, [rip + ALL_BONUS]: PROF_ALL_LEVELS
        .long   ALL_BONUS - BASE - (4f - start)
4:      call    append
3:      cmp     r13, 3
        ja      restore
        .byte   0x48, 0x8d, 0x35                        # lea rsi, [rip + ALL_BONUS]
        .long   ALL_BONUS - BASE - (5f - start)
5:      mov     eax, r13d
        shl     eax, 5
        add     rsi, rax
        mov     eax, 0x10000
        call    append
restore:
        pop     r9
        pop     r8
        pop     rdi
        pop     rsi
        pop     rdx
        pop     rcx
        pop     rax
check:
        cmp     byte ptr [rbp + 0x77d0], 0
        ret

# append: dependency ecx of func r8 becomes the 24-byte name and hash at rsi, with weight eax; ecx counts it.
append:
        cmp     ecx, 16
        jae     6f
        mov     dword ptr [r8 + 4*rcx + 0x880], eax
        mov     edx, ecx
        shl     edx, 6
        lea     rdi, [r8 + rdx + 0x80]
        mov     edx, ecx
        mov     ecx, 24
        rep movsb
        mov     rax, qword ptr [rsi]
        mov     qword ptr [rdi - 24 + 0x38], rax
        lea     ecx, [rdx + 1]
6:      ret
end:
