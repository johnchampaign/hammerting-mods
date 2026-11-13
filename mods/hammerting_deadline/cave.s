# Code cave for hammerting_deadline, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# deadline: replaces `lea rax,[2*rax+0xa]; mov [r14+0x128],rax; jmp RESUME` (17 bytes) at
# 0x1801ae396 in talk_system_start_or_join_conversation, run only when the conversation being
# created is the Hammerting (the global place). A conversation starts its first bubble when
# +0x118 (16.16 game time) is set and due; vanilla sets it only in talk_system_start_talking,
# when the last participant is seated, so one dwarf who never arrives holds every attendee
# forever (BUGS A11). Here the Hammerting also gets a deadline of now + TIMEOUT; start_talking
# still sets now + 1 s if everyone sits down sooner. In: rdi talk data, r14 the conversation.
deadline:
        lea     rax, [2*rax + 0xa]              # bubble count: 14..44, as vanilla
        mov     qword ptr [r14 + 0x128], rax
        mov     rax, qword ptr [rdi + 0x60]     # gamestate
        mov     rax, qword ptr [rax + 0xd0]     # now (16.16), as start_talking reads it
        add     rax, TIMEOUT
        mov     qword ptr [r14 + 0x118], rax
        .byte   0xe9
        .long   RESUME - BASE - (1f - start)
1:
end:
