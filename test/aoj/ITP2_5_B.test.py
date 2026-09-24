# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/5/ITP2_5_B

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
items: list[tuple[int, int, str, int, str]] = []

for _ in range(N):
    v = FastIO.read_int()
    w = FastIO.read_int()
    t = FastIO.read()
    d = FastIO.read_int()
    s = FastIO.read()
    items.append((v, w, t, d, s))

items.sort()

for item in items:
    FastIO.writeln(' '.join(map(str, item)))
