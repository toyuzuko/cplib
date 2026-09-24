# verification-helper: PROBLEM https://judge.yosupo.jp/problem/ordered_set

from cplib.tools.fastio import FastIO
from cplib.datastructure.binarytrie import BinaryTrie


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N) # sorted and unique

S = BinaryTrie(30)

for a in A:
    S.add(a)

for _ in range(Q):
    t, x = FastIO.read_ints(2)
    if t == 0:
        S.add(x)
    elif t == 1:
        S.discard(x)
    elif t == 2:
        try:
            FastIO.writeln(f'{S[x - 1]}')
        except IndexError:
            FastIO.writeln('-1')
    elif t == 3:
        FastIO.writeln(f'{S.bisect_right(x)}')
    elif t == 4:
        value = S.predecessor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
    elif t == 5:
        value = S.successor(x)
        FastIO.writeln(f'{value if value is not None else -1}')
