# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_inversions_query

from cplib.algorithm.mo import HilbertMo
from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

comp = {value: index for index, value in enumerate(sorted(set(A)))}
arr = [comp[value] for value in A]

mo = HilbertMo[int](N)
for _ in range(Q):
    l, r = FastIO.read_ints(2)
    mo.add_query(l, r)

ft = FenwickTree(len(comp) + 1)
count = 0
inv = 0


def add_left(index: int) -> None:
    global count, inv
    value = arr[index]
    inv += ft.sum(value)
    count += 1
    ft.add(value, 1)


def add_right(index: int) -> None:
    global count, inv
    value = arr[index]
    inv += count - ft.sum(value + 1)
    count += 1
    ft.add(value, 1)


def remove_left(index: int) -> None:
    global count, inv
    value = arr[index]
    inv -= ft.sum(value)
    count -= 1
    ft.add(value, -1)


def remove_right(index: int) -> None:
    global count, inv
    value = arr[index]
    inv -= count - ft.sum(value + 1)
    count -= 1
    ft.add(value, -1)


answers = mo.run(add_left, add_right, remove_left, remove_right, lambda _: inv)

for value in answers:
    FastIO.writeln(f'{value}')
