# verification-helper: PROBLEM https://judge.yosupo.jp/problem/chromatic_number

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.graph.counting import chromatic_number
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()
graph = Graph(N)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

FastIO.writeln(f'{chromatic_number(graph)}')
