# verification-helper: PROBLEM https://judge.yosupo.jp/problem/cartesian_tree

from cplib.sequence.cartesian import cartesian_tree


N = int(input())
A = list(map(int, input().split()))

tree = cartesian_tree(A)
par = tree.par_v.copy()
par[tree.root] = tree.root

print(' '.join(map(str, par)))
