# verification-helper: PROBLEM https://judge.yosupo.jp/problem/unionfind

from cplib.datastructure.dsu import DisjointSetUnion
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

dsu = DisjointSetUnion(N)

for _ in range(Q):
    t = FastIO.read_int()
    u = FastIO.read_int()
    v = FastIO.read_int()
    if t == 0:
        dsu.merge(u, v)
    else:
        FastIO.writeln(f'{int(dsu.same(u, v))}')
