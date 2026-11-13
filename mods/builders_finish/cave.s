# Code cave for builders_finish, in the .hmod section (see tools/cave.py).

        .intel_syntax noprefix
        .text
start:

# builder_bonus: replaces `mov qword ptr [rbp+0x7c], 0` (8 bytes) at 0x1803c39ee in sensor_craft_init, which
# zeroes the job type's current-job bonuses before JOB_CRAFT_<profession> is registered: flat +0x10c and
# multiplier +0x110 of the job type (16.16), at rbp+0x7c and rbp+0x80 here. rbx is the profession record (tag
# at +0, its hash at +0x38). rax is live, so only rcx and rdx are used; rdx is loaded again right after.
#
# job_broker_system::calc_assignments scores a worker's current job with M = 5 + mult - 4t and
# F = 1500 + flat - 1500t, t = min(time on the job / 300 s, 1), so after five minutes a craft job keeps no
# bonus. A build is about five times a normal craft's work, and walking to the site counts too, so a builder
# could be pulled off near the end. JOB_HAUL has flat 10000 for the same reason; builders get FLAT here.
builder_bonus:
        xor     edx, edx
        movabs  rcx, H_BUILDER
        cmp     qword ptr [rbx + 0x38], rcx
        jne     1f
        mov     edx, FLAT
1:      mov     dword ptr [rbp + 0x7c], edx
        mov     dword ptr [rbp + 0x80], 0
        .byte   0xe9
        .long   RESUME - BASE - (2f - start)
2:
end:
