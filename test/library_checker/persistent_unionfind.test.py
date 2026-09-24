# verification-helper: PROBLEM https://judge.yosupo.jp/problem/persistent_unionfind

from cplib.datastructure.persistent import FullyPersistentDSU
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
dsu = FullyPersistentDSU(N)
versions = [-1] * Q

for i in range(Q):
    t, k, u, v = FastIO.read_ints(4)
    version = -1 if k == -1 else versions[k]
    if t == 0:
        _, new_version = dsu.merge(u, v, version)
        versions[i] = new_version - 1
    else:
        if dsu.leader(u, version) == dsu.leader(v, version):
            FastIO.writeln('1')
        else:
            FastIO.writeln('0')
