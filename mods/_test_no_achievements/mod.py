"""Test only, never for play: the game unlocks no Steam achievements.

Steam stays online during tests, and a test that reaches a victory unlocked a real achievement on the
user's account. Steam's offline mode is no help, since it uploads achievements earned offline once it
reconnects. The game unlocks achievements only through `liveops_liveops_unlock_achievement_ptr`,
called once, from liveops_func (0x18006b0fb); this skips that call. The other liveops pointer that
could move an achievement, `liveops_liveops_modify_stat_ptr`, is never called. Adds no .hmod code.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))

DESCRIPTION = 'TEST ONLY: no Steam achievements (DLL patch)'

SITE = 0x18006b0fb
SITE_OLD = bytes.fromhex('ff150fc25200')   # call [liveops_liveops_unlock_achievement_ptr]


def apply(ctx):
    ctx.patch_dll(SITE, SITE_OLD, bytes.fromhex('660f1f440000'), 'skip unlock_achievement')
