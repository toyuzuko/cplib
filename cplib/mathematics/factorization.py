#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
from math import gcd, isqrt
from random import randint


class PrimeFactor:
    """
    Provides utility functions related to prime factorization, primality testing,
    and other number theoretic properties.

    Tables are initialized lazily up to 1,000,000 unless ``set_max_value``
    is called first. Bounds 0 and 1 are supported; subsequent calls only grow
    the tables. Method complexities exclude this one-time initialization and
    count integer arithmetic operations rather than bit operations.

    Primality tests are deterministic for unsigned 64-bit integers. Above that
    range, 20 random Miller-Rabin bases give a probable-prime result; methods
    using factorization inherit that probabilistic guarantee.

    Attributes:
        m: Maximum value covered by the sieve tables.
        _built: Whether the sieve tables have been initialized.
        _isprime: Primality table for values up to ``m``.
        _minfac: Smallest prime factor table for values up to ``m``.
        _mobius: Möbius function table for values up to ``m``.
        _totient: Euler totient table for values up to ``m``.

    Space Complexity:
        ``O(m)``

    Complexity Notation:
        ``m`` is the maximum value covered by the sieve tables. For methods
        taking an integer ``n``, ``k`` is the number of prime factors with
        multiplicity, ``d(n)`` is the number of divisors of ``n``, and
        ``omega(n)`` is the number of distinct prime factors of ``n``.
    """
    m = 0
    _built = False
    _isprime: "list[bool]" = []
    _minfac: "list[int]" = []
    _mobius: "list[int]" = []
    _totient: "list[int]" = []

    @classmethod
    def set_max_value(cls, max_val: int) -> None:
        """
        Ensure the internal tables cover all integers up to ``max_val``.

        Args:
            max_val: Nonnegative inclusive bound. Smaller bounds do not shrink
                tables that have already been built.

        Returns:
            None.

        Raises:
            ValueError: If ``max_val`` is negative.

        Time Complexity:
            O(1) if the existing tables already cover ``max_val``; otherwise
            O(max_val log log max_val)
        """
        cls._initialize(max_val)

    @classmethod
    def _initialize(cls, max_val: int = 1000000) -> None:
        if max_val < 0:
            raise ValueError('maximum sieve value must be nonnegative')
        if cls._built and cls.m >= max_val:
            return
        cls._built = True
        cls.m = max_val
        cls._isprime = [True] * (cls.m + 1)
        cls._minfac = [-1] * (cls.m + 1)
        cls._mobius = [1] * (cls.m + 1)
        cls._totient = list(range(cls.m + 1))
        cls._isprime[0] = False
        cls._mobius[0] = 0
        if cls.m >= 1:
            cls._isprime[1] = False
            cls._minfac[1] = 1
        for p in range(2, cls.m + 1):
            if not cls._isprime[p]:
                continue
            cls._minfac[p] = p
            cls._mobius[p] = -1
            cls._totient[p] = p - 1
            for q in range(2 * p, cls.m + 1, p):
                cls._isprime[q] = False
                cls._totient[q] = cls._totient[q] // p * (p - 1)
                if cls._minfac[q] == -1:
                    cls._minfac[q] = p
                if (q // p) % p:
                    cls._mobius[q] *= -1
                else:
                    cls._mobius[q] = 0

    @classmethod
    def is_prime(cls, n: int) -> bool:
        """
        Checks if a number is prime.

        Args:
            n: Any integer; values below 2 are not prime.

        Returns:
            True for a prime (probable prime above 64 bits), False otherwise.

        Time Complexity:
            O(1) if ``n <= m``; otherwise O(log n) modular multiplications
            per base, with a fixed number of bases.
        """
        if n < 2:
            return False
        if not cls._built:
            cls._initialize()
        if n <= cls.m:
            return cls._isprime[n]
        if n == 2:
            return True
        if not n & 1:
            return False
        return cls._miller_rabin_test(n)

    @staticmethod
    def _miller_rabin_test(n: int) -> bool:
        if n <= 4294967295:
            # For numbers <= 4,294,967,295, these bases deterministically test primality.
            p = [2, 7, 61]
        elif n <= 18446744073709551615:
            # For numbers <= 18,446,744,073,709,551,615, these bases deterministically test primality.
            p = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]
        else:
            # For larger numbers, we use random bases to probabilistically test primality.
            p = [randint(1, n - 1) for _ in range(20)]
        d = n - 1
        d = d // (d & -d)
        for a in p:
            if a % n == 0:
                continue
            t = d
            y = pow(a, t, n)
            if y == 1:
                continue
            while y != n - 1:
                y = (y * y) % n
                if y == 1 or t == n - 1:
                    return False
                t <<= 1
        return True

    @classmethod
    def factorize(cls, n: int) -> "list[int]":
        """
        Factorize a number into its prime factors.

        Args:
            n: Positive integer to factorize.

        Returns:
            Prime factors in ascending order, with multiplicity; [] for 1.

        Raises:
            ValueError: If ``n`` is not positive.

        Time Complexity:
            O(k) if ``n <= m``. For larger ``n``, expected Pollard-Rho
            factorization time plus ``O(k log k)`` for sorting the factors.

        Space Complexity:
            O(k)
        """
        if n <= 0:
            raise ValueError('n must be positive')
        if n == 1:
            return []
        if not cls._built:
            cls._initialize()
        if n <= cls.m:
            return cls._factorize_fast(n)
        if cls.is_prime(n):
            return [n]
        res: "list[int]" = []
        stack: "list[int]" = [n]
        while stack:
            tmp = stack.pop()
            if tmp <= cls.m:
                res.extend(cls._factorize_fast(tmp))
                continue
            p = cls._pollard_rho(tmp)
            q = tmp // p
            if cls.is_prime(p):
                res.append(p)
            else:
                stack.append(p)
            if cls.is_prime(q):
                res.append(q)
            else:
                stack.append(q)
        return sorted(res)

    @classmethod
    def _factorize_fast(cls, n: int) -> "list[int]":
        res: "list[int]" = []
        while n > 1:
            p = cls._minfac[n]
            while cls._minfac[n] == p:
                n //= p
                res.append(p)
        return res

    @staticmethod
    def _pollard_rho(n: int) -> int:
        if n % 2 == 0:
            return 2
        if n % 3 == 0:
            return 3
        m = isqrt(isqrt(isqrt(n))) + 1
        s = randint(1, n - 1)
        while True:
            y, r, q = 2, 1, 1
            d = 1
            x = -1 # To avoid unused variable warning
            ys = -1 # To avoid unused variable warning
            while d == 1:
                x = y
                for _ in range(r):
                    y = (y * y + s) % n
                for k in range(0, r, m):
                    ys = y
                    for _ in range(min(m, r - k)):
                        y = (y * y + s) % n
                        q = q * abs(x - y) % n
                    d = gcd(n, q)
                    if d != 1:
                        break
                r <<= 1
            if d == n:
                # Recover a factor hidden by multiplying several differences.
                d = 1
                while d == 1:
                    ys = (ys * ys + s) % n
                    d = gcd(n, abs(x - ys))
            if d != n:
                break
            s += 1
        return d

    @classmethod
    def divisors(cls, n: int) -> "list[int]":
        """
        Compute the divisors of a number.

        Args:
            n: Positive integer whose divisors are requested.

        Returns:
            Positive divisors in ascending order; [1] for 1.

        Raises:
            ValueError: If ``n`` is not positive.

        Time Complexity:
            Factorization time plus ``O(d(n) log d(n))``.

        Space Complexity:
            O(d(n))
        """
        if n <= 0:
            raise ValueError('n must be positive')
        if not cls._built:
            cls._initialize()
        res: list[int] = [1]
        f = Counter(cls.factorize(n))
        for p, d in f.items():
            s = len(res)
            for i in range(s):
                v = 1
                for _ in range(d):
                    v *= p
                    res.append(res[i] * v)
        return sorted(res)

    @classmethod
    def mobius(cls, n: int) -> int:
        """
        Compute the Möbius function for a number.

        Args:
            n: Positive integer at which to evaluate the function.

        Returns:
            The Möbius function value; 1 for n=1.

        Raises:
            ValueError: If ``n`` is not positive.

        Time Complexity:
            O(1) if ``n <= m``; otherwise factorization time.
        """
        if n <= 0:
            raise ValueError('n must be positive')
        if n == 1:
            return 1
        if not cls._built:
            cls._initialize()
        if n <= cls.m:
            return cls._mobius[n]
        res = 1
        f = Counter(cls.factorize(n))
        for v in f.values():
            if v > 1:
                return 0
            res *= -1
        return res

    @classmethod
    def totient(cls, n: int) -> int:
        """
        Compute the Euler's totient function for a number.

        Args:
            n: Positive integer at which to evaluate the function.

        Returns:
            The number of integers in [1, n] coprime to n; 1 for n=1.

        Raises:
            ValueError: If ``n`` is not positive.

        Time Complexity:
            O(1) if ``n <= m``; otherwise factorization time.
        """
        if n <= 0:
            raise ValueError('n must be positive')
        if n == 1:
            return 1
        if not cls._built:
            cls._initialize()
        if n <= cls.m:
            return cls._totient[n]
        f = set(cls.factorize(n))
        res = n
        for p in f:
            res -= res // p
        return res

    @classmethod
    def primitive_root(cls, n: int) -> int:
        """
        Find a primitive root modulo n.

        Args:
            n: Modulus; values <= 1 return -1.

        Returns:
            A primitive root modulo n, or -1 if none exists.

        Time Complexity:
            Totient evaluation and factorization time for ``phi(n)``, plus
            ``O(n omega(phi(n)) log n)`` in the worst case.
        """
        if n <= 1:
            return -1
        if n == 2:
            return 1
        if n == 998244353:
            return 3
        tot = cls.totient(n)
        fac = list(set(cls.factorize(tot)))
        for g in range(1, n):
            if gcd(n, g) != 1:
                continue
            if pow(g, tot, n) != 1:
                return -1
            for p in fac:
                if pow(g, tot // p, n) == 1:
                    break
            else:
                return g
        return -1

    @classmethod
    def tetration(cls, base: int, height: int, mod: int) -> int:
        """
        Compute the tetration (iterated exponentiation) of `base` with height `height` modulo `mod`.

        Tetration is the operation of repeated exponentiation. This method calculates
        a right-associated tower containing ``height`` copies of ``base``.
        The empty tower is 1, and 0**0 is interpreted as 1.

        Args:
            base: Nonnegative base.
            height: Nonnegative number of copies of the base in the tower.
            mod: Positive modulus.

        Returns:
            The tower value modulo ``mod``, in [0, mod).

        Raises:
            ValueError: If base or height is negative, or mod is not positive.

        Time Complexity:
            ``O(L * C)``, where ``L <= height`` is the number of
            totient reductions until the modulus becomes ``1`` and ``C`` is
            the maximum cost of ``totient`` plus one modular exponentiation.

        Space Complexity:
            O(L) explicit stack entries, excluding factorization workspace.
        """
        if base < 0 or height < 0 or mod <= 0:
            raise ValueError('base and height must be nonnegative and mod positive')
        if mod == 1:
            return 0
        if base == 0:
            return ~height & 1
        if base == 1:
            return 1
        if height == 0:
            return 1
        if height == 1:
            return base % mod
        if height == 2:
            return pow(base, base, mod)

        moduli: list[tuple[int, int]] = []
        while height > 2 and mod > 1:
            totient_val = cls.totient(mod)
            moduli.append((mod, totient_val))
            mod = totient_val
            height -= 1
        result = pow(base, base, mod) if mod > 1 else 0
        for modulus, totient_val in reversed(moduli):
            result = pow(base, result if result else totient_val, modulus)
        return result
