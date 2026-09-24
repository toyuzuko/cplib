# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/6/ALDS1_6_A

from cplib.algorithm.sort import counting_sort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

FastIO.writeln(' '.join(map(str, counting_sort(A, max_value=10000))))
