# Code cave for _test_equip_fail, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# equip_log_on: replaces `mov [rip+g_debuginator_gamestate_settings], rax` (7 bytes) at 0x1802aecb0 in
# gamestate::gamestate. rax points at the settings flags, one byte per log group.
equip_log_on:
        .byte   0x48, 0x89, 0x05                # mov [rip + SETTINGS_PTR], rax
        .long   SETTINGS_PTR - BASE - (1f - start)
1:
        mov     byte ptr [rax + 9], 1       # inventory moves and toolbelt
        mov     byte ptr [rax + 12], 1      # equip sensor
        .byte   0xe9
        .long   RESUME - BASE - (2f - start)
2:

# force_fail: replaces `mov esi, r9d; imul rdi, [rdx+0x18]` (8 bytes) at 0x1803b0dc0 in
# equip_action_end (rcx = the utility system, r9d = the end reason). While `left` is above 0, an
# automatic equip (action data +0x10 = 0) that ends with UT_SUCCEEDED (2) ends with UT_FAILED (1)
# instead, and `left` counts down. `failed` counts the forced ends.
force_fail:
        mov     esi, r9d
        imul    rdi, qword ptr [rdx + 0x18]
        cmp     esi, 2
        jne     back
        mov     rax, qword ptr [rcx + 0x68]
        add     rax, rdi
        cmp     word ptr [rax + 0x10], 0
        jne     back                            # an equip order
        .byte   0x48, 0x8d, 0x05                # lea rax, [rip + left]
        .long   left - 3f
3:
        cmp     dword ptr [rax], 0
        je      back
        dec     dword ptr [rax]
        inc     dword ptr [rax + 4]
        mov     esi, 1
        mov     r9d, 1
back:
        .byte   0xe9
        .long   FAIL_RESUME - BASE - (4f - start)
4:
        .p2align 3
left:   .long   FAILS
failed: .long   0
end:
