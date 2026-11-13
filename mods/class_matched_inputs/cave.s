# Code caves for class_matched_inputs, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# relax_count: replaces `mov r8,[rdx+rcx+0x80]; cmp r8,1` (12 bytes) at 0x18014d3a2 in
# production_system_calc_input_slot_ready. The `ja` after it takes the "largest group of
# identical items" path for slots needing more than one item. That is right for crafts, whose
# output inherits the input's material, but buildings, upgrades and deliveries set
# use_classification_matching (recipe +0x971) and slots with remove_input_modifier
# (recipe +0xe68 + slot) don't pass their material on: for those every claimed item counts,
# as for one-item slots. In: rcx recipe, rdx slot * 0x108, rbx slot. Out: r8 = count and the
# flags for `ja` (above = identical items needed).
relax_count:
        mov     r8, qword ptr [rdx + rcx + 0x80]
        cmp     r8, 1
        jbe     1f
        cmp     byte ptr [rcx + 0x971], 0
        jne     2f
        cmp     byte ptr [rcx + rbx + 0xe68], 0
        jne     2f
        cmp     r8, 1                           # count > 1 and identical items needed
1:      ret
2:      cmp     r8, r8                          # ZF=1: `ja` not taken, every claimed item counts
        ret

# keep_template: replaces `mov [rcx+rax+0x18], r8` (5 bytes) at 0x18014ce6b in
# production_system_set_template_recipe, which resets the station's material choice, amount
# and repeat whenever a recipe is clicked. Clicking the recipe the station already has now
# keeps them. set_template_recipe pushes nothing, so dropping our return address and
# returning leaves it for its caller (it returns void).
keep_template:
        cmp     qword ptr [rcx + rax + 0x18], r8
        je      3f
        mov     qword ptr [rcx + rax + 0x18], r8
        ret
3:      add     rsp, 8
        ret
end:
