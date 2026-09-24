# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/5/DPL_5_G

from cplib.mathematics.combinatorics import TwelvefoldWay
from cplib.tools.fastio import FastIO


n, k = FastIO.read_ints(2)

FastIO.writeln(f'{TwelvefoldWay(True, False).count(n, k)}')
