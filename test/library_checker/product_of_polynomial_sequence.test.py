# verification-helper: PROBLEM https://judge.yosupo.jp/problem/product_of_polynomial_sequence

from cplib.mathematics.polynomial import FormalPowerSeriesMod, polynomial_product
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

polys: list[FormalPowerSeriesMod] = []

for _ in range(N):
    d = FastIO.read_int()
    a = FastIO.read_ints(d + 1)
    polys.append(FormalPowerSeriesMod(a))

FastIO.writeln(f'{polynomial_product(polys)}')
