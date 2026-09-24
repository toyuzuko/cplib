# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_tree_path_composite_sum_fixed_root

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.treedp import FixedRootTreeDP
from cplib.tools.fastio import FastIO


MOD = 998244353


def norm(value: int) -> int:
    return value % MOD


def merge(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return norm(left[0] + right[0]), left[1] + right[1]


def inv(value: tuple[int, int]) -> tuple[int, int]:
    return norm(-value[0]), -value[1]


def put_vertex(value: int, _vertex: int) -> tuple[int, int]:
    return norm(value), 1


def put_edge(value: tuple[int, int], edge_value: tuple[int, int], _edge_id: int) -> tuple[int, int]:
    subtree_sum, subtree_size = value
    b, c = edge_value
    return norm(b * subtree_sum + c * subtree_size), subtree_size


def compose(upper: tuple[int, int, int, int], lower: tuple[int, int, int, int],) -> tuple[int, int, int, int]:
    upper_a, upper_b, upper_c, upper_d = upper
    lower_a, lower_b, lower_c, lower_d = lower
    return norm(upper_a * lower_a), norm(upper_a * lower_b + upper_b), norm(upper_a * lower_c + upper_b * lower_d + upper_c), lower_d + upper_d,


def apply(transform: tuple[int, int, int, int], value: tuple[int, int]) -> tuple[int, int]:
    a, b, c, d = transform
    subtree_sum, subtree_size = value
    return norm(a * subtree_sum + b * subtree_size + c), subtree_size + d


def make_transform(_vertex_value: int, light_value: tuple[int, int], _vertex: int, heavy_edge_value: tuple[int, int] | None, _heavy_edge_id: int | None) -> tuple[int, int, int, int]:
    light_sum, light_size = light_value
    if heavy_edge_value is None:
        return 0, 0, light_sum, light_size
    b, c = heavy_edge_value
    return b, c, light_sum, light_size


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
edge_values = [(0, 0)] * (N - 1)

tree = Tree(N)

for edge_id in range(N - 1):
    u, v, b, c = FastIO.read_ints(4)
    edge_values[edge_id] = (b, c)
    tree.add_edge(Node(u), Node(v))

tree.build(Node(0))

structure = FixedRootTreeDP[int, tuple[int, int], tuple[int, int], tuple[int, int, int, int]](
    tree=tree,
    vertex_values=A,
    edge_values=edge_values,
    value_identity=(0, 0),
    merge=merge,
    inv=inv,
    put_vertex=put_vertex,
    put_edge=put_edge,
    transform_identity=(1, 0, 0, 0),
    compose=compose,
    apply=apply,
    make_transform=make_transform,
)

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        vertex, x = FastIO.read_ints(2)
        structure.set_vertex(vertex, x)
    else:
        edge_id, b, c = FastIO.read_ints(3)
        structure.set_edge(edge_id, (b, c))
    FastIO.writeln(f'{structure.tree_value()[0]}')
