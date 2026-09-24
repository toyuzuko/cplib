# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/8/ITP1_8_B

from cplib.tools.fastio import FastIO


while True:
    x = FastIO.read()
    if x == '0':
        break
    FastIO.writeln(f'{sum(map(int, x))}')
