#!/usr/bin/env python3
"""List where to send dwarves to explore: explored open tiles next to unexplored cave that is open-connected to a start tile.

Flood-fills open (non-front) map tiles 4-connected to the start (default: the cave entrance area of the
current colony, given as X Y), counts the unexplored ones, and prints the explored tiles that touch
them, grouped by 12x12 area and sorted by distance from the start. A Move To order needs an explored
target tile, so these are the tiles to click. The fill ignores climbing rules, so a group high up a
shaft may still be out of reach.

usage: frontier.py <save name> [X Y]
"""
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from save import Save, SAVE_DIR  # noqa: E402

FRONT, EXPLORED = 1 << 21, 1 << 22
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def main():
    s = Save(os.path.join(SAVE_DIR, sys.argv[1] + '.2.save'))
    _, m = s.unpack('map/map.bin')
    mw, mh = struct.unpack_from('<2I', m, 0)
    w = mw // 16

    def tile(x, y):
        return struct.unpack_from('<I', m, 16 + 4 * ((((y >> 4) * w + (x >> 4)) << 8) | ((y & 15) << 4) | (x & 15)))[0]

    start = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (528, 967)
    seen = {start}
    queue = collections.deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in STEPS:
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < mw and 0 <= n[1] < mh and not tile(*n) & FRONT:
                seen.add(n)
                queue.append(n)
    unexplored = [p for p in seen if not tile(*p) & EXPLORED]
    print('connected open tiles', len(seen), 'unexplored', len(unexplored))
    edge = {(x + dx, y + dy) for x, y in unexplored for dx, dy in STEPS
            if (x + dx, y + dy) in seen and tile(x + dx, y + dy) & EXPLORED}
    groups = collections.defaultdict(list)
    for x, y in sorted(edge):
        groups[(x // 12, y // 12)].append((x, y))
    for tiles in sorted(groups.values(), key=lambda t: abs(t[0][0] - start[0]) + abs(t[0][1] - start[1])):
        print(len(tiles), tiles[:4])


if __name__ == '__main__':
    main()
