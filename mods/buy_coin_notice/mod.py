"""Buy Coin Notice: a buy the vault can't pay for raises an alert.

buy_items_is_valid refuses a purchase when one item costs more than the vault holds, and the click then does
nothing at all, with nothing in the session log. Now each refusal raises a red "Not enough coin" alert in the
Alerts panel for about SHOW_SECONDS. Buy All that the vault covers only in part still buys what it can, with no
alert. The alert is the game's unused ALERT_NO_ENERGY_ITEM (its condition was FALSE). Adding a new log book entry
type crashed startup, and posting to the log book from the check didn't work. See re/notes/market_buying.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import cave  # noqa: E402
import dllpatch  # noqa: E402
from loc import Entry  # noqa: E402

DESCRIPTION = "A buy the vault can't pay for raises a 'Not enough coin' alert (DLL patch)"

SHOW_SECONDS = 15
FRAMES_PER_SECOND = 10          # gamestate updates, counted while paused
ALERTS = 'database/alert/alert.bin'
ALERT = 'ALERT_NO_ENERGY_ITEM'
TITLE = 'Not enough coin'
DESC = ("The vault couldn't pay for that purchase, so nothing was bought. Coin comes from selling goods, and "
        "dwarves keep drawing their wages from it.")

CAVE = dllpatch.CAVE_VA + 0x1c00
SITE = 0x1802eb833
SITE_OLD = bytes.fromhex('4839430877' '3e')    # cmp [rbx+8], rax; ja 0x1802eb877
TICK = 0x1802af40a
TICK_OLD = bytes.fromhex('4c8d0587eb2900')     # lea r8, [rip + format string]
SYMBOLS = {
    'BASE': CAVE,
    'AFFORDABLE': 0x1802eb839,
    'REFUSE': 0x1802eb877,
    'FORMAT': 0x18054df98,              # "[GAMESTATE] Frame %i  Speed %.1f"
    'RESUME': 0x1802af411,
    'EVAL_PTR': 0x180599268,            # property_component_system_evaluate_chain_string_args
    'SHOW_FRAMES': SHOW_SECONDS * FRAMES_PER_SECOND,
}


def apply(ctx):
    d = bytearray(ctx.read(ALERTS))
    rec = d.index(ALERT.encode() + b'\0')
    cond = rec + 0x80
    assert d[cond:cond + 6] == b'FALSE\0', d[cond:cond + 8]
    new = b"MOUNTAINHOME.KEY_VALUE_OR_DEFAULT('HMOD_BUY_REFUSED', FALSE)"
    end = cond + 6
    while d[end] == 0:
        end += 1
    assert len(new) < end - cond
    d[cond:cond + len(new)] = new
    ctx.write(ALERTS, bytes(d))
    table = ctx.loc('dubious_entries')
    table.set(ALERT, Entry(TITLE))
    table.set(ALERT + '_DESC', Entry(DESC))

    code, labels = cave.assemble(os.path.join(HERE, 'cave.s'), SYMBOLS)
    assert len(code) <= 0x200, 'cave outgrew its share of .hmod'
    ctx.patch_dll(CAVE, bytes(len(code)), code, 'buy_coin_notice code cave')
    jmp = b'\xe9' + (CAVE + labels['check'] - (SITE + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(SITE, SITE_OLD, jmp + b'\x90', 'buy_items_is_valid coin check -> count refusal')
    jmp = b'\xe9' + (CAVE + labels['tick'] - (TICK + 5)).to_bytes(4, 'little', signed=True)
    ctx.patch_dll(TICK, TICK_OLD, jmp + b'\x90\x90', 'gamestate update -> coin alert flag')
