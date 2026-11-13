"""Autosave Interval: autosave every INTERVAL_MINUTES of game time instead of every 5.

The gamestate update (around 0x1802af1d3) autosaves when the debug flag at 0x1805917ed is set
(on by default) and a countdown in seconds of unpaused game time runs out; after each autosave
it is reset to 300.0 (`movabs rax, 0x4072c00000000000` at 0x1802af377), then replaced by the
debug-menu value "Game/Gamestate/Autosave interval" (gamemedia.x86_64.dll; settings object
0x1805a77e8 +0x28) whenever that object exists, which in the shipped game it always does. In a
big colony each autosave can stall the game for up to a minute (BUGS A18). This changes the
reset value and skips the debug-menu override.

Autosaves can also be switched off without a mod: add `--gamestate-autosave false` to the
Steam launch options (see mods/README.md). Manual saves keep working either way.
"""
import struct

INTERVAL_MINUTES = 15
DESCRIPTION = f'Autosave every {INTERVAL_MINUTES} game minutes instead of 5 (DLL patch)'

SITE = 0x1802af379                      # imm64 of `movabs rax, 300.0` at 0x1802af377
OVERRIDE = 0x1802af393                  # je: skip the debug-menu interval only if it's absent


def apply(ctx):
    assert INTERVAL_MINUTES > 0
    ctx.patch_dll(SITE, struct.pack('<d', 300.0), struct.pack('<d', INTERVAL_MINUTES * 60.0),
                  f'autosave interval 300 s -> {INTERVAL_MINUTES * 60} s')
    ctx.patch_dll(OVERRIDE, bytes.fromhex('7430'), bytes.fromhex('eb30'),
                  'autosave interval: ignore the debug-menu value')
