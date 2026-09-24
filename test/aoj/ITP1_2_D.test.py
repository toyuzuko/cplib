# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/2/ITP1_2_D

from cplib.tools.fastio import FastIO


W, H, x, y, r = FastIO.read_ints(5)
FastIO.writeln('Yes' if r <= x <= W - r and r <= y <= H - r else 'No')
