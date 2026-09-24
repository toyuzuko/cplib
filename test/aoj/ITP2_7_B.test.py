# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/7/ITP2_7_B

from cplib.datastructure.treap import TreapMultiset
from cplib.tools.fastio import FastIO

Q = FastIO.read_int()
S = TreapMultiset[int]()

for _ in range(Q):
    com = FastIO.read_int()
    x = FastIO.read_int()
    if com == 0:
        if S.count(x) == 0:
            S.add(x)
        FastIO.writeln(f'{S.size()}')
    elif com == 1:
        FastIO.writeln(f'{S.count(x)}')
    else:
        S.discard(x)
