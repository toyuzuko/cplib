# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_set_range_composite

from cplib.tools.fastio import FastIO
from cplib.datastructure.segtree import LazySegmentTree


MOD = 998244353
MASK = (1 << 31) - 1

N, Q = FastIO.read_ints(2)
A = [((a << 31) + b, 1) for a, b in (FastIO.read_ints(2) for _ in range(N))] # できれば一つの64bit整数にまとめたいが、998244353 * 998244353 * 19 = 18933343977631383571 > 2^64 なので難しそう


def op(l: tuple[int, int], r: tuple[int, int]) -> tuple[int, int]:
    lv, ls = l
    rv, rs = r
    la, lb = lv >> 31, lv & MASK
    ra, rb = rv >> 31, rv & MASK
    return ((la * ra) % MOD << 31) + (ra * lb + rb) % MOD, ls + rs


def mapping(f: int, x: tuple[int, int]) -> tuple[int, int]:
    if f == -1:
        return x
    fa, fb = cs[f], ds[f]
    xv, xs = x
    xa, xb = xv >> 31, xv & MASK
    if fa != 1 and fb != 0:
        xs_log = xs.bit_length() - 1
        xa = pow_c[f][xs_log]
        if fa == 1:
            xb = fb * xs % MOD
        else:
            xb = fb * (1 - xa) % MOD * inv_c[f] % MOD
    return (xa << 31) + xb, xs


def composition(f: int, g: int) -> int:
    if f == -1:
        return g
    return f


st = LazySegmentTree(N, op, ((1 << 31), 0), mapping, composition, -1)
st.build(A)

cs: list[int] = []
ds: list[int] = []
pow_c: list[list[int]] = []
inv_c: list[int] = []

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, c, d = FastIO.read_ints(4)
        cs.append(c)
        ds.append(d)

        pow_c.append([c] * 20) # pow(c, 2^x, MOD) (1 <= x <= 20)の前計算
        p = c
        for i in range(1, 20):
            p = p * p % MOD
            pow_c[-1][i] = p

        inv_c.append(pow(1 - c, MOD - 2, MOD)) # inv(1 - c)の前計算
        st.range_apply(l, r, len(cs) - 1)

    else:
        l, r, x = FastIO.read_ints(3)
        prod = st.prod(l, r)
        v, s = prod
        a, b = v >> 31, v & MASK
        FastIO.writeln(f'{(a * x + b) % MOD}')