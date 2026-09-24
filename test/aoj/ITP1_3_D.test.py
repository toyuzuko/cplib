# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/3/ITP1_3_D

from cplib.tools.fastio import FastIO


a, b, c = FastIO.read_ints(3)
ans = 0
for x in range(a, b + 1):
    if c % x == 0:
        ans += 1
FastIO.writeln(f'{ans}')
