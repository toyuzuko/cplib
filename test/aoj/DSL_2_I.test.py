# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_I

from cplib.datastructure.segtree import LazySegmentTree
from cplib.tools.fastio import FastIO


def op(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return left[0] + right[0], left[1] + right[1]


def mapping(value: int | None, data: tuple[int, int]) -> tuple[int, int]:
    if value is None:
        return data
    return value * data[1], data[1]


def composition(new_value: int | None, old_value: int | None) -> int | None:
    return old_value if new_value is None else new_value


N, Q = FastIO.read_ints(2)

seg = LazySegmentTree(N, op, (0, 0), mapping, composition, None)
seg.build([(0, 1)] * N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        s, t, x = FastIO.read_ints(3)
        seg.range_apply(s, t + 1, x)
    else:
        s, t = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.prod(s, t + 1)[0]}')
