#!/usr/bin/env python3
"""Ask the window manager to focus the Hammerting window, and exit 1 unless it has focus.
Run before tools/uinput.py, whose input goes to whatever window is focused."""
import ctypes
import subprocess
import sys
import time

x = ctypes.cdll.LoadLibrary('libX11.so.6')
x.XOpenDisplay.restype = ctypes.c_void_p
x.XOpenDisplay.argtypes = [ctypes.c_char_p]
x.XDefaultRootWindow.restype = ctypes.c_ulong
x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
x.XInternAtom.restype = ctypes.c_ulong
x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
x.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
x.XFlush.argtypes = [ctypes.c_void_p]


class XClientMessageEvent(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int), ('serial', ctypes.c_ulong), ('send_event', ctypes.c_int),
                ('display', ctypes.c_void_p), ('window', ctypes.c_ulong), ('message_type', ctypes.c_ulong),
                ('format', ctypes.c_int), ('data', ctypes.c_long * 5)]


class XEvent(ctypes.Union):
    _fields_ = [('xclient', XClientMessageEvent), ('pad', ctypes.c_long * 24)]


def xprop(*args):
    return subprocess.run(['xprop', '-display', ':0', *args], capture_output=True, text=True).stdout


def game_window():
    tree = subprocess.run(['xwininfo', '-display', ':0', '-root', '-tree'], capture_output=True, text=True).stdout
    return int(next(line.split()[0] for line in tree.splitlines() if '"Hammerting":' in line), 16)


def active():
    return int(xprop('-root', '_NET_ACTIVE_WINDOW').split()[-1], 16)


def main():
    win = game_window()
    if active() != win:
        d = x.XOpenDisplay(b':0')
        ev = XEvent()
        ev.xclient.type = 33  # ClientMessage
        ev.xclient.send_event = 1
        ev.xclient.display = d
        ev.xclient.window = win
        ev.xclient.message_type = x.XInternAtom(d, b'_NET_ACTIVE_WINDOW', 0)
        ev.xclient.format = 32
        ev.xclient.data[0] = 2  # source: pager, which mutter does not treat as focus stealing
        x.XSendEvent(d, x.XDefaultRootWindow(d), 0, (1 << 19) | (1 << 20), ctypes.byref(ev))
        x.XFlush(d)
        time.sleep(1)
    sys.exit(0 if active() == win else 1)


if __name__ == '__main__':
    main()
