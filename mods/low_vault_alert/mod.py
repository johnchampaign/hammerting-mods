"""Low Vault Alert: a red alert while the vault holds too little coin to buy with.

A buy the vault can't pay for does nothing at all: no message, nothing logged (buy_items_is_valid needs the price
of one item <= vault coin). This shows a "Vault nearly empty" alert, with the current coin, whenever the vault holds
less than THRESHOLD, so you can tell before clicking. It reuses the game's unused ALERT_NO_ENERGY_ITEM, whose
condition was FALSE. Data only.

A per-click notice was tried in mods/buy_coin_notice and dropped: a new log book entry type crashed startup, and
setting state from a code hook froze the game. See re/notes/market_buying.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
from evalchain import compile_chain  # noqa: E402
from loc import Entry  # noqa: E402

DESCRIPTION = 'Red alert while the vault holds under 100 coin, since buys then fail silently'

THRESHOLD = 100
ALERTS = 'database/alert/alert.bin'
ALERT = 'ALERT_NO_ENERGY_ITEM'
TITLE = 'Vault nearly empty'
DESC = ('The vault holds %Oproperty_comp. Buying from a settlement does nothing when an item costs more than '
        'the vault holds. Sell goods to refill it; dwarves keep drawing their wages from it.')


def apply(ctx):
    d = bytearray(ctx.read(ALERTS))
    rec = d.index(ALERT.encode() + b'\0')
    cond = rec + 0x80                   # the alert's condition chain
    assert d[cond:cond + 6] == b'FALSE\0', d[cond:cond + 8]
    new = f"VAULT_COIN_CURRENT.LESS('{THRESHOLD}')".encode()
    d[cond:cond + len(new)] = new
    ctx.write(ALERTS, bytes(d))
    table = ctx.loc('dubious_entries')
    table.set(ALERT, Entry(TITLE))
    table.set(ALERT + '_DESC', Entry(DESC, [compile_chain('VAULT_COIN_CURRENT.TO_CURRENCY')]))
