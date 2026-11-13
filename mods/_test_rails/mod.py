"""Test only, never for play: every rail, elevator, cart and chest recipe is unlocked and free.

The colony copies used for tests have no Machinery research or rail stock. This clears the
recipes' dependencies and input counts, so pieces can be placed and built at once. BUGS A13,
A14, B7. Tests about materials need the real recipes: set HMOD_RAILS_PAID=1 when installing to
keep the pieces' costs and instead make the foundry's Rail Track recipe unlocked and free of
ingots and slabs (fuel still applies), so a colony can build up rail stock quickly. Free tracks
carry no metal; HMOD_RAILS_PAID=real unlocks the recipe with its real inputs instead.
"""
import os
import re
import struct

DESCRIPTION = 'TEST ONLY: rail, elevator, cart and chest recipes unlocked and free'
RECORDS = 'database/recipe/recipe_rooms_cdb.bin'
DEPENDENCIES = 2440
FIRST_SLOT_COUNT = 0x80
SLOT_SIZE = 0x108
SMELTER = 'database/recipe/recipe_smelter_cdb.bin'


def apply(ctx):
    paid = os.environ.get('HMOD_RAILS_PAID') in ('1', 'real')
    real = os.environ.get('HMOD_RAILS_PAID') == 'real'
    free = not paid
    d = bytearray(ctx.read(RECORDS))
    count, total = struct.unpack_from('<QQ', d, 0)
    size = total // count
    done = []
    for i in range(count):
        r = 16 + size * i
        name = d[r:r + 56].split(b'\0')[0].decode()
        if not re.search('RAILWAY|ELEVATOR|CART|CHEST', name) or not name.startswith('MECH_'):
            continue
        for k in range(4):
            struct.pack_into('<Q', d, r + DEPENDENCIES + 8 * k, 0)
            if free:
                struct.pack_into('<q', d, r + FIRST_SLOT_COUNT + SLOT_SIZE * k, 0)
        done.append(name)
    assert len(done) >= 11, done
    ctx.write(RECORDS, bytes(d))
    if paid:
        d = bytearray(ctx.read(SMELTER))
        count, total = struct.unpack_from('<QQ', d, 0)
        size = total // count
        for i in range(count):
            r = 16 + size * i
            if d[r:r + 56].split(b'\0')[0] != b'CLS_RAIL_TRACK':
                continue
            for k in range(4):
                struct.pack_into('<Q', d, r + DEPENDENCIES + 8 * k, 0)
                if not real:
                    struct.pack_into('<q', d, r + FIRST_SLOT_COUNT + SLOT_SIZE * k, 0)
            break
        else:
            raise AssertionError('no CLS_RAIL_TRACK smelter recipe')
        ctx.write(SMELTER, bytes(d))
