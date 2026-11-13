"""Fair Jobs: a job that has waited a long time eventually beats a dwarf's habit of going back.

Each job's score is about (age + 100) / (time to do it + 100), plus 500 if it is at the workplace
the dwarf last left, which also multiplies that fraction by up to 5. One 60-second trip earns all
of it, and that fraction is rarely more than single digits, so a dwarf keeps returning to any
workplace that still has work, and far jobs wait indefinitely: in the user's colony nothing reached
the foundry or 5 construction sites for 400 game seconds while haulers served a farm and an infirmary.

Two edits, no cave. The +500 goes; the x5 stays, so crafters still tend to stay at their bench.
A job's age now restarts when a dwarf leaves it, so it means "time since anyone worked on this",
and it no longer gains the "already worked on" bonus (worked time, up to x2; old values in a save
stay). See re/notes/job_broker.md.
"""

DESCRIPTION = "Jobs that have waited a long time beat a dwarf's habit of returning to the last workplace (DLL patch)"

# calc_assignments: imul rcx, rdx, 500 is the last-workplace bonus
BONUS_IMM = 0x1801377b5
# unassign_worker: add [rdi+0x98], rax (job.worked += elapsed) -> mov [rdi+0x90], rsi (job.age = 0)
# rsi is 0 since 0x18012a9ad
AGE_SITE = 0x18012a9cd


def apply(ctx):
    ctx.patch_dll(BONUS_IMM, bytes.fromhex('f4010000'), bytes.fromhex('00000000'),
                  'no flat bonus for returning to the last workplace')
    ctx.patch_dll(AGE_SITE, bytes.fromhex('48018798000000'), bytes.fromhex('4889b790000000'),
                  'job age restarts when a worker leaves the job')
