# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/7/GRL_7_A

from cplib.graph.matching import BipartiteMaximumMatching
from cplib.tools.fastio import FastIO


X, Y, E = FastIO.read_ints(3)
matching = BipartiteMaximumMatching(X, Y)

for _ in range(E):
    x, y = FastIO.read_ints(2)
    matching.add_edge(x, y)

FastIO.writeln(f'{matching.solve().weight}')
