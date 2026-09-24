# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/1/NTL_1_E

from math import gcd

from cplib.mathematics.arithmetic import linear_indeterminate_equation_min_abs_sum
from cplib.tools.fastio import FastIO


a, b = FastIO.read_ints(2)
_, x, y = linear_indeterminate_equation_min_abs_sum(a, b, gcd(a, b))

FastIO.writeln(f'{x} {y}')
