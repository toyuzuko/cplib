# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/11/ALDS1_11_A

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
graph = Graph(N, is_directed=True)

for _ in range(N):
    u = FastIO.read_int() - 1
    K = FastIO.read_int()
    for v in FastIO.read_ints(K):
        graph.add_edge(Node(u), Node(v - 1))

for row in graph.adjacency_matrix():
    FastIO.writeln(' '.join(map(str, row)))
