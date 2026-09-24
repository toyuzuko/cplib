# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/6/GRL_6_B

from cplib.graph.flow import MinimumCostBFlow, Node, Capacity, Cost
from cplib.tools.fastio import FastIO

V, E, F = FastIO.read_ints(3)

solver = MinimumCostBFlow(V)

for _ in range(E):
    u, v, c, d = FastIO.read_ints(4)
    solver.add_edge(Node(u), Node(v), Capacity(0), Capacity(c), Cost(d))

solver.add_excess(Node(0), Capacity(F))
solver.add_excess(Node(V - 1), Capacity(-F))

result = solver.solve()

if result.feasible:
    FastIO.writeln(f'{result.cost}')
else:
    FastIO.writeln('-1')
