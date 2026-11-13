"""Attribute Hint: the attribute help says statuses and traits can lower attributes for a while.

Players report attributes "randomly decreasing" (BUGS B15). A dwarf's stored attributes never go down: across 42
saves of three colonies no KV_ATTRIBUTE_* value fell between saves. What drops is the shown value, which adds
modifiers on top: 26 statuses from the energy, morale, greed and hunger bars lower one by 1-3 while they last
(Could Eat Rocks -3 Robustness, Unslakable Thirst -3 Awareness, Bankruptcy Proceedings -3 Wisdom), and 19 traits
lower one from the start. The game's own help only says attributes increase on level-up. This only changes texts.
"""

DESCRIPTION = 'Attribute help explains that statuses and traits can lower attributes temporarily'

TEXT = {
    'core': {
        'These are the |GOLD*|DWARF-attributes|!|.\nThey will grant a |GOLD*|bonus|!| to |GOLD*|specific tasks|!| and '
        'increase |GOLD*|certain stats|!| (found in the Stats panel).\nThe attributes will |GOLD*|automatically '
        'increase|!| according to the dwarfs best job whenever they level up.':
            'These are the |GOLD*|DWARF-attributes|!|.\nThey will grant a |GOLD*|bonus|!| to |GOLD*|specific tasks|!| and '
            'increase |GOLD*|certain stats|!| (found in the Stats panel).\nThe attributes will |GOLD*|automatically '
            'increase|!| according to the dwarfs best job whenever they level up.\nThe shown value includes '
            '|GOLD*|statuses|!| from the energy, morale, greed and hunger bars, which can lower an attribute by 1-3 '
            'while they last, and |GOLD*|traits|!|. Learned attributes are never lost.',
        'Dwarves have five primary attributes, the DWARF-attributes, namely Deftness, Wisdom, Awareness, Robustness '
        'and Fervor. Increasing any of the Attributes by leveling up, will allow the Dwarves to excel at their various '
        'Professions, found under the Professions & Skills tab of their interface.':
            'Dwarves have five primary attributes, the DWARF-attributes, namely Deftness, Wisdom, Awareness, Robustness '
            'and Fervor. Increasing any of the Attributes by leveling up, will allow the Dwarves to excel at their '
            'various Professions, found under the Professions & Skills tab of their interface. Statuses from the '
            'energy, morale, greed and hunger bars, and some traits, lower an attribute while they last; the '
            'attributes a dwarf has learned are never lost.',
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
