# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sum_of_floor_of_linear

from cplib.mathematics.utility import floor_sum
from cplib.tools.fastio import FastIO


T = FastIO.read_int()
for _ in range(T):
    n = FastIO.read_int()
    m = FastIO.read_int()
    a = FastIO.read_int()
    b = FastIO.read_int()
    FastIO.writeln(str(floor_sum(n, m, a, b)))
