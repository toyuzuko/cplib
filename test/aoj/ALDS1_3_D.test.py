# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/3/ALDS1_3_D

from cplib.sequence.stack import matched_interval_areas
from cplib.tools.fastio import FastIO


areas = matched_interval_areas(FastIO.read(), '\\', '/')

FastIO.writeln(f'{sum(areas)}')
FastIO.writeln(' '.join(map(str, [len(areas), *areas])))
