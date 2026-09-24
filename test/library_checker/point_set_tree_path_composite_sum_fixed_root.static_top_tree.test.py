# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_tree_path_composite_sum_fixed_root

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.toptree import StaticTopTreeWithEdges
from cplib.tools.fastio import FastIO


MOD = 998244353


def norm(value: int) -> int:
    return value % MOD


def vertex_cluster(point: tuple[int, int], value: int) -> tuple[int, int, int, int]:
    return 1, 0, norm(point[0] + value), point[1] + 1


def edge_cluster(point: tuple[int, int], value: tuple[int, int]) -> tuple[int, int, int, int]:
    b, c = value
    return b, c, norm(b * point[0] + c * point[1]), point[1]


def add_edge(path: tuple[int, int, int, int]) -> tuple[int, int]:
    return path[2], path[3]


def compress(upper: tuple[int, int, int, int], lower: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    upper_a, upper_b, upper_c, upper_d = upper
    lower_a, lower_b, lower_c, lower_d = lower
    return norm(upper_a * lower_a), norm(upper_a * lower_b + upper_b), norm(upper_a * lower_c + upper_b * lower_d + upper_c), upper_d + lower_d


def rake(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return norm(left[0] + right[0]), left[1] + right[1]


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
edge_values = [(0, 0)] * (N - 1)

tree = Tree(N)

for edge_id in range(N - 1):
    u, v, b, c = FastIO.read_ints(4)
    edge_values[edge_id] = (b, c)
    tree.add_edge(Node(u), Node(v))

tree.build(Node(0))

structure = StaticTopTreeWithEdges[int, tuple[int, int], tuple[int, int], tuple[int, int, int, int]](
    tree=tree,
    vertex_values=A,
    edge_values=edge_values,
    point_identity=(0, 0),
    vertex_cluster=vertex_cluster,
    edge_cluster=edge_cluster,
    add_edge=add_edge,
    compress=compress,
    rake=rake,
)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        vertex_id, value = FastIO.read_ints(2)
        structure.set_vertex(vertex_id, value)
    else:
        edge_id, b, c = FastIO.read_ints(3)
        structure.set_edge(edge_id, (b, c))
    FastIO.writeln(f'{structure.tree_value()[2]}')
