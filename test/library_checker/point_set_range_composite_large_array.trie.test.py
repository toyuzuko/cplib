# verification-helper: PROBLEM https://judge.yosupo.jp/problem/point_set_range_composite_large_array

from cplib.tools.fastio import FastIO
from cplib.datastructure.binarytrie import MergeableBinaryTrie


MOD = 998244353
MASK = (1 << 31) - 1


def op(l: int, r: int) -> int:
    la, lb = l >> 31, l & MASK
    ra, rb = r >> 31, r & MASK
    return ((la * ra) % MOD << 31) + (ra * lb + rb) % MOD


N = FastIO.read_int()
Q = FastIO.read_int()

seg = MergeableBinaryTrie(30, op, 1 << 31)
root = seg.new_trie()

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        p, c, d = FastIO.read_ints(3)
        seg.add(root, p, (c << 31) + d, update=True)
    else:
        l, r, x = FastIO.read_ints(3)
        r1, r2 = seg.safe_split(root, l)
        r2, r3 = seg.safe_split(r2, r)
        prod, _ = seg.prod(r2)
        root = seg.merge(r1, r2)
        root = seg.merge(root, r3)
        a, b = prod >> 31, prod & MASK
        FastIO.writeln(f'{(a * x + b) % MOD}')