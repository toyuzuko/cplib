# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/3/ITP1_3_C

from cplib.tools.fastio import FastIO


while True:
    x, y = FastIO.read_ints(2)
    if x == 0 and y == 0:
        break
    if x > y:
        x, y = y, x
    FastIO.writeln(f'{x} {y}')
