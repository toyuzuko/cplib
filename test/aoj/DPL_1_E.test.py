# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/1/DPL_1_E

from cplib.sequence.alignment import edit_distance
from cplib.tools.fastio import FastIO


s = FastIO.read()
t = FastIO.read()

FastIO.writeln(f'{edit_distance(s, t)}')
