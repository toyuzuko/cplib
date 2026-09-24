# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/9/ALDS1_9_B

from cplib.datastructure.queue import heapify
from cplib.tools.fastio import FastIO


H = FastIO.read_int()
A = FastIO.read_ints(H)

FastIO.writeln(' ' + ' '.join(map(str, heapify(A, ascending=False))))
