# verification-helper: PROBLEM https://judge.yosupo.jp/problem/ordered_set

from cplib.datastructure.treap import TreapMultiset
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

S = TreapMultiset[int]()
S.build(list(A), is_sorted=True)

for _ in range(Q):
    t, x = FastIO.read_ints(2)
    if t == 0:
        if not S.contains(x):
            S.add(x)
    elif t == 1:
        S.discard(x)
    elif t == 2:
        if 1 <= x <= S.size():
            FastIO.writeln(f'{S.get(x - 1)}')
        else:
            FastIO.writeln('-1')
    elif t == 3:
        FastIO.writeln(f'{S.bisect_right(x)}')
    elif t == 4:
        value = S.predecessor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
    elif t == 5:
        value = S.successor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
