# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_rectangle_add_rectangle_sum

from cplib.datastructure.range2d import static_rectangle_add_rectangle_sum
from cplib.tools.fastio import FastIO


MOD = 998244353

N, Q = FastIO.read_ints(2)

rectangles: list[tuple[int, int, int, int, int]] = []

for _ in range(N):
    x1, y1, x2, y2, v = FastIO.read_ints(5)
    rectangles.append((x1, y1, x2, y2, v))

queries: list[tuple[int, int, int, int]] = []

for _ in range(Q):
    x1, y1, x2, y2 = FastIO.read_ints(4)
    queries.append((x1, y1, x2, y2))

answers = static_rectangle_add_rectangle_sum(rectangles, queries, MOD)
for answer in answers:
    FastIO.writeln(f'{answer}')
