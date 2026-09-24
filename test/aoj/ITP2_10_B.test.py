# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/10/ITP2_10_B

from cplib.mathematics import format_bitmask
from cplib.tools.fastio import FastIO


a = FastIO.read_int()
b = FastIO.read_int()
FastIO.writeln(format_bitmask(a & b, 32))
FastIO.writeln(format_bitmask(a | b, 32))
FastIO.writeln(format_bitmask(a ^ b, 32))
