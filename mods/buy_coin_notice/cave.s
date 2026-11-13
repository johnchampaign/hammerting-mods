# Code cave for buy_coin_notice, in the .hmod section (see tools/cave.py for the conventions).

        .intel_syntax noprefix
        .text
start:

# check: replaces `cmp [rbx+8],rax; ja 0x1802eb877` at 0x1802eb833 in buy_items_is_valid, where rax is the
# vault's coin and [rbx+8] the price of one item. That check doesn't run against the simulation's gamestate
# (a log book entry posted from there never appeared, and an eval chain crashed), so it only counts the refusal.
check:
        cmp     qword ptr [rbx + 8], rax
        ja      1f
        .byte   0xe9                            # affordable: carry on
        .long   AFFORDABLE - BASE - (2f - start)
2:
1:      .byte   0xf0, 0xff, 0x05                # lock inc dword ptr [rip + refused]
        .long   refused - 3f
3:      .byte   0xe9                            # refuse, as before
        .long   REFUSE - BASE - (4f - start)
4:

# tick: replaces `lea r8,[rip + "[GAMESTATE] Frame %i  Speed %.1f"]` at 0x1802af40a in gamestate::update, reached
# on every frame (paused too) with r12 the gamestate. xmm0 is live; the other volatile registers are set after
# this. A new refusal sets the mountainhome's HMOD_BUY_REFUSED key value, which the alert shows, and SHOW_FRAMES
# frames later it is cleared.
tick:
        sub     rsp, 0x880
        movsd   qword ptr [rsp + 0x870], xmm0
        .byte   0x8b, 0x05                      # mov eax, dword ptr [rip + refused]
        .long   refused - 5f
5:      .byte   0x3b, 0x05                      # cmp eax, dword ptr [rip + posted]
        .long   posted - 6f
6:      je      7f
        .byte   0x89, 0x05                      # mov dword ptr [rip + posted], eax
        .long   posted - 8f
8:      .byte   0xc7, 0x05                      # mov dword ptr [rip + shown], SHOW_FRAMES
        .long   shown - 9f
        .long   SHOW_FRAMES
9:      .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + set_on]
        .long   set_on - 10f
10:     call    eval
        jmp     12f
7:      .byte   0x83, 0x3d                      # cmp dword ptr [rip + shown], 0
        .long   shown - 11f
        .byte   0
11:     je      12f
        .byte   0xff, 0x0d                      # dec dword ptr [rip + shown]
        .long   shown - 13f
13:     jnz     12f
        .byte   0x48, 0x8d, 0x15                # lea rdx, [rip + set_off]
        .long   set_off - 14f
14:     call    eval
12:     movsd   xmm0, qword ptr [rsp + 0x870]
        add     rsp, 0x880
        .byte   0x4c, 0x8d, 0x05                # lea r8, [rip + format string]: the replaced instruction
        .long   FORMAT - BASE - (15f - start)
15:     .byte   0xe9
        .long   RESUME - BASE - (16f - start)
16:

# eval(rdx chain): evaluates a chain on the gamestate in r12, with an entity as context and ARG('0'), as
# known_capital_missions does. Uses the caller's frame below its xmm0 save.
eval:
        mov     rcx, qword ptr [r12 + 0x28]
        add     rcx, 0x1e80                     # property ecs
        mov     dword ptr [rsp + 0x48], 0x00010002      # PCT_ENTITY, one
        mov     dword ptr [rsp + 0x4c], 0x1a486         # PC_ENTITY_TAG_GAME
        mov     qword ptr [rsp + 0x50], 1
        xor     eax, eax
        mov     qword ptr [rsp + 0x58], rax     # out
        mov     qword ptr [rsp + 0x60], rax
        lea     r8, [rsp + 0x48]
        lea     r9, [rsp + 0x58]
        mov     qword ptr [rsp + 0x28], r8      # args: the same entity
        mov     qword ptr [rsp + 0x30], 1
        lea     rax, [rsp + 0x70]
        mov     qword ptr [rsp + 0x38], rax
        mov     qword ptr [rsp + 0x40], 0x800
        sub     rsp, 8
        .byte   0xff, 0x15                      # call [rip + evaluate_chain_string_args]
        .long   EVAL_PTR - BASE - (17f - start)
17:     add     rsp, 8
        ret

set_on:  .asciz "MOUNTAINHOME.SET_KEY_VALUE('HMOD_BUY_REFUSED', TRUE)"
set_off: .asciz "MOUNTAINHOME.SET_KEY_VALUE('HMOD_BUY_REFUSED', FALSE)"
        .p2align 3
refused: .long  0                               # refused clicks, read from memory in tests
posted: .long   0
shown:  .long   0
end:
