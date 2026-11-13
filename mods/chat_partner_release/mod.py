"""Chat Partner Release: a dwarf whose chat partner leaves is no longer stuck waiting forever.

Reported in Mar 2022 (S1/4658416565929454438): "When 2 guys are talking to each other and I
accidentally told one guy to go do something", the other stands there forever with Conversation
as his task. A chat starts only when its last participant sits down and finds everyone seated.
When someone leaves, talk_system_leave_conversation removes a conversation with at most one
participant left, except the Hammerting's. It tells the Hammerting apart by its place, which is 0
when no Hammerting is set, and chats between nearby dwarves have place 0 too. So a partner who sat
down first keeps a chat that can never start, and ACTION_TALK (rank 5) outranks work, food and
sleep. Any end of the talk action does this, not only a move order: falls, fights, health desires.

This removes such a chat (the partner goes back to work at once), and a chat that keeps two or
more participants but hasn't started starts if everyone left is seated. The Hammerting is
untouched (hammerting_deadline covers it). See re/notes/hammerting_meeting.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'A dwarf is released when his chat partner leaves before the chat starts (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x580
SITE = 0x1801ae61d
SITE_OLD = bytes.fromhex('0fb74f6884c07414663' '94b02740e')
KEEP = 0x1801ae639
REMOVE = 0x1801ae62b


def apply(ctx):
    symbols = {'BASE': CAVE, 'KEEP': KEEP, 'REMOVE': REMOVE}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x80, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'chat_partner_release code cave')
    jmp = b'\xe9' + (CAVE + labels['leave_fix'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5),
                  'talk_system_leave_conversation -> leave_fix')
