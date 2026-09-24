# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_set_path_composite

from cplib.graph.toptree import TopTree
from cplib.tools.fastio import FastIO

MOD = 998244353
SHIFT = 30
MASK = (1 << SHIFT) - 1


def compose(left: int, right: int) -> int:
    a = (right >> SHIFT) * (left >> SHIFT) % MOD
    b = ((right >> SHIFT) * (left & MASK) + (right & MASK)) % MOD
    return a << SHIFT | b


N, Q = FastIO.read_ints(2)
A: list[int] = []
for _ in range(N):
    a, b = FastIO.read_ints(2)
    A.append(a << SHIFT | b)

tree = TopTree[int, None, int](A, None, lambda point, value: value, lambda path: None, lambda left, right: None, compose)
for _ in range(N - 1):
    child, parent = FastIO.read_ints(2)
    tree.link(child, parent)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, child, parent = FastIO.read_ints(4)
        tree.cut(u, v)
        tree.link(child, parent)
    elif t == 1:
        vertex, a, b = FastIO.read_ints(3)
        tree.set(vertex, a << SHIFT | b)
    else:
        u, v, x = FastIO.read_ints(3)
        value = tree.path_cluster_value(u, v)
        FastIO.writeln(f'{((value >> SHIFT) * x + (value & MASK)) % MOD}')
