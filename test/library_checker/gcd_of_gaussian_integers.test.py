# verification-helper: PROBLEM https://judge.yosupo.jp/problem/gcd_of_gaussian_integers

from cplib.mathematics.arithmetic import GaussianInteger
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    a, b, c, d = FastIO.read_ints(4)
    g = GaussianInteger.gcd(GaussianInteger(a, b), GaussianInteger(c, d))
    FastIO.writeln(f'{g.real} {g.imag}')
