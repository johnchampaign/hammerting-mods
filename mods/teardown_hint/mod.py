"""Teardown Hint: say why a tear-down order waits, and how to help a stranded dwarf.

A tear-down is an ordinary builder job. update_teardown_jobs gives the piece farthest from the
entrance normal priority and every other one low, so an order can sit at 0% for minutes with no
message, and clicking the piece again only says there's already an order. Stranded dwarves are often
cut off by a stair or bridge piece, and the alert doesn't say what to do. This only changes the texts.
"""

DESCRIPTION = "Tear-down and Stranded Dwarves texts say why orders wait and how to reopen a route"

TEXT = {
    'core': {
        'Tearing down a building.':
            'Tearing down a building. It waits its turn behind other building orders, '
            'farthest from the entrance first.',
        "There's already an order here.":
            "There's already an order here. Click its marker to cancel it.",
    },
    'dubious_entries': {
        'Some of your dwarves are stranded, unable to reach the Entrance:\n%Oproperty_comp':
            'Some of your dwarves are stranded, unable to reach the Entrance:\n%Oproperty_comp\n'
            'A stair or bridge piece may have closed their route. Adding a stair piece beside '
            'it, or tearing it down, can open the way again.',
    },
}


def apply(ctx):
    for name, texts in TEXT.items():
        table = ctx.loc(name)
        found = 0
        for entry in table.entries.values():
            if entry.text in texts:
                entry.text = texts[entry.text]
                found += 1
        assert found == len(texts), (name, found)
