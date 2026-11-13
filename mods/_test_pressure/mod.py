"""Test only, never for play: the 75% entity pressure band applies at any entity count.

Stored and loose items then rot at that band's rates in a normal colony, so keep_stored_items can be
measured without a 48K entity save. Items really are lost, so use it on save copies only.
"""

DESCRIPTION = 'TEST ONLY: entity pressure band always on, items rot fast (DLL patch)'

SITE = 0x180463fbe
SITE_OLD = bytes.fromhex('8d0c40')             # lea ecx, [rax + rax*2]: 3/4 of the limit
SITE_NEW = bytes.fromhex('31c990')             # xor ecx, ecx; nop


def apply(ctx):
    ctx.patch_dll(SITE, SITE_OLD, SITE_NEW, 'pressure band always on')
