# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sum_of_exponential_times_polynomial

from cplib.mathematics.polynomial import sum_of_exponential_times_polynomial
from cplib.tools.fastio import FastIO


R, D, N = FastIO.read_ints(3)

FastIO.writeln(f'{sum_of_exponential_times_polynomial(R, D, N)}')
