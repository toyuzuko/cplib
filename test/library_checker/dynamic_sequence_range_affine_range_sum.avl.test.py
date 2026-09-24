# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_sequence_range_affine_range_sum

from cplib.datastructure.avltree import ImplicitAVLTree
from cplib.tools.fastio import FastIO


MOD = 998244353
mask = (1 << 31) - 1


def op(a: int, b: int) -> int:
    a1, a2 = a >> 31, a & mask
    b1, b2 = b >> 31, b & mask
    c1 = (a1 + b1) % MOD
    c2 = (a2 + b2) % MOD
    return (c1 << 31) + c2


def mapping(x: int, a: int) -> int:
    x1, x2 = x >> 31, x & mask
    a1, a2 = a >> 31, a & mask
    c1 = (a1 * x1 + a2 * x2) % MOD
    c2 = a2
    return (c1 << 31) + c2


def composition(x: int, y: int) -> int:
    x1, x2 = x >> 31, x & mask
    y1, y2 = y >> 31, y & mask
    z1 = (x1 * y1) % MOD
    z2 = (x1 * y2 + x2) % MOD
    return (z1 << 31) + z2


N, Q = FastIO.read_ints(2)
A = [(a << 31) + 1 for a in FastIO.read_ints(N)]

seq = ImplicitAVLTree(op, 0, mapping, composition, 1 << 31, commutative=True)
seq.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        i, x = FastIO.read_ints(2)
        if i < seq.size():
            seq.insert(i, (x << 31) + 1)
        else:
            seq.insert(seq.size(), (x << 31) + 1)
    elif t == 1:
        i, = FastIO.read_ints(1)
        seq.erase(i)
    elif t == 2:
        l, r = FastIO.read_ints(2)
        seq.reverse(l, r)
    elif t == 3:
        l, r, b, c = FastIO.read_ints(4)
        seq.range_apply(l, r, (b << 31) + c)
    else:
        l, r = FastIO.read_ints(2)
        ret = seq.prod(l, r) >> 31
        FastIO.writeln(f'{ret}')
