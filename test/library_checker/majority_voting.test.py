# verification-helper: PROBLEM https://judge.yosupo.jp/problem/majority_voting

from cplib.datastructure.segtree import SegmentTree
from cplib.datastructure.treap import Treap
from cplib.tools.fastio import FastIO

from collections import defaultdict


N = FastIO.read_int()
Q = FastIO.read_int()
A = list(FastIO.read_ints(N))

pos_list: defaultdict[int, list[int]] = defaultdict(list)

for i, v in enumerate(A):
    pos_list[v].append(i)

pos: defaultdict[int, Treap[int]] = defaultdict(Treap[int])

for v, lst in pos_list.items():
    pos[v].build(lst, is_sorted=True)

MSK = (1 << 31) - 1


def op(lt: int, rt: int) -> int:
    c1, k1 = lt >> 31, lt & MSK
    c2, k2 = rt >> 31, rt & MSK
    if k1 == 0: return rt
    if k2 == 0: return lt
    if c1 == c2: return lt + k2
    if k1 > k2: return lt - k2
    return rt - k1


st = SegmentTree(N, op, 0)
init_nodes: list[int] = [(a << 31) + 1 for a in A]
st.build(init_nodes)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        p = FastIO.read_int()
        x = FastIO.read_int()
        if A[p] == x: continue
        pos[A[p]].discard(p, validity_check=False)
        A[p] = x
        pos[A[p]].add(p, validity_check=False)
        st.set(p, (x << 31) + 1)
    else:
        l = FastIO.read_int()
        r = FastIO.read_int()
        cand = st.prod(l, r) >> 31
        li = pos[cand].bisect_left(l)
        ri = pos[cand].bisect_left(r)
        if ri - li > (r - l) // 2:
            FastIO.writeln(f'{cand}')
        else:
            FastIO.writeln('-1')
