# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/5/ALDS1_5_B

from _educational_sort import merge_sort_count
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

B, count = merge_sort_count(A)
FastIO.writeln(' '.join(map(str, B)))
FastIO.writeln(f'{count}')
