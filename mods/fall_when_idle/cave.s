# Code cave for fall_when_idle, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# stand_gate: replaces `xorps xmm0,xmm0; lea rcx,[rip+"MOVEMENT_STATE"]` at 0x1803f4ef1 in
# fall_sensor_update. The original goes on to read the dwarf's MOVEMENT_STATE key and checks
# the tile below for support only if the key is missing or STAND. Walking never writes the
# key, so a dwarf keeps a stale JUMP or CLIMB after a jump and never falls when the ground
# under him is dug away. Here a dwarf with no movement behaviour running goes straight to the
# support check; a moving dwarf takes the original path.
# Registers: rbp frame, [rbp+0x488] the sensor context (4th argument), di the entity. Every
# volatile register is dead here; the support check at SUPPORT reads only r15 and the stack.
stand_gate:
        mov     rax, qword ptr [rbp + 0x488]
        mov     rax, qword ptr [rax]
        mov     rcx, qword ptr [rax + 0x28]     # mainstate
        add     rcx, 0x17f0                     # movement ecs
        movzx   edx, di
        .byte   0xe8                            # movement_system_is_active (leaf)
        .long   IS_ACTIVE - BASE - (1f - start)
1:      test    al, al
        .byte   0x0f, 0x84                      # jz SUPPORT: idle, check support
        .long   SUPPORT - BASE - (2f - start)
2:      xorps   xmm0, xmm0
        .byte   0x48, 0x8d, 0x0d                # lea rcx, [rip + "MOVEMENT_STATE"]
        .long   STATE_KEY - BASE - (3f - start)
3:      .byte   0xe9                            # back to the original path
        .long   RESUME - BASE - (4f - start)
4:
end:
