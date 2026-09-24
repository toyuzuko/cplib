# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/8/ITP1_8_D

from cplib.tools.fastio import FastIO


s = FastIO.read()
p = FastIO.read()
FastIO.writeln('Yes' if p in s + s else 'No')
