# verification-helper: PROBLEM https://judge.yosupo.jp/problem/ordered_set

from cplib.datastructure.avltree import AVLTree
from cplib.tools.fastio import FastIO

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)
S = AVLTree[int]()
S.build(list(A), is_sorted=True)

for _ in range(Q):
    t, x = FastIO.read_ints(2)
    if t == 0:
        S.add(x)
    elif t == 1:
        S.discard(x)
    elif t == 2:
        try:
            value = S.get(x - 1)
        except IndexError:
            value = -1
        FastIO.writeln(f'{value}')
    elif t == 3:
        FastIO.writeln(f'{S.bisect_right(x)}')
    elif t == 4:
        value = S.predecessor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
    else:
        value = S.successor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
