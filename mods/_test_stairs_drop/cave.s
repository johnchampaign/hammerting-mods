# Code cave for _test_stairs_drop (test only), in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# drop_end: replaces `mov byte ptr [r15],1; jmp 0x1804dd106` at 0x1804dd036 in event_callback_stairs_anim_done,
# where a walk_stairs walk ends: the dwarf has just been put on the end tile and taken off animation driving,
# and the byte tells bt_walk_stairs_update to finish. The first time this happens to TARGET the byte is not set.
drop_end:
        cmp     word ptr [rbp + 0x1270], TARGET
        jne     keep_end
        .byte   0x80, 0x3d                      # cmp byte ptr [rip + FLAG], 0
        .long   FLAG - BASE - (1f - start)
        .byte   0
1:      jne     keep_end
        .byte   0xc6, 0x05                      # mov byte ptr [rip + FLAG], 1
        .long   FLAG - BASE - (2f - start)
        .byte   1
2:      jmp     out_end
keep_end:
        mov     byte ptr [r15], 1
out_end:
        .byte   0xe9                            # the callback's return
        .long   END_RETURN - BASE - (3f - start)
3:

# drop_event: replaces `mov r14,[r14]; lea rcx,[rbp+0x90]` at 0x1804dc9de, right after the callback matched the
# event to the stepping dwarf (cx = entity). The first such event for TARGET takes the callback's early return, as
# if the step animation's done event never came.
drop_event:
        cmp     cx, TARGET
        jne     keep_event
        .byte   0x80, 0x3d                      # cmp byte ptr [rip + FLAG], 0
        .long   FLAG - BASE - (4f - start)
        .byte   0
4:      jne     keep_event
        .byte   0xc6, 0x05                      # mov byte ptr [rip + FLAG], 1
        .long   FLAG - BASE - (5f - start)
        .byte   1
5:      .byte   0xe9                            # the callback's early return
        .long   EVENT_RETURN - BASE - (6f - start)
6:
keep_event:
        mov     r14, qword ptr [r14]
        lea     rcx, [rbp + 0x90]
        .byte   0xe9
        .long   EVENT_RESUME - BASE - (7f - start)
7:
end:
