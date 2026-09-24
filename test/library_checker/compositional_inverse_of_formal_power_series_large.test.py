# verification-helper: PROBLEM https://judge.yosupo.jp/problem/compositional_inverse_of_formal_power_series_large

from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
F = FormalPowerSeriesMod(FastIO.read_ints(N))

G = F.compositional_inverse()

FastIO.writeln(' '.join(map(str, G.coef)))
