# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/8/ITP2_8_D

from cplib.datastructure.treap import Treap
from cplib.tools.fastio import FastIO

Q = FastIO.read_int()
keys = Treap[str]()
M: dict[str, list[int]] = {}

for _ in range(Q):
    com = FastIO.read_int()
    if com == 3:
        L = FastIO.read()
        R = FastIO.read()
        for key in keys.iter_range(L, R):
            for x in M[key]:
                FastIO.writeln(f'{key} {x}')
    else:
        key = FastIO.read()
        if com == 0:
            if key not in M:
                keys.add(key, validity_check=False)
                M[key] = []
            M[key].append(FastIO.read_int())
        elif com == 1:
            values = M.get(key)
            if values is not None:
                for x in values:
                    FastIO.writeln(f'{x}')
        else:
            if key in M:
                del M[key]
                keys.discard(key, validity_check=False)
