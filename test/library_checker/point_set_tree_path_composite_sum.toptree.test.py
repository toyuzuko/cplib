# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_tree_path_composite_sum

from cplib.graph.toptree import TopTreeWithEdges
from cplib.tools.fastio import FastIO


MOD = 998244353
# Each residue fits in 30 bits; packed words stay below 2**60.
# Point: (sum << 30) | size; Path: ((a << 30) | b, Point).
SHIFT = 30
MASK = (1 << SHIFT) - 1


def vertex_cluster(point: int, value: int) -> tuple[int, int]:
    return 1 << SHIFT, (((point >> SHIFT) + value) % MOD << SHIFT) | ((point & MASK) + 1)


def edge_cluster(point: int, value: int) -> tuple[int, int]:
    b, c = value >> SHIFT, value & MASK
    point_sum, point_size = point >> SHIFT, point & MASK
    return value, ((b * point_sum + c * point_size) % MOD << SHIFT) | point_size


def add_edge(path: tuple[int, int]) -> int:
    return path[1]


def rake(left: int, right: int) -> int:
    return (((left >> SHIFT) + (right >> SHIFT)) % MOD << SHIFT) | (((left & MASK) + (right & MASK)) % MOD)


def compress(parent: tuple[int, int], child: tuple[int, int]) -> tuple[int, int]:
    parent_ab, parent_sx = parent
    child_ab, child_sx = child
    parent_a, parent_b = parent_ab >> SHIFT, parent_ab & MASK
    child_a, child_b = child_ab >> SHIFT, child_ab & MASK
    child_s, child_x = child_sx >> SHIFT, child_sx & MASK
    ab = (parent_a * child_a % MOD << SHIFT) | ((parent_a * child_b + parent_b) % MOD)
    sx = (((parent_sx >> SHIFT) + parent_a * child_s + parent_b * child_x) % MOD << SHIFT) | (((parent_sx & MASK) + child_x) % MOD)
    return ab, sx


N, Q = FastIO.read_ints(2)

values = list(FastIO.read_ints(N))
edges: list[tuple[int, int]] = []
edge_values: list[int] = []
for _ in range(N - 1):
    u, v, b, c = FastIO.read_ints(4)
    edges.append((u, v))
    edge_values.append((b << SHIFT) | c)

tree = TopTreeWithEdges[int, int, int, tuple[int, int]](values, edges, edge_values, 0, vertex_cluster, edge_cluster, add_edge, rake, compress)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        vertex, value = FastIO.read_ints(2)
        tree.set_vertex(vertex, value)
    else:
        edge_id, b, c = FastIO.read_ints(3)
        tree.set_edge(edge_id, (b << SHIFT) | c)
    root = FastIO.read_int()
    FastIO.writeln(f'{tree.tree_value(root)[1] >> SHIFT}')
