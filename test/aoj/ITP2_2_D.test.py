# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/2/ITP2_2_D

from cplib.datastructure.linkedlist import SpliceableLinkedLists
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
lists = SpliceableLinkedLists[int](N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        lists.append(FastIO.read_int(), FastIO.read_int())
    elif com == 1:
        FastIO.writeln(' '.join(map(str, lists.to_list(FastIO.read_int()))))
    else:
        s = FastIO.read_int()
        t = FastIO.read_int()
        lists.splice_back(s, t)
