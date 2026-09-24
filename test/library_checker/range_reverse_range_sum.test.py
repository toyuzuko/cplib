# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_reverse_range_sum

from cplib.datastructure.treap import ImplicitTreap
from cplib.tools.fastio import FastIO

from operator import add


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

seq = ImplicitTreap(add, 0, lambda f, value: value, lambda f, g: 0, 0, commutative=True)
seq.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r = FastIO.read_ints(2)
        seq.reverse(l, r)
    else:
        l, r = FastIO.read_ints(2)
        ret = seq.prod(l, r)
        FastIO.writeln(f'{ret}')