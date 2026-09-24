# verification-helper: PROBLEM https://judge.yosupo.jp/problem/tree_path_composite_sum

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.treedp import rerooting_dp
from cplib.tools.fastio import FastIO


MOD = 998244353
MASK = (1 << 30) - 1

N = FastIO.read_int()
A = list(FastIO.read_ints(N))
B: list[int] = []
C: list[int] = []

tree = Tree(N)

for _ in range(N - 1):
    u, v, b, c = FastIO.read_ints(4)
    B.append(b)
    C.append(c)
    tree.add_edge(Node(u), Node(v))

tree.build()


def merge(lt: int, rt: int) -> int:
    lv, ls = lt >> 30, lt & MASK
    rv, rs = rt >> 30, rt & MASK
    return ((lv + rv) % MOD << 30) + (ls + rs) % MOD


def put_edge(x: int, e: int) -> int:
    xv, xs = x >> 30, x & MASK
    return ((xv * B[e] + xs * C[e]) % MOD << 30) + xs


def put_vertex(x: int, v: int) -> int:
    xv, xs = x >> 30, x & MASK
    return ((xv + A[v]) % MOD << 30) + xs + 1


res = rerooting_dp(tree, 0, merge, put_edge, put_vertex)

for x in res:
    FastIO.write(f'{x >> 30}')
    FastIO.write(' ')
FastIO.writeln('')
