# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/9/ALDS1_9_D

from cplib.datastructure.queue import worst_case_heap_for_heapsort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

FastIO.writeln(' '.join(map(str, worst_case_heap_for_heapsort(A))))
