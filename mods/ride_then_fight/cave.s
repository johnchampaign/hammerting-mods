# Code cave for ride_then_fight, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# seated: replaces `mov r11, rsp; mov [r11+0x20], r9` (7 bytes) at the top of
# combat_attack_melee_impact_consideration (0x1803aa540): rcx = the score out (u32 16.16), r8 = the
# action instance (entity at +0x20), r9 = the context ([r9]+0x28 = gamestate). A dwarf seated in a
# Handcar is a family child of it (everyone else has parent 0 here). Starting a swing there stops his
# ride, which dequeues him, so the Handcar drives off to a station with him on it and the swing lands
# tiles away from the enemy; then his job sends the Handcar back past it. Here a seated combateer
# scores 0 for melee, so he rides on, and the approach action takes him off at a station and walks
# him back to fight on foot.
seated:
        push    rcx
        push    rdx
        push    r8
        push    r9
        sub     rsp, 0x28
        mov     rax, qword ptr [r9]
        mov     rax, qword ptr [rax + 0x28]     # gamestate
        lea     rcx, [rax + 0xe18]              # family component system
        xor     edx, edx
        xor     r8d, r8d
        .byte   0x48, 0x8b, 0x05                # mov rax, [rip + FAMILY]: family records, 10 bytes per entity
        .long   FAMILY - BASE - (1f - start)
1:      call    rax
        mov     r8, qword ptr [rsp + 0x30]
        movzx   edx, word ptr [r8 + 0x20]
        lea     rdx, [rdx + 4*rdx]
        movzx   eax, word ptr [rax + 2*rdx]     # parent
        add     rsp, 0x28
        pop     r9
        pop     r8
        pop     rdx
        pop     rcx
        test    eax, eax
        jnz     2f
        mov     r11, rsp                        # as before
        mov     qword ptr [r11 + 0x20], r9
        .byte   0xe9
        .long   RESUME - BASE - (3f - start)
3:
2:      mov     dword ptr [rcx], 0
        mov     rax, rcx
        ret
end:
