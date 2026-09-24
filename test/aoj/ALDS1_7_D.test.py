# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/7/ALDS1_7_D

from cplib.graph.tree import reconstruct_postorder_from_preorder_inorder
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
preorder = FastIO.read_ints(N)
inorder = FastIO.read_ints(N)

postorder = reconstruct_postorder_from_preorder_inorder(preorder, inorder)
FastIO.writeln(' '.join(map(str, postorder)))
