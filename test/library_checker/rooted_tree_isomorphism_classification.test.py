# verification-helper: PROBLEM https://judge.yosupo.jp/problem/rooted_tree_isomorphism_classification

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.tree import TreeHashContext
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
T = Tree(N)
if N > 1:
    P = FastIO.read_ints(N - 1)
    for i, p in enumerate(P, 1):
        T.add_edge(Node(p), Node(i))

ctx = TreeHashContext()
ids = ctx.rooted_subtree_ids(T, Node(0))
compressed: dict[int, int] = {}
A = [0] * N
for i, value in enumerate(ids):
    index = compressed.get(value)
    if index is None:
        index = len(compressed)
        compressed[value] = index
    A[i] = index

FastIO.writeln(f'{len(compressed)}')
FastIO.writeln(' '.join(map(str, A)))
