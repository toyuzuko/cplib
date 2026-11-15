# verification-helper: PROBLEM https://judge.yosupo.jp/problem/min_plus_convolution_convex_arbitrary

from cplib.algorithm import monotone_minima
from cplib.tools.fastio import FastIO


n, m = FastIO.read_ints(2)
a = FastIO.read_ints(n)
b = FastIO.read_ints(m)

# The valid interval of j moves right with k. Convexity of a implies
# that the leftmost minimizing j is nondecreasing. For this judge, all
# valid sums are <= 2e9 and each row has a valid entry.
def value(k: int, j: int) -> int:
    i = k - j
    return a[i] + b[j] if 0 <= i < n else 1 << 60


argmin = monotone_minima(n + m - 1, m, value)
FastIO.writeln(' '.join(f'{a[k - j] + b[j]}' for k, j in enumerate(argmin)))
