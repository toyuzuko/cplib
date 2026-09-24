# verification-helper: PROBLEM https://judge.yosupo.jp/problem/vertex_set_path_composite

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.treequery import TreePathQuery
from cplib.tools.fastio import FastIO


MOD = 998244353
MASK = (1 << 31) - 1
IDENTITY = 1 << 31


def compose(left: int, right: int) -> int:
    left_a, left_b = left >> 31, left & MASK
    right_a, right_b = right >> 31, right & MASK
    return ((left_a * right_a) % MOD << 31) + (right_a * left_b + right_b) % MOD


N, Q = FastIO.read_ints(2)
initial_values = tuple((a << 31) + b for a, b in (FastIO.read_ints(2) for _ in range(N)))

tree = Tree(N)

for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    tree.add_edge(Node(u), Node(v))

tree.build(Node(0))

path_query = TreePathQuery(tree, initial_values, compose, IDENTITY)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        p, c, d = FastIO.read_ints(3)
        path_query.set(p, (c << 31) + d)
    else:
        u, v, x = FastIO.read_ints(3)
        result = path_query.path_prod(u, v)
        a, b = result >> 31, result & MASK
        FastIO.writeln(f'{(a * x + b) % MOD}')
