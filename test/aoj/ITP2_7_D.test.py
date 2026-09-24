# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/7/ITP2_7_D

from cplib.datastructure.treap import TreapMultiset
from cplib.tools.fastio import FastIO

Q = FastIO.read_int()
S = TreapMultiset[int]()

for _ in range(Q):
    com = FastIO.read_int()
    if com == 3:
        L = FastIO.read_int()
        R = FastIO.read_int()
        for x in S.iter_range(L, R):
            FastIO.writeln(f'{x}')
    else:
        x = FastIO.read_int()
        if com == 0:
            S.add(x)
            FastIO.writeln(f'{S.size()}')
        elif com == 1:
            FastIO.writeln(f'{S.count(x)}')
        else:
            S.discard(x, S.count(x))
