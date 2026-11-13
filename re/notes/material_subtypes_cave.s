# Draft code caves for B3/B4 (material subtypes), see re/notes/material_subtypes.md and
# tools/cave.py for the conventions. Not installed by any mod. Meant to replace the
# whole_batch_inputs cave (its call site at 0x180153102 is retargeted to batch_limit2).
# Placed at .hmod + 0x600 (0x18060c600): 0x000-0x400 are taken, and the unbuilt drafts in
# discovery_quests_cave.s / plant_growth_cave.s already claim 0x400.
# Symbols: BASE = 0x18060c600,
#   CLAIMED = 0x1801d4890 claim_system_get_claimed_entities_with_ref(ecs, claimer, ref, out, max)
#   ALTS    = 0x1801ff7c0 global_inventory_system_get_input_slot_alternatives(ecs, recipe hash,
#             slot, &list)
#   CCI     = 0x1801536f0 check_correct_input(production data, producer, entry)
# Windows x64 calling convention; rbx, rsi, rdi, rbp, r12-r15 are callee-saved.
#
# Layouts used: production data (ecs->_data) +0xb8 claim ecs, +0x478 global inventory ecs
# (its _data at +0x4b8; data+0x70 = global_inventory_entry* per entity). Queue entry: uid u16
# @0, producer u16 @2, recipe* @0x10, input_status[s] @0x18 + 0x148*s (selected total-modifier
# hashes u64[8] @+0x108, i.e. entry + 0x120 + 0x148*s), queued u64 @0x538. Recipe: hash @0x38,
# input[s] @0x80 + 0x108*s (u64 count first), use_classification_matching @0x971,
# remove_input_modifier[s] @0xe68 + s, deliver_only @0xec0. global_inventory_entry: hash @0,
# _claimed_count[GITC_UNCLAIMED] @8, [GITC_HAUL] @0x18.

        .intel_syntax noprefix
        .text
start:

# ---------------------------------------------------------------------------------------
# batch_limit2: replaces `mov r13, [rsi+0x538]; imul r13, rdx` (0x180153102, 11 bytes:
# call + 6-byte nop) in production_queue_entry_wants_entity. The caller then refuses the item
# for this slot when r13 <= rax, and otherwise stores rax as the slot's "already delivered".
# In: rbp production data, rsi entry, rdx count of this slot, rax what calc_input_slot_ready
# returned, rdi slot index; the item entity is the caller's [rsp+0x2d0] (u16).
# Out: r13 = limit, rax = items held of the type this slot is collecting (strict slots) or
# the original value (relaxed slots, refusals). Every other register is preserved.
# Rules: deliver-only recipes keep the original limit; an entry with queued amount 0 wants
# nothing; otherwise the entry asks for one craft, only while every slot can be completed
# (slot_plan), and a strict slot takes only items of its target type.
batch_limit2:
        mov     r13, qword ptr [rsi + 0x10]     # recipe
        cmp     byte ptr [r13 + 0xec0], 0       # deliver_only
        mov     r13, qword ptr [rsi + 0x538]    # queued amount
        jne     whole_queue
        test    r13, r13
        jz      done_a                          # amount 0: want nothing (r13 = 0)
        mov     r13, rdx                        # one craft's worth
        cmp     rax, rdx
        jae     done_a                          # slot full; the caller skips it
        push    rcx
        push    rdx
        push    r8
        push    r9
        push    r10
        push    r11
        push    rbx
        push    r12
        push    r14
        push    r15
        sub     rsp, 0x258                      # 0x40 orig rax, 0x48 target, 0x50 held,
        mov     qword ptr [rsp + 0x40], rax     # 0x58..0x258 claim buffer
        mov     qword ptr [rsp + 0x48], 0
        mov     qword ptr [rsp + 0x50], rax
        mov     r12, qword ptr [rsi + 0x10]
        lea     r15, [rsp + 0x58]
        xor     ebx, ebx
