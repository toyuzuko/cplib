# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/5/ITP1_5_D

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
for i in range(1, n + 1):
    if i % 3 == 0 or '3' in str(i):
        FastIO.write(f' {i}')
FastIO.writeln('')
