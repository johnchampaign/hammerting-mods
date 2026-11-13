#!/usr/bin/env python3
"""Read the game camera's view rectangle (tile units) from the running game, read-only.

The camera keeps its four view corners as float32 (x, y, z) triples with z = 4.0, x growing rightward
and y upward, in tile units. `find` scans writable memory for them (it was 0x6d6f030 in two launches);
`read ADDR` prints the rectangle and the window pixel scale, and `px X Y ADDR` gives the screen point
(for tools/uinput.py) of tile coordinates X Y in the windowed game (1280x1024 at +67+32, game area from
window y 30).

usage: camera.py find | read ADDR | px X Y ADDR
"""
import os
import struct
import sys

WIN_X, WIN_Y, WIN_W, TOP = 67, 32, 1280, 30


def game_pid():
    return next(p for p in os.listdir('/proc')
                if p.isdigit() and open(f'/proc/{p}/comm').read().strip() == 'boot.exe')


def find(pid):
    four = struct.pack('<f', 4.0)
    with open(f'/proc/{pid}/mem', 'rb') as mem:
        for line in open(f'/proc/{pid}/maps'):
            span, perm = line.split()[:2]
            s, e = (int(x, 16) for x in span.split('-'))
            if 'rw' not in perm or e - s > 512 << 20:
                continue
            try:
                mem.seek(s)
                d = mem.read(e - s)
            except OSError:
                continue
            i = d.find(four)
            while i >= 0:
                b = i - 8
                if 0 <= b and b + 48 <= len(d):
                    v = struct.unpack_from('<12f', d, b)
                    xs, ys = v[0::3], v[1::3]
                    if (all(v[3 * k + 2] == 4.0 for k in range(4)) and all(0 < c < 1100 for c in xs + ys)
                            and len({round(x, 2) for x in xs}) == 2 and len({round(y, 2) for y in ys}) == 2):
                        yield s + b, rect(v)
                i = d.find(four, i + 4)


def rect(v):
    xs, ys = v[0::3], v[1::3]
    return min(xs), max(xs), min(ys), max(ys)


def read(pid, addr):
    with open(f'/proc/{pid}/mem', 'rb') as mem:
        mem.seek(addr)
        return rect(struct.unpack('<12f', mem.read(48)))


def main(argv):
    pid = game_pid()
    if argv[0] == 'find':
        for addr, r in find(pid):
            print(hex(addr), 'x %.1f-%.1f y %.1f-%.1f' % r)
    elif argv[0] == 'read':
        x0, x1, y0, y1 = read(pid, int(argv[1], 16))
        print('x %.2f-%.2f y %.2f-%.2f, %.1f px/tile' % (x0, x1, y0, y1, WIN_W / (x1 - x0)))
    elif argv[0] == 'px':
        x, y = float(argv[1]), float(argv[2])
        x0, x1, y0, y1 = read(pid, int(argv[3], 16))
        scale = WIN_W / (x1 - x0)
        print(round(WIN_X + (x - x0) * scale), round(WIN_Y + TOP + (y1 - y) * scale))


if __name__ == '__main__':
    main(sys.argv[1:])
