"""Plant Timer Fix: a growth stage whose timer is overdue still finishes.

plant_system_update (0x1801ebfa0) advances a timed growth stage only when the plant's
next_time equals the current game second exactly (`cmp ecx,esi; jne` at 0x1801ec8de). A timer
that is ever in the past (a skipped second, a clock that jumped) never matches again, and the
plant sits at that stage for good (one candidate for BUGS B9, "plants stop growing"). This
makes the test `ja`: skip only while the timer is still in the future. Plants with no timer
(0xffffffff: tender and harvest stages) are unaffected; an overdue plant advances on the next
tick. See re/notes/plant_growth.md.
"""
DESCRIPTION = 'Growing plants with an overdue stage timer advance instead of stalling (DLL patch)'


def apply(ctx):
    ctx.patch_dll(0x1801ec8e0, bytes.fromhex('7513'), bytes.fromhex('7713'),
                  'plant timer: advance when due or overdue (jne -> ja)')
