"""LZ4 block-format decoder (no frame header)."""


def decompress(src, start=0, end=None, limit=1 << 28):
    end = len(src) if end is None else end
    out = bytearray()
    i = start
    while i < end:
        tok = src[i]
        i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        out += src[i:i + lit]
        i += lit
        if i >= end:
            break
        off = src[i] | (src[i + 1] << 8)
        i += 2
        if off == 0 or off > len(out):
            raise ValueError(f'bad offset {off} at {i}')
        ml = (tok & 15) + 4
        if (tok & 15) == 15:
            while True:
                b = src[i]
                i += 1
                ml += b
                if b != 255:
                    break
        for _ in range(ml):
            out.append(out[-off])
        if len(out) > limit:
            raise ValueError('too large')
    return bytes(out)
