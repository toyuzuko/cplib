# verification-helper: PROBLEM https://judge.yosupo.jp/problem/binomial_coefficient

from cplib.mathematics.factorial import BinomialCoefficient
from cplib.tools.fastio import FastIO


T, m = FastIO.read_ints(2)

BinomialCoefficient.set_mod(m)
bc = BinomialCoefficient()

for _ in range(T):
    n, k = FastIO.read_ints(2)
    FastIO.writeln(f'{bc.binom(n, k)}')
