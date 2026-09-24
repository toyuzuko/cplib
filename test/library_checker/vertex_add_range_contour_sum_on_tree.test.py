# verification-helper: PROBLEM https://judge.yosupo.jp/problem/vertex_add_range_contour_sum_on_tree

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.treequery import RangeContourSum
from cplib.tools.fastio import FastIO

from operator import add


N, Q = FastIO.read_ints(2)
initial_values = FastIO.read_ints(N)

tree = Tree(N)
for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    tree.add_edge(Node(u), Node(v))
tree.build(Node(0))

range_contour_sum = RangeContourSum(tree, initial_values, add, lambda x: -x, 0)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        p, x = FastIO.read_ints(2)
        range_contour_sum.add(p, x)
    else:
        p, l, r = FastIO.read_ints(3)
        FastIO.writeln(f'{range_contour_sum.aggregate(p, l, r)}')
