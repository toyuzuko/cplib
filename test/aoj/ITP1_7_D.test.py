# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/7/ITP1_7_D

from cplib.tools.fastio import FastIO


n, m, l = FastIO.read_ints(3)
A = [FastIO.read_ints(m) for _ in range(n)]
B = [FastIO.read_ints(l) for _ in range(m)]

for i in range(n):
    row: list[int] = []
    for j in range(l):
        row.append(sum(A[i][k] * B[k][j] for k in range(m)))
    FastIO.writeln(' '.join(map(str, row)))
