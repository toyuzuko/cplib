# verification-helper: PROBLEM https://judge.yosupo.jp/problem/rooted_tree_topological_order_with_minimum_inversions

from cplib.graph import Tree, Node
from cplib.graph.scheduling import optimal_scheduling_on_tree
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

tree = Tree(N)

for i in range(1, N):
    p = FastIO.read_int()
    tree.add_edge(Node(p), Node(i))

tree.build(Node(0))

weight = list(FastIO.read_ints(N))
proc_time = list(FastIO.read_ints(N))

x, perm = optimal_scheduling_on_tree(tree, proc_time, weight)

FastIO.writeln(f'{x}')
FastIO.writeln(' '.join(map(str, perm)))