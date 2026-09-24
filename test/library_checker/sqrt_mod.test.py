# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sqrt_mod

from cplib.mathematics.modular import sqrt_mod
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    y, p = FastIO.read_ints(2)
    result = sqrt_mod(y, p)
    FastIO.writeln(f'{result}')