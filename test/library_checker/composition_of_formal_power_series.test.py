# verification-helper: PROBLEM https://judge.yosupo.jp/problem/composition_of_formal_power_series

from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
F = FormalPowerSeriesMod(FastIO.read_ints(N))
G = FormalPowerSeriesMod(FastIO.read_ints(N))

H = F.compose(G)

FastIO.writeln(' '.join(map(str, H.coef)))