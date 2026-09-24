# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_range_frequency

from cplib.tools.fastio import FastIO
from math import isqrt


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

M = isqrt(N) + 1

data: list[dict[int, int]] = [{} for _ in range(M)]

for i in range(N):
    data[i // M][A[i]] = data[i // M].get(A[i], 0) + 1

for _ in range(Q):
    q = FastIO.read_int()
    if q == 0:
        k, v = FastIO.read_ints(2)
        data[k // M][A[k]] = data[k // M].get(A[k], 0) - 1
        A[k] = v
        data[k // M][A[k]] = data[k // M].get(A[k], 0) + 1

    else:
        l, r, x = FastIO.read_ints(3)
        res = 0
        while l < r and l % M:
            res += A[l] == x
            l += 1
        while l < r and r % M:
            r -= 1
            res += A[r] == x
        while l < r:
            r -= M
            res += data[r // M].get(x, 0)
        FastIO.writeln(f'{res}')
