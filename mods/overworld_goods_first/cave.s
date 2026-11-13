# Code cave for overworld_goods_first, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# goods_first: replaces `mov r13, [rbp+0xa0]` at 0x1804f8b65 in bt_haul_update, right after
# station_system_are_positions_accessible has filled this container's cached distance at [r14+8]
# (16.16, negative when unreachable). The hauler then takes the item with the smallest distance.
# Items in a settlement get their distance scaled down, so they beat loose items and nearer towns
# still come first. Only the choice uses the value; the trip is routed separately.
# rbp is bt_haul_update's frame: [rbp-0x7c] the item, [rbp+0x11c88] the node state. Volatile
# registers are free here: the code after the call site reloads what it needs.
goods_first:
        mov     r13, qword ptr [rbp + 0xa0]
        cmp     qword ptr [r14 + 8], 0
        jl      done
        sub     rsp, 0x28
        movzx   ecx, word ptr [rbp - 0x7c]
        lea     rcx, [rcx + rcx*4]
        mov     rax, qword ptr [rbp + 0x11c88]
        mov     rdx, qword ptr [rax + 0xea8]            # family records, 10 bytes each
        movzx   r8d, word ptr [rdx + rcx*2]             # the item's parent
        mov     rax, qword ptr [rax]
        mov     rcx, qword ptr [rax + 0x28]
        add     rcx, 0x2498
        .byte   0x48, 0x8d, 0x15                        # lea rdx, [rip + "CURRENTLY_IN_OVERWORLD"]
        .long   IN_OVERWORLD - BASE - (after_lea - start)
after_lea:
        .byte   0xff, 0x15                              # call [rip + has tag], as add_haulable_items does
        .long   HAS_TAG_PTR - BASE - (after_call - start)
after_call:
        add     rsp, 0x28
        test    al, al
        jz      done
        sar     qword ptr [r14 + 8], 12
done:
        ret

end:
