# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/11/ALDS1_11_D

from cplib.datastructure.dsu import DisjointSetUnion
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
dsu = DisjointSetUnion(N)

for _ in range(M):
    s, t = FastIO.read_ints(2)
    dsu.merge(s, t)

Q = FastIO.read_int()
for _ in range(Q):
    s, t = FastIO.read_ints(2)
    FastIO.writeln('yes' if dsu.same(s, t) else 'no')