slot_a:
        imul    rax, rbx, 0x108
        cmp     qword ptr [r12 + rax + 0x80], 0
        je      next_a
        call    slot_plan
        test    ecx, ecx
        jz      infeasible_a
        cmp     rbx, rdi
        jne     next_a
        mov     qword ptr [rsp + 0x48], r14     # target type of the slot being asked about
        mov     qword ptr [rsp + 0x50], rax     # held of that type
next_a:
        inc     rbx
        cmp     rbx, 4
        jb      slot_a
        mov     rax, qword ptr [rsp + 0x50]
        mov     rcx, qword ptr [rsp + 0x48]
        test    rcx, rcx
        jz      restore_a                       # relaxed slot: any matching item
        movzx   edx, word ptr [rsp + 0x580]     # item (caller rsp+0x2d0)
        mov     r8, qword ptr [rbp + 0x4b8]
        mov     r8, qword ptr [r8 + 0x70]
        cmp     qword ptr [r8 + 8*rdx], rcx
        je      restore_a
        xor     r13d, r13d                      # another type: refuse it for this slot
        jmp     restore_a
infeasible_a:
        xor     r13d, r13d                      # this craft cannot be completed now
        mov     rax, qword ptr [rsp + 0x40]
restore_a:
        add     rsp, 0x258
        pop     r15
        pop     r14
        pop     r12
        pop     rbx
        pop     r11
        pop     r10
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
done_a:
        ret
whole_queue:
        imul    r13, rdx
        ret

# ---------------------------------------------------------------------------------------
# slot_plan: can slot rbx of entry rsi be completed, and with which item type?
# In: rbp production data, rsi entry, rbx slot (count > 0), r12 recipe, r15 0x200-byte buffer.
# Out: ecx = 1 feasible / 0 not; r14 = target global_inventory_entry* (0 = any type: relaxed
# slot); rax = items held of the target type (relaxed: all held); r11 = all items held.
# Relaxed slot (count <= 1, use_classification_matching, or remove_input_modifier[slot]):
#   held + SUM over alternatives (unclaimed + hauled) >= count.
# Strict slot: some alternative T has held_T + unclaimed_T + hauled_T >= count; the target is
#   the feasible T with the most held, then the most in total.
# Alternatives are limited to the entry's selected total-modifier hashes when it has any.
# Clobbers rax, rcx, rdx, r8-r11, r14.
slot_plan:
        sub     rsp, 0x38                       # home, 5th arg, 0x28 list, 0x30 k
        lea     rcx, [rbp + 0xb8]               # claim system
        movzx   edx, word ptr [rsi + 2]         # producer (claimant)
        movzx   r8d, word ptr [rsi + 2]
        shl     r8, 16
        movzx   eax, word ptr [rsi]             # uid
        or      r8, rax
        shl     r8, 32
        or      r8, rbx                         # producer_claim_ref
        mov     r9, r15
        mov     qword ptr [rsp + 0x20], 0x100
        .byte   0xe8
        .long   CLAIMED - BASE - (1f - start)
1:      mov     eax, eax
        cmp     rax, 0x100
        jbe     2f
        mov     eax, 0x100
2:      mov     qword ptr [rsp + 0x30], rax     # k
        lea     rcx, [rbp + 0x478]
        mov     rdx, qword ptr [r12 + 0x38]     # recipe hash
        mov     r8, rbx
        lea     r9, [rsp + 0x28]
        .byte   0xe8
        .long   ALTS - BASE - (3f - start)
3:      mov     r8, rax                         # alternative count
        mov     r10, qword ptr [rsp + 0x28]     # alternatives
        imul    rcx, rbx, 0x108
        mov     r9, qword ptr [r12 + rcx + 0x80]        # count per craft
        cmp     r9, 1
        jbe     relaxed
        cmp     byte ptr [r12 + 0x971], 0
        jne     relaxed
        cmp     byte ptr [r12 + rbx + 0xe68], 0
        jne     relaxed
        mov     r11, qword ptr [rbp + 0x4b8]
        mov     r11, qword ptr [r11 + 0x70]     # entity -> global_inventory_entry*
        mov     qword ptr [rsp], 0              # best type   (home space is free now)
        mov     qword ptr [rsp + 8], -1         # best held
        mov     qword ptr [rsp + 0x10], 0       # best total
