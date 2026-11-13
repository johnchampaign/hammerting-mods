# Code caves for invader_cap, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# attack_gate: replaces `add qword ptr [rbx+0x2a0], 3` at 0x180452002 in
# enemy_wave_system_launch_overworld_attack, after the army has arrived. rbx is the wave system,
# +0x278 its u32 count of living wave members (+0x27c is the capacity, so compare 32 bits), and
# +0x2a0 the difficulty counter. At the cap there is no wave and no difficulty rise. The caller
# destroys the army either way.
attack_gate:
        cmp     dword ptr [rbx + 0x278], CAP
        jae     attack_skip
        add     qword ptr [rbx + 0x2a0], 3
        .byte   0xe9
        .long   ATTACK_RESUME - BASE - (1f - start)
1:
attack_skip:
        add     rsp, 0x20                       # the function's own epilogue
        pop     rbx
        ret

# wave_gate: replaces `call spawn_wave_from_record` at 0x180459e4b in enemy_wave_system_update, for
# generic waves only. rcx is the wave system. At the cap it returns 0, which the caller takes as a
# failed spawn; lair waves are not affected, because they clear their own previous members.
wave_gate:
        cmp     dword ptr [rcx + 0x278], CAP
        jae     wave_fail
        .byte   0xe9
        .long   SPAWN_WAVE - BASE - (2f - start)
2:
wave_fail:
        xor     eax, eax
        ret
end:
