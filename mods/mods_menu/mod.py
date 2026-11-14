"""Mods Menu: the menus say the mods are installed, and list them.

- The version in the corner of the main menu and in game reads "1.2.39.0 + Fix-Up Mods <version>".
  Both are a text whose one %Oproperty_comp shows the chain GAME_VERSION (ui/main_menu/main_menu
  and ui/version_ingame); the mod appends to the chain.
- The news window (ui/main_menu/newsletter, the patch notes shown at start and by Newsletter) gets
  a section about the mods above the 1.2.39 notes. Its text is one plain text component.
- A Mods button between Credits and Exit (main menu and pause menu) opens a window listing every
  installed mod with its description. The buttons are records under LABEL__BUTTONS in
  ui/main_menu/start, stacked in record order (their stored y offsets aren't used). The new button
  is a copy of the Newsletter button and its label without the Newsletter event: its click closes
  an open Mods window and spawns entity/ui/main_menu/hmod_mods.entity (SPAWN_CHILD_ENTITY, as the
  top bar spawns its overlays). That window is a copy of the news window with its own id and text.
Record and component layouts are in tools/entity.py. Data only.
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import entity as E  # noqa: E402
from evalchain import compile_chain  # noqa: E402
from loc import Entry  # noqa: E402

MODS_VERSION = '1.4.0'
URL = 'github.com/johnchampaign/hammerting-mods'

DESCRIPTION = 'Menus show the mods version and news, and a Mods button lists the installed mods'

START = 'entity/ui/main_menu/start.entity'
NEWS = 'entity/ui/main_menu/newsletter.entity'
WINDOW = 'entity/ui/main_menu/hmod_mods.entity'
VERSION_TEXTS = ('entity/ui/main_menu/main_menu.entity', 'entity/ui/version_ingame.entity')
WINDOW_ID = 'HMOD_MODS'
FRAME_SIZE = 0x12c4         # float width, height
CHAIN = 0x4c48              # u8 1, then a compiled chain run when the record is created
BUTTON_STEP = 62            # the buttons' spacing (LABEL__SAVE sits at y -78, LABEL__EXIT at -444)
TITLE = f'|GOLD26**|Hammerting Fix-Up Mods - Version {MODS_VERSION}|!|'


def show_version(ctx):
    for name in VERSION_TEXTS:
        recs = E.parse(ctx.read(name))
        found = 0
        for r in recs:
            for i in r.find(E.CHAIN_TEXT):
                if r.comps[i][1].endswith(b'GAME_VERSION$O\0'):
                    r.comps[i][1] = E.chain_text(r.comps[i][1], f"GAME_VERSION.APPEND(' + Fix-Up Mods {MODS_VERSION}')")
                    found += 1
        assert found == 1, (name, found)
        ctx.write(name, E.pack(recs))


def scroll_text(recs):
    r, = [r for r in recs if r.name == 'LABEL__SCROLL_CONTENT']
    return r


def add_news(ctx, count):
    recs = E.parse(ctx.read(NEWS))
    r = scroll_text(recs)
    old = E.text(r.get(E.TEXT))
    assert old.startswith('\n\n\n|GOLD26**|Quality of Life 4 Update'), old[:60]
    news = (f'\n\n\n{TITLE}\n\n'
            f'⦿ {count} unofficial mods are installed. |YELLOW|Mods|!| in the main menu lists them.\n'
            f'⦿ To add or remove mods, close the game, edit |YELLOW|mods/recommended.txt|!| and run the '
            f'installer again.\n'
            f'⦿ Updates, details and bug reports: |YELLOW|{URL}|!|\n')
    r.set(E.TEXT, E.set_text(r.get(E.TEXT), news + old))
    ctx.write(NEWS, E.pack(recs))


def short(description):
    """A mod's DESCRIPTION for the window, without "(DLL patch)". A plain text component shows %
    as it is (%% is only needed in texts with chains)."""
    return re.sub(r'\s*\((?:entity )?DLL patch\)$', '', description)


def mods_window(ctx):
    sys.path.insert(0, os.path.dirname(HERE))
    from importlib.util import module_from_spec, spec_from_file_location
    lines = []
    for name in ctx.mods:
        spec = spec_from_file_location(f'hmod_desc_{name}', os.path.join(os.path.dirname(HERE), name, 'mod.py'))
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        lines.append(f'⦿ |YELLOW|{name}|!|: {short(mod.DESCRIPTION)}')
    text = (f'\n\n\n{TITLE}\n\n'
            f'Unofficial fixes for Hammerting 1.2.39. Details, updates and bug reports: '
            f'|YELLOW|{URL}|!|\n\n'
            f'To change which mods are installed, close the game, edit |YELLOW|mods/recommended.txt|!| '
            f'in the mods folder and run the installer again.\n\n'
            f'|GOLD20**|Installed mods ({len(lines)}):|!|\n' + '\n'.join(lines) + '\n')
    recs = E.parse(ctx.read(NEWS))      # the original window, without the news section
    root = recs[0]
    root.set(E.ID, E.tag(WINDOW_ID))
    # The news window is spawned on its own (spawn/mainmenu_ui.bin), where y 0 is the screen's
    # centre, and slides in once per run (LABEL__ANIM_START); later opens set y 0 directly
    # (LABEL__ANIM_INGAME_TWO). Spawned as a child of the menu, its position is the centre in a
    # space whose origin is the bottom-left corner, so drop the slide and set both coordinates.
    E.remove(recs, [r.name for r in recs].index('LABEL__ANIM_START'))
    r, = [r for r in recs if r.name == 'LABEL__ANIM_INGAME_TWO']
    assert r.get(CHAIN) == b'\x01' + compile_chain("PARENT.PARENT.BOUNDS_SET_Y(FLOAT('0'))")
    r.set(CHAIN, b'\x01' + compile_chain(
        "PARENT.PARENT.BOUNDS_SET_POS(UI_RESOLUTION.X.DIV('2'), UI_RESOLUTION.Y.DIV('2'))"))
    r = scroll_text(recs)
    r.set(E.TEXT, E.set_text(r.get(E.TEXT), text))
    ctx.write(WINDOW, E.pack(recs))
    return len(lines)


def add_button(ctx):
    recs = E.parse(ctx.read(START))
    names = [r.name for r in recs]
    news, exit_ = names.index('LABEL__NEWSLETTER'), names.index('LABEL__EXIT')
    button, label = recs[news].copy(), recs[news + 1].copy()
    assert label.parent == news and label.find(E.LABEL)
    # Drop the Newsletter event; replace its close-the-news action with ours.
    events = [i for i in button.find(E.ACTION) if b'TDTD_EVENT_MAINMENU_NEWSLETTER\0' in button.comps[i][1]]
    close, = [i for i in button.find(E.ACTION) if b"CHILD_WITH_ID_RECURSIVE('NEWSLETTER'" in button.comps[i][1]]
    template = button.comps[close][1]
    button.comps[close][1] = E.action(
        template, f"TOP_PARENT.CHILD_WITH_ID_RECURSIVE('{WINDOW_ID}', FALSE).CLEAR_ID.DESTROY_SELF")
    button.comps.insert(close + 1, [E.ACTION, E.action(template, f"TOP_PARENT.SPAWN_CHILD_ENTITY('{WINDOW}')")])
    assert len(events) == 1
    del button.comps[events[0] + (events[0] > close)]
    tooltip, = [i for i in button.find(0x5ae5) if b'TOOLTIP_MAIN_MENU_NEWSLETTER\0' in button.comps[i][1]]
    button.comps[tooltip][1] = button.comps[tooltip][1][:8] + b'TOOLTIP_MAIN_MENU_HMOD_MODS\0'
    button.set(E.NAME, b'LABEL__HMOD_MODS\0')
    label.set(E.LABEL, E.label(label.get(E.LABEL), 'MAINMENU_HMOD_MODS'))
    label.parent = exit_
    E.insert(recs, exit_, [button, label])
    # The frame (LABEL__BASE, centred on its anchor) is sized for nine buttons; add one row.
    base, = [r for r in recs if r.name == 'LABEL__BASE']
    w, h = struct.unpack('<ff', base.get(FRAME_SIZE))
    base.set(FRAME_SIZE, struct.pack('<ff', w, h + BUTTON_STEP))
    ctx.write(START, E.pack(recs))
    core = ctx.loc('core')
    core.set('MAINMENU_HMOD_MODS', Entry('Mods'))
    core.set('TOOLTIP_MAIN_MENU_HMOD_MODS', Entry('List the installed Fix-Up Mods'))


def apply(ctx):
    show_version(ctx)
    count = mods_window(ctx)
    add_news(ctx, count)
    add_button(ctx)
