# Code cave for rail_queue_keep, in the .hmod section (see tools/cave.py for the convention).

        .intel_syntax noprefix
        .text
start:

# pick: replaces the vehicle comparison in station_system_enqueue at 0x18035c21e, run once per
# passenger vehicle that reaches the rider. r8 = dwarves ahead of him on this vehicle (his index
# if he is queued on it, else its queue length), r13 = the best count so far, rcx = this vehicle's
# cost, rbx = the best cost, r9b = he is queued on this vehicle, r15b = he is queued on the best.
# The game took any vehicle with a lower cost whenever its count was not smaller, so a waiting
# dwarf followed whichever Handcar was nearest, to the back of its queue each time. Now fewer
# dwarves ahead wins, a tie keeps the vehicle he is queued on, and only then the lower cost wins.
pick:
        cmp     r8, r13
        jb      choose
        ja      skip
        test    r9b, r9b
        jnz     choose
        test    r15b, r15b
        jnz     skip
        cmp     rcx, rbx
        jge     skip
choose:
        mov     r13, r8
        .byte   0xe9                            # take this vehicle (sets r15b from r9b)
        .long   CHOOSE - BASE - (1f - start)
1:
skip:
        .byte   0xe9                            # next vehicle
        .long   SKIP - BASE - (2f - start)
2:
end:
