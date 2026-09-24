# verification-helper: PROBLEM https://judge.yosupo.jp/problem/segment_add_get_min

from cplib.datastructure.convex import LiChaoTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

initial_segments: list[tuple[int, int, int, int]] = []
queries: list[tuple[int, int, int, int, int]] = []
query_x: list[int] = []

for _ in range(N):
    l, r, a, b = FastIO.read_ints(4)
    initial_segments.append((l, r, a, b))

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, a, b = FastIO.read_ints(4)
        queries.append((0, l, r, a, b))
    else:
        x = FastIO.read_int()
        queries.append((1, x, 0, 0, 0))
        query_x.append(x)

xs = sorted(set(query_x))
li_chao = LiChaoTree(xs)

for l, r, a, b in initial_segments:
    li_chao.add_segment(a, b, l, r)

for op_type, op_l, op_r, op_a, op_b in queries:
    if op_type == 0:
        li_chao.add_segment(op_a, op_b, op_l, op_r)
    else:
        value = li_chao.get_min(op_l)
        FastIO.writeln('INFINITY' if value is None else f'{value}')
