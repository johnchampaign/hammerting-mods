"""Ground Pickup: new storages take loose items from the ground by default.

haul_system_create_components gives every GENERAL_STORAGE destination the haul source
mask 0x04 (take from overworld only), so no storage ever collects what mining, harvests,
fishing piers or full buildings drop on the floor until the player finds the per-storage
"take from ground" toggle. Loose items rot in about 2.8 game hours, so the colony loses
them, and food that never reaches a storage is easy to starve next to. This makes the
default 0x05 (ground and overworld). The toggle still works; storage filters still apply.

Existing storages keep their saved setting: switch it on in each storage's settings, or
copy a save with `tools/save.py ground <save> <new-name>`.
"""

DESCRIPTION = "New storages take loose items from the ground by default (DLL patch)"

# mov byte [rax+0x58], 4  ->  mov byte [rax+0x58], 5
SITE = 0x1801dfc86


def apply(ctx):
    ctx.patch_dll(SITE, bytes.fromhex('c6405804'), bytes.fromhex('c6405805'),
                  'GENERAL_STORAGE default haul sources: ground + overworld')
