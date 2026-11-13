# Second cave for discovery_counts_found_rooms, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# drain: replaces `mov [rsp+8], rbx` at the entry of on_event_callback (rcx = system, rdx, r8, r9 = event).
# The generator can run during a load, where a finished mission is paid but never removed, because removal
# follows the destruction of its entity. So parts it met wait in LIST, and finish here, where missions
# normally finish. A part is checked against the current instance list first: LIST can outlive a load.
# attempt_finish raises an event, so this can nest; the _completed test stops a part finishing twice.
drain:
        mov     qword ptr [rsp + 0x10], rbx
        .byte   0x83, 0x3d                      # cmp dword ptr [rip + COUNT], 0
        .long   COUNT - BASE - (1f - start)
        .byte   0
1:      jne     work
        ret
work:
        push    rcx
        push    rdx
        push    r8
        push    r9
        push    rbx
        push    rsi
        sub     rsp, 0x20
        mov     rsi, rcx
        xor     ebx, ebx
next:
        .byte   0x3b, 0x1d                      # cmp ebx, [rip + COUNT]
        .long   COUNT - BASE - (2f - start)
2:      jae     done
        .byte   0x48, 0x8d, 0x05                # lea rax, [rip + LIST]
        .long   LIST - BASE - (3f - start)
3:      mov     rdx, qword ptr [rax + rbx*8]
        inc     ebx
        mov     rcx, qword ptr [rsi + 0x11]     # instance pointers
        mov     eax, dword ptr [rsi + 0x19]
scan:
        test    eax, eax
        jz      next
        dec     eax
        mov     r8, qword ptr [rcx + rax*8]
        lea     r9, [r8 + 0x520]                # parts: 16 of 0x5e0 bytes
        cmp     rdx, r9
        jb      scan
        add     r9, 0x5e00
        cmp     rdx, r9
        jae     scan
        cmp     byte ptr [rdx + 0x550], 0
        jne     next
        mov     byte ptr [rdx + 0x550], 1       # part->_completed
        mov     rcx, rsi
        mov     rdx, r8
        xor     r8d, r8d
        xor     r9d, r9d
        .byte   0xe8                            # attempt_advancement(system, instance, 0, 0)
        .long   ADVANCE - BASE - (4f - start)
4:      jmp     next
done:
        xor     eax, eax
        .byte   0x89, 0x05                      # mov [rip + COUNT], eax
        .long   COUNT - BASE - (5f - start)
5:      add     rsp, 0x20
        pop     rsi
        pop     rbx
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
        ret
end:
