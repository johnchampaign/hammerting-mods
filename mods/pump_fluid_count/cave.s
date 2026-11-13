# Code cave for pump_fluid_count, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:
# Replaces `call 0x18020ab00` at 0x180200460 in global_inventory_system_get_matching_inventory.
# In: rcx class map, rdx &hash, rdi queue entry, rbx gis data, r11 recipe (caller reads it after
# the call; the real lookup does not touch r11). Stack on entry: return address.
fluid_lookup:
        .byte   0x48, 0x8b, 0x05                # mov rax, [rip + CLS_FLUID_CRAFT hash slot]
        .long   CRAFT_SLOT - BASE - (1f - start)
1:
        cmp     qword ptr [rdx], rax
        je      pump
        .byte   0xe9                            # not a pump: vanilla lookup
        .long   LOOKUP - BASE - (2f - start)
2:
pump:
        push    rcx                             # map
        sub     rsp, 0x40                       # shadow, out comp at +0x20, saved r11 at +0x30
        mov     qword ptr [rsp + 0x30], r11
        xorps   xmm0, xmm0
        movups  xmmword ptr [rsp + 0x20], xmm0
        mov     rcx, qword ptr [rbx]            # gamestate
        mov     rcx, qword ptr [rcx + 0x28]     # mainstate
        add     rcx, 0x1520                     # key_value ecs
        movzx   edx, word ptr [rdi + 2]         # producer
        movabs  r8, 0xc0c3affce0cc531c
        lea     r9, [rsp + 0x20]
        .byte   0xff, 0x15                      # call [key_value_component_system_get_value]
        .long   KV_GET - BASE - (3f - start)
3:
        mov     r11, qword ptr [rsp + 0x30]
        mov     rax, qword ptr [rsp + 0x28]     # fluid record tag hash
        cmp     dword ptr [rsp + 0x20], 0x10003 # type 3, count 1, as the pump writes it
        mov     rcx, qword ptr [rsp + 0x40]
        lea     rsp, [rsp + 0x48]               # stack back to the return address
        jne     unknown
        movabs  rdx, 0x06e6d8d33729c486
        cmp     rax, rdx
        lea     rdx, [rip + cls_lava]
        je      known
        movabs  rdx, 0xae40785ecb6d7f8e
        cmp     rax, rdx
        lea     rdx, [rip + cls_water]
        je      known
unknown:
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + CLS_FLUID_CRAFT hash slot]
        .long   CRAFT_SLOT - BASE - (4f - start)
4:
        .byte   0xe9                            # vanilla: lookup misses, sums all fluids
        .long   LOOKUP - BASE - (5f - start)
5:
known:
        .byte   0xe8
        .long   LOOKUP - BASE - (6f - start)
6:
        test    rax, rax
        jne     done
        add     rsp, 8                          # this fluid never existed: count is 0
        .byte   0xe9
        .long   RET_ZERO - BASE - (7f - start)
7:
done:
        ret
        .p2align 3
cls_lava:
        .quad   0x858a26a36c16c5af
cls_water:
        .quad   0xa76eb257674850db
end:
