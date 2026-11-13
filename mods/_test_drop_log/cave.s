# Code cave for _test_drop_log, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# haul_log_on: replaces `mov [rip+g_debuginator_gamestate_settings], rax` (7 bytes) at 0x1802aecb0 in
# gamestate::gamestate. rax points at the settings flags, one byte per log group; +8 is GAMESTATE-HAUL.
haul_log_on:
        .byte   0x48, 0x89, 0x05                # mov [rip + SETTINGS_PTR], rax
        .long   SETTINGS_PTR - BASE - (1f - start)
1:
        mov     byte ptr [rax + 8], 1       # haul, pick up, claims for hauls
        mov     byte ptr [rax + 10], 1      # movement, idle, stations
        mov     byte ptr [rax + 12], 1      # equip sensor
        mov     byte ptr [rax + 14], 1      # talk
        .byte   0xe9
        .long   RESUME - BASE - (2f - start)
2:

# drop_stack: replaces `mov word ptr [rsp+8], cx` (5 bytes) at the entry of try_drop_item_on_ground
# (cx = item, rdx = haul context). Copies the item id, rsp and 126 qwords of stack into a ring of 32
# 0x400-byte entries at DATA+0x100, counting drops in the u64 at DATA, so the callers can be read from
# memory. Flags are dead at a function entry.
drop_stack:
        push    rax
        push    rcx
        push    rsi
        push    rdi
        .byte   0x48, 0x8d, 0x05                # lea rax, [rip + DATA]
        .long   DATA - BASE - (3f - start)
3:
        mov     rdi, qword ptr [rax]
        inc     qword ptr [rax]
        and     edi, 31
        shl     edi, 10
        lea     rdi, [rax + rdi + 0x100]
        mov     word ptr [rdi], cx
        lea     rsi, [rsp + 0x20]
        mov     qword ptr [rdi + 8], rsi
        add     rdi, 16
        mov     ecx, 126
        cld
        rep movsq
        pop     rdi
        pop     rsi
        pop     rcx
        pop     rax
        mov     word ptr [rsp + 8], cx
        .byte   0xe9
        .long   DROP_RESUME - BASE - (4f - start)
4:
end:
