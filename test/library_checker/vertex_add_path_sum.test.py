# verification-helper: PROBLEM https://judge.yosupo.jp/problem/vertex_add_path_sum


from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.treequery import TreePathQuery
from cplib.tools.fastio import FastIO

from operator import add


N, Q = FastIO.read_ints(2)
initial_values = FastIO.read_ints(N)

tree = Tree(N)

for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    tree.add_edge(Node(u), Node(v))

tree.build(Node(0))

path_query = TreePathQuery(tree, initial_values, add, 0)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        p, x = FastIO.read_ints(2)
        path_query.set(p, path_query.get(p) + x)
    else:
        u, v = FastIO.read_ints(2)
        FastIO.writeln(f'{path_query.path_prod(u, v)}')
