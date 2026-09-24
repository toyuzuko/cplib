# verification-helper: PROBLEM https://judge.yosupo.jp/problem/chromatic_polynomial

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.graph.counting import chromatic_polynomial
from cplib.tools.fastio import FastIO


MOD = 998244353

N = FastIO.read_int()
M = FastIO.read_int()
graph = Graph(N)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

FastIO.writeln(' '.join(map(str, chromatic_polynomial(graph, MOD).coef)))
