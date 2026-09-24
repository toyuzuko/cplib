# verification-helper: PROBLEM https://judge.yosupo.jp/problem/polynomial_root_finding

from cplib.mathematics.polynomial import FormalPowerSeriesMod, polynomial_roots
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
F = FormalPowerSeriesMod(FastIO.read_ints(N + 1))

roots = polynomial_roots(F)

FastIO.writeln(f'{len(roots)}')
FastIO.writeln(' '.join(map(str, roots)))
