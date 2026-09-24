# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/2/DPL_2_A

from cplib.graph import Graph, Node, Weight
from cplib.graph import traveling_salesman_problem
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V, is_directed=True)
for _ in range(E):
    s, t, d = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(d))

try:
    result = traveling_salesman_problem(graph)
    FastIO.writeln(f'{result.weight}')
except ValueError:
    FastIO.writeln('-1')
