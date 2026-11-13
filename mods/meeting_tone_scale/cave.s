# Code cave for meeting_tone_scale, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# tone_scale: replaces `mov rax, [rbp+0x3b8]; mov ecx, [rax+0x110]` (13 bytes) at 0x1801b2d75 in
# talk_system_resolve_conversation, inside the loop over pairs of seated participants. rax = the conversation
# (participants inline count u16 +0x104, or 0xffff with the dynamic count at +0xc), ecx = its tone (+0x110),
# edx = the pair's relation value, which the next instruction needs. The relation change range is then
# 3 * (tone + 2 * rel). The tone builds up over every talk turn of the whole conversation, so in a meeting
# one large tone hits every pair. Here it is divided by (participants - 1); chats of two are unchanged.
tone_scale:
        mov     rax, qword ptr [rbp + 0x3b8]
        mov     ecx, dword ptr [rax + 0x110]
        movzx   r11d, word ptr [rax + 0x104]
        cmp     r11d, 0xffff
        jne     1f
        mov     r11d, dword ptr [rax + 0xc]
1:      cmp     r11d, 2
        jbe     back                            # two or fewer: as before
        dec     r11d
        mov     r9d, edx
        mov     eax, ecx
        cdq
        idiv    r11d
.if DIAG
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + diag]
        .long   diag - 3f
3:
        inc     dword ptr [rdx]                 # pairs scaled
        mov     dword ptr [rdx + 4], ecx        # last tone before
        mov     dword ptr [rdx + 8], eax        # and after
        inc     r11d
        mov     dword ptr [rdx + 12], r11d      # participants
.endif
        mov     ecx, eax
        mov     edx, r9d
        mov     rax, qword ptr [rbp + 0x3b8]
back:
        .byte   0xe9
        .long   RESUME - BASE - (2f - start)
2:
.if DIAG
        .p2align 2
diag:   .long   0, 0, 0, 0
.endif
end:
