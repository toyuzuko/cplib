# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dominatortree

from cplib.tools.fastio import FastIO
from cplib.graph import Graph, Node, dominator_tree


N, M, S = FastIO.read_ints(3)

graph = Graph(N, is_directed=True)

for _ in range(M):
    a, b = FastIO.read_ints(2)
    graph.add_edge(Node(a), Node(b))

par = dominator_tree(graph, Node(S))

FastIO.writeln(' '.join(map(str, par)))
