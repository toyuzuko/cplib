# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/6/ITP1_6_C

from cplib.tools.fastio import FastIO


rooms = [[[0] * 10 for _ in range(3)] for _ in range(4)]
n = FastIO.read_int()
for _ in range(n):
    b, f, r, v = FastIO.read_ints(4)
    rooms[b - 1][f - 1][r - 1] += v

for b in range(4):
    if b:
        FastIO.writeln('#' * 20)
    for f in range(3):
        FastIO.writeln(''.join(f' {rooms[b][f][r]}' for r in range(10)))
