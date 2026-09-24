# verification-helper: PROBLEM https://judge.yosupo.jp/problem/double_ended_priority_queue

from cplib.datastructure.treap import TreapMultiset
from cplib.tools.fastio import FastIO

N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
S = TreapMultiset[int]()
S.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        S.add(FastIO.read_int())
    else:
        x = S.get(0 if t == 1 else S.size() - 1)
        S.remove(x, validity_check=False)
        FastIO.writeln(f'{x}')
