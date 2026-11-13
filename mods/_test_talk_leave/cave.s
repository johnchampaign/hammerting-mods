# Code cave for _test_talk_leave (test only), in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# sit_or_leave: replaces `mov rax,[r15]; movzx edx,word ptr [rbp+0x378]` (10 bytes) at 0x1804d1e9b in
# bt_talk_update, where a walking dwarf has reached his seat and is about to call
# talk_system_start_talking. [rbp+0x378] is the dwarf's entity. A dwarf with an odd entity id fails
# BT_TALK here instead (return 2, like the no-seat failure at 0x1804d1df4), so his talk action ends
# and he leaves the conversation the way a move order makes him leave. rsi was saved at
# [rsp+0x460] on this path and must be restored, as the other exits of this branch do.
sit_or_leave:
        test    byte ptr [rbp + 0x378], 1
        jnz     1f
        mov     rax, qword ptr [r15]
        movzx   edx, word ptr [rbp + 0x378]
        .byte   0xe9
        .long   RESUME - BASE - (2f - start)
2:
1:      mov     rsi, qword ptr [rsp + 0x460]
        .byte   0xe9
        .long   FAIL - BASE - (3f - start)
3:
end:
