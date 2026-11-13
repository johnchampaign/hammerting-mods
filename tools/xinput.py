#!/usr/bin/env python3
"""Send mouse and key input to the Hammerting window (Xwayland) through XTest.

The game window sits at +0+0 at 1920x1080, so coordinates match tools/shot.sh screenshots.

usage:
  xinput.py move X Y          hover (for tooltips)
  xinput.py click X Y [button]
  xinput.py key NAME          e.g. Escape, space
"""
import ctypes
import sys
import time

x11 = ctypes.cdll.LoadLibrary('libX11.so.6')
xtst = ctypes.cdll.LoadLibrary('libXtst.so.6')
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XFlush.argtypes = [ctypes.c_void_p]
x11.XStringToKeysym.restype = ctypes.c_ulong
x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]

d = x11.XOpenDisplay(b':0')
assert d, 'cannot open display :0'


def move(x, y):
    xtst.XTestFakeMotionEvent(d, -1, x, y, 0)
    x11.XFlush(d)


def click(x, y, button=1):
    move(x, y)
    time.sleep(0.15)
    xtst.XTestFakeButtonEvent(d, button, 1, 0)
    x11.XFlush(d)
    time.sleep(0.25)  # the game polls input per frame and misses shorter presses
    xtst.XTestFakeButtonEvent(d, button, 0, 0)
    x11.XFlush(d)


def key(name):
    code = x11.XKeysymToKeycode(d, x11.XStringToKeysym(name.encode()))
    xtst.XTestFakeKeyEvent(d, code, 1, 0)
    x11.XFlush(d)
    time.sleep(0.25)
    xtst.XTestFakeKeyEvent(d, code, 0, 0)
    x11.XFlush(d)


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'move':
        move(int(args[0]), int(args[1]))
    elif cmd == 'click':
        click(int(args[0]), int(args[1]), int(args[2]) if len(args) > 2 else 1)
    elif cmd == 'key':
        key(args[0])
