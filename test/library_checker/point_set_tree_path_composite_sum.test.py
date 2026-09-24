# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_tree_path_composite_sum

from cplib.graph.linkcut import RerootingLinkCutTreeWithEdges
from cplib.tools.fastio import FastIO


MOD = 998244353
# Residues fit in 30 bits, so each packed word is below 2**60.
# Point: (sum << 30) | size; Path: ((a << 30) | b, Point).
# Payload: ~value for vertices, (b << 30) | c for edges.
SHIFT = 30
MASK = (1 << SHIFT) - 1


def add_vertex(point: int, info: int) -> tuple[int, int]:
    point_sum, point_size = point >> SHIFT, point & MASK
    if info < 0:
        return 1 << SHIFT, ((point_sum + ~info) % MOD << SHIFT) | ((point_size + 1) % MOD)
    a, b = info >> SHIFT, info & MASK
    return info, ((a * point_sum + b * point_size) % MOD << SHIFT) | point_size


def add_edge(path: tuple[int, int]) -> int:
    return path[1]


def rake(left: int, right: int) -> int:
    return (((left >> SHIFT) + (right >> SHIFT)) % MOD << SHIFT) | (((left & MASK) + (right & MASK)) % MOD)


def point_inv(point: int) -> int:
    return (-(point >> SHIFT) % MOD << SHIFT) | (-(point & MASK) % MOD)


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

tree = RerootingLinkCutTreeWithEdges[int, int, tuple[int, int]](N, 0, add_vertex, add_edge, rake, point_inv, compress)

for vertex in range(N):
    value = FastIO.read_int()
    tree.set_vertex(vertex, ~value)

for _ in range(N - 1):
    u, v, b, c = FastIO.read_ints(4)
    tree.add_edge(u, v, (b << SHIFT) | c)

tree.build()

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        vertex, value = FastIO.read_ints(2)
        tree.set_vertex(vertex, ~value)
    else:
        edge_id, b, c = FastIO.read_ints(3)
        tree.set_edge(edge_id, (b << SHIFT) | c)
    root = FastIO.read_int()
    FastIO.writeln(f'{tree.tree_value(root)[1] >> SHIFT}')
