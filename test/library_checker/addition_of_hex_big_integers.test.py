# verification-helper: PROBLEM https://judge.yosupo.jp/problem/addition_of_hex_big_integers

from cplib.mathematics.bigint import BigIntHex
from cplib.tools.fastio import FastIO


T = FastIO.read_int()
for _ in range(T):
    a = BigIntHex(FastIO.read())
    b = BigIntHex(FastIO.read())
    value = a + b
    FastIO.writeln(str(value).replace('0x', '').upper())
