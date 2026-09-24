# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_add_subtree_sum

from cplib.graph.toptree import TopTreeWithEdges
from cplib.tools.fastio import FastIO

from operator import add

N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
edges = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N - 1)]
edge_ids = {(min(u, v), max(u, v)): edge_id for edge_id, (u, v) in enumerate(edges)}
tree = TopTreeWithEdges(A, edges, [0] * (N - 1), 0, add, add, lambda path: path, add, add)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, child, parent = FastIO.read_ints(4)
        edge_id = edge_ids.pop((min(u, v), max(u, v)))
        tree.cut_edge(edge_id)
        tree.link_edge(edge_id, child, parent)
        edge_ids[min(child, parent), max(child, parent)] = edge_id
    elif t == 1:
        vertex, value = FastIO.read_ints(2)
        tree.set_vertex(vertex, tree.get_vertex(vertex) + value)
    else:
        vertex, parent = FastIO.read_ints(2)
        FastIO.writeln(f'{tree.subtree_value(vertex, root=parent)}')
