# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_range_composite

from cplib.tools.fastio import FastIO
from cplib.datastructure.segtree import SegmentTree

MOD = 998244353
MASK = (1 << 31) - 1

N, Q = FastIO.read_ints(2)
A = [(a << 31) + b for a, b in (FastIO.read_ints(2) for _ in range(N))]


def op(l: int, r: int) -> int:
    la, lb = l >> 31, l & MASK
    ra, rb = r >> 31, r & MASK
    return ((la * ra) % MOD << 31) + (ra * lb + rb) % MOD


st = SegmentTree(N, op, 1 << 31)
st.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        p, c, d = FastIO.read_ints(3)
        st.set(p, (c << 31) + d)
    else:
        l, r, x = FastIO.read_ints(3)
        prod = st.prod(l, r)
        a, b = prod >> 31, prod & MASK
        FastIO.writeln(f'{(a * x + b) % MOD}')