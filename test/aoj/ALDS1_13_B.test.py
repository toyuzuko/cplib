# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/13/ALDS1_13_B

from cplib.algorithm.search import sliding_puzzle_distance
from cplib.tools.fastio import FastIO


A = FastIO.read_ints(9)
FastIO.writeln(f'{sliding_puzzle_distance(A, 3, 3)}')
