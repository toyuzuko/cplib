#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from math import gcd, isqrt

from cplib.mathematics.factorization import PrimeFactor


def batch_inverse_mod(values: Sequence[int], mod: int) -> list[int]:
    """Compute modular inverses using one inverse of a product.

    Args:
        values: Integers to invert, in output order. Negative and unreduced
            values are accepted. Every value must be coprime to ``mod``.
        mod: Modulus greater than one; it need not be prime.

    Returns:
        List of inverses in ``[0, mod)``. An empty input returns ``[]``.
        The input is not modified.

    Raises:
        ValueError: If ``mod <= 1`` or an element has no modular inverse.

    Time Complexity:
        O(n + log mod) arithmetic operations for n input values.

    Space Complexity:
        O(n).

    Examples:
        >>> batch_inverse_mod([2, 3, 4], 7)
        [4, 5, 2]
        >>> batch_inverse_mod([2, 4], 15)
        [8, 4]
        >>> batch_inverse_mod([], 7)
        []
    """
    if mod <= 1:
        raise ValueError('mod must be greater than one')
    if not values:
        return []
    n = len(values)
    prefix = [1] * (n + 1)
    for i, value in enumerate(values):
        prefix[i + 1] = prefix[i] * value % mod
    inverse = pow(prefix[-1], -1, mod)
    result = [0] * n
    for i in range(n - 1, -1, -1):
        result[i] = prefix[i] * inverse % mod
        inverse = inverse * values[i] % mod
    return result


def discrete_logarithm(base: int, value: int, mod: int) -> int:
    """
    Find the smallest nonnegative exponent with base**exponent == value modulo mod.

    Base and value are reduced modulo mod. Composite moduli and bases not
    coprime to the modulus are supported. The convention 0**0 == 1 is used.

    Args:
        base: The base.
        value: The number for which we want to find the exponent.
        mod: Positive modulus; mod=1 returns zero.

    Returns:
        The smallest nonnegative exponent satisfying the congruence,
        or -1 if no exponent exists.

    Raises:
        ValueError: If mod is nonpositive.

    Time Complexity:
        O(sqrt(mod) log mod)

    Space Complexity:
        O(sqrt(mod))
    """
    if mod <= 0:
        raise ValueError('mod must be positive')
    base %= mod
    value %= mod
    if mod == 1:
        return 0
    if value == 1:
        return 0
    if base == value == 0:
        return 1
    max_sq = isqrt(mod) + 1
    precalc_pows: dict[int, int] = {}
    cur_pow = 1
    for i in range(max_sq + 1):
        if cur_pow % mod == value:
            return i  # base**i % mod == value
        precalc_pows[cur_pow * value % mod] = i
        cur_pow *= base
        cur_pow %= mod
    z_mult = pow(base, max_sq, mod)
    giant_step = z_mult
    for i in range(1, max_sq + 1):
        if giant_step in precalc_pows:
            computed_exp = i * max_sq - precalc_pows[giant_step]
            if pow(base, computed_exp, mod) == value:
                return computed_exp
        giant_step *= z_mult
        giant_step %= mod
    return -1


class _KthRootMemo:
    def __init__(self, base: int, step_limit: int, period: int, mod: int) -> None:
        self.mod = mod
        self.period = period
        self.size = 1 << (min(step_limit, period).bit_length() - 1)
        self.table: dict[int, int] = {}
        x = 1
        for i in range(self.size):
            self.table[x] = i
            x = x * base % mod
        self.gpow = x

    def find(self, x: int) -> int:
        cur = x
        for t in range(0, self.period, self.size):
            if cur in self.table:
                return (self.table[cur] - t) % self.period
            cur = cur * self.gpow % self.mod
        raise AssertionError('discrete logarithm not found')


