# verification-helper: PROBLEM https://judge.yosupo.jp/problem/ordered_set

from cplib.tools.fastio import FastIO
from cplib.datastructure.fenwicktree import SortedSetBIT

from bisect import bisect_left


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N) # sorted and unique

T: list[int] = []
X: list[int] = []

for _ in range(Q):
    t, x = FastIO.read_ints(2)
    T.append(t)
    X.append(x)

sorted_x = sorted(X)
sorted_x = [x for i, x in enumerate(sorted_x) if i == 0 or x != sorted_x[i - 1]]

# merge A and sorted_x

sorted_ax: list[int] = []

i, j = 0, 0
while i < N and j < len(sorted_x):
    if A[i] < sorted_x[j]:
        if not sorted_ax or sorted_ax[-1] != A[i]:
            sorted_ax.append(A[i])
        i += 1
    else:
        if not sorted_ax or sorted_ax[-1] != sorted_x[j]:
            sorted_ax.append(sorted_x[j])
        j += 1

while i < N:
    if not sorted_ax or sorted_ax[-1] != A[i]:
        sorted_ax.append(A[i])
    i += 1

while j < len(sorted_x):
    if not sorted_ax or sorted_ax[-1] != sorted_x[j]:
        sorted_ax.append(sorted_x[j])
    j += 1

init_set = [False] * len(sorted_ax)

for a in A:
    init_set[bisect_left(sorted_ax, a)] = True

S = SortedSetBIT(sorted_ax)
S.build(init_set)

for t, x in zip(T, X):
    if t == 0:
        S.add(x)
    elif t == 1:
        S.discard(x)
    elif t == 2:
        try:
            FastIO.writeln(str(S[x - 1]))
        except IndexError:
            FastIO.writeln('-1')
    elif t == 3:
        FastIO.writeln(f'{S.bisect_right(x)}')
    elif t == 4:
        value = S.predecessor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
    elif t == 5:
        value = S.successor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
