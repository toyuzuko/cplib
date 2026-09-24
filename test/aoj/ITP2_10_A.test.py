# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/10/ITP2_10_A

from cplib.mathematics import BitFlagSet, format_bitmask
from cplib.tools.fastio import FastIO


x = FastIO.read_int()
flags = BitFlagSet(32, x)
FastIO.writeln(flags.to_binary())
FastIO.writeln(format_bitmask(flags.complement_value(), 32))
FastIO.writeln(format_bitmask(flags.logical_left_shift_value(), 32))
FastIO.writeln(format_bitmask(flags.logical_right_shift_value(), 32))
