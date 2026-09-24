# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/4/ALDS1_4_D

from cplib.algorithm.bisearch import binary_search
from cplib.tools.fastio import FastIO


N, K = FastIO.read_ints(2)
W = [FastIO.read_int() for _ in range(N)]


def can_load(capacity: int) -> bool:
    trucks = 1
    load = 0
    for w in W:
        if w > capacity:
            return False
        if load + w <= capacity:
            load += w
        else:
            trucks += 1
            load = w
    return trucks <= K


FastIO.writeln(f'{binary_search(max(W) - 1, sum(W), can_load)}')
