# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_count_distinct

from cplib.algorithm.mo import RollbackMo
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

comp = {value: index for index, value in enumerate(sorted(set(A)))}
arr = [comp[value] for value in A]

mo = RollbackMo[int, int](N)
for _ in range(Q):
    l, r = FastIO.read_ints(2)
    mo.add_query(l, r)

freq = [0] * len(comp)
history: list[tuple[int, int, int]] = []
distinct = [0]


def add(index: int) -> None:
    value = arr[index]
    history.append((value, freq[value], distinct[0]))
    if freq[value] == 0:
        distinct[0] += 1
    freq[value] += 1


def snapshot() -> int:
    return len(history)


def rollback(snap: int) -> None:
    while len(history) > snap:
        value, prev_freq, prev_distinct = history.pop()
        freq[value] = prev_freq
        distinct[0] = prev_distinct


answers = mo.run(add, snapshot, rollback, lambda _: distinct[0])
for value in answers:
    FastIO.writeln(f'{value}')
