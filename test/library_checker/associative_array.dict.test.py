# verification-helper: PROBLEM https://judge.yosupo.jp/problem/associative_array

from cplib.tools.fastio import FastIO
from cplib.datastructure.hash import SafeIntegerDict


Q = FastIO.read_int()
D = SafeIntegerDict[int]()

for _ in range(Q):
    t = FastIO.read_int()
    k = FastIO.read_int()
    if t == 0:
        v = FastIO.read_int()
        D[k] = v
    else:
        FastIO.writeln(f'{D.get(k, 0)}')