def tonelli_shanks(square: int, mod: int) -> int:
    """
    Compute the square root modulo a prime using the Tonelli-Shanks algorithm.

    Finds x such that x^2 ≡ square (mod mod) for a given integer square.
    The modulus mod must be a prime.

    Args:
        square (int): The number to find the square root of.
        mod (int): The modulus, which must be a prime.

    Returns:
        int: The square root x of square modulo mod (0 <= x < mod).
             Returns -1 if no square root exists.

    Raises:
        ValueError: If mod < 2. Primality of mod is a caller precondition
            and is not checked.

    Time Complexity:
        O(log^2 mod) - Average case complexity of the Tonelli-Shanks algorithm.

    Examples:
        >>> # 2^2 ≡ 4 (mod 7)
        >>> pow(tonelli_shanks(4, 7), 2, 7)
        4

        >>> # 5 is not a quadratic residue modulo 7
        >>> tonelli_shanks(5, 7)
        -1

        >>> # 1^2 ≡ 1 (mod 13)
        >>> pow(tonelli_shanks(1, 13), 2, 13)
        1

        >>> # 6^2 ≡ 36 ≡ 10 (mod 13)
        >>> pow(tonelli_shanks(10, 13), 2, 13)
        10

        >>> # 4^2 ≡ 16 ≡ 2 (mod 7)
        >>> pow(tonelli_shanks(2, 7), 2, 7)
        2

    Notes:
        - mod must be a prime number.
        - Returns one of the two square roots (the other is mod - x).
        - Returns -1 if square is not a quadratic residue modulo mod.
        - For composite moduli, use sqrt_mod() instead.

    Space Complexity:
        O(1)
    """
    if mod < 2:
        raise ValueError('mod must be a prime greater than one')
    square = square % mod
    if square == 0: return 0
    if square == 1: return 1
    h = (mod - 1) // 2
    if pow(square, h, mod) != 1: return -1
    q, s = mod - 1, 0
    while not q & 1:
        q >>= 1
        s += 1
    z = 1
    while pow(z, h, mod) != mod - 1:
        z += 1
    m, c, t, r = s, pow(z, q, mod), pow(square, q, mod), pow(square, (q + 1) // 2, mod)
    while t != 1:
        k = 1
        while pow(t, 1 << k, mod) != 1:
            k += 1
        x = pow(c, pow(2, m - k - 1, mod - 1), mod)
        m = k
        c = (x * x) % mod
        t = (t * c) % mod
        r = (r * x) % mod
    if r * r % mod != square: return -1
    return r


def _sqrt_mod_power_of_two(a: int, e: int) -> int:
    """
    Compute square root modulo 2^e.

    Args:
        a (int): The number to find the square root of.
        e (int): The exponent (e >= 1).

    Returns:
        int: A square root of a modulo 2^e, or -1 if none exists.

    Algorithm:
        - For e = 1, 2: Direct computation.
        - For e >= 3: Uses Hensel lifting starting from root modulo 8.
    """
    if e <= 0:
        raise ValueError("e must be positive")

    mod = 1 << e
    a &= mod - 1
    if a == 0:
        return 0

    if e == 1:
        return a & 1
    if e == 2:
        return 1 if (a & 3) == 1 else -1

    if (a & 7) != 1:
        return -1

    root = 1
    cur_pow = 8
    while cur_pow < mod:
        next_pow = cur_pow << 1
        if (root * root) & (next_pow - 1) != a & (next_pow - 1):
            root += cur_pow >> 1
        cur_pow = next_pow
    return root & (mod - 1)


def _sqrt_mod_prime_power(a: int, p: int, e: int) -> int:
    """
    Compute square root modulo p^e where p is prime.

    Args:
        a (int): The number to find the square root of.
        p (int): The prime base.
        e (int): The exponent (e >= 1).

    Returns:
        int: A square root of a modulo p^e, or -1 if none exists.

    Algorithm:
        Uses Hensel's lemma to lift solutions from mod p to mod p^e.
        Special handling for p = 2.
    """
    if e <= 0:
        raise ValueError("e must be positive")

    mod: int = p**e
    a %= mod
    if a == 0:
        return 0

    v = 0
    tmp = a
    while tmp % p == 0:
        tmp //= p
        v += 1

    if v & 1:
        return -1

    if v:
        sub = _sqrt_mod_prime_power(a // (p**v), p, e - v)
        if sub == -1:
            return -1
        result: int = (sub * pow(p, v // 2, mod)) % mod
        return result

    if p == 2:
        return _sqrt_mod_power_of_two(a, e)

    r = tonelli_shanks(a % p, p)
    if r == -1:
        return -1

    cur_mod = p
    for _ in range(1, e):
        diff = ((a - r * r) // cur_mod) % p
        inv = pow(2 * r, -1, p)
        t = (diff * inv) % p
        r = (r + t * cur_mod) % (cur_mod * p)
        cur_mod *= p
    return r


def extended_gcd(a: int, mod: int) -> tuple[int, int]:
    """Return the gcd and a normalized coefficient from extended Euclid.

    Args:
        a: Integer whose coefficient is sought.
        mod: Positive modulus.

    Returns:
        ``(g, x)`` with ``g = gcd(a, mod)``, ``a * x % mod == g % mod``,
        and ``0 <= x < mod // g``. If ``g == 1``, ``x`` is the modular
        inverse of ``a``. Otherwise, it is the inverse of ``a // g``
        modulo ``mod // g``; the modulus-one case returns zero.

    Raises:
        ValueError: If mod is nonpositive.

    Time Complexity:
        O(log(mod + 1)) arithmetic operations after reducing ``a`` modulo ``mod``.

    Space Complexity:
        O(1) auxiliary integers.

    Examples:
        >>> extended_gcd(3, 7)
        (1, 5)
        >>> extended_gcd(6, 15)
        (3, 3)
    """
    if mod <= 0:
        raise ValueError('mod must be positive')
    a %= mod
    if a == 0:
        return mod, 0
    mod_val = mod
    num = a
    inv0 = 0
    inv1 = 1
    while num:
        quotient = mod_val // num
        mod_val -= num * quotient
        inv0 -= inv1 * quotient
        mod_val, num = num, mod_val
        inv0, inv1 = inv1, inv0
    if inv0 < 0:
        inv0 += mod // mod_val
    return mod_val, inv0


def chinese_remainder_theorem(rems: Sequence[int], mods: Sequence[int]) -> "tuple[int, int]":
    """
    Chinese Remainder Theorem (CRT) solver.

    Args:
        rems: List of remainders.
        mods: Positive moduli; they need not be coprime.

    Returns:
        (solution, period), where solution is the smallest nonnegative
        solution and period is the least common multiple of the moduli.
        Returns (0, 0) if the equations are inconsistent, and (0, 1) for
        empty input.

    Raises:
        AssertionError: If lengths differ or any modulus is nonpositive.

    Time Complexity:
        O(k log M), where ``k = len(rems)`` and ``M`` is the final combined modulus.

    Space Complexity:
        O(1)
    """
    assert len(rems) == len(mods)
    assert all(mod >= 1 for mod in mods)
    count = len(rems)
    cur_rem = 0
    cur_mod = 1
    for i in range(count):
        nxt_rem = rems[i] % mods[i]
        nxt_mod = mods[i]
        if cur_mod < nxt_mod:
            cur_rem, nxt_rem = nxt_rem, cur_rem
            cur_mod, nxt_mod = nxt_mod, cur_mod
        if cur_mod % nxt_mod == 0:
            if cur_rem % nxt_mod != nxt_rem:
                return 0, 0
            continue
        gcd_val, inverse_mod = extended_gcd(cur_mod, nxt_mod)
        mod_step = nxt_mod // gcd_val
        if (nxt_rem - cur_rem) % gcd_val:
            return 0, 0
        factor = (nxt_rem - cur_rem) // gcd_val * inverse_mod % mod_step
        cur_rem += factor * cur_mod
        cur_mod *= mod_step
        if cur_rem < 0:
            cur_rem += cur_mod
    return cur_rem, cur_mod


def sqrt_mod(square: int, mod: int) -> int:
    """
    Compute a square root modulo any positive integer.

    Finds x such that x^2 ≡ square (mod mod) for any positive modulus.
    Uses factorization and the Chinese Remainder Theorem to handle composite moduli.

    Args:
        square (int): The number to find the square root of.
        mod (int): The modulus (any positive integer).

    Returns:
        int: A square root x of square modulo mod (0 <= x < mod).
             Returns -1 if no square root exists.

    Time Complexity:
        Factorization time for ``mod``, plus root finding on each prime-power
        factor and CRT merge time.

    Examples:
        >>> # 13^2 ≡ 169 ≡ 4 (mod 15)
        >>> pow(sqrt_mod(4, 15), 2, 15)
        4

        >>> # 5^2 ≡ 25 ≡ 9 (mod 16)
        >>> pow(sqrt_mod(9, 16), 2, 16)
        9

        >>> # 1^2 ≡ 1 (mod 8)
        >>> pow(sqrt_mod(1, 8), 2, 8)
        1

        >>> # 4^2 ≡ 16 ≡ 2 (mod 7)
        >>> pow(sqrt_mod(2, 7), 2, 7)
        2

        >>> # 3 is not a quadratic residue modulo 7
        >>> sqrt_mod(3, 7)
        -1

    Notes:
        - Works for any positive modulus (prime, composite, or prime power).
        - Returns only one of potentially multiple square roots.
        - For prime moduli, internally uses the Tonelli-Shanks algorithm.
        - For composite moduli, uses factorization and CRT.

    Raises:
        ValueError: If mod is non-positive.

    Space Complexity:
        O(omega(mod))
    """
    if mod <= 0:
        raise ValueError("mod must be positive")

    square %= mod
    if square == 0 or mod == 1:
        return square

    primes = PrimeFactor.factorize(mod)
    counts: dict[int, int] = {}
    for p in primes:
        counts[p] = counts.get(p, 0) + 1

    rems: list[int] = []
    mods: list[int] = []
    for p, e in counts.items():
        pe = p**e
        r = _sqrt_mod_prime_power(square, p, e)
        if r == -1:
            return -1
        rems.append(r)
        mods.append(pe)

    root, prod = chinese_remainder_theorem(rems, mods)
    if prod == 0:
        return -1
    return root % mod


def _prime_power_root_mod(c: int, q: int, e: int, mod: int) -> int:
    s = mod - 1
    t = 0
    while s % q == 0:
        s //= q
        t += 1

    qe = int(q ** e)
    u = pow(-s, -1, qe)
    z = pow(c, (s * u + 1) // qe, mod)
    zqe = pow(c, s * u, mod)
    if zqe == 1:
        return z

    qt1 = q ** (t - 1)
    v = 2
    while True:
        vs = pow(v, s, mod)
        if pow(vs, qt1, mod) != 1:
            break
        v += 1

    vsqe = pow(vs, qe, mod)
    vs_e = e
    base = vsqe
    for _ in range(t - e - 1):
        base = pow(base, q, mod)
    memo = _KthRootMemo(base, int((t - e) ** 0.5 * q ** 0.5) + 1, q, mod)

    while zqe != 1:
        tmp = zqe
        td = 0
        while tmp != 1:
            td += 1
            tmp = pow(tmp, q, mod)
        need_e = t - td
        while vs_e != need_e:
            vs = pow(vs, q, mod)
            vsqe = pow(vsqe, q, mod)
            vs_e += 1

        target = pow(pow(zqe, -1, mod), q ** (td - 1), mod)
        bsgs = memo.find(target)
        z = z * pow(vs, bsgs, mod) % mod
        zqe = zqe * pow(vsqe, bsgs, mod) % mod

    return z


def kth_root_mod(k: int, y: int, mod: int) -> int:
    """
    Compute a kth root modulo a prime.

    Args:
        k: Nonnegative exponent.
        y: Target residue.
        mod: Prime modulus.

    Returns:
        ``x`` such that ``x^k == y (mod mod)``, or ``-1`` if no such ``x``
        exists. The convention ``0^0 == 1`` is used.

    Raises:
        ValueError: If k is negative or mod < 2. Primality is a caller
            precondition and is not checked.

    Time Complexity:
        Factorization time for ``gcd(k, mod - 1)`` plus generalized
        Tonelli-Shanks steps.

    Space Complexity:
        ``O(sqrt(q))`` for the largest prime factor ``q`` handled in one
        prime-power root step.
    """
    if k < 0:
        raise ValueError('exponent must be nonnegative')
    if mod < 2:
        raise ValueError('mod must be a prime greater than one')
    y %= mod
    if k == 0:
        return 1 if y == 1 else -1
    if y <= 1 or k == 1:
        return y
    if mod == 2:
        return y

    g = gcd(k, mod - 1)
    if pow(y, (mod - 1) // g, mod) != 1:
        return -1

    a = pow(y, pow(k // g, -1, (mod - 1) // g), mod)
    for q, e in Counter(PrimeFactor.factorize(g)).items():
        a = _prime_power_root_mod(a, q, e, mod)
    return a
