# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/2/ITP1_2_C

from cplib.tools.fastio import FastIO


A = sorted(FastIO.read_ints(3))
FastIO.writeln(' '.join(map(str, A)))
