# verification-helper: PROBLEM https://judge.yosupo.jp/problem/staticrmq

from cplib.datastructure.sparsetable import DisjointSparseTable
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

st = DisjointSparseTable(A, min)

for _ in range(Q):
    l, r = FastIO.read_ints(2)
    FastIO.writeln(f'{st.prod(l, r)}')