alt_s:
        test    r8, r8
        jz      done_s
        dec     r8
        mov     rdx, qword ptr [r10 + 8*r8]
        call    is_selected
        test    eax, eax
        jz      alt_s
        xor     eax, eax                        # held of this type
        mov     rcx, qword ptr [rsp + 0x30]
held_s:
        test    rcx, rcx
        jz      total_s
        dec     rcx
        movzx   r14d, word ptr [r15 + 2*rcx]
        cmp     qword ptr [r11 + 8*r14], rdx
        jne     held_s
        inc     rax
        jmp     held_s
total_s:
        mov     rcx, qword ptr [rdx + 8]        # unclaimed
        add     rcx, qword ptr [rdx + 0x18]     # being hauled
        add     rcx, rax
        cmp     rcx, r9
        jb      alt_s                           # this type cannot fill the slot
        cmp     rax, qword ptr [rsp + 8]
        jl      alt_s
        jg      take_s
        cmp     rcx, qword ptr [rsp + 0x10]
        jbe     alt_s
take_s:
        mov     qword ptr [rsp], rdx
        mov     qword ptr [rsp + 8], rax
        mov     qword ptr [rsp + 0x10], rcx
        jmp     alt_s
done_s:
        mov     r14, qword ptr [rsp]
        mov     rax, qword ptr [rsp + 8]
        mov     r11, qword ptr [rsp + 0x30]
        xor     ecx, ecx
        test    r14, r14
        jz      no_s
        inc     ecx
        jmp     out_p
no_s:
        xor     eax, eax
        jmp     out_p
relaxed:
        mov     r11, qword ptr [rsp + 0x30]
        xor     r14d, r14d
        mov     rax, r11
        cmp     rax, r9
        jae     yes_r
        mov     qword ptr [rsp], rax            # running total, starts at held
sum_r:
        test    r8, r8
        jz      cmp_r
        dec     r8
        mov     rdx, qword ptr [r10 + 8*r8]
        call    is_selected
        test    eax, eax
        jz      sum_r
        mov     rcx, qword ptr [rdx + 8]
        add     rcx, qword ptr [rdx + 0x18]
        add     qword ptr [rsp], rcx
        jmp     sum_r
cmp_r:
        mov     rax, r11
        cmp     qword ptr [rsp], r9
        jb      no_r
yes_r:
        mov     ecx, 1
        jmp     out_p
no_r:
        xor     ecx, ecx
out_p:
        add     rsp, 0x38
        ret

# is_selected: eax = 1 if alternative rdx may be used for slot rbx of entry rsi (no selection,
# or its hash is among the selected total-modifier hashes). Clobbers rax only.
is_selected:
        push    rcx
        imul    rcx, rbx, 0x148
        lea     rcx, [rsi + rcx + 0x120]
        mov     eax, 1
        cmp     qword ptr [rcx], 0
        je      9f
        mov     rax, qword ptr [rdx]
        cmp     qword ptr [rcx], rax
        je      8f
        cmp     qword ptr [rcx + 8], rax
        je      8f
        cmp     qword ptr [rcx + 0x10], rax
        je      8f
        cmp     qword ptr [rcx + 0x18], rax
        je      8f
        cmp     qword ptr [rcx + 0x20], rax
        je      8f
        cmp     qword ptr [rcx + 0x28], rax
        je      8f
        cmp     qword ptr [rcx + 0x30], rax
        je      8f
        cmp     qword ptr [rcx + 0x38], rax
        je      8f
        xor     eax, eax
        jmp     9f
8:      mov     eax, 1
9:      pop     rcx
        ret

