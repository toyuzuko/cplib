# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_add_rectangle_sum

from cplib.datastructure.range2d import PointAddRectangleSum
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

X: list[int] = []
Y: list[int] = []
W: list[int] = []

all_x: list[int] = []
all_y: list[int] = []

for _ in range(N):
    x, y, w = FastIO.read_ints(3)
    X.append(x)
    Y.append(y)
    W.append(w)
    all_x.append(x)
    all_y.append(y)

query_types: list[int] = []
queries: list[tuple[int, int, int, int]] = []

for _ in range(Q):
    query_type = FastIO.read_int()
    query_types.append(query_type)
    if query_type == 0:
        x, y, w = FastIO.read_ints(3)
        queries.append((x, y, w, 0))
        all_x.append(x)
        all_y.append(y)
    else:
        left, down, right, up = FastIO.read_ints(4)
        queries.append((left, down, right, up))

ds = PointAddRectangleSum(zip(all_x, all_y))
answers: list[str] = []

for i in range(N):
    ds.add_point(X[i], Y[i], W[i])

for i in range(Q):
    if query_types[i] == 0:
        x, y, w, _ = queries[i]
        ds.add_point(x, y, w)
    else:
        l, d, r, u = queries[i]
        answers.append(f"{ds.rectangle_sum(l, d, r, u)}\n")

FastIO.writeln(''.join(answers))
