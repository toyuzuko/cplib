# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_point_set_rectangle_affine_rectangle_sum

from cplib.datastructure.range2d import LazyKDTree2D
from cplib.tools.fastio import FastIO


MOD = 998244353


def op(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return ((left[0] + right[0]) % MOD, left[1] + right[1])


def mapping_prod(lazy_value: tuple[int, int], prod: tuple[int, int], count: int) -> tuple[int, int]:
    a, b = lazy_value
    total, active = prod
    return ((a * total + b * active) % MOD, active)


def mapping_value(lazy_value: tuple[int, int], value: tuple[int, int]) -> tuple[int, int]:
    a, b = lazy_value
    total, active = value
    return ((a * total + b * active) % MOD, active)


def composition(f: tuple[int, int], g: tuple[int, int]) -> tuple[int, int]:
    af, bf = f
    ag, bg = g
    return (af * ag % MOD, (af * bg + bf) % MOD)


N, Q = FastIO.read_ints(2)

points: list[tuple[int, int]] = []
values: list[tuple[int, int]] = []
queries: list[tuple[int, ...]] = []

for _ in range(N):
    x, y, w = FastIO.read_ints(3)
    points.append((x, y))
    values.append((w, 1))

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        x, y, w = FastIO.read_ints(3)
        queries.append((0, len(points), w))
        points.append((x, y))
        values.append((0, 0))
    elif query_type == 1:
        p, w = FastIO.read_ints(2)
        queries.append((1, p, w))
    elif query_type == 2:
        left, down, right, up = FastIO.read_ints(4)
        queries.append((2, left, down, right, up))
    else:
        left, down, right, up, a, b = FastIO.read_ints(6)
        queries.append((3, left, down, right, up, a, b))

tree = LazyKDTree2D(points, values, op, (0, 0), mapping_prod, mapping_value, composition, (1, 0))

for query in queries:
    query_type = query[0]
    if query_type == 0:
        point_id, w = query[1:]
        tree.set(point_id, (w, 1))
    elif query_type == 1:
        point_id, w = query[1:]
        tree.set(point_id, (w, 1))
    elif query_type == 2:
        left, down, right, up = query[1:]
        FastIO.writeln(f'{tree.rectangle_prod(left, down, right, up)[0]}')
    else:
        left, down, right, up, a, b = query[1:]
        tree.rectangle_apply(left, down, right, up, (a, b))
