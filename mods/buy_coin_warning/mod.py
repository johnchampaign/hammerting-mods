"""Buy Coin Warning: the Buy tooltips say when the vault can't pay.

buy_items_is_valid refuses a purchase when one item costs more than the vault holds, and the click
then does nothing at all: no message, and the button looks the same. With enough for some but not
all, the game buys what the coin covers. The Buy and Buy All tooltips now add a red line in those
two cases. The button itself is unchanged. See re/notes/market_buying.md.
"""
from evalchain import compile_chain

DESCRIPTION = "Buy tooltips warn in red when the vault can't pay"

NONE = '\nNot enough coins: this click will do nothing.'
SOME = '\nNot enough coins for all of these: only some will be bought.'


def warning(total):
    return compile_chain(
        f"IFTHENELSE(VAULT_COIN_CURRENT.LESS(GAME_CTX.PRICE),'{NONE}',"
        f"IFTHENELSE(VAULT_COIN_CURRENT.LESS({total}),'{SOME}',''))")


def apply(ctx):
    table = ctx.loc('overworld')
    for key, total in (('UI_MARKET_BUY_X_DESC', "PARENT.KEY_VALUE('TOTAL_SALE_VALUE').INT"),
                       ('UI_MARKET_BUY_ALL_DESC',
                        "GAME_CTX.ENTRY.CLAIMED_COUNT(GAME_CTX('2')).MUL(GAME_CTX.PRICE)")):
        entry = table.key(key)
        assert entry.text == 'Total bought will cost |GOLD|%Oproperty_comp|!|.', entry.text
        entry.text += '|TOMATO*|%Oproperty_comp|!|'
        entry.blobs.append(warning(total))
