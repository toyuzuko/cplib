# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/7/ALDS1_7_B

from cplib.graph.tree import binary_tree_info
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
left = [-1] * N
right = [-1] * N

for _ in range(N):
    v = FastIO.read_int()
    left[v] = FastIO.read_int()
    right[v] = FastIO.read_int()

info = binary_tree_info(left, right)

for v in range(N):
    if info.parent[v] == -1:
        kind = 'root'
    elif info.degree[v] == 0:
        kind = 'leaf'
    else:
        kind = 'internal node'
    FastIO.writeln(
        f'node {v}: parent = {info.parent[v]}, sibling = {info.sibling[v]}, '
        f'degree = {info.degree[v]}, depth = {info.depth[v]}, height = {info.height[v]}, {kind}'
    )
