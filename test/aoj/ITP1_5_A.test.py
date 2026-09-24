# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/5/ITP1_5_A

from cplib.tools.fastio import FastIO


while True:
    H, W = FastIO.read_ints(2)
    if H == 0 and W == 0:
        break
    line = '#' * W
    for _ in range(H):
        FastIO.writeln(line)
    FastIO.writeln('')
