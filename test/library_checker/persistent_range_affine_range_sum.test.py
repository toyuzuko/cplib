# verification-helper: PROBLEM https://judge.yosupo.jp/problem/persistent_range_affine_range_sum

from cplib.datastructure.persistent import FullyPersistentLazySegmentTree
from cplib.tools.fastio import FastIO


MOD = 998244353
BIT = 31
MASK = (1 << BIT) - 1
ID_F = (1 << BIT)


def op(x: int, y: int) -> int:
    sx, lx = x >> BIT, x & MASK
    sy, ly = y >> BIT, y & MASK
    return (((sx + sy) % MOD) << BIT) + (lx + ly)


def mapping(f: int, x: int) -> int:
    a, b = f >> BIT, f & MASK
    s, l = x >> BIT, x & MASK
    return (((a * s + b * l) % MOD) << BIT) + l


def composition(f: int, g: int) -> int:
    af, bf = f >> BIT, f & MASK
    ag, bg = g >> BIT, g & MASK
    return (((af * ag) % MOD) << BIT) + (af * bg + bf) % MOD


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

seg = FullyPersistentLazySegmentTree(N, op, 0, mapping, composition, ID_F)
init_arr = [(a << BIT) + 1 for a in A]
seg.build(init_arr)

for _ in range(Q):
    q = FastIO.read_int()
    if q == 0:
        k, l, r, b, c = FastIO.read_ints(5)
        seg.range_apply(l, r, (b << BIT) + c, k)
    elif q == 1:
        k, s, l, r = FastIO.read_ints(4)
        seg.range_copy(l, r, k, s)
    else:
        k, l, r = FastIO.read_ints(3)
        res = seg.prod(l, r, k)
        FastIO.writeln(f'{res >> BIT}')
        seg.update()
