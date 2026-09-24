# verification-helper: PROBLEM https://judge.yosupo.jp/problem/set_xor_min

from cplib.tools.fastio import FastIO
from cplib.datastructure.binarytrie import BinaryTrie


Q = FastIO.read_int()

trie = BinaryTrie(30)

for _ in range(Q):
    q = FastIO.read_int()
    if q == 0:
        x = FastIO.read_int()
        trie.add(x)
    elif q == 1:
        x = FastIO.read_int()
        trie.discard(x)
    else:
        x = FastIO.read_int()
        trie.all_xor(x)
        FastIO.writeln(f'{trie.min()}')
        trie.all_xor(x)
