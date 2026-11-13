"""Keep Stored Items: stored items keep their normal slow rot until 90% of the entity limit.

decay_system_update (0x180463f30) speeds up rot as the 64K entity limit nears. Past 75% stored items
rot 500 times faster, about 5.6 game hours, so a big colony loses gems and hoards without any message
(BUGS A1). Loose items rot in about 17 minutes in that band, and they are the clutter that fills
the limit, so this leaves them alone. Past 90% everything is as before: that is the game's last
defence against going over the limit, which has broken saves.
"""

DESCRIPTION = "Stored items don't rot faster until 90% of the entity limit (DLL patch)"

SITE = 0x180463fa6
SITE_OLD = bytes.fromhex('41b90000f401')       # mov r9d, 500 << 16
SITE_NEW = bytes.fromhex('41b900000100')       # mov r9d, 1 << 16


def apply(ctx):
    ctx.patch_dll(SITE, SITE_OLD, SITE_NEW, 'stored rot past 75% of the entity limit')
