#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
from math import isqrt
from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.modular import batch_inverse_mod, chinese_remainder_theorem
from cplib.mathematics.convolution import ConvolutionMod, ConvolutionLargeIntegers


class FactorialMod:
    """
    A class for computing factorials, permutations and combinations with modulo.

    This class pre-computes factorials, inverse factorials, and inverses up to max_n
    to enable fast computation of combinations and permutations under modulo.
    Each instance keeps the modulus selected at construction. Later calls to
    ``set_mod`` change the default for new instances only.

    Attributes:
        _mod: Modulus used for arithmetic.
        _max_n: Maximum value of n for which computations can be performed.
        _fact: List of pre-computed factorials mod p.
        _invf: List of pre-computed inverse factorials mod p.
        _inv: List of pre-computed inverses mod p.

    Examples:
        >>> # Using default modulus 998244353
        >>> f = FactorialMod(10)
        >>> f.factorial(5)  # computes 5! mod 998244353
        120
        >>> f.comb(5, 2)   # computes 5C2 mod 998244353
        10
        >>> f.perm(5, 2)   # computes 5P2 mod 998244353
        20

        >>> # Using custom modulus
        >>> FactorialMod.set_mod(1000000007)
        >>> f2 = FactorialMod(10)
        >>> f2.factorial(5)  # computes 5! mod 1000000007
        120

    Space Complexity:
        ``O(max_n)``

    Complexity Notation:
        ``max_n`` is the largest argument supported by the precomputed tables.
    """

    _mod = 998244353

    def __init__(self, max_n: int) -> None:
        """Initialize FactorialMod with pre-computed values up to max_n.

        Args:
            max_n: Maximum value for which to pre-compute values. Must satisfy
                ``0 <= max_n < p``, where the configured modulus ``p`` is prime.
                Primality is a caller precondition and is not checked.

        Returns:
            None.

        Raises:
            ValueError: If max_n is outside [0, p).

        Time Complexity:
            O(max_n)
        """
        self._mod = self.get_mod()
        if not 0 <= max_n < self._mod:
            raise ValueError('max_n must satisfy 0 <= max_n < mod')
        self._max_n = max_n
        self._fact = [0] * (max_n + 1)
        self._invf = [0] * (max_n + 1)
        self._inv = [0] * (max_n + 1)
        self._fact[0] = 1
        self._invf[0] = 1
        if max_n >= 1:
            self._fact[1] = 1
            self._invf[1] = 1
            self._inv[1] = 1
        for i in range(2, max_n + 1):
            self._fact[i] = self._fact[i - 1] * i % self._mod
            self._inv[i] = -self._inv[self._mod % i] * (self._mod // i) % self._mod
            self._invf[i] = self._invf[i - 1] * self._inv[i] % self._mod

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the default modulus for future instances.

        Args:
            mod: Prime modulus >= 2 for new instances. Primality is not checked.

        Returns:
            None. Existing instances retain their precomputed modulus.

        Raises:
            ValueError: If mod < 2.

        Time Complexity:
            O(1)
        """
        if mod < 2:
            raise ValueError('mod must be at least 2')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get the default modulus for future instances.

        Returns:
            Current class default, even when called through an instance.

        Time Complexity:
            O(1)
        """
        return cls._mod

    def factorial(self, n: int) -> int:
        """
        Compute n! mod p.

        Args:
            n: Non-negative integer for which to compute factorial.

        Returns:
            n! mod p

        Raises:
            AssertionError: If n is negative or greater than max_n.

        Time Complexity:
            O(1)
        """
        assert 0 <= n <= self._max_n
        return self._fact[n]

    def factorial_inv(self, n: int) -> int:
        """
        Compute inverse of n! mod p.

        Args:
            n: Non-negative integer for which to compute inverse factorial.

        Returns:
            (n!)^(-1) mod p

        Raises:
            AssertionError: If n is negative or greater than max_n.

        Time Complexity:
            O(1)
        """
        assert 0 <= n <= self._max_n
        return self._invf[n]

    def perm(self, n: int, k: int) -> int:
        """
        Compute P(n,k) = n!/(n-k)! mod p.

        Args:
            n: Number of elements to choose from.
            k: Number of positions to fill.

        Returns:
            P(n,k) mod p, or 0 if k > n.

        Raises:
            AssertionError: If n is negative or greater than max_n, or if k is negative.

        Examples:
            >>> FactorialMod.set_mod(7)
            >>> f = FactorialMod(5)
            >>> f.perm(5, 2)  # 5P2 = 20 ≡ 6 (mod 7)
            6

        Time Complexity:
            O(1)
        """
        assert 0 <= n <= self._max_n and 0 <= k
        if n < k: return 0
        return self._fact[n] * self._invf[n - k] % self._mod

    def comb(self, n: int, k: int) -> int:
        """
        Compute C(n,k) = n!/(k!(n-k)!) mod p.

        Args:
            n: Number of elements to choose from.
            k: Number of elements to choose.

        Returns:
            C(n,k) mod p, or 0 if k > n.

        Raises:
            AssertionError: If n is negative or greater than max_n, or if k is negative.

        Examples:
            >>> FactorialMod.set_mod(7)
            >>> f = FactorialMod(5)
            >>> f.comb(5, 2)  # 5C2 = 10 ≡ 3 (mod 7)
            3

        Time Complexity:
            O(1)
        """
        assert 0 <= n <= self._max_n and 0 <= k
        if n < k: return 0
        return self._fact[n] * self._invf[k] % self._mod * self._invf[n - k] % self._mod

    def inv(self, n: int) -> int:
        """
        Compute multiplicative inverse of n mod p.

        Args:
            n: Number to compute inverse for.

        Returns:
            Multiplicative inverse of n mod p.

        Raises:
            AssertionError: If n is negative or greater than max_n.
            ZeroDivisionError: If n is 0.

        Examples:
            >>> FactorialMod.set_mod(7)
            >>> f = FactorialMod(5)
            >>> f.inv(3)  # 3 * 5 ≡ 1 (mod 7)
            5

        Time Complexity:
            O(1)
        """
        assert 0 <= n <= self._max_n
        if n == 0: raise ZeroDivisionError
        return self._inv[n]


class LargeFactorialMod:
    """
    Compute large factorials modulo a prime without a full factorial table.

    This class is intended for cases such as ``998244353`` where precomputing
    all factorials up to ``mod - 1`` is too large. Queries are processed
    offline in :meth:`factorials`; :meth:`factorial` is a convenience wrapper
    for a single value.

    Attributes:
        _mod: Prime modulus used for computations.
        _block_size: Optional block size override for batched evaluation.

    Space Complexity:
        ``O(B + M / B + Q)``

    Complexity Notation:
        ``B`` is the selected block size, ``M`` is the maximum active query
        value below the modulus, and ``Q`` is the number of active queries.
    """

    _mod = 998244353

    def __init__(self, block_size: int | None = None) -> None:
        """Initialize the large factorial helper.

        Args:
            block_size: Optional block size. If omitted, a value is selected
                from the number of queries passed to :meth:`factorials`.
                Must be positive; it is capped at the largest active query.

        Returns:
            None.

        Raises:
            ValueError: If block_size is not positive.

        Time Complexity:
            O(1)
        """
        if block_size is not None and block_size <= 0:
            raise ValueError('block_size must be positive')
        self._block_size = block_size

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the prime modulus for large factorial computations.

        Args:
            mod: Prime modulus >= 2; primality is a caller precondition.

        Returns:
            None. Both existing and future helpers use this modulus.

        Raises:
            ValueError: If mod < 2.

        Time Complexity:
            O(1)
        """
        if mod < 2:
            raise ValueError('mod must be at least 2')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get the current modulus.

        Returns:
            Current prime modulus.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def _convolution(cls, a: list[int], b: list[int]) -> list[int]:
        mod = cls._mod
        if ConvolutionMod.get_mod() != mod:
            ConvolutionMod.set_mod(mod)
        try:
            return ConvolutionMod.convolution(a, b)
        except ValueError:
            return ConvolutionLargeIntegers.convolution(a, b, mod)

    @classmethod
    def _shift_sampling(cls, n: int, m: int, ys: list[int], c: int) -> list[int]:
        mod = cls._mod
        c %= mod
        if m == 0:
            return []
        if c < n:
            direct = min(m, n - c)
            res = ys[c:c + direct]
            if direct < m:
                res += cls._shift_sampling(n, m - direct, ys, n)
            return res
        if mod < c + m:
            pre = cls._shift_sampling(n, mod - c, ys, c)
            return pre + cls._shift_sampling(n, m - len(pre), ys, 0)

        fact = [1] * n
        inv_fact = [1] * n
        for i in range(1, n):
            fact[i] = fact[i - 1] * i % mod
        inv_fact[-1] = pow(fact[-1], mod - 2, mod)
        for i in range(n - 1, 0, -1):
            inv_fact[i - 1] = inv_fact[i] * i % mod

        d = [0] * n
        for i in range(n):
            v = ys[i] * inv_fact[i] % mod * inv_fact[n - 1 - i] % mod
            d[i] = -v % mod if (n - 1 - i) & 1 else v

        h_values = [(c - n + 1 + i) % mod for i in range(n + m - 1)]
        h = batch_inverse_mod(h_values, mod)
        g = cls._convolution(d, h)

        cur = c
        for i in range(1, n):
            cur = cur * ((c - i) % mod) % mod

        res = [0] * m
        for i in range(m):
            res[i] = cur * g[n - 1 + i] % mod
            cur = cur * ((c + i + 1) % mod) % mod * h[i] % mod
        return res

    @classmethod
    def _block_products(cls, block_size: int, count: int) -> list[int]:
        mod = cls._mod
        sample_count = min(block_size + 1, count)
        samples = [1] * sample_count
        for t in range(sample_count):
            base = block_size * t
            prod = 1
            for i in range(1, block_size + 1):
                prod = prod * (base + i) % mod
            samples[t] = prod
        if count <= block_size + 1:
            return samples
        return cls._shift_sampling(block_size + 1, count, samples, 0)

    def _select_block_size(self, query_count: int, max_n: int) -> int:
        if self._block_size is not None:
            return min(self._block_size, max_n)
        mod = self._mod
        if query_count <= 8:
            return min(4096, max(1, mod - 1), max(1, isqrt(max_n) + 1))
        return min(512, max(1, mod - 1))

    def factorial(self, n: int) -> int:
        """
        Compute ``n!`` modulo the current prime modulus.

        Args:
            n: Non-negative integer.

        Returns:
            ``n! mod p``.

        Time Complexity:
            Same asymptotic cost as :meth:`factorials` with a single query.
        """
        return self.factorials([n])[0]

    def factorials(self, ns: list[int]) -> list[int]:
        """
        Compute many factorials modulo the current prime modulus.

        Args:
            ns: Query values.

        Returns:
            Values ``[n! mod p for n in ns]``.

        Raises:
            ValueError: If any query value is negative.

        Time Complexity:
            ``O(B^2 + (B + M / B) log(B + M / B) + Q log Q + QB)``

        Space Complexity:
            ``O(B + M / B + Q)``
        """
        mod = self._mod
        if not ns:
            return []
        if any(n < 0 for n in ns):
            raise ValueError('factorial is undefined for negative values')

        ans = [0] * len(ns)
        active: list[tuple[int, int]] = []
        for i, n in enumerate(ns):
            if n >= mod:
                ans[i] = 0
            else:
                active.append((n, i))
        if not active:
            return ans

        max_n = max(n for n, _ in active)
        if max_n <= 1:
            for n, i in active:
                ans[i] = 1
            return ans

        block_size = self._select_block_size(len(active), max_n)
        block_count = max_n // block_size
        products = self._block_products(block_size, block_count)
        prefix = [1] * (block_count + 1)
        for i, v in enumerate(products):
            prefix[i + 1] = prefix[i] * v % mod

        queries = sorted((n // block_size, n % block_size, i) for n, i in active)
        pos = 0
        while pos < len(queries):
            q = queries[pos][0]
            block_base = q * block_size
            cur = prefix[q]
            r_now = 0
            while pos < len(queries) and queries[pos][0] == q:
                r = queries[pos][1]
                while r_now < r:
                    r_now += 1
                    cur = cur * (block_base + r_now) % mod
                ans[queries[pos][2]] = cur
                pos += 1
        return ans


class PowMod:
    """
    A class for computing powers of a fixed base with modulo efficiently.

    This class pre-computes powers of a given base up to max_n to enable fast
    computation of both positive and negative powers under a positive modulus,
    which may be composite. The base must be invertible if max_n > 0.
    Each instance retains its construction modulus when set_mod is called.

    Attributes:
        _mod: Modulus used for arithmetic.
        _base: The base number for power calculations.
        _max_n: Maximum absolute value of exponent for which computations can be performed.
        _pow: List of pre-computed positive powers mod p.
        _invp: List of pre-computed negative powers (inverses) mod p.

    Examples:
        >>> # Using default modulus
        >>> p = PowMod(3, 5)  # compute powers of 3 mod 998244353
        >>> p.pow(4)   # 3^4 = 81
        81

        >>> # Using custom modulus
        >>> PowMod.set_mod(7)
        >>> p = PowMod(3, 5)  # compute powers of 3 mod 7
        >>> p.pow(4)   # 3^4 = 81 ≡ 4 (mod 7)
        4
        >>> p.pow(-2)  # 3^(-2) = (1/3)^2 = 5^2 = 25 ≡ 4 (mod 7)
        4

    Space Complexity:
        ``O(max_n)``

    Complexity Notation:
        ``max_n`` is the largest absolute exponent supported by the
        precomputed tables.
    """

    _mod = 998244353

    def __init__(self, base: int, max_n: int) -> None:
        """Initialize PowMod with pre-computed powers up to max_n.

        Args:
            base: Base, coprime to the modulus if max_n > 0.
            max_n: Nonnegative maximum absolute exponent to pre-compute.

        Returns:
            None.

        Raises:
            ValueError: If max_n is negative or a required inverse does not exist.

        Time Complexity:
            O(max_n + log mod) arithmetic operations.
        """
        if max_n < 0:
            raise ValueError('max_n must be nonnegative')
        self._mod = self.get_mod()
        self._base = base % self._mod
        self._max_n = max_n
        self._pow = [1 % self._mod] * (max_n + 1)
        self._invp = [1 % self._mod] * (max_n + 1)
        invb = pow(self._base, -1, self._mod) if max_n else 0
        for i in range(1, max_n + 1):
            self._pow[i] = self._pow[i - 1] * self._base % self._mod
            self._invp[i] = self._invp[i - 1] * invb % self._mod

    def pow(self, n: int) -> int:
        """
        Compute base^n mod p.

        Args:
            n: Integer exponent in range [-max_n, max_n].

        Returns:
            base^n mod p.

        Raises:
            AssertionError: If |n| > max_n.

        Examples:
            >>> PowMod.set_mod(7)
            >>> p = PowMod(3, 5)
            >>> p.pow(4)   # 3^4 = 81 ≡ 4 (mod 7)
            4
            >>> p.pow(-2)  # 3^(-2) = (1/3)^2 = 5^2 = 25 ≡ 4 (mod 7)
            4

        Time Complexity:
            O(1)
        """
        assert -self._max_n <= n <= self._max_n
        if n >= 0:
            return self._pow[n]
        else:
            return self._invp[-n]

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the default modulus for future instances.

        Args:
            mod: Positive modulus, not necessarily prime.

        Returns:
            None. Existing instances keep their modulus.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod < 1:
            raise ValueError('mod must be at least 1')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get the default modulus for future instances.

        Returns:
            The class default, even when called through an existing instance.

        Time Complexity:
            O(1)
        """
        return cls._mod


class BinomialCoefficient:
    """
    Compute binomial coefficients modulo a positive integer using prime powers.

    This class handles binomial coefficient calculations for any modulus (not necessarily prime)
    by factorizing the modulus and using factorials with prime factors removed,
    then combining results using the Chinese Remainder Theorem.

    Key differences from FactorialMod:
    - Works with any modulus (not just primes)
    - No limit on n and k values (FactorialMod requires precomputation up to max_n)
    - Uses a prime-power generalization of the factorial method
    - More memory efficient for large n values
    - Slower for small values due to factorization overhead

    Instances keep their construction modulus. set_mod only changes the
    default for future instances; modulus 1 always gives zero.

    Attributes:
        _mod: Modulus used for arithmetic.
        factorization: Prime factorization of the modulus.
        facs: Precomputed factorials for each prime power modulus.
        invs: Precomputed inverse factorials for each prime power modulus.
        pows: Powers of primes for each prime factor.

    Examples:
        >>> BinomialCoefficient.set_mod(12)
        >>> bc = BinomialCoefficient()
        >>> bc.binom(10, 3)  # C(10, 3) = 120 ≡ 0 (mod 12)
        0

    Notes:
        This implementation precomputes arrays of total size ``S``. For a large
        prime modulus, use :class:`FactorialMod` when ``n`` is bounded.

    Space Complexity:
        ``O(S)``

    Complexity Notation:
        ``P`` is the number of distinct prime factors of ``mod`` and
        ``S = sum p_i^{q_i}`` over prime-power factors of ``mod``.
    """

    _mod = 998244353

    def __init__(self) -> None:
        """
        Initialize tables for the current class default modulus.

        Args:
            None.

        Returns:
            None.

        Time Complexity:
            Factorization time for ``mod`` plus ``O(S)``.
        """
        self._mod = type(self)._mod
        self.factorization = Counter(PrimeFactor.factorize(self._mod))
        self.facs: list[list[int]] = []
        self.invs: list[list[int]] = []
        self.pows: list[list[int]] = []
        for p, q in self.factorization.items():
            pq = pow(p, q)
            fac = [1] * pq
            inv = [1] * pq
            for i in range(1, pq):
                fac[i] = fac[i - 1] * (i if i % p else 1) % pq
            inv[pq - 1] = fac[pq - 1]
            for i in range(1, pq)[::-1]:
                inv[i - 1] = inv[i] * (i if i % p else 1) % pq
            self.facs.append(fac)
            self.invs.append(inv)
            pw = [1]
            while pw[-1] * p != pq:
                pw.append(pw[-1] * p)
            self.pows.append(pw)

    def _e(self, n: int, k: int, r: int, p: int) -> int:
        """Calculate the exponent of p in n!/(k!r!) using Legendre's formula.

        Args:
            n: Upper value (n).
            k: Lower value (k).
            r: n-k.
            p: Prime number.

        Returns:
            The exponent of p in n!/(k!r!).
        """
        e = 0
        while n:
            n //= p
            k //= p
            r //= p
            e += n - k - r
        return e

    def _lucas(self, n: int, k: int, p: int, q: int, i: int) -> int:
        """Compute a binomial coefficient modulo a prime power.

        Args:
            n: Upper value of binomial coefficient.
            k: Lower value of binomial coefficient.
            p: Prime factor of modulus.
            q: Power of prime in modulus.
            i: Index in pre-computed arrays.

        Returns:
            Value of binomial coefficient modulo p^q.
        """
        pw: list[int] = self.pows[i]
        fac: list[int] = self.facs[i]
        inv: list[int] = self.invs[i]
        r: int = n - k
        pq: int = pow(p, q)
        e: int = self._e(n, k, r, p)
        if e >= len(pw): return 0
        res: int = pw[e]
        if (p != 2 or q < 3) and self._e(n // pw[-1], k // pw[-1], r // pw[-1], p) % 2:
            res = -res
        while n:
            res = (res * fac[n % pq] % pq * inv[k % pq] % pq * inv[r % pq]) % pq
            n //= p
            k //= p
            r //= p
        return res

    def binom(self, n: int, k: int) -> int:
        """
        Compute the binomial coefficient n choose k modulo the modulus selected at construction.

        Args:
            n: Upper value of the binomial coefficient.
            k: Lower value of the binomial coefficient.

        Returns:
            C(n, k) modulo the construction modulus; 0 if n < 0, k < 0,
            or k > n. The result is also 0 for modulus 1.

        Notes:
            Unlike FactorialMod, this method can handle arbitrarily large n and k values
            without precomputation limits.

        Time Complexity:
            ``O(P log n + P log mod)``

        Space Complexity:
            ``O(P)``
        """
        if k < 0 or k > n: return 0
        if k == 0 or k == n: return 1 % self._mod
        r: list[int] = []
        m: list[int] = []
        for i, p in enumerate(self.factorization):
            q = self.factorization[p]
            r.append(self._lucas(n, k, p, q, i))
            m.append(pow(p, q))
        res, _ = chinese_remainder_theorem(r, m)
        return res

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the default modulus for future instances.

        Args:
            mod: Positive modulus, not necessarily prime.

        Returns:
            None. Existing instances keep their modulus.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod < 1:
            raise ValueError('mod must be at least 1')
        cls._mod = mod
