# Code cave for eat_reserved_food, placed in the unused tail of game.x86_64.dll's .text.
# Assembled by mod.py with llvm-mc; BASE and the absolute addresses are passed as --defsym.
# RIP-relative operands and calls are written as opcode bytes plus a computed rel32,
# because llvm-mc will not take label arithmetic inside a memory operand.
# Windows x64 calling convention: args rcx, rdx, r8, r9, then the stack above 32 bytes of
# home space; rbx, rsi, rdi, r12-r15 are callee-saved; rsp is 16-byte aligned at calls.

        .intel_syntax noprefix
        .text
start:

# filter: drop-in for claim_system_get_claim_type(claims, item, out_claimant, out_type)
# at refill process_fillers, which keeps a claimed item only if the claim type is
# CLAIM_REFILL_STATUSBAR. A CLAIM_PRODUCE claim (a production queue's reserved input) is
# reported as the CLAIM_REFILL_STATUSBAR tag, whose hash sits at the same +0x38.
filter:
        push    rbx
        sub     rsp, 0x20
        mov     rbx, r9
        .byte   0xe8
        .long   GET_CLAIM_TYPE - BASE - (1f - start)
1:      test    al, al
        jz      2f
        mov     rcx, qword ptr [rbx]
        .byte   0x48, 0x8b, 0x15                # mov rdx, [rip + PRODUCE_HASH]
        .long   PRODUCE_HASH - BASE - (3f - start)
3:      cmp     rdx, qword ptr [rcx + 0x38]
        jne     2f
        .byte   0x48, 0x8d, 0x0d                # lea rcx, [rip + REFILL_TAG]
        .long   REFILL_TAG - BASE - (4f - start)
4:      mov     qword ptr [rbx], rcx
2:      add     rsp, 0x20
        pop     rbx
        ret

        .p2align 4
# pick: drop-in for claim_system_is_claimed(claims, item) in calc_best_filler. Returns 0
# ("free") for an item whose only claim is a production queue's CLAIM_PRODUCE, unless the
# item already sits in that producer's inventory (it may be mid-craft).
pick:
        xor     r9d, r9d
        jmp     common

# take: the same check in refill_statusbar_job_begin, which claims the item right after.
# When it hands out a reserved item it first releases the production queue's claim, so
# the queue re-plans as if the item had been hauled away.
take:
        mov     r9d, 1

common:
        push    rbx
        push    rsi
        push    rdi
        push    r12
        sub     rsp, 0x58
        mov     rbx, rcx                        # claim system
        movzx   esi, dx                         # item
        mov     r12d, r9d                       # 1 = take
        .byte   0xe8
        .long   IS_CLAIMED - BASE - (5f - start)
5:      test    al, al
        jz      free
        mov     word ptr [rsp + 0x38], 0
        mov     rcx, rbx
        mov     edx, esi
        lea     r8, [rsp + 0x38]                # claimant
        lea     r9, [rsp + 0x30]                # claim type
        .byte   0xe8
        .long   GET_CLAIM_TYPE - BASE - (6f - start)
6:      test    al, al
        jz      claimed
        mov     rax, qword ptr [rsp + 0x30]
        mov     rax, qword ptr [rax + 0x38]
        .byte   0x48, 0x3b, 0x05                # cmp rax, [rip + PRODUCE_HASH]
        .long   PRODUCE_HASH - BASE - (7f - start)
7:      jne     claimed
        lea     rcx, [rbx + 0xf00]              # inventory system (mainstate +0x1430)
        mov     edx, esi
        mov     word ptr [rsp + 0x40], 0
        lea     r8, [rsp + 0x40]                # carrier
        lea     r9, [rsp + 0x44]                # inventory type
        lea     rax, [rsp + 0x48]               # index
        mov     qword ptr [rsp + 0x20], rax
        .byte   0xe8
        .long   GET_ITEM_DETAILS - BASE - (8f - start)
8:      movzx   eax, word ptr [rsp + 0x40]
        cmp     ax, word ptr [rsp + 0x38]
        je      claimed
        test    r12d, r12d
        jz      free
        mov     rcx, rbx
        movzx   edx, word ptr [rsp + 0x38]
        mov     r8d, esi
        .byte   0xe8
        .long   RELEASE_CLAIM - BASE - (9f - start)
9:
free:
        xor     eax, eax
        jmp     done
claimed:
        mov     eax, 1
done:
        add     rsp, 0x58
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbx
        ret
end:
