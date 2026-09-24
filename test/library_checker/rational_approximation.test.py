# verification-helper: PROBLEM https://judge.yosupo.jp/problem/rational_approximation

from cplib.mathematics.rational import Rational
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    N = FastIO.read_int()
    x = FastIO.read_int()
    y = FastIO.read_int()
    a = Rational(x, y)
    lower = a.bounded_floor(N)
    upper = a.bounded_ceil(N)
    FastIO.writeln(f'{lower.num} {lower.den} {upper.num} {upper.den}')
