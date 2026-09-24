# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/8/ALDS1_8_B

from cplib.datastructure.bst import BinarySearchTree
from cplib.tools.fastio import FastIO


M = FastIO.read_int()
tree = BinarySearchTree[int]()

for _ in range(M):
    command = FastIO.read()
    if command == 'insert':
        tree.add(FastIO.read_int())
    elif command == 'find':
        FastIO.writeln('yes' if tree.contains(FastIO.read_int()) else 'no')
    else:
        FastIO.writeln(' ' + ' '.join(map(str, tree.inorder())))
        FastIO.writeln(' ' + ' '.join(map(str, tree.preorder())))
