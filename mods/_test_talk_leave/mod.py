"""_test_talk_leave (TEST ONLY): dwarves with odd entity ids walk off when they reach their chat seat.

Reproduces the "conversation partner freezes" report without catching a dwarf by hand in the
second before a chat starts: the odd dwarf's talk action fails as he would sit down, so he leaves
the conversation the way a move order makes him leave. In vanilla his partner, if already seated,
then waits forever (see chat_partner_release). Uses .hmod 0x1e00, like _test_pier_diag: don't
install both.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'TEST ONLY: odd-id dwarves leave chats as they reach their seat (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x1e00
SITE = 0x1804d1e9b
SITE_OLD = bytes.fromhex('498b070fb79578030000')
RESUME = 0x1804d1ea5
FAIL = 0x1804d1df4


def apply(ctx):
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'FAIL': FAIL}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x100
    ctx.patch_dll(CAVE, bytes(len(code)), code, '_test_talk_leave code cave')
    jmp = b'\xe9' + (CAVE + labels['sit_or_leave'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'bt_talk_update sit -> sit_or_leave')
