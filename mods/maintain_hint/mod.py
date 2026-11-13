"""Maintain Hint: say what the Local maintain mode actually counts.

refresh_maintain_locally counts only the items inside the producing building. Haulers
carry finished goods to storage, the count drops, and the order crafts again, so a Local
maintain order on anything that gets hauled away never stops. Global mode counts the whole
Mountainhome. This only changes the tooltips.
"""

DESCRIPTION = "Maintain-mode tooltips warn that Local keeps crafting once items are hauled away"

TEXT = {
    'Maintain amount in building inventory':
        'Maintain amount in building inventory (counts only this building: if haulers carry '
        'the items away it keeps crafting. Use Mountainhome for goods that get stored)',
    'Maintain amount in the Mountainhome':
        'Maintain amount in the Mountainhome (counts every storage)',
}


def apply(ctx):
    table = ctx.loc('dubious_entries')
    found = 0
    for entry in table.entries.values():
        if entry.text in TEXT and not entry.blobs:
            entry.text = TEXT[entry.text]
            found += 1
    assert found == len(TEXT), found
