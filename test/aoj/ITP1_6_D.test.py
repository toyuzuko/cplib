# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/6/ITP1_6_D

from cplib.tools.fastio import FastIO


n, m = FastIO.read_ints(2)
A = [FastIO.read_ints(m) for _ in range(n)]
b = FastIO.read_ints(m)

for row in A:
    FastIO.writeln(f'{sum(a * x for a, x in zip(row, b))}')
