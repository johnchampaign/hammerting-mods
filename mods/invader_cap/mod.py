"""Invader Cap: no new overworld attack or generic wave while CAP invaders are alive.

enemy_wave_system spawns invaders without ever reading its count of living wave members
(+0x278), and only lair waves clean up after themselves. Invaders who stop moving where no dwarf
reaches them therefore pile up without limit, towards the 64K entity limit that breaks saves (BUGS
A8, A1). This bounds that count. It does not cure the freeze, whose cause is unknown: if CAP stuck
invaders exist, overworld attacks and generic waves stay off until they die. Lair waves continue.
The check runs before each wave, so the last wave can take the count past CAP.
See re/notes/overworld_invaders.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

CAP = 24
DESCRIPTION = f'No new overworld attack or generic wave while {CAP} invaders are alive (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x540
ATTACK_SITE = 0x180452002
ATTACK_OLD = bytes.fromhex('488383a002000003')  # add qword ptr [rbx+0x2a0], 3
ATTACK_RESUME = 0x18045200a
WAVE_SITE = 0x180459e4b
SPAWN_WAVE = 0x180454e50                        # spawn_wave_from_record


def apply(ctx):
    symbols = {'BASE': CAVE, 'CAP': CAP, 'ATTACK_RESUME': ATTACK_RESUME, 'SPAWN_WAVE': SPAWN_WAVE}
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), symbols)
    assert len(code) <= 0x40
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'invader_cap code caves')
    jmp = b'\xe9' + (CAVE + labels['attack_gate'] - (ATTACK_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(ATTACK_SITE, ATTACK_OLD, jmp + b'\x90' * 3, 'overworld attack -> cap')
    old = b'\xe8' + (SPAWN_WAVE - (WAVE_SITE + 5)).to_bytes(4, 'little', signed=True)
    new = b'\xe8' + (CAVE + labels['wave_gate'] - (WAVE_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(WAVE_SITE, old, new, 'generic wave -> cap')
