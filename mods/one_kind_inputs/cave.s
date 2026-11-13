# Code caves for one_kind_inputs, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# lock: replaces `cmp rax, rdx; jb 0x180153159` (5 bytes) at 0x180153122 in
# production_queue_entry_wants_entity. rax = the slot's largest group of identical claimed items
# (calc_input_slot_ready, whose first entity is the caller's [rsp+0x70]), rdx = the slot's count
# per craft, rsi entry, rdi slot. The game compares the item with that group (MATCH_PATH:
# match_modifiers, skipped for building recipes) only once the group holds a craft's worth, and
# until then takes any item of the class, so a slot needing several identical items could hold one
# of each kind for good. Here a slot holding part of a craft takes only items like the group, unless
# the recipe drops the slot's material (remove_input_modifier), where any kinds combine. rcx is free
# on both paths.
lock:
        test    rax, rax
        jz      select
        cmp     rax, rdx
        jae     match                           # a full group: as before
        mov     rcx, qword ptr [rsi + 0x10]     # recipe
        cmp     byte ptr [rcx + rdi + 0xe68], 0 # remove_input_modifier[slot]
        jne     select
match:
        .byte   0xe9
        .long   MATCH_PATH - BASE - (1f - start)
1:
select:
        .byte   0xe9
        .long   SELECT_PATH - BASE - (2f - start)
2:

# release: replaces `mov rax, [rbx+8]; mov rbx, rax` (7 bytes) at 0x180152f84, where
# production_system_update's walk over a building's queue moves on to the next entry. rbx entry,
# rsi the production system (data at +0x40); the flags are set by the `test rax, rax` after it.
# If a slot needing several identical items holds more than one kind (claimed before this mod),
# check_correct_input releases the entry's claims and offers the building's items again, and lock
# lets the slot take back one kind. Identical means the same global_inventory_entry, the notion
# calc_input_slot_ready and match_modifiers use, so a released entry doesn't come back mixed.
release:
        push    rcx
        push    rdx
        push    r8
        push    r9
        push    r10
        push    r11
        push    rsi
        push    rdi
        push    r12
        sub     rsp, 0x230                      # 0x20 home, 0x20 5th arg, 0x30..0x230 claims
        mov     r12, qword ptr [rsi + 0x40]     # production data
        mov     rsi, qword ptr [rbx + 0x10]     # recipe
        test    rsi, rsi
        jz      done
        cmp     byte ptr [rsi + 0xec0], 0       # deliver-only
        jne     done
        cmp     byte ptr [rsi + 0x971], 0       # building recipes count any kind (class_matched_inputs)
        jne     done
        xor     edi, edi
slot:
        imul    rax, rdi, 0x108
        cmp     qword ptr [rsi + rax + 0x80], 1
        jbe     next
        cmp     byte ptr [rsi + rdi + 0xe68], 0
        jne     next
        lea     rcx, [r12 + 0xb8]               # claim system
        movzx   edx, word ptr [rbx + 2]         # producer
        mov     r8, rdx
        shl     r8, 16
        movzx   eax, word ptr [rbx]             # uid
        or      r8, rax
        shl     r8, 32
        or      r8, rdi                         # producer << 48 | uid << 32 | slot
        lea     r9, [rsp + 0x30]
        mov     dword ptr [rsp + 0x20], 0x100
        .byte   0xe8                            # claim_system_get_claimed_entities_with_ref
        .long   CLAIMED - BASE - (3f - start)
3:      mov     ecx, eax
        cmp     ecx, 0x100
        jbe     4f
        mov     ecx, 0x100
4:      cmp     ecx, 2
        jb      next
        mov     rax, qword ptr [r12 + 0xa8]
        mov     rax, qword ptr [rax + 0x28]     # gamestate
        mov     rax, qword ptr [rax + 0x11a0]   # global inventory system data
        mov     r8, qword ptr [rax + 0x70]      # entity -> global_inventory_entry*
        movzx   edx, word ptr [rsp + 0x30]
        mov     r9, qword ptr [r8 + 8*rdx]
        mov     r10d, 1
5:      movzx   edx, word ptr [rsp + 0x30 + 2*r10]
        cmp     qword ptr [r8 + 8*rdx], r9
        jne     mixed
        inc     r10d
        cmp     r10d, ecx
        jb      5b
next:
        inc     edi
        cmp     edi, 4
        jb      slot
        jmp     done
mixed:
.if TEST_DIAG
        .byte   0x48, 0xff, 0x05                # inc qword ptr [rip + diag]: releases so far
        .long   diag - 7f
7:
        movzx   eax, word ptr [rbx + 2]
        shl     eax, 16
        movzx   ecx, word ptr [rbx]
        or      eax, ecx
        .byte   0x89, 0x05                      # mov [rip + diag + 8], eax: last producer << 16 | uid
        .long   diag + 8 - 8f
8:
.endif
        mov     rcx, r12
        movzx   edx, word ptr [rbx + 2]
        mov     r8, rbx
        .byte   0xe8                            # check_correct_input(data, producer, entry)
        .long   CCI - BASE - (6f - start)
6:
done:
        add     rsp, 0x230
        pop     r12
        pop     rdi
        pop     rsi
        pop     r11
        pop     r10
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
        mov     rax, qword ptr [rbx + 8]
        mov     rbx, rax
        ret
.if TEST_DIAG
        .p2align 3
diag:
        .fill   16, 1, 0
.endif
end:
