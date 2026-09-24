# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_graph_vertex_add_component_sum

from cplib.graph.connectivity import OfflineDynamicConnectivity
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

dc = OfflineDynamicConnectivity[int, int, int](N, Q, values=A)

for t in range(Q):
    typ = FastIO.read_int()
    if typ == 0:
        u, v = FastIO.read_ints(2)
        dc.insert_edge(u, v, t)
    elif typ == 1:
        u, v = FastIO.read_ints(2)
        dc.erase_edge(u, v, t)
    elif typ == 2:
        v, x = FastIO.read_ints(2)
        dc.set_query_vertex_add(v, x, t)
    else:
        v = FastIO.read_int()
        dc.set_query_component_sum(v, t)

for x in dc.run():
    FastIO.writeln(f'{x}')
