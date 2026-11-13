# Draft code caves for a tool auto-upgrade mod (see re/notes/tool_upgrade.md, tools/cave.py for
# the conventions). Not installed by any mod. Symbols: BASE = 0x18060c580 (.hmod + 0x580),
# REMOVE_DONE = 0x1801d22d1 (toolbelt_system::remove_tool_from_component epilogue),
# FAIL_RESUME = 0x1803ef366 (sensor_equip_on_action_done: utility_system_remove_action_instance),
# RELEASE_IF = 0x1801d3240 claim_system_release_claim_if_claimed(ecs, claimer, item).

        .intel_syntax noprefix
        .text
start:

# clear_slot: replaces the 17 bytes at 0x1801d22c0 in remove_tool_from_component, which clear
# the slot's cache entry and tool entity when a tool leaves a dwarf (drop command, hauled or
# given away). The slot's auto-upgrade setting is left as it was, so in the default mode
# (upgrade to recommended) the empty slot keeps the professions of the tool that left, and
# sensor_equip_try_equip_upgrade refills it with the best unclaimed tool for them: the
# dropped tool itself (drop -> re-equip loop) or a second tool of a kind the belt already
# holds (duplicates). Here a slot in recommended mode also gets its allowed professions
# cleared, as for a fresh empty slot; custom-mode slots keep the player's choices.
# In: rbx = toolbelt component (0x410 B), rdi = slot, r15 = 0. xmm0 and rax are dead.
clear_slot:
        mov     rax, rdi
        add     rax, rax
        mov     dword ptr [rbx + 8*rax + 0x24], r15d    # original: cache entry
        mov     word ptr [rbx + 2*rdi + 0x10], r15w     # original: tool entity
        imul    rax, rdi, 0x43                          # setting stride
        cmp     byte ptr [rbx + rax + 0x7e], 0          # _upgrade_to_recommended
        je      1f
        xorps   xmm0, xmm0
        movups  xmmword ptr [rbx + rax + 0x7f], xmm0    # _allowed_professions[64]
        movups  xmmword ptr [rbx + rax + 0x8f], xmm0
        movups  xmmword ptr [rbx + rax + 0x9f], xmm0
        movups  xmmword ptr [rbx + rax + 0xaf], xmm0
1:      .byte   0xe9
        .long   REMOVE_DONE - BASE - (2f - start)
2:

# failed_equip: target of the `jne` at 0x1803ee4a8 in sensor_equip_on_action_done (taken for
# every end reason except SUCCEEDED and REMOVED). On UT_FAILED the original drops the equip
# definition but keeps the dwarf's busy flag (sensor + 0x50, a byte per entity; try_upgrade
# skips busy dwarves) and the item's auto-equip claim, so the dwarf never auto-upgrades again
# this session and the tool stays reserved until a reload (sensor_equip_load_post releases
# auto-equip claims on items the claimer does not hold). Here a failed automatic equip (no
# order entity) clears the flag and releases the claim.
# In: eax = end reason, rdi = action instance (+0x20 entity), rsi = sensor data,
# rdx = equip_action_data_t (+0 item, +0x10 order entity), r12 = utility context.
# FAIL_RESUME reloads every volatile register it uses.
failed_equip:
        cmp     eax, 1                                  # UT_FAILED
        jne     4f
        cmp     word ptr [rdx + 0x10], 0                # player equip order: leave it
        jne     4f
        movzx   ecx, word ptr [rdi + 0x20]              # dwarf
        mov     rax, qword ptr [rsi + 0x50]
        mov     byte ptr [rax + rcx], 0                 # busy flag
        movzx   r8d, word ptr [rdx]                     # item
        test    r8d, r8d
        je      4f
        mov     edx, ecx
        mov     rax, qword ptr [r12]
        mov     rcx, qword ptr [rax + 0x28]
        add     rcx, 0x530                              # claim system
        .byte   0xe8
        .long   RELEASE_IF - BASE - (3f - start)
3:
4:      .byte   0xe9
        .long   FAIL_RESUME - BASE - (5f - start)
5:
end:
