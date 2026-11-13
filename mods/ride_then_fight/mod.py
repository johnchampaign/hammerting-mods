"""Ride Then Fight: dwarves in a Handcar don't swing at monsters from the seat; they get off and fight.

Reported as "Handcar attacking bug" (S1/3193621324037871655, Mar 2022): with rail through monster dens,
riders "bounce back and forth", hit by monsters but never killing them. Starting a melee attack stops
the dwarf's movement, which ends his wait in the Handcar and takes him out of its queue, while he stays
seated. The Handcar then drives off to a station with him on it, so the swing lands tiles away from
the enemy, and when it ends his job queues the Handcar back past the enemy, and so on. Tested on copies
of KrazJomsglind savegame32 with a Killer Plant moved beside a rail 24 tiles from both stations:
without this, riders swung 44 and 104 times from the seat while the Handcar shuttled past it, and it
lived 162 and 231 game seconds, until a dwarf walked up and killed it in 3 swings.

This scores melee 0 for a combateer that has a family parent (a seated rider; dwarves on foot have
none), so a rider rides on, and the approach action takes him off at a station and walks him back.
With it the plant died 2.8 game seconds after its first attack, to a rider who got off and walked
back, and rides went on as before (1 run).
DLL patch, code in .hmod+0x2400. See docs/BUGS.md B14 and re/notes/carts_elevators.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dwarves riding a Handcar get off to fight monsters instead of swinging from the seat (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x2400
SITE = 0x1803aa540                      # combat_attack_melee_impact_consideration
SITE_OLD = bytes.fromhex('4c8bdc' '4d894b20')   # mov r11, rsp; mov [r11+0x20], r9
SYMBOLS = {
    'BASE': CAVE,
    'RESUME': 0x1803aa547,
    'FAMILY': 0x180599070,              # import: family component records (u16 parent first)
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, len(code)
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'ride_then_fight code cave')
    jmp = b'\xe9' + (CAVE + labels['seated'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * 2, 'melee consideration: 0 while seated in a vehicle')
