# verification-helper: PROBLEM https://judge.yosupo.jp/problem/double_ended_priority_queue

from cplib.datastructure.fenwicktree import SortedMultisetBIT
from cplib.tools.fastio import FastIO

from collections import Counter

N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
queries: list[tuple[int, int]] = []
values = set(A)
for _ in range(Q):
    t = FastIO.read_int()
    x = FastIO.read_int() if t == 0 else 0
    queries.append((t, x))
    if t == 0:
        values.add(x)

S = SortedMultisetBIT(sorted(values))
for x, count in Counter(A).items():
    S.add(x, count=count)

for t, x in queries:
    if t == 0:
        S.add(x)
    else:
        x = S[0 if t == 1 else len(S) - 1]
        S.remove(x, validity_check=False)
        FastIO.writeln(f'{x}')
