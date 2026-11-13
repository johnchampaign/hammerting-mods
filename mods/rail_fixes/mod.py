"""Rail Fixes: two station_system cleanup bugs that can strand vehicles and riders.

rider_cleanup: station_system::destroy_entities removes stations and vehicles but never the queue
entries of destroyed riders. A dwarf who dies holding an entry stays first in the queue, so the
Handcar waits for him for good and everyone else waits for the Handcar, until a reload (queues
aren't saved). This dequeues every destroyed entity first; dequeue is a no-op for anything else.

teardown_riders: on_event_teardown's loop that puts a torn-down Handcar's riders back on the ground
never advances, so only the first rider is freed.

Both are read in the code and neither was reproduced in play. See re/notes/carts_elevators.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

DESCRIPTION = 'Dead riders leave vehicle queues, and tearing down a Handcar frees all riders (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x700
CLEANUP_SITE = 0x18035f060
CLEANUP_OLD = bytes.fromhex('488b4940e9b73c0000')   # mov rcx,[rcx+0x40]; jmp destroy_entities
TEARDOWN_SITE = 0x18035eb3a
TEARDOWN_OLD = bytes.fromhex('0fb79424e0000000663bfa74056685d27594')
SYMBOLS = {
    'BASE': CAVE,
    'DEQUEUE': 0x18035cd80,         # station_system_dequeue(ecs, entity)
    'DESTROY': 0x180362d20,         # station_system::destroy_entities(system, ids, count)
    'TEARDOWN_TOP': 0x18035eae0,    # detach the rider in dx
    'TEARDOWN_END': 0x18035eb4c,
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x80, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'rail_fixes code cave')
    jmp = b'\xe9' + (CAVE + labels['rider_cleanup'] - (CLEANUP_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(CLEANUP_SITE, CLEANUP_OLD, jmp + b'\xcc' * 4, 'station cleanup dequeues destroyed riders')
    jmp = b'\xe9' + (CAVE + labels['teardown_next'] - (TEARDOWN_SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(TEARDOWN_SITE, TEARDOWN_OLD, jmp + b'\x90' * 13, 'vehicle teardown frees every rider')
