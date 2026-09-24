# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/7/ALDS1_7_C

from cplib.graph.tree import binary_tree_traversals
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
left = [-1] * N
right = [-1] * N

for _ in range(N):
    v = FastIO.read_int()
    left[v] = FastIO.read_int()
    right[v] = FastIO.read_int()

traversal = binary_tree_traversals(left, right)

FastIO.writeln('Preorder')
FastIO.writeln(' ' + ' '.join(map(str, traversal.preorder)))
FastIO.writeln('Inorder')
FastIO.writeln(' ' + ' '.join(map(str, traversal.inorder)))
FastIO.writeln('Postorder')
FastIO.writeln(' ' + ' '.join(map(str, traversal.postorder)))
