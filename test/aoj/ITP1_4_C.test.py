# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/4/ITP1_4_C

from cplib.tools.fastio import FastIO


while True:
    a = FastIO.read_int()
    op = FastIO.read()
    b = FastIO.read_int()
    if op == '?':
        break
    if op == '+':
        ans = a + b
    elif op == '-':
        ans = a - b
    elif op == '*':
        ans = a * b
    else:
        ans = a // b
    FastIO.writeln(f'{ans}')
