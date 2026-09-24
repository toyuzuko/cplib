# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/9/ITP1_9_C

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
taro = 0
hanako = 0
for _ in range(n):
    a = FastIO.read()
    b = FastIO.read()
    if a > b:
        taro += 3
    elif a < b:
        hanako += 3
    else:
        taro += 1
        hanako += 1
FastIO.writeln(f'{taro} {hanako}')
