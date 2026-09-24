# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/2/ALDS1_2_D

from _educational_sort import shell_sort_count
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = [FastIO.read_int() for _ in range(N)]

B, gaps, count = shell_sort_count(A)
FastIO.writeln(f'{len(gaps)}')
FastIO.writeln(' '.join(map(str, gaps)))
FastIO.writeln(f'{count}')
for value in B:
    FastIO.writeln(f'{value}')
