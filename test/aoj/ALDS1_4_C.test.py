# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/4/ALDS1_4_C

from cplib.string.trie import Trie
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
trie = Trie()

for _ in range(N):
    command = FastIO.read()
    word = FastIO.read().lower()
    if command == 'insert':
        trie.insert(word)
    else:
        FastIO.writeln('yes' if trie.contains(word) else 'no')
