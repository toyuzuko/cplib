# verification-helper: PROBLEM https://judge.yosupo.jp/problem/aho_corasick

from cplib.string.matching import AhoCorasick
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

ac = AhoCorasick()

end_node: list[int] = []

for i in range(N):
    s = FastIO.read().rstrip()
    end_node.append(ac.insert(s))

ac.build()

n = len(ac.trie)

FastIO.writeln(f'{n}')

for i in range(1, n):
    FastIO.writeln(f'{ac.par[i]} {ac.fail[i]}')

FastIO.writeln(' '.join(map(str, end_node)))