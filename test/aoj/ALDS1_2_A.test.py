# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/2/ALDS1_2_A

from _educational_sort import bubble_sort_count
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

B, count = bubble_sort_count(A)
FastIO.writeln(' '.join(map(str, B)))
FastIO.writeln(f'{count}')