# ---------------------------------------------------------------------------------------
# release_mixed: replaces `cmp dword ptr [rbx+0x548], 4` (0x180152ed0, 7 bytes: call + 2-byte
# nop) in production_system_update's walk over every queue entry; the `jne` that follows
# uses the flags this cave leaves. Live there: r14 production data, rbx entry; everything is
# preserved.
# If a slot holds items it cannot use (another type than its target, or the entry cannot be
# completed at all), check_correct_input releases the entry's claims and offers the
# building's items again, entry first; batch_limit2 then lets it take back only the target
# type, and other entries or haulers get the rest.
release_mixed:
        push    rax
        push    rcx
        push    rdx
        push    r8
        push    r9
        push    r10
        push    r11
        push    rbx
        push    rbp
        push    rsi
        push    rdi
        push    r12
        push    r14
        push    r15
        sub     rsp, 0x228                      # home, 0x28..0x228 claim buffer
        mov     rbp, r14                        # production data
        mov     rsi, rbx                        # entry
        mov     r12, qword ptr [rsi + 0x10]
        test    r12, r12
        jz      done_b
        cmp     byte ptr [r12 + 0xec0], 0       # deliver-only entries gather over time
        jne     done_b
        movzx   eax, word ptr [rsi]             # uid
        imul    rax, rax, 0x68
        add     rax, qword ptr [rbp + 0x90]     # production_queue_entry_extra
        cmp     byte ptr [rax + 0xc], 0         # paused: leave its claims alone
        jne     done_b
        lea     r15, [rsp + 0x28]
        xor     ebx, ebx
slot_b:
        imul    rax, rbx, 0x108
        cmp     qword ptr [r12 + rax + 0x80], 0
        je      next_b
        call    slot_plan
        test    r11, r11
        jz      next_b                          # holds nothing here
        cmp     qword ptr [rsi + 0x538], 0
        je      release_b                       # amount 0, yet holds items
        test    ecx, ecx
        jz      release_b                       # cannot complete, yet holds items
        cmp     r11, rax
        ja      release_b                       # holds items of another type
next_b:
        inc     rbx
        cmp     rbx, 4
        jb      slot_b
        jmp     done_b
release_b:
        mov     rcx, rbp
        movzx   edx, word ptr [rsi + 2]
        mov     r8, rsi
        .byte   0xe8
        .long   CCI - BASE - (4f - start)
4:
done_b:
        add     rsp, 0x228
        pop     r15
        pop     r14
        pop     r12
        pop     rdi
        pop     rsi
        pop     rbp
        pop     rbx
        pop     r11
        pop     r10
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
        pop     rax
        cmp     dword ptr [rbx + 0x548], 4
        ret

# ---------------------------------------------------------------------------------------
# relax_count: replaces `mov r8, [rdx+rcx+0x80]; cmp r8, 1` (0x18014d3a2, 12 bytes: call +
# 7-byte nop) in production_system_calc_input_slot_ready; the `ja 0x18014d3e1` after it
# takes the "largest group of identical items" path. Here that path is skipped (the slot
# counts every claimed item, as for count <= 1) when the recipe sets
# use_classification_matching (all building, upgrade and overworld-delivery recipes) or
# remove_input_modifier for the slot (the output does not inherit the slot's material).
# In: rcx recipe, rdx slot*0x108, rbx slot. Out: r8 = count, flags for `ja`.
relax_count:
        mov     r8, qword ptr [rdx + rcx + 0x80]
        cmp     r8, 1
        jbe     7f
        cmp     byte ptr [rcx + 0x971], 0
        jne     6f
        cmp     byte ptr [rcx + rbx + 0xe68], 0
        jne     6f
        cmp     r8, 1                           # count > 1: identical items needed
        ret
6:      cmp     r8, r8                          # ZF=1, CF=0: `ja` not taken; r8 stays > 0
7:      ret

# ---------------------------------------------------------------------------------------
# keep_template: replaces `mov [rcx+rax+0x18], r8` (0x18014ce6b, 5 bytes) in
# production_system_set_template_recipe, which wipes the template's material choices
# (total-modifier hashes), amount and repeat whenever a recipe is clicked. Clicking the
# recipe the template already has now keeps them. set_template_recipe has no frame, so the
# early exit returns straight to its caller.
keep_template:
        cmp     qword ptr [rcx + rax + 0x18], r8
        je      5f
        mov     qword ptr [rcx + rax + 0x18], r8
        ret
5:      add     rsp, 8
        ret
end:
