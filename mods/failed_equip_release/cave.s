# Code cave for failed_equip_release, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# failed_release: replaces the target of `jne 0x1803ef366` (6 bytes) at 0x1803ee4a8 in
# sensor_equip_on_action_done, taken for every end reason but UT_SUCCEEDED (2) and UT_REMOVED (3).
# There eax = the reason, rdx = the action's data (+0x10 its equip order, 0 for an automatic
# upgrade), rsi = the equip sensor (+0x50 busy bytes, one per entity), rdi = the action instance
# (+0x20 the dwarf), r12 = the system context ([r12] +0x28 = mainstate, claim system at +0x530) and
# word [rsp+0x50] = the tool of the def that was just removed (0 when none matched).
#
# Vanilla only removes the action instance, so after UT_FAILED the dwarf keeps his busy byte (he is
# never offered another upgrade) and his auto-equip claim on the tool (nobody else can take it)
# until the game is reloaded. This clears both for automatic upgrades, then carries on as before.
failed_release:
        cmp     eax, 1                          # UT_FAILED
        jne     out
        cmp     word ptr [rdx + 0x10], 0
        jne     out                             # an equip order: unchanged
        movzx   r8d, word ptr [rsp + 0x50]      # the tool
        test    r8d, r8d
        jz      out
        movzx   edx, word ptr [rdi + 0x20]      # the dwarf
        mov     rax, qword ptr [rsi + 0x50]
        mov     byte ptr [rax + rdx], 0         # not busy any more
        mov     rcx, qword ptr [r12]
        mov     rcx, qword ptr [rcx + 0x28]
        add     rcx, 0x530                      # claim system
        .byte   0xe8                            # claim_system_release_claim_if_claimed(claims, dwarf, tool)
        .long   RELEASE - BASE - (1f - start)
1:
out:
        .byte   0xe9
        .long   DONE - BASE - (2f - start)
2:
end:
