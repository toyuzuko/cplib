# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/5/ITP1_5_C

from cplib.tools.fastio import FastIO


while True:
    H, W = FastIO.read_ints(2)
    if H == 0 and W == 0:
        break
    for i in range(H):
        FastIO.writeln(''.join('#' if (i + j) % 2 == 0 else '.' for j in range(W)))
    FastIO.writeln('')
