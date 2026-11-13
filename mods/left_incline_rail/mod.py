"""Left Incline Rail: the incline that rises to the left joins the Railway build menu.

The game ships two incline pieces, MECH_RAILWAY_RIGHT_INCLINE (track from -1,0 up to 1,1) and
MECH_RAILWAY_LEFT_INCLINE (1,0 up to -1,1), each with an entity, model, path, mirrored footprint
and recipe, and the right one's room record even names the left one as its mirror. But the left one
was never finished: the build menu's list leaves it out, its recipe has no unlock dependency and a
menu weight of -1, it has no icon, and both are named "Incline Railway". So only the up-right
incline can be placed.

This mod:
- adds the left incline after the right one in the Railway section of the build menu (both list
  chains in category_mech_window_generate.entity, and the section's ENABLE checks);
- gives its recipe the right incline's unlock (Cogborne Transmission) and menu weight, so the two
  appear together;
- adds a mirrored copy of the right incline's icon;
- names them "Incline Railway (Up Right)" and "Incline Railway (Up Left)".
Data only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
from evalchain import compile_chain  # noqa: E402
from wchash import wc_hash_string  # noqa: E402

DESCRIPTION = 'The incline rail that rises to the left can be built, unlocked together with the right one'

RIGHT, LEFT = 'MECH_RAILWAY_RIGHT_INCLINE', 'MECH_RAILWAY_LEFT_INCLINE'
MENU = 'entity/ui/window/build_menu/mech/category_mech_window_generate.entity'
RECIPES = 'database/recipe/recipe_rooms_cdb.bin'
DEPS, WEIGHT = 0x988, 0xeb0              # u64 _dependencies[4]; i64 menu weight (-1 on the left one)
ICON_SIZES = (16, 32, 48, 64, 96, 128, 256)
ICON_HEADER = 0x48                       # u32 format, u32 w, u32 h, ..., then w*h RGBA8
NAMES = {RIGHT: 'Incline Railway (Up Right)', LEFT: 'Incline Railway (Up Left)'}


def records(d):
    """(offset, size) of each record. The file starts with u16 record count, u16 component count,
    u32 file size; each record starts with u16 1, u16 components, u32 size, and its component table
    of (u64 hash, u64 offset from the record start) is at +0x90."""
    out, o = [], 0x90
    while o < len(d):
        size = struct.unpack_from('<I', d, o + 4)[0]
        out.append((o, size))
        o += size
    return out


def replace_blob(d, at, old_len, new):
    """Replace the compiled chain at d[at:at+old_len] and fix the sizes and offsets that follow it."""
    delta = len(new) - old_len
    rec, size = next((o, s) for o, s in records(d) if o <= at < o + s)
    count = struct.unpack_from('<H', d, rec + 2)[0]
    for i in range(count):
        p = rec + 0x90 + 16 * i + 8
        off = struct.unpack_from('<Q', d, p)[0]
        if off > at - rec:
            struct.pack_into('<Q', d, p, off + delta)
    struct.pack_into('<I', d, rec + 4, size + delta)
    d[at:at + old_len] = new
    struct.pack_into('<I', d, 4, len(d))


def chain_sources(d, text):
    """Source texts of the compiled chains whose source contains text. A blob's source starts right
    after its tokens (u64 hash, u8 token count, u8, u16, 8 bytes per token), and the hash checks it."""
    found, i = [], d.find(text)
    while i >= 0:
        for start in range(i, max(i - 400, 0), -1):
            end = d.find(b'\0', start)
            src = d[start:end]
            if not all(0x20 <= c < 0x7f for c in src):
                break
            for ntok in range(1, 64):
                head = start - 12 - 8 * ntok
                if (head >= 0 and d[head + 8] == ntok
                        and struct.unpack_from('<Q', d, head)[0] == wc_hash_string(src.decode())):
                    found.append(src.decode())
                    break
            else:
                continue
            break
        i = d.find(text, i + 1)
    return found


def add_to_menu(ctx):
    d = bytearray(ctx.read(MENU))
    old_item, new_item = f"'{RIGHT}', ", f"'{RIGHT}', '{LEFT}', "
    sources = chain_sources(d, old_item.encode())
    assert len(sources) == 4, sources   # ENABLE and list, for the icon and the text menu
    for src in sources:
        blob = compile_chain(src)
        at = d.find(blob)
        assert at >= 0 and d.find(blob, at + 1) < 0, src
        replace_blob(d, at, len(blob), compile_chain(src.replace(old_item, new_item)))
    assert struct.unpack_from('<I', d, 4)[0] == len(d)
    ctx.write(MENU, bytes(d))


def unlock_with_right(ctx):
    d = bytearray(ctx.read(RECIPES))
    n, size = struct.unpack_from('<QQ', d, 0)
    rs = size // n
    rec = {}
    for i in range(n):
        o = 16 + i * rs
        rec[d[o:o + 64].split(b'\0')[0].decode()] = o
    left, right = rec[LEFT], rec[RIGHT]
    assert d[left + DEPS:left + DEPS + 32] == bytes(32), 'left incline already has an unlock'
    d[left + DEPS:left + DEPS + 32] = d[right + DEPS:right + DEPS + 32]
    d[left + WEIGHT:left + WEIGHT + 8] = d[right + WEIGHT:right + WEIGHT + 8]
    ctx.write(RECIPES, bytes(d))


def mirrored_icons(ctx):
    for px in ICON_SIZES:
        img = ctx.read(f'ui/icon/{px}/{RIGHT.lower()}.ui.img')
        w, h = struct.unpack_from('<II', img, 4)
        assert len(img) == ICON_HEADER + w * h * 4, px   # the 48 and 96 folders hold 64 and 128 px images
        rows = [img[ICON_HEADER + y * w * 4:ICON_HEADER + (y + 1) * w * 4] for y in range(h)]
        flipped = b''.join(b''.join(r[x * 4:x * 4 + 4] for x in reversed(range(w))) for r in rows)
        ctx.write(f'ui/icon/{px}/{LEFT.lower()}.ui.img', img[:ICON_HEADER] + flipped)


def apply(ctx):
    add_to_menu(ctx)
    unlock_with_right(ctx)
    mirrored_icons(ctx)
    items = ctx.loc('items')
    for key, name in NAMES.items():
        assert items.key(key).text == 'Incline Railway', key
        items.key(key).text = name
