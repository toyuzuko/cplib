# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sum_of_exponential_times_polynomial_limit

from cplib.mathematics.polynomial import sum_of_exponential_times_polynomial
from cplib.tools.fastio import FastIO


R, D = FastIO.read_ints(2)

FastIO.writeln(f'{sum_of_exponential_times_polynomial(R, D)}')
