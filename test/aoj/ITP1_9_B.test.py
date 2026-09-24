# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/9/ITP1_9_B

from cplib.tools.fastio import FastIO


while True:
    s = FastIO.read()
    if s == '-':
        break
    m = FastIO.read_int()
    cut = 0
    n = len(s)
    for _ in range(m):
        cut = (cut + FastIO.read_int()) % n
    FastIO.writeln(s[cut:] + s[:cut])
