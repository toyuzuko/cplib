# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_graph_vertex_add_component_sum

from cplib.graph.connectivity import OnlineDynamicConnectivity
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

dc = OnlineDynamicConnectivity[int](N, 0, lambda x, y: x + y, A)

for _ in range(Q):
    typ = FastIO.read_int()
    if typ == 0:
        u, v = FastIO.read_ints(2)
        dc.insert_edge(u, v)
    elif typ == 1:
        u, v = FastIO.read_ints(2)
        dc.erase_edge(u, v)
    elif typ == 2:
        v, x = FastIO.read_ints(2)
        dc.set(v, dc.get(v) + x)
    else:
        v = FastIO.read_int()
        FastIO.writeln(f'{dc.component_aggregate(v)}')
