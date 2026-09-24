# verification-helper: PROBLEM https://judge.yosupo.jp/problem/division_of_hex_big_integers

from cplib.mathematics.bigint import BigIntHex
from cplib.tools.fastio import FastIO


T = FastIO.read_int()
for _ in range(T):
    a = BigIntHex(FastIO.read())
    b = BigIntHex(FastIO.read())
    q, r = divmod(a, b)
    FastIO.writeln(f"{str(q).replace('0x', '').upper()} {str(r).replace('0x', '').upper()}")
