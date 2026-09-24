# verification-helper: PROBLEM https://judge.yosupo.jp/problem/ordered_set

from cplib.datastructure.binarytrie import MergeableBinaryTrie
from cplib.tools.fastio import FastIO

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)
S = MergeableBinaryTrie(30, lambda a, b: a + b, 0)
root = S.new_trie()
for x in A:
    S.add(root, x, 0)

for _ in range(Q):
    t, x = FastIO.read_ints(2)
    if t == 0:
        S.add(root, x, 0)
    elif t == 1:
        S.discard(root, x)
    elif t == 2:
        if 1 <= x <= S.size(root):
            FastIO.writeln(f'{S.get(root, x - 1)[0]}')
        else:
            FastIO.writeln('-1')
    elif t == 3:
        FastIO.writeln(f'{S.bisect_right(root, x)}')
    elif t == 4:
        value = S.predecessor(root, x)
        FastIO.writeln(f'{value if value is not None else -1}')
    else:
        value = S.successor(root, x)
        FastIO.writeln(f'{value if value is not None else -1}')
