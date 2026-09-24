# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_add_subtree_sum

from cplib.graph.connectivity import OfflineDynamicConnectivity
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

dc = OfflineDynamicConnectivity[int, int, int](N, 2 * Q, values=A)

for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    dc.insert_edge(u, v, 0)

cur_time = 1

for i in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, w, x = FastIO.read_ints(4)
        dc.erase_edge(u, v, cur_time)
        dc.insert_edge(w, x, cur_time)
        cur_time += 1
    elif t == 1:
        p, x = FastIO.read_ints(2)
        dc.set_query_vertex_add(p, x, cur_time)
        cur_time += 1
    else:
        v, p = FastIO.read_ints(2)
        dc.erase_edge(v, p, cur_time)
        dc.set_query_component_sum(v, cur_time)
        dc.insert_edge(v, p, cur_time + 1)
        cur_time += 2

res = dc.run()

for r in res:
    FastIO.writeln(f'{r}')
