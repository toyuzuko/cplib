# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/1/ALDS1_1_A

from _educational_sort import insertion_sort_states
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

for state in insertion_sort_states(A):
    FastIO.writeln(' '.join(map(str, state)))
