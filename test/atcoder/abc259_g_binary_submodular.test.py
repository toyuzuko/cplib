# verification-helper: PROBLEM https://atcoder.jp/contests/abc259/tasks/abc259_g

from cplib.graph.base import Node
from cplib.graph.binary_submodular_minimizer import BinarySubmodularMinimizer
from cplib.tools.fastio import FastIO


h, w = FastIO.read_ints(2)
grid = [FastIO.read_ints(w) for _ in range(h)]
solver = BinarySubmodularMinimizer(h + w)
positive = sum(max(value, 0) for row in grid for value in row)
# Choosing nothing has loss `positive`; all losses below are nonnegative.
penalty = positive + 1
for i, row in enumerate(grid):
    for j, value in enumerate(row):
        # Row variable 1 means selected; column variable 0 means selected.
        # Opposite polarity makes each interaction submodular.
        if value >= 0:
            solver.add_pairwise(Node(i), Node(h + j), 0, value, 0, 0)
        else:
            solver.add_unary(Node(i), 0, -value)
            solver.add_unary(Node(h + j), -value, 0)
            solver.add_pairwise(Node(i), Node(h + j), 0, 0, penalty, 0)
FastIO.writeln(f'{positive - solver.solve().cost}')
