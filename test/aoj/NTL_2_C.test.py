# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/2/NTL_2_C

from cplib.mathematics.bigint import BigInt
from cplib.tools.fastio import FastIO


a = BigInt(FastIO.read())
b = BigInt(FastIO.read())

FastIO.writeln(f'{a * b}')
