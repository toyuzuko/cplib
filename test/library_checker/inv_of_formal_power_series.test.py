# verification-helper: PROBLEM https://judge.yosupo.jp/problem/inv_of_formal_power_series

from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FormalPowerSeriesMod(FastIO.read_ints(N))

FastIO.writeln(f'{~A}')
