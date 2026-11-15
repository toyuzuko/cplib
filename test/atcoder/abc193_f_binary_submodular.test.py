# verification-helper: PROBLEM https://atcoder.jp/contests/abc193/tasks/abc193_f

from cplib.graph.base import Node
from cplib.graph.binary_submodular_minimizer import BinarySubmodularMinimizer
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
grid = [FastIO.read() for _ in range(n)]
solver = BinarySubmodularMinimizer(n * n)
edges = 2 * n * (n - 1)
# A feasible colouring loses at most `edges`, so this penalty fixes a colour.
penalty = edges + 1
for i in range(n):
    for j in range(n):
        v = Node(i * n + j)
        if grid[i][j] != '?':
            # Flip one side of the grid's bipartition. Original unequal
            # neighbours then correspond to equal transformed colours.
            colour = (grid[i][j] == 'W') ^ ((i + j) & 1)
            solver.add_unary(v, penalty if colour else 0, 0 if colour else penalty)
        if i + 1 < n:
            solver.add_pairwise(v, Node(v + n), 0, 1, 1, 0)
        if j + 1 < n:
            solver.add_pairwise(v, Node(v + 1), 0, 1, 1, 0)
FastIO.writeln(f'{edges - solver.solve().cost}')
