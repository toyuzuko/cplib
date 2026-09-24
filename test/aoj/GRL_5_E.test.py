# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/5/GRL_5_E

from cplib.datastructure.segtree import LazySegmentTree
from cplib.graph import HeavyLightDecomposition, Node, Tree
from cplib.tools.fastio import FastIO


def op(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return a[0] + b[0], a[1] + b[1]


def mapping(f: int, x: tuple[int, int]) -> tuple[int, int]:
    return x[0] + f * x[1], x[1]


def composition(f: int, g: int) -> int:
    return f + g


N = FastIO.read_int()
tree = Tree(N)

for v in range(N):
    K = FastIO.read_int()
    for _ in range(K):
        c = FastIO.read_int()
        tree.add_edge(Node(v), Node(c))

tree.build(Node(0))
hld = HeavyLightDecomposition(tree)
seg = LazySegmentTree[tuple[int, int], int](N, op, (0, 0), mapping, composition, 0)
seg.build([(0, 1)] * N)

Q = FastIO.read_int()
for _ in range(Q):
    query = FastIO.read_int()
    if query == 0:
        v = FastIO.read_int()
        w = FastIO.read_int()
        for l, r in hld.path_ranges(Node(0), Node(v), edge_query=True):
            seg.range_apply(l, r, w)
    else:
        u = FastIO.read_int()
        answer = 0
        for l, r in hld.path_ranges(Node(0), Node(u), edge_query=True):
            answer += seg.prod(l, r)[0]
        FastIO.writeln(f'{answer}')
