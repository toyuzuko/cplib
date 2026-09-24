# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/6/GRL_6_A

from cplib.graph.flow import MaximumFlow, Node, Capacity
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)

solver = MaximumFlow(V)

for _ in range(E):
    u, v, c = FastIO.read_ints(3)
    solver.add_edge(Node(u), Node(v), Capacity(c))

result = solver.solve(Node(0), Node(V - 1))
FastIO.writeln(f'{result.flow}')
