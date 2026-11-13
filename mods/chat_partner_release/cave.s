# Code cave for chat_partner_release, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# leave_fix: replaces `movzx ecx,word ptr [rdi+0x68]; test al,al; je KEEP; cmp [rbx+2],cx; je KEEP`
# (14 bytes) at 0x1801ae61d in talk_system_leave_conversation, right after the leaver was removed.
# There al = (participants left <= 1), rbx the conversation (0x1338 bytes: place +2, participants
# +4, 0x20 each, inline count u16 +0x104 or 0xffff = dynamic with pointer +4 and count +0xc, first
# bubble time +0x118, 0 until started; more than 8 participants move to a dynamic array, which this
# leaves alone) and rdi the talk data (components [+0] 0x50 each: entity +0,
# state +4 (3 seated), count +8; gamestate +0x60; the Hammerting's place +0x68, 0 when none).
#
# Vanilla removes a conversation with at most one participant left unless its place is the
# Hammerting's. With no Hammerting that place is 0, and so is the place of a chat between nearby
# dwarves, so such a chat is kept: a partner who was already seated waits for a start that never
# comes, frozen in ACTION_TALK. Here the place test only counts while a Hammerting is set. And a
# conversation that is kept but not started gets the check start_talking runs when someone sits
# down: if every participant left is seated, it starts.
leave_fix:
        movzx   ecx, word ptr [rdi + 0x68]
        test    al, al
        jz      recheck                         # two or more stay
        test    ecx, ecx
        jz      remove                          # no Hammerting: an ordinary chat
        cmp     word ptr [rbx + 2], cx
        je      recheck                         # the Hammerting stays
remove:
        .byte   0xe9
        .long   REMOVE - BASE - (6f - start)
6:
recheck:
        cmp     qword ptr [rbx + 0x118], 0
        jne     keep                            # already started
        movzx   ecx, word ptr [rbx + 0x104]
        lea     eax, [rcx - 1]
        cmp     eax, 7
        ja      keep                            # nobody left, or more than 8 (not checked)
        lea     r8, [rbx + 4]
        mov     r10, qword ptr [rdi]
        imul    r11d, dword ptr [rdi + 8], 0x50
        add     r11, r10                        # end of the talk components
2:      movzx   edx, word ptr [r8]
        mov     rax, r10
3:      cmp     rax, r11
        jae     keep
        cmp     word ptr [rax], dx
        je      4f
        add     rax, 0x50
        jmp     3b
4:      cmp     dword ptr [rax + 4], 3
        jne     keep                            # someone is still on the way
        add     r8, 0x20
        dec     ecx
        jnz     2b
        mov     rax, qword ptr [rdi + 0x60]
        mov     rax, qword ptr [rax + 0xd0]     # now (16.16)
        mov     qword ptr [rbx + 0x118], rax    # first bubble now, then every 1-3 s as usual
keep:
        .byte   0xe9
        .long   KEEP - BASE - (5f - start)
5:
end:
