# Code cave for whole_batch_inputs, placed in the .hmod section that tools/dllpatch.py appends.
# Assembled by mod.py through tools/cave.py; BASE and the absolute addresses come in as --defsym.
# Windows x64 calling convention: args rcx, rdx, r8, r9, then the stack above 32 bytes of
# home space; rbx, rsi, rdi, rbp, r12-r15 are callee-saved; rsp is 16-byte aligned at calls.

        .intel_syntax noprefix
        .text
start:

# batch_limit: replaces `mov r13, [rsi+0x538]; imul r13, rdx` in
# production_queue_entry_wants_entity, which then refuses the item for this input slot when
# r13 <= rax. Registers there: rsi queue entry, rdx this slot's count per craft, rax how many
# items the entry already holds for the slot. The caller still needs rax and rdx; every register
# but r13 is preserved.
#
# Originally r13 = queued amount * count: an entry reserves inputs for its whole queue and holds
# them while it waits for the rest, so entries with large amounts soak up all the supply. Here an
# entry with several inputs asks for one craft's worth, so once it has that, further items stay
# free for others. An entry with one input can't wait on another input, so it may hold SINGLE_CRAFTS
# crafts' worth. Deliver-only recipes (missions) keep the original rule; they gather their amount over time.
batch_limit:
        mov     r13, qword ptr [rsi + 0x538]    # queued amount
        test    r13, r13
        jz      done                            # nothing queued: want nothing (vanilla: 0 * count)
        mov     r13, qword ptr [rsi + 0x10]     # recipe
        cmp     byte ptr [r13 + 0xec0], 0       # deliver_only
        jne     whole_queue
        cmp     qword ptr [r13 + 0x188], 0      # input[1].count: used slots are contiguous
        je      one_input
        mov     r13, rdx                        # one craft's worth
done:
        ret
one_input:
        mov     r13, qword ptr [rsi + 0x538]    # queued amount
        cmp     r13, SINGLE_CRAFTS
        jbe     scale
        mov     r13d, SINGLE_CRAFTS
scale:
        imul    r13, rdx
        ret
whole_queue:
        mov     r13, qword ptr [rsi + 0x538]    # queued amount
        imul    r13, rdx
        ret
end:
