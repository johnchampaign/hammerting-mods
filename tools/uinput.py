#!/usr/bin/env python3
"""Drive the game through virtual input devices (/dev/uinput).

Use this when GNOME stops passing XTest input from tools/xinput.py (its Remote Desktop
grant lapses, for example after the game restarts, and no new prompt appears). uinput
devices are real input as far as the desktop is concerned: they act on whatever window
is under the pointer or has focus, so nobody should use the mouse or keyboard meanwhile.
The user approved this on 2026-11-01.

Coordinates are screen pixels (one 1920x1080 monitor, game window at +0+0), the same
as tools/shot.sh screenshots. Steps run in order with the devices created once:

usage: uinput.py STEP...
  move X Y | click X Y | dclick X Y | rclick X Y | key NAME | wait SECONDS
  scroll X Y N            N wheel clicks at X Y (positive = down)
  down NAME | up NAME     hold a key (modifier clicks: down ctrl click X Y up ctrl)
  press X Y | release X Y hold the left button (drag: press, move, release)
  e.g. uinput.py click 1071 46 key space

A new device takes the desktop a few seconds to register, and input sent before that is
lost, so a sequence of separate runs drops clicks and key presses at random. For a longer
session keep one pair of devices open:

  uinput.py serve SOCKET          run in the background; wait about 5 s before the first send
  uinput.py send SOCKET STEP...   runs the steps on those devices, returns when they are done
"""
import fcntl
import os
import socket
import struct
import sys
import time

W, H = 1920, 1080
EV_SYN, EV_KEY, EV_REL, EV_ABS = 0, 1, 2, 3
REL_WHEEL = 8
ABS_X, ABS_Y = 0, 1
BTN_LEFT, BTN_RIGHT = 0x110, 0x111
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT, UI_SET_ABSBIT = 0x40045564, 0x40045565, 0x40045566, 0x40045567
UI_DEV_SETUP, UI_ABS_SETUP = 0x405c5503, 0x401c5504
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502
BUS_VIRTUAL = 0x06
# Linux key codes (input-event-codes.h)
KEYS = {'escape': 1, 'space': 57, 'return': 28, 'tab': 15, 'backspace': 14, 'semicolon': 39, 'minus': 12,
        'up': 103, 'down': 108, 'left': 105, 'right': 106, 'ctrl': 29, 'shift': 42,
        **{str(i): 1 + i for i in range(1, 10)}, '0': 11,
        **{f'f{i}': 58 + i for i in range(1, 11)},
        **{c: k for c, k in zip('qwertyuiop', range(16, 26))},
        **{c: k for c, k in zip('asdfghjkl', range(30, 39))},
        **{c: k for c, k in zip('zxcvbnm', range(44, 51))}}


def device(name, keys, absolute=False):
    fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
    for k in keys:
        fcntl.ioctl(fd, UI_SET_KEYBIT, k)
    if absolute:
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_ABS)
        for axis, size in ((ABS_X, W), (ABS_Y, H)):
            fcntl.ioctl(fd, UI_SET_ABSBIT, axis)
            # u16 code, pad, input_absinfo {value, minimum, maximum, fuzz, flat, resolution}
            fcntl.ioctl(fd, UI_ABS_SETUP, struct.pack('<HxxiiiiII', axis, 0, 0, size - 1, 0, 0, 0))
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_REL)
        fcntl.ioctl(fd, UI_SET_RELBIT, REL_WHEEL)
    fcntl.ioctl(fd, UI_DEV_SETUP, struct.pack('<HHHH80sI', BUS_VIRTUAL, 0x1234, 0x5678, 1,
                                              name.encode(), 0))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    return fd


def emit(fd, *events):
    for typ, code, value in events + ((EV_SYN, 0, 0),):
        os.write(fd, struct.pack('<qqHHi', 0, 0, typ, code, value))


class Input:
    def __init__(self):
        self.mouse = device('hammerting-tools pointer', (BTN_LEFT, BTN_RIGHT), absolute=True)
        self.kbd = device('hammerting-tools keyboard', sorted(set(KEYS.values())))
        time.sleep(1.0)  # let the compositor pick the new devices up

    def close(self):
        for fd in (self.mouse, self.kbd):
            fcntl.ioctl(fd, UI_DEV_DESTROY)
            os.close(fd)

    def move(self, x, y):
        emit(self.mouse, (EV_ABS, ABS_X, x), (EV_ABS, ABS_Y, y))
        time.sleep(0.15)

    def click(self, x, y, button=BTN_LEFT):
        self.move(x, y)
        emit(self.mouse, (EV_KEY, button, 1))
        time.sleep(0.25)  # the game polls input per frame and misses shorter presses
        emit(self.mouse, (EV_KEY, button, 0))
        time.sleep(0.1)

    def scroll(self, x, y, clicks):
        """Wheel clicks at (x, y); positive scrolls down."""
        self.move(x, y)
        for _ in range(abs(clicks)):
            emit(self.mouse, (EV_REL, REL_WHEEL, -1 if clicks > 0 else 1))
            time.sleep(0.1)

    def key(self, name):
        code = KEYS[name.lower()]
        emit(self.kbd, (EV_KEY, code, 1))
        time.sleep(0.25)
        emit(self.kbd, (EV_KEY, code, 0))
        time.sleep(0.1)


def run_steps(inp, argv):
    i = 0
    while i < len(argv):
        cmd = argv[i]
        if cmd in ('move', 'click', 'dclick', 'rclick'):
            x, y = int(argv[i + 1]), int(argv[i + 2])
            i += 3
            if cmd == 'move':
                inp.move(x, y)
            elif cmd == 'rclick':
                inp.click(x, y, BTN_RIGHT)
            else:
                for _ in range(2 if cmd == 'dclick' else 1):
                    inp.click(x, y)
        elif cmd == 'scroll':
            inp.scroll(int(argv[i + 1]), int(argv[i + 2]), int(argv[i + 3]))
            i += 4
        elif cmd == 'key':
            inp.key(argv[i + 1])
            i += 2
        elif cmd in ('press', 'release'):
            inp.move(int(argv[i + 1]), int(argv[i + 2]))
            emit(inp.mouse, (EV_KEY, BTN_LEFT, int(cmd == 'press')))
            time.sleep(0.25)
            i += 3
        elif cmd in ('down', 'up'):
            emit(inp.kbd, (EV_KEY, KEYS[argv[i + 1].lower()], int(cmd == 'down')))
            time.sleep(0.1)
            i += 2
        elif cmd == 'wait':
            time.sleep(float(argv[i + 1]))
            i += 2
        else:
            raise ValueError(f'unknown step {cmd!r}')


def serve(path):
    if os.path.exists(path):
        os.unlink(path)
    inp = Input()
    srv = socket.socket(socket.AF_UNIX)
    try:
        srv.bind(path)
        srv.listen()
        while True:
            conn, _ = srv.accept()
            with conn, conn.makefile('r') as f:
                try:
                    try:
                        run_steps(inp, f.readline().split())
                        conn.sendall(b'ok\n')
                    except (ValueError, KeyError, IndexError) as e:
                        conn.sendall(f'error: {e}\n'.encode())
                except OSError:
                    pass    # the client went away (killed or timed out) before reading the reply
    finally:
        srv.close()
        os.unlink(path)
        inp.close()


def send(path, steps):
    with socket.socket(socket.AF_UNIX) as c:
        c.connect(path)
        c.sendall((' '.join(steps) + '\n').encode())
        reply = c.makefile('r').readline().strip()
    if reply != 'ok':
        sys.exit(reply)


def main(argv):
    if argv[:1] == ['serve']:
        serve(argv[1])
    elif argv[:1] == ['send']:
        send(argv[1], argv[2:])
    else:
        inp = Input()
        try:
            run_steps(inp, argv)
        except (ValueError, KeyError, IndexError) as e:
            sys.exit(str(e))
        finally:
            inp.close()


if __name__ == '__main__':
    main(sys.argv[1:])
