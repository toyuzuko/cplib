# verification-helper: PROBLEM https://judge.yosupo.jp/problem/rectangle_add_point_get

from cplib.datastructure.range2d import RectangleAddPointGet
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

rectangles: list[tuple[int, int, int, int, int]] = []
query_types: list[int] = []
queries: list[tuple[int, int, int, int, int]] = []
all_left: list[int] = []
all_down: list[int] = []
all_right: list[int] = []
all_up: list[int] = []

for _ in range(N):
    left, down, right, up, weight = FastIO.read_ints(5)
    rectangles.append((left, down, right, up, weight))
    all_left.append(left)
    all_down.append(down)
    all_right.append(right)
    all_up.append(up)

for _ in range(Q):
    query_type = FastIO.read_int()
    query_types.append(query_type)
    if query_type == 0:
        left, down, right, up, weight = FastIO.read_ints(5)
        queries.append((left, down, right, up, weight))
        all_left.append(left)
        all_down.append(down)
        all_right.append(right)
        all_up.append(up)
    else:
        x, y = FastIO.read_ints(2)
        queries.append((x, y, 0, 0, 0))

ds = RectangleAddPointGet(zip(all_left, all_down, all_right, all_up))
answers: list[str] = []

for i in range(N):
    l, d, r, u, w = rectangles[i]
    ds.add_rectangle(l, d, r, u, w)

for i in range(Q):
    if query_types[i] == 0:
        l, d, r, u, w = queries[i]
        ds.add_rectangle(l, d, r, u, w)
    else:
        x, y = queries[i][:2]
        answers.append(f'{ds.point_get(x, y)}\n')
FastIO.writeln(''.join(answers))
