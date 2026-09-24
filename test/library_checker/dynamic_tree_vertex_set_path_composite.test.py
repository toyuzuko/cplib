# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_set_path_composite

from cplib.graph.linkcut import BidirectionalLinkCutTree
from cplib.tools.fastio import FastIO


MOD = 998244353
SHIFT = 30
MASK = (1 << SHIFT) - 1


def pack(a: int, b: int) -> int:
    return a << SHIFT | b


def compose(left: int, right: int) -> int:
    a0 = left >> SHIFT
    b0 = left & MASK
    a1 = right >> SHIFT
    b1 = right & MASK
    return pack(a0 * a1 % MOD, (a0 * b1 + b0) % MOD)


N, Q = FastIO.read_ints(2)

A: list[int] = []

for _ in range(N):
    c, d = FastIO.read_ints(2)
    A.append(pack(c, d))

IDENTITY = pack(1, 0)
lct = BidirectionalLinkCutTree[int](N, IDENTITY, compose)
lct.build(A)

for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    lct.link(u, v)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, w, x = FastIO.read_ints(4)
        lct.cut(u, v)
        lct.link(w, x)
    elif t == 1:
        p, c, d = FastIO.read_ints(3)
        value = pack(c, d)
        lct.set(p, value)
    else:
        u, v, x = FastIO.read_ints(3)
        value = lct.path_prod(u, v)[1]
        a = value >> SHIFT
        b = value & MASK
        FastIO.writeln(f'{(a * x + b) % MOD}')
