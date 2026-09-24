# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_range_sort_range_composite

from cplib.datastructure.binarytrie import RangeSortRangeProd
from cplib.tools.fastio import FastIO


MOD = 998244353
MASK = (1 << 30) - 1

N, Q = FastIO.read_ints(2)


def composite(f: int, x: int) -> int:
    fa, fb = f >> 30, f & MASK
    return (fa * x + fb) % MOD


def op(lt: int, rt: int) -> int:
    la, lb = lt >> 30, lt & MASK
    ra, rb = rt >> 30, rt & MASK
    a = la * ra % MOD
    b = (lb * ra + rb) % MOD
    return a << 30 | b


e = 1 << 30

keys = [0] * N
vals = [0] * N

for i in range(N):
    p, a, b = FastIO.read_ints(3)
    keys[i] = p
    vals[i] = a << 30 | b

trie = RangeSortRangeProd(N, keys, vals, 30, op, e)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        i, p, a, b = FastIO.read_ints(4)
        trie.set(i, p, a << 30 | b)
    elif t == 1:
        l, r, x = FastIO.read_ints(3)
        f = trie.prod(l, r)
        ret = composite(f, x)
        FastIO.writeln(f'{ret}')
    elif t == 2:
        l, r = FastIO.read_ints(2)
        trie.sort(l, r)
    else:
        l, r = FastIO.read_ints(2)
        trie.sort(l, r, reverse=True)
