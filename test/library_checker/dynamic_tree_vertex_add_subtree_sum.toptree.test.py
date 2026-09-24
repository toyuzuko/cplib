# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_add_subtree_sum

from cplib.graph.toptree import TopTree
from cplib.tools.fastio import FastIO

from operator import add

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)
tree = TopTree[int, int, int](A, 0, add, lambda path: path, add, add)

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
        vertex, value = FastIO.read_ints(2)
        tree.set(vertex, tree.get(vertex) + value)
    else:
        vertex, parent = FastIO.read_ints(2)
        FastIO.writeln(f'{tree.subtree_value(vertex, root=parent)}')
