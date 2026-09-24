# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_inversions_query

from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.fastio import FastIO
from math import isqrt


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

comp_map = {a: i for i, a in enumerate(sorted(set(A)))}
comped_A = [comp_map[a] for a in A]

query: list[tuple[int, int]] = []

for i in range(Q):
    l, r = FastIO.read_ints(2)
    query.append((l, r))

# Mo's algorithm

M = max(1, N // isqrt(Q * 2 // 3))

sorted_idx = list(range(Q))
sorted_key = [((l // M) << 30) + r if (l // M) & 1 else ((l // M) << 30) - r for l, r in query]
sorted_idx.sort(key=lambda i: sorted_key[i])

l, r = 0, 0
ft = FenwickTree(len(comp_map) + 1)

inv = 0
cnt = 0
res = [0] * Q

for i in sorted_idx:
    ql, qr = query[i]
    while l > ql:
        l -= 1
        # add left
        inv += ft.sum(comped_A[l])
        cnt += 1
        ft.add(comped_A[l], 1)
    while r < qr:
        # add right
        inv += cnt - ft.sum(comped_A[r] + 1)
        cnt += 1
        ft.add(comped_A[r], 1)
        r += 1
    while l < ql:
        # remove left
        inv -= ft.sum(comped_A[l])
        cnt -= 1
        ft.add(comped_A[l], -1)
        l += 1
    while r > qr:
        r -= 1
        # remove right
        inv -= cnt - ft.sum(comped_A[r] + 1)
        cnt -= 1
        ft.add(comped_A[r], -1)
    res[i] = inv

for x in res:
    FastIO.writeln(f'{x}')
