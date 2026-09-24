# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/3/ITP1_3_B

from cplib.tools.fastio import FastIO


case = 1
while True:
    x = FastIO.read_int()
    if x == 0:
        break
    FastIO.writeln(f'Case {case}: {x}')
    case += 1
