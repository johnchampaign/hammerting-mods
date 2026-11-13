"""Victory Tracker: make the Affluence victory's progress readable.

The Affluence objective reads "Fill vaults: X% / Y%" instead of "Fill vault: X %", and its
tooltip starts with "Hoard: current / max". World Conquest already shows "Control X / Y".

(The outliner panel flags are named *_MINIMIZED but default TRUE for panels that start
open, such as Cave Missions; the Victory Conditions panel already starts open.)
"""
from evalchain import retarget
from loc import Entry

DESCRIPTION = "Affluence objective shows fill % against its target; its tooltip shows the hoard"


def find_blob(table, source):
    for e in table.entries.values():
        for b in e.blobs:
            if source.encode() + b'\0' in b:
                return b
    raise KeyError(source)


def apply(ctx):
    cave, core = ctx.loc('cave'), ctx.loc('core')
    done = find_blob(cave, "STATE_GET( 'AMOUNT_DONE' )")
    wanted = find_blob(cave, "STATE_GET('AMOUNT_WANTED')")
    coin_max = find_blob(core, 'VAULT_COIN_MAX.TO_CURRENCY')
    coin_cur = retarget(coin_max, 'VAULT_COIN_MAX.TO_CURRENCY', 'VAULT_COIN_CURRENT.TO_CURRENCY',
                        {'VAULT_COIN_MAX': 'VAULT_COIN_CURRENT'})
    # The outliner gives each objective one line; anything longer wraps onto itself.
    cave.set('MISSION_AFFLUENCE_AMASS', Entry(
        'Fill vaults: %Oproperty_comp%% / %Oproperty_comp%%', [done, wanted]))
    desc = cave.key('MISSION_AFFLUENCE_AMASS_DESC')
    assert '%O' not in desc.text and not desc.blobs
    desc.text = 'Hoard: %Oproperty_comp / %Oproperty_comp\n' + desc.text
    desc.blobs = [coin_cur, coin_max]
