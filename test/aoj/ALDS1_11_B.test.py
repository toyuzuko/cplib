# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/11/ALDS1_11_B

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.graph.walk import depth_first_search
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
graph = Graph(N, is_directed=True)

for _ in range(N):
    u = FastIO.read_int() - 1
    k = FastIO.read_int()
    for v in FastIO.read_ints(k):
        graph.add_edge(Node(u), Node(v - 1))

res = depth_first_search(graph)

for v in range(N):
    FastIO.writeln(f'{v + 1} {res.discovery[v]} {res.finish[v]}')
