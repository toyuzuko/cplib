# verification-helper: PROBLEM https://judge.yosupo.jp/problem/min_cost_b_flow

from cplib.graph.flow import Node, Capacity, Cost, MinimumCostBFlow
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)

flow_solver = MinimumCostBFlow(N)

for i in range(N):
    b = FastIO.read_int()
    flow_solver.add_excess(Node(i), Capacity(b))

for i in range(M):
    s, t, l, u, c = FastIO.read_ints(5)
    flow_solver.add_edge(Node(s), Node(t), Capacity(l), Capacity(u), Cost(c))

result = flow_solver.solve()

if result.feasible:
    FastIO.writeln(f'{result.cost}')
    p = flow_solver.dual
    if p:
        FastIO.writeln('\n'.join(map(str, p)))
    f = [edge.flow for edge in result.edges]
    if f:
        FastIO.writeln('\n'.join(map(str, f)))

else:
    FastIO.writeln('infeasible')
