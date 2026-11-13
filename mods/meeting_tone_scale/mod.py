"""Meeting Tone Scale: a Hammerting meeting changes each pair's relationship about as much as one ordinary chat.

Reported before 1.2.39 as "mass Nemesis relations after a meeting", and seen in the user's colony: one Hammerting
before savegame29 turned 35 of 72 relation sides Spiteful and 17 Cold, from none, and moved every relation value
(median -240 of 1000, 21 to 0). When a conversation ends, talk_system_resolve_conversation gives every pair of seated
participants a random relation change within 3 * (tone + 2 * relation), where the tone is the sum of every talk turn
in the conversation (up when the topic is liked, down otherwise). Nothing scales it by the number of participants, so
a meeting applies one large tone to every pair at once.

This divides the tone by (participants - 1) for that relation change, so chats between two dwarves are unchanged and
group chats and meetings affect each pair like one chat. The morale and energy change after a conversation is
unchanged. Set HMOD_TONE_DIAG=1 when installing to count scaled pairs in memory (`diag` label, 4 u32: pairs, last tone,
scaled tone, participants). See re/notes/hammerting_meeting.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'A Hammerting or group chat changes each pair of dwarves about as much as one chat (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x80
SITE = 0x1801b2d75                      # talk_system_resolve_conversation, per pair
SITE_OLD = bytes.fromhex('488b85b80300008b8810010000')   # mov rax, [rbp+0x3b8]; mov ecx, [rax+0x110]
RESUME = 0x1801b2d82


def apply(ctx):
    diag = int(os.environ.get('HMOD_TONE_DIAG', '0'))
    symbols = {'BASE': CAVE, 'RESUME': RESUME, 'DIAG': diag}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x80, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'meeting_tone_scale code cave')
    jmp = b'\xe9' + (CAVE + labels['tone_scale'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'talk_system_resolve_conversation -> tone_scale')
    if diag:
        print(f'  meeting_tone_scale: diag at .hmod {0x80 + labels["diag"]:#x}')
