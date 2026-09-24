# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/5/ITP1_5_B

from cplib.tools.fastio import FastIO


while True:
    H, W = FastIO.read_ints(2)
    if H == 0 and W == 0:
        break
    if H == 1:
        line = '#' * W
        FastIO.writeln(line)
    else:
        border = '#' * W
        middle = '#' + '.' * (W - 2) + '#'
        FastIO.writeln(border)
        for _ in range(H - 2):
            FastIO.writeln(middle)
        FastIO.writeln(border)
    FastIO.writeln('')
