"""Away Dwarf Alerts: dwarf alerts leave out dwarves who are away on the overworld.

A dwarf carrying goods to a settlement is tagged CURRENTLY_IN_OVERWORLD, and his position is then in
overworld coordinates (small numbers like -3.5, 2.0). The dwarf alerts (Wrong Tools Equipped, Idle,
Outdated Equipment, Low Health and others) still listed him, and their click action,
CAMERA_MOVE_TO_POSITION(DATA.GET_AT(NEXT_CLICK_INDEX).POS), moved the cave camera to that position:
the empty, unexplored corner at the bottom left of the cave map. Seen in the user's colony
(savegame58: entity 2346, favourite Miner, at -3.5, 2.0, -2.23 while tagged as in the overworld).

Each alert whose list starts from TAGGED_ENTITIES('PLAYER_CHARACTER') now filters those dwarves out, so
an alert lists only dwarves in the cave and shows again for a traveller once he is back. Data only.
"""

DESCRIPTION = 'Dwarf alerts skip dwarves away on the overworld, so a click never jumps to an empty map corner'

ALERTS = 'database/alert/alert.bin'
RECORD_START, RECORD_SIZE, RECORDS = 0x10, 0xc80, 18
COND, COND_SIZE = 0x80, 0x400        # the condition chain buffer in each record
DWARVES = "TAGGED_ENTITIES('PLAYER_CHARACTER')"
IN_CAVE = DWARVES + """.FILTER("NOT(HAS_TAG('CURRENTLY_IN_OVERWORLD'))")"""
EXPECTED = {'ALERT_MISSING_DWELLING', 'ALERT_LOW_HEALTH', 'ALERT_OUTDATED_EQUIPMENT',
            'ALERT_UNMANAGED_PROFESSIONS', 'ALERT_IDLE_DWARVES', 'ALERT_DWARVES_WITH_WRONG_TOOLS',
            'ALERT_STRANDED_DWARVES'}


def apply(ctx):
    d = bytearray(ctx.read(ALERTS))
    changed = set()
    for r in range(RECORDS):
        rec = RECORD_START + r * RECORD_SIZE
        tag = d[rec:rec + 0x40].split(b'\0')[0].decode()
        at = rec + COND
        cond = d[at:at + COND_SIZE].split(b'\0')[0].decode()
        if DWARVES not in cond:
            continue
        new = cond.replace(DWARVES, IN_CAVE).encode()
        assert len(new) < COND_SIZE, tag
        d[at:at + COND_SIZE] = new.ljust(COND_SIZE, b'\0')
        changed.add(tag)
    assert changed == EXPECTED, changed ^ EXPECTED
    ctx.write(ALERTS, bytes(d))
