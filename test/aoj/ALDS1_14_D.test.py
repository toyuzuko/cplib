# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/14/ALDS1_14_D

from cplib.string.suffix import CompactSuffixAutomaton
from cplib.tools.fastio import FastIO


T = FastIO.read()
Q = FastIO.read_int()

sam = CompactSuffixAutomaton(T)
for _ in range(Q):
    FastIO.writeln('1' if sam.contains(FastIO.read()) else '0')
