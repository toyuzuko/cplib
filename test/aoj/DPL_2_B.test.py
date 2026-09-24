# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/2/DPL_2_B

from cplib.graph import Graph, Node, Weight, undirected_chinese_postman_problem
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V)

for _ in range(E):
    s, t, d = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(d))

FastIO.writeln(f'{undirected_chinese_postman_problem(graph)}')
