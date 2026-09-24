# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/14/ALDS1_14_B

from cplib.string.matching import knuth_morris_pratt
from cplib.tools.fastio import FastIO


T = FastIO.read()
P = FastIO.read()

for i in knuth_morris_pratt(T, P):
    FastIO.writeln(f'{i}')
