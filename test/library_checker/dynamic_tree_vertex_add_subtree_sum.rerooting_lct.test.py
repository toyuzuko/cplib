# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_add_subtree_sum

from cplib.graph.linkcut import RerootingLinkCutTreeWithEdges
from cplib.tools.fastio import FastIO

from operator import add

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)
tree = RerootingLinkCutTreeWithEdges[int, int, int](N, 0, add, lambda x: x, add, lambda x: -x, add)
for v, value in enumerate(A):
    tree.set_vertex(v, value)

edge_ids: dict[tuple[int, int], int] = {}
for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    edge_ids[min(u, v), max(u, v)] = tree.add_edge(u, v, 0)
tree.build()

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, w, x = FastIO.read_ints(4)
        edge_id = edge_ids.pop((min(u, v), max(u, v)))
        tree.cut_edge(edge_id)
        tree.link_edge(edge_id, w, x)
        edge_ids[min(w, x), max(w, x)] = edge_id
    elif t == 1:
        v, value = FastIO.read_ints(2)
        tree.set_vertex(v, tree.get_vertex(v) + value)
    else:
        v, p = FastIO.read_ints(2)
        FastIO.writeln(f'{tree.subtree_value(v, root=p)}')
