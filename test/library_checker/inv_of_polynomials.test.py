# verification-helper: PROBLEM https://judge.yosupo.jp/problem/inv_of_polynomials

from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()
F = FormalPowerSeriesMod(FastIO.read_ints(N))
G = FormalPowerSeriesMod(FastIO.read_ints(M))

H = F.inv_mod_poly(G)

if H is None:
    FastIO.writeln('-1')
else:
    FastIO.writeln(f'{len(H)}')
    FastIO.writeln(' '.join(map(str, H.coef)))
