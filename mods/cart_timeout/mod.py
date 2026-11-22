"""Cart Timeout: a Cart that stops partway through a delivery gives it up, so the job is offered again.

Reported on Steam (2026-11-20, a colony with about 20 Handcars, 5-10 Carts and 6 ore grinders): now and then a Cart
picks up ore for a smelter and never arrives, and the smelter waits for good. Pausing and unpausing the smelter's
production starts the delivery again. BUGS A13 has older reports of loaded Carts stopping at a station or beside their
target without unloading.

A Cart (mech/cart_hauling) has no behaviour of its own (BT_CART is an empty node); the job broker gives it haul jobs,
and it runs the same bt_haul behaviour as a dwarf. Its movement is its own queue entry in station_system
(station_system_enqueue_vehicle), and the station update drives it to the first entry with a reachable node. With no
reachable entry a Cart simply stops, and bt_haul_update keeps returning BT_RUNNING with no timeout
(re/notes/carts_elevators.md, "Cart's own move"). Why a trip stops was not found, and the stall was not reproduced.

This watches each vehicle's position while bt_haul_update runs. When it has not changed for LIMIT_SECONDS game seconds
(default 30, `HMOD_CART_TIMEOUT`), the Cart's own route entry is dropped (station_system_dequeue) and the update
returns BT_FAILURE. bt_haul_exit then releases the trip's claims, the same path that pausing the building takes, and
the job is offered again. What the Cart carries stays in it (with haulers_keep_load) or is dropped where it stands.
Dwarves are not affected: the check runs only for entities that station_system lists as vehicles. Positions live in
a 16-slot table by entity id in the .hmod section (not saved).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402

LIMIT_SECONDS = float(os.environ.get('HMOD_CART_TIMEOUT', '30'))

DESCRIPTION = 'A Cart stopped for 30 game seconds during a delivery gives it up, so the job is offered again (DLL patch)'

CAVE = dllpatch.CAVE_VA + 0x3000
TABLE = dllpatch.CAVE_VA + 0x3100       # SLOTS * 16 bytes, to 0x3200
SLOTS = 16
COUNT = TABLE + SLOTS * 16              # u32 timeouts, u32 last Cart, i32 x, y (read from memory in tests)
SITE = 0x1804ef230                      # bt_haul_update
SITE_OLD = bytes.fromhex('48895c2418' '4889542410')  # mov [rsp+0x18],rbx; mov [rsp+0x10],rdx
SYMBOLS = {
    'BASE': CAVE,
    'TABLE': TABLE,
    'SLOTS': SLOTS,
    'COUNT': COUNT,
    'LIMIT': round(LIMIT_SECONDS * 0x10000),
    'RESUME': 0x1804ef23a,
    'IS_VEHICLE': 0x18035d4c0,          # station_system_is_vehicle(station system, entity)
    'DEQUEUE': 0x18035cd80,             # station_system_dequeue(station system, rider)
    'WORLD_POSITIONS': 0x1800e9720,     # fixed_transform_system_get_world_positions(ecs)
}


def apply(ctx):
    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= TABLE - CAVE, f'cave outgrew its share of .hmod: {len(code)}'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'cart_timeout code cave')
    jmp = b'\xe9' + (CAVE + labels['watch'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90' * (len(SITE_OLD) - 5), 'haul update -> Cart stall timeout')
