# Test only: see mod.py. Assembled through tools/cave.py.

        .intel_syntax noprefix
        .text
start:

# test_wave: replaces `call update_spawners` in enemy_wave_system_update, reached only when the
# wave timer is due. rcx is the wave system. enemy_wave_system_launch_overworld_attack takes the
# system from +0x40 of its argument, so it gets a small stand-in. Calls it BURST times, then the
# original call.
test_wave:
        push    rcx
        push    rbx
        sub     rsp, 0x68
        mov     qword ptr [rsp + 0x60], rcx     # stand-in + 0x40
        mov     ebx, BURST
again:
        lea     rcx, [rsp + 0x20]
        .byte   0xe8                            # enemy_wave_system_launch_overworld_attack
        .long   LAUNCH - BASE - (1f - start)
1:      dec     ebx
        jnz     again
        add     rsp, 0x68
        pop     rbx
        pop     rcx
        .byte   0xe9                            # update_spawners
        .long   UPDATE_SPAWNERS - BASE - (2f - start)
2:
end:
