# Second code cave for overworld_goods_first, at .hmod 0x2580 (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# no_steal: replaces `mov rcx, [rdi]; add rcx, 0xa0000` at 0x1804ee326 in should_haul_item, the test
# that lets a hauler take an item another hauler has claimed when it is 10 tiles nearer: rcx is
# compared with the claimant's distance in rax, and only rcx <= rax steals. [rdi] is this hauler's
# distance, which goods_first has scaled down for a settlement item, while the claimant's is computed
# fresh, so every hauler beat every claimant and they took the item from each other every tick
# without moving. A claim on a settlement item is now never taken. r13 is the node state,
# [rbp+0x60] the item. rax must survive.
no_steal:
        push    rax
        sub     rsp, 0x20
        movzx   ecx, word ptr [rbp + 0x60]
        lea     rcx, [rcx + rcx*4]
        mov     rdx, qword ptr [r13 + 0xea8]            # family records, 10 bytes each
        movzx   r8d, word ptr [rdx + rcx*2]             # the item's parent
        mov     rax, qword ptr [r13]
        mov     rcx, qword ptr [rax + 0x28]
        add     rcx, 0x2498
        .byte   0x48, 0x8d, 0x15                        # lea rdx, [rip + "CURRENTLY_IN_OVERWORLD"]
        .long   IN_OVERWORLD - BASE - (after_lea - start)
after_lea:
        .byte   0xff, 0x15                              # call [rip + has tag]
        .long   HAS_TAG_PTR - BASE - (after_call - start)
after_call:
        add     rsp, 0x20
        test    al, al
        pop     rax
        mov     rcx, qword ptr [rdi]
        jz      1f
        movabs  rcx, 0x7fffffffffffffff
        ret
1:      add     rcx, 0xa0000
        ret
end:
