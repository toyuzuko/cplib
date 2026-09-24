# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_affine_range_sum_large_array

from cplib.datastructure.treap import SegmentedImplicitTreap
from cplib.tools.fastio import FastIO


MOD = 998244353
MASK32 = (1 << 32) - 1


def pack(b: int, c: int) -> int:
    return ((b % MOD) << 32) | (c & MASK32)


def unpack(x: int) -> tuple[int, int]:
    return (x >> 32) % MOD, x & MASK32


def mapping_affine(f: int, node_sum: int, length: int, node_val: int) -> tuple[int, int]:
    b, c = unpack(f)
    return (node_sum * b + c * length) % MOD, (node_val * b + c) % MOD


def composition_affine(f: int, g: int) -> int:
    bf, cf = unpack(f)
    bg, cg = unpack(g)
    return pack((bf * bg) % MOD, (bf * cg + cf) % MOD)


ID_AFFINE = pack(1, 0)

N, Q = FastIO.read_ints(2)

seg = SegmentedImplicitTreap[int, int](
    lambda x, y: (x + y) % MOD,
    0,
    lambda length, value: length * value % MOD,
    mapping_affine,
    composition_affine,
    ID_AFFINE,
)

root = seg.new_root(N, 0)
answers: list[str] = []

for _ in range(Q):
    query_type = FastIO.read_int()
    if query_type == 0:
        l, r, b, c = FastIO.read_ints(4)
        root = seg.range_apply(root, l, r, pack(b, c))
    else:
        l, r = FastIO.read_ints(2)
        value, root = seg.prod(root, l, r)
        answers.append(f"{value}\n")

FastIO.write("".join(answers))
