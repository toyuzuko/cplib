# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/9/ITP1_9_D

from cplib.tools.fastio import FastIO


s = FastIO.read()
q = FastIO.read_int()
for _ in range(q):
    op = FastIO.read()
    a = FastIO.read_int()
    b = FastIO.read_int()
    if op == 'print':
        FastIO.writeln(s[a:b + 1])
    elif op == 'reverse':
        s = s[:a] + s[a:b + 1][::-1] + s[b + 1:]
    else:
        p = FastIO.read()
        s = s[:a] + p + s[b + 1:]
