# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/4/ITP2_4_D

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)
unique: list[int] = []

for x in A:
    if not unique or unique[-1] != x:
        unique.append(x)

FastIO.writeln(' '.join(map(str, unique)))
