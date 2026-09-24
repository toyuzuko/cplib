# verification-helper: PROBLEM https://judge.yosupo.jp/problem/line_add_get_min

from cplib.datastructure.convex import LiChaoTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

A: list[int] = []
B: list[int] = []

for _ in range(N):
    a, b = FastIO.read_ints(2)
    A.append(a)
    B.append(b)

queries: list[tuple[int, int, int]] = []
query_x: list[int] = []

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        a, b = FastIO.read_ints(2)
        queries.append((0, a, b))
    else:
        x = FastIO.read_int()
        queries.append((1, x, 0))
        query_x.append(x)

xs = sorted(set(query_x))

li_chao = LiChaoTree(xs)

for i in range(N):
    li_chao.add_line(A[i], B[i])

for i in range(Q):
    op_type, op_a, op_b = queries[i]
    if op_type == 0:
        li_chao.add_line(op_a, op_b)
    else:
        value = li_chao.get_min(op_a)
        FastIO.writeln('INFINITY' if value is None else f'{value}')
