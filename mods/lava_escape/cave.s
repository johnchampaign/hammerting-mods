# Code cave for lava_escape, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# lava_only: replaces `movzx edx, byte ptr [rax + 4*rcx + 3]` at 0x1803a70a4 in the fluid amount
# consideration of ACTION_AVOID_FLUID. rax is map data, rcx the tile index, r10 the out value. Map
# byte +3 holds the amount in bits 0-2 and the fluid type in bits 3-6 (2 = lava). Only lava deep
# enough to burn (amount 2 or more, as in fluid_effect::update) scores, so the raised rank does not pull
# workers out of water, or out of a lava film that lava_no_walk lets them enter.
lava_only:
        movzx   edx, byte ptr [rax + 4*rcx + 3]
        mov     eax, edx
        and     eax, 0x78
        cmp     eax, 0x10
        jne     zero
        and     edx, 7
        cmp     edx, 1                          # lava's effect threshold: shallower lava does no harm
        jbe     zero
        shl     edx, 16
        mov     dword ptr [r10], edx
        mov     rax, r10
        ret
zero:
        mov     dword ptr [r10], 0
        mov     rax, r10
        ret
end:
