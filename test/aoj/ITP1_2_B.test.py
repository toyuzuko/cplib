# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/2/ITP1_2_B

from cplib.tools.fastio import FastIO


a, b, c = FastIO.read_ints(3)
FastIO.writeln('Yes' if a < b < c else 'No')
