"""The engine's 64-bit hash: wc_hash(data, len) in wc_sys.dll is MetroHash64 with seed 0
(constants 0xD6D018F5, 0xA2AA033B, 0x62992FC1, 0x30BC5B29, verified by disassembly)."""
import struct

M = (1 << 64) - 1
K0, K1, K2, K3 = 0xD6D018F5, 0xA2AA033B, 0x62992FC1, 0x30BC5B29


def _rotr(x, r):
    return ((x >> r) | (x << (64 - r))) & M


def metrohash64(data, seed=0):
    n = len(data)
    p = 0
    h = ((seed + K2) * K0) & M
    if n >= 32:
        v = [h, h, h, h]
        while p + 32 <= n:
            a, b, c, d = struct.unpack_from('<4Q', data, p)
            v[0] = (_rotr((v[0] + a * K0) & M, 29) + v[2]) & M
            v[1] = (_rotr((v[1] + b * K1) & M, 29) + v[3]) & M
            v[2] = (_rotr((v[2] + c * K2) & M, 29) + v[0]) & M
            v[3] = (_rotr((v[3] + d * K3) & M, 29) + v[1]) & M
            p += 32
        v[2] ^= (_rotr(((v[0] + v[3]) * K0 + v[1]) & M, 37) * K1) & M
        v[3] ^= (_rotr(((v[1] + v[2]) * K1 + v[0]) & M, 37) * K0) & M
        v[0] ^= (_rotr(((v[0] + v[2]) * K0 + v[3]) & M, 37) * K1) & M
        v[1] ^= (_rotr(((v[1] + v[3]) * K1 + v[2]) & M, 37) * K0) & M
        h = (h + (v[0] ^ v[1])) & M
    if n - p >= 16:
        a, b = struct.unpack_from('<2Q', data, p)
        v0 = (_rotr((h + a * K2) & M, 29) * K3) & M
        v1 = (_rotr((h + b * K2) & M, 29) * K3) & M
        v0 ^= (_rotr((v0 * K0) & M, 21) + v1) & M
        v1 ^= (_rotr((v1 * K3) & M, 21) + v0) & M
        h = (h + v1) & M
        p += 16
    if n - p >= 8:
        h = (h + struct.unpack_from('<Q', data, p)[0] * K3) & M
        h ^= (_rotr(h, 55) * K1) & M
        p += 8
    if n - p >= 4:
        h = (h + struct.unpack_from('<I', data, p)[0] * K3) & M
        h ^= (_rotr(h, 26) * K1) & M
        p += 4
    if n - p >= 2:
        h = (h + struct.unpack_from('<H', data, p)[0] * K3) & M
        h ^= (_rotr(h, 48) * K1) & M
        p += 2
    if n - p >= 1:
        h = (h + data[p] * K3) & M
        h ^= (_rotr(h, 37) * K1) & M
    h ^= _rotr(h, 28)
    h = (h * K0) & M
    h ^= _rotr(h, 29)
    return h


def wc_hash_string(s, seed=0):
    return metrohash64(s.encode('utf-8'), seed)
