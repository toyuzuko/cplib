# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/14/ALDS1_14_B

from cplib.string.hashing import RollingHashMersenneMod
from cplib.tools.fastio import FastIO


T = FastIO.read()
P = FastIO.read()

rh = RollingHashMersenneMod(T, base=911382323)
l = 0
m = len(P)

if m <= len(T):
    pattern_hash = RollingHashMersenneMod(P, base=rh.base).get_hash(0, m)
    while True:
        idx = rh.search_hash(m, pattern_hash, l)
        if idx == -1:
            break
        if T.startswith(P, idx):
            FastIO.writeln(f'{idx}')
        l = idx + 1
