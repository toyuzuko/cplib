# verification-helper: PROBLEM https://judge.yosupo.jp/problem/predecessor_problem

from cplib.tools.fastio import FastIO
from cplib.datastructure.fenwicktree import RangeSetBIT


N, Q = FastIO.read_ints(2)
T = [True if a == '1' else False for a in FastIO.read().strip()]

S = RangeSetBIT(N)
S.build(T)

for _ in range(Q):
    t, k = FastIO.read_ints(2)
    if t == 0:
        S.add(k)
    elif t == 1:
        S.discard(k)
    elif t == 2:
        if k in S:
            FastIO.writeln('1')
        else:
            FastIO.writeln('0')
    elif t == 3:
        succ = S.successor(k)
        FastIO.writeln(f'{succ if succ is not None else -1}')
    else:
        pred = S.predecessor(k)
        FastIO.writeln(f'{pred if pred is not None else -1}')
