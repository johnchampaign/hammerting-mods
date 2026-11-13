"""Hammerting Deadline: a Hammerting starts within two minutes even if a dwarf never arrives.

A Hammerting is the talk system's global conversation at the Great Hall. Every free dwarf who
can reach the hall is summoned, attendees can't work (their work score is 0) and ACTION_TALK
outranks work, eating and sleep. The session begins only when every participant is seated, and
nothing times out a dwarf who can't get to his seat, so one stuck dwarf freezes the colony
with nobody free to rescue him (BUGS A11). This gives the Hammerting a deadline: TIMEOUT_SECONDS
after it is called, the session starts with whoever is seated, runs its 30-90 s and ends as
usual (law applied, cooldown, everyone released). See re/notes/hammerting_meeting.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

TIMEOUT_SECONDS = 120
DESCRIPTION = f'A Hammerting starts within {TIMEOUT_SECONDS} s even if a dwarf is stuck (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x500
SITE = 0x1801ae396
SITE_OLD = bytes.fromhex('488d04450a00000049898628010000eb0e')
RESUME = 0x1801ae3b5


def apply(ctx):
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'TIMEOUT': TIMEOUT_SECONDS << 16}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x40
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'hammerting_deadline code cave')
    jmp = b'\xe9' + (CAVE + labels['deadline'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5),
                  'Hammerting conversation creation -> deadline cave')
