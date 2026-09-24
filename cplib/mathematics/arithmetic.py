#!/usr/bin/env python3

from __future__ import annotations

from array import array
from math import isqrt, gcd
from collections import Counter

from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.sieve import enumerate_primes
from cplib.mathematics.modular import (
    chinese_remainder_theorem as chinese_remainder_theorem,
    discrete_logarithm as discrete_logarithm,
    extended_gcd as extended_gcd,
    kth_root_mod as kth_root_mod,
    sqrt_mod as sqrt_mod,
    tonelli_shanks,
)


class GaussianInteger:
    """
    Gaussian integer ``real + imag * i``.

    Args:
        real: Real part.
        imag: Imaginary part.

    Space Complexity:
        O(1)
    """

    __slots__ = ('real', 'imag')

    def __init__(self, real: int, imag: int = 0) -> None:
        """Initialize a Gaussian integer.

        Args:
            real: Integer real coordinate.
            imag: Integer imaginary coordinate, defaulting to zero.

        Returns:
            None.

        Time Complexity:
            O(1) integer operations.
        """
        self.real = real
        self.imag = imag

    def norm(self) -> int:
        """
        Return ``real^2 + imag^2``.

        Returns:
            Norm of this Gaussian integer.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return self.real * self.real + self.imag * self.imag

    def conjugate(self) -> 'GaussianInteger':
        """
        Return the complex conjugate.

        Returns:
            ``real - imag * i``.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return GaussianInteger(self.real, -self.imag)

    def rotate_first_quadrant(self) -> 'GaussianInteger':
        """
        Multiply by a unit until both coordinates are non-negative.

        Returns:
            An associate in the first quadrant.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        real, imag = self.real, self.imag
        while real < 0 or imag < 0:
            real, imag = -imag, real
        return GaussianInteger(real, imag)

    def to_tuple(self) -> tuple[int, int]:
        """
        Convert to ``(real, imag)``.

        Returns:
            Pair of real and imaginary parts.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return self.real, self.imag

    def __mul__(self, other: 'GaussianInteger') -> 'GaussianInteger':
        """Multiply two Gaussian integers.

        Args:
            other: Other factor.

        Returns:
            A new Gaussian integer containing the product.

        Time Complexity:
            O(1) integer operations.
        """
        return GaussianInteger(self.real * other.real - self.imag * other.imag, self.real * other.imag + self.imag * other.real)

    def __pow__(self, n: int) -> 'GaussianInteger':
        """Raise this Gaussian integer to a nonnegative integer power.

        Args:
            n: Nonnegative exponent; exponent zero returns 1, including 0**0.

        Returns:
            A new Gaussian integer containing the power.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(log(n + 1)) integer operations.
        """
        if n < 0:
            raise ValueError('exponent must be nonnegative')
        res = GaussianInteger(1, 0)
        base = self
        while n:
            if n & 1:
                res = res * base
            base = base * base
            n >>= 1
        return res

    @staticmethod
    def _div_round(num: int, den: int) -> int:
        if num >= 0:
            return (2 * num + den) // (2 * den)
        return -((2 * (-num) + den) // (2 * den))

    @classmethod
    def divmod(cls, a: 'GaussianInteger', b: 'GaussianInteger') -> tuple['GaussianInteger', 'GaussianInteger']:
        """
        Divide ``a`` by ``b`` with nearest Gaussian integer quotient.

        Args:
            a: Dividend.
            b: Nonzero divisor.

        Returns:
            Pair ``(q, r)`` such that ``a = b*q + r`` and ``norm(r) < norm(b)``.

        Raises:
            ZeroDivisionError: If b is zero.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        den = b.norm()
        real_num = a.real * b.real + a.imag * b.imag
        imag_num = a.imag * b.real - a.real * b.imag
        q = GaussianInteger(cls._div_round(real_num, den), cls._div_round(imag_num, den))
        r = GaussianInteger(a.real - (b.real * q.real - b.imag * q.imag), a.imag - (b.real * q.imag + b.imag * q.real))
        return q, r

    @classmethod
    def gcd(cls, a: 'GaussianInteger', b: 'GaussianInteger') -> 'GaussianInteger':
        """
        Compute a greatest common divisor in ``Z[i]``.

        Args:
            a: First Gaussian integer.
            b: Second Gaussian integer.

        Returns:
            A greatest common divisor, up to multiplication by a unit.

        Time Complexity:
            O(log(max(norm(a), norm(b))))

        Space Complexity:
            O(1)
        """
        while b.real or b.imag:
            _, r = cls.divmod(a, b)
            a, b = b, r
        return a


class NimProduct64:
    """
    Nim product for unsigned 64-bit integers.

    This uses the bilinearity over xor and precomputes 8-bit block products.

    Space Complexity:
        O(1) per value, plus fixed-size class tables after initialization.
    """

    _pow_table: list[list[int]] = []
    _subtables: list[array[int]] = []

    @classmethod
    def _mul_power(cls, a: int, b: int, memo: dict[tuple[int, int], int]) -> int:
        if a < b:
            a, b = b, a
        key = (a, b)
        if key in memo:
            return memo[key]
        if b == 0:
            res = 1 << a
        else:
            common = a & b
            if common == 0:
                res = 1 << (a | b)
            else:
                h = common & -common
                rest = cls._mul_power(a ^ h, b ^ h, memo)
                res = 0
                x = rest
                while x:
                    lsb = x & -x
                    e = lsb.bit_length() - 1
                    res ^= cls._mul_power(e, h, memo)
                    res ^= cls._mul_power(e, h - 1, memo)
                    x ^= lsb
        memo[key] = res
        return res

    @classmethod
    def _prepare(cls) -> None:
        if cls._subtables:
            return

        memo: dict[tuple[int, int], int] = {}
        cls._pow_table = [[cls._mul_power(i, j, memo) for j in range(64)] for i in range(64)]

        subtables: list[array[int]] = []
        for e in range(8):
            for f in range(8):
                basis = [[0] * 256 for _ in range(8)]
                for p in range(8):
                    row = basis[p]
                    for y in range(1, 256):
                        lsb = y & -y
                        q = lsb.bit_length() - 1
                        row[y] = row[y ^ lsb] ^ cls._pow_table[e * 8 + p][f * 8 + q]

                table = array('Q', [0]) * 65536
                for x in range(1, 256):
                    lsb = x & -x
                    p = lsb.bit_length() - 1
                    prev = (x ^ lsb) << 8
                    cur = x << 8
                    row = basis[p]
                    for y in range(256):
                        table[cur | y] = table[prev | y] ^ row[y]
                subtables.append(table)
        cls._subtables = subtables

    @classmethod
    def multiply(cls, a: int, b: int) -> int:
        """
        Return the nim product ``a ⊗ b``.

        Args:
            a: First unsigned 64-bit integer.
            b: Second unsigned 64-bit integer.

        Returns:
            Nim product of ``a`` and ``b``.

        Raises:
            ValueError: If an operand is outside [0, 2**64).

        Time Complexity:
            ``O(64)`` after precomputation.

        Space Complexity:
            ``O(2^22)`` for the 8-bit block product tables.
        """
        if not 0 <= a < 1 << 64 or not 0 <= b < 1 << 64:
            raise ValueError('operands must be unsigned 64-bit integers')
        cls._prepare()
        res = 0
        for e in range(8):
            x = (a >> (e * 8)) & 255
            for f in range(8):
                y = (b >> (f * 8)) & 255
                res ^= cls._subtables[e * 8 + f][(x << 8) | y]
        return res


def _two_square_sum_prime(p: int) -> GaussianInteger:
    if p == 2:
        return GaussianInteger(1, 1)
    r = tonelli_shanks(-1, p)
    a, b = p, r
    while b * b > p:
        a, b = b, a % b
    c = isqrt(p - b * b)
    return GaussianInteger(b, c)


def two_square_sum(n: int) -> list[tuple[int, int]]:
    """
    Enumerate representations of ``n`` as a sum of two squares.

    This returns all pairs ``(x, y)`` of non-negative integers satisfying
    ``x^2 + y^2 = n``. If ``x != y`` and both coordinates are nonzero, both
    ``(x, y)`` and ``(y, x)`` are included.

    Args:
        n: Number to represent.

    Returns:
        List of pairs ``(x, y)`` such that ``x^2 + y^2 = n``.

    Time Complexity:
        Factorization time for ``n``, plus output-size polynomial arithmetic.

    Space Complexity:
        O(R + omega(n)) where ``R`` is the number of returned pairs.
    """
    if n < 0:
        return []
    if n == 0:
        return [(0, 0)]

    counts = Counter(PrimeFactor.factorize(n))
    res: list[GaussianInteger] = [GaussianInteger(1, 0)]

    for p, c in counts.items():
        next_res: list[GaussianInteger] = []
        if p % 4 == 3:
            if c & 1:
                return []
            mul = p ** (c // 2)
            for z in res:
                next_res.append(GaussianInteger(z.real * mul, z.imag * mul))
        elif p == 2:
            mul = GaussianInteger(1, 1) ** c
            for z in res:
                next_res.append(z * mul)
        else:
            base = _two_square_sum_prime(p)
            conj = base.conjugate()
            factors: list[GaussianInteger] = []
            for i in range(c + 1):
                factors.append((base ** i) * (conj ** (c - i)))
            for z in res:
                for mul in factors:
                    next_res.append(z * mul)
        res = next_res

    ans: list[tuple[int, int]] = []
    for z in res:
        real, imag = z.rotate_first_quadrant().to_tuple()
        ans.append((real, imag))
        if real == 0 or imag == 0:
            ans.append((imag, real))
    return sorted(ans)


def linear_indeterminate_equation(a: int, b: int, c: int) -> 'tuple[bool, int, int]':
    """
    Solve the linear Diophantine equation ax + by = c.

    This function finds a particular integer solution (x, y) to the equation ax + by = c if it exists.

    Args:
        a: The coefficient of x.
        b: The coefficient of y.
        c: The constant term.

    Returns:
        (True, x, y) for one solution, or (False, 0, 0) if no solution exists.

    Notes:
    The function uses the extended Euclidean algorithm. If gcd(a, b) divides c, then a solution exists.
    Moreover, if (x, y) is a solution, then all solutions are given by:
    x = x + (b/gcd(a,b))*t
    y = y - (a/gcd(a,b))*t
    where t is any integer.

    Time Complexity:
        O(log(min(abs(a), abs(b)) + 1)) integer operations

    Space Complexity:
        O(1)
    """
    if a == 0 and b == 0:
        return c == 0, 0, 0
    if a == 0:
        return (True, 0, c // b) if c % b == 0 else (False, 0, 0)
    if b == 0:
        return (True, c // a, 0) if c % a == 0 else (False, 0, 0)
    gcd_val, x = extended_gcd(a, abs(b))
    if c % gcd_val != 0:
        return False, 0, 0
    multiplier = c // gcd_val
    x *= multiplier
    y = (c - a * x) // b
    return True, x, y


def linear_indeterminate_equation_min_abs_sum(a: int, b: int, c: int) -> 'tuple[bool, int, int]':
    """
    Solve ``a * x + b * y = c`` while minimizing ``abs(x) + abs(y)``.

    Args:
        a: Coefficient of x.
        b: Coefficient of y.
        c: Constant term.

    Returns:
        (True, x, y) for a minimum solution, or (False, 0, 0) if none exists.

    Among solutions with the same minimum ``abs(x) + abs(y)``, a solution with
    ``x <= y`` is preferred when such a solution exists.

    Time Complexity:
        O(log(min(abs(a), abs(b)) + 1)) integer operations

    Space Complexity:
        O(1)
    """

    if a == 0 and b == 0:
        return c == 0, 0, 0
    if a == 0:
        if c % b != 0:
            return False, 0, 0
        return True, 0, c // b
    if b == 0:
        if c % a != 0:
            return False, 0, 0
        return True, c // a, 0

    aa = abs(a)
    bb = abs(b)
    old_r, r = aa, bb
    old_x, x = 1, 0
    old_y, y = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_x, x = x, old_x - q * x
        old_y, y = y, old_y - q * y
    g = old_r
    if c % g != 0:
        return False, 0, 0

    if a < 0:
        old_x = -old_x
    if b < 0:
        old_y = -old_y
    mul = c // g
    x0 = old_x * mul
    y0 = old_y * mul
    dx = b // g
    dy = a // g

    candidates = {0}
    for num, den in [(-x0, dx), (y0, dy)]:
        if den == 0:
            continue
        t = num // den
        for dt in range(-3, 4):
            candidates.add(t + dt)

    best_x = x0
    best_y = y0
    best_key = (abs(best_x) + abs(best_y), 0 if best_x <= best_y else 1, best_x, best_y)
    for t in candidates:
        nx = x0 + dx * t
        ny = y0 - dy * t
        key = (abs(nx) + abs(ny), 0 if nx <= ny else 1, nx, ny)
        if key < best_key:
            best_key = key
            best_x = nx
            best_y = ny
    return True, best_x, best_y


def linear_indeterminate_equation_with_limits(a: int, b: int, c: int, x_min: int, x_max: int, y_min: int, y_max: int) -> 'tuple[bool, int, int]':
    """
    Solve the linear Diophantine equation ax + by = c with constraints on the solution.

    This function finds a particular integer solution (x, y) to the equation ax + by = c if it exists, subject to the constraints:
    x_min <= x <= x_max
    y_min <= y <= y_max

    Args:
        a: The coefficient of x.
        b: The coefficient of y.
        c: The constant term.
        x_min: The minimum value for x.
        x_max: The maximum value for x.
        y_min: The minimum value for y.
        y_max: The maximum value for y.

    Returns:
        (True, x, y) for one solution, or (False, 0, 0) if no solution exists.

    Notes:
    The function uses the extended Euclidean algorithm. If gcd(a, b) divides c, then a solution exists.
    Moreover, if (x, y) is a solution, then all solutions are given by:
    x = x + (b/gcd(a,b))*t
    y = y - (a/gcd(a,b))*t
    where t is any integer.

    Raises:
        AssertionError: If ``x_min <= x_max and y_min <= y_max`` is false.

    Time Complexity:
        O(log(min(abs(a), abs(b)) + 1)) integer operations

    Space Complexity:
        O(1)
    """
    assert x_min <= x_max and y_min <= y_max
    exist, x, y = linear_indeterminate_equation(a, b, c)
    if not exist:
        return False, 0, 0
    if a == 0 and b == 0:
        return True, x_min, y_min
    if a == 0:
        return (True, x_min, y) if y_min <= y <= y_max else (False, 0, 0)
    if b == 0:
        return (True, x, y_min) if x_min <= x <= x_max else (False, 0, 0)
    divisor = gcd(a, b)
    step_x = b // divisor
    step_y = -a // divisor
    if step_x > 0:
        t_min = -((x - x_min) // step_x)
        t_max = (x_max - x) // step_x
    else:
        t_min = -((x_max - x) // -step_x)
        t_max = (x - x_min) // -step_x
    if step_y > 0:
        t_min = max(t_min, -((y - y_min) // step_y))
        t_max = min(t_max, (y_max - y) // step_y)
    else:
        t_min = max(t_min, -((y_max - y) // -step_y))
        t_max = min(t_max, (y - y_min) // -step_y)
    if t_min > t_max:
        return False, 0, 0
    return True, x + step_x * t_min, y + step_y * t_min


def linear_congruence(a: int, b: int, m: int) -> 'tuple[bool, int]':
    """
    Solve the linear congruence equation a * x ≡ b (mod m).

    This function finds a particular integer solution x to the equation a * x ≡ b (mod m) if it exists.

    Args:
        a: Coefficient.
        b: Remainder.
        m: Modulus.

    Returns:
        (True, x) for the smallest nonnegative solution, or (False, 0)
        if no solution exists.

    Notes:
    The function uses the extended Euclidean algorithm. A solution exists if and only if gcd(a, m) divides b.
    Moreover, if x_0 is a solution, then all solutions are given by:
    x = x_0 + (m/gcd(a,m))*t
    where t is any integer.

    Raises:
        AssertionError: If ``m > 0`` is false.

    Time Complexity:
        O(log(min(abs(a), m) + 1)) integer operations

    Space Complexity:
        O(1)
    """
    assert m > 0
    gcd_val, inv_a = extended_gcd(a, m)
    if b % gcd_val != 0:
        return False, 0
    x = inv_a * b // gcd_val % (m // gcd_val)
    return True, x


class GcdConvolution:
    """
    A class for computing convolutions based on Greatest Common Divisor (GCD).

    This class provides methods for computing GCD-based convolutions using Möbius inversion.
    The convolution is computed modulo 998244353 (a prime commonly used in competitive programming).

    The GCD convolution of two sequences a and b is defined as:
    c[k] = Σ{gcd(i,j)=k} a[i] * b[j]
    where the sum is taken over all pairs (i,j) whose GCD equals k.

    Methods:
        zeta: Compute the zeta transform of a sequence.
        mobius: Compute the Möbius transform of a sequence.
        convolution: Compute the GCD convolution of two sequences.

    Examples:
        >>> a = [0, 1, 1]  # 1-indexed array
        >>> b = [0, 1, 1]
        >>> # c[1] = 3 because there are 3 pairs with gcd=1:
        >>> #   - gcd(1,1) = 1
        >>> #   - gcd(1,2) = 1
        >>> #   - gcd(2,1) = 1
        >>> # c[2] = 1 because there is 1 pair with gcd=2:
        >>> #   - gcd(2,2) = 2
        >>> GcdConvolution.convolution(a, b)
        [0, 3, 1]

    Raises:
        AssertionError: If convolution operands have different lengths.

    Space Complexity:
        - ``O(N)``

    Complexity Notation:
        ``N`` is the length of the input sequence, including the unused index
        ``0`` in the 1-indexed representation.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the modulus for this convolution class.

        Args:
            mod: Modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is nonpositive; the current modulus is unchanged.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            Current positive modulus.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def zeta(cls, arr: list[int]) -> list[int]:
        """
        Compute the zeta transform of a sequence.

        The zeta transform converts a sequence to its multiple-sum representation:
        zeta(f)[n] = Σ{n|m} f[m]
        where the sum is over multiples m of n within the input length.

        Args:
            arr: Input sequence (1-indexed). Slot zero is unused and passed
                through modulo the current modulus; the input is not modified.

        Returns:
            The zeta transform of the input sequence.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        n = len(arr)
        res = [value % cls._mod for value in arr]
        for i in enumerate_primes(n - 1):
            for j in range((n - 1) // i , 0, -1):
                res[j] += res[i * j]
                res[j] %= cls._mod
        return res

    @classmethod
    def mobius(cls, arr: list[int]) -> list[int]:
        """
        Compute the Möbius transform (inverse of zeta transform) of a sequence.

        This transform inverts the zeta transform using the Möbius inversion formula:
        f[n] = Σ{n|m} μ(m/n) * g[m]
        where g is the zeta transform of f and μ is the Möbius function.

        Args:
            arr: Input sequence (1-indexed). Slot zero is unused and passed
                through modulo the current modulus; the input is not modified.

        Returns:
            The Möbius transform of the input sequence.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        n = len(arr)
        res = [value % cls._mod for value in arr]
        for i in enumerate_primes(n - 1):
            for j in range(i, n, i):
                res[j // i] -= res[j]
                res[j // i] %= cls._mod
        return res

    @classmethod
    def convolution(cls, a: list[int], b: list[int]) -> list[int]:
        """
        Compute the GCD convolution of two sequences.

        For two sequences a and b, computes sequence c where:
        c[k] = Σ{gcd(i,j)=k} a[i] * b[j]
        The sum is taken over all pairs (i,j) whose GCD equals k.

        Args:
            a: First sequence (1-indexed).
            b: Second sequence (1-indexed).

        Returns:
            The GCD convolution of the input sequences.

        Examples:
            >>> a = [0, 1, 1]  # 1-indexed array
            >>> b = [0, 1, 1]
            >>> # Result explanation:
            >>> # c[1] = 3: from pairs (1,1), (1,2), (2,1) where gcd=1
            >>> # c[2] = 1: from pair (2,2) where gcd=2
            >>> GcdConvolution.convolution(a, b)
            [0, 3, 1]

        Raises:
            AssertionError: If ``len(a) == len(b)`` is false.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        assert len(a) == len(b)
        zeta_a = cls.zeta(a)
        zeta_b = cls.zeta(b)
        res = [0] * len(a)
        for i in range(1, len(a)):
            res[i] = zeta_a[i] * zeta_b[i]
            res[i] %= cls._mod
        return cls.mobius(res)


class LcmConvolution:
    """
    A class for computing convolutions based on Least Common Multiple (LCM).

    This class provides methods for computing LCM-based convolutions using Möbius inversion.
    The convolution is computed modulo 998244353 (a prime commonly used in competitive programming).

    The LCM convolution of two sequences a and b is defined as:
    c[k] = Σ{lcm(i,j)=k} a[i] * b[j]
    where the sum is taken over all pairs (i,j) whose LCM equals k.

    Methods:
        zeta: Compute the zeta transform of a sequence.
        mobius: Compute the Möbius transform of a sequence.
        convolution: Compute the LCM convolution of two sequences.

    Examples:
        >>> a = [0, 1, 1]  # 1-indexed array
        >>> b = [0, 1, 1]
        >>> # c[1] = 1 because there is 1 pair with lcm=1:
        >>> #   - lcm(1,1) = 1
        >>> # c[2] = 3 because there are 3 pairs with lcm=2:
        >>> #   - lcm(1,2) = 2
        >>> #   - lcm(2,1) = 2
        >>> #   - lcm(2,2) = 2
        >>> LcmConvolution.convolution(a, b)
        [0, 1, 3]

    Raises:
        AssertionError: If convolution operands have different lengths.

    Space Complexity:
        - ``O(N)``

    Complexity Notation:
        ``N`` is the length of the input sequence, including the unused index
        ``0`` in the 1-indexed representation.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set the modulus for this convolution class.

        Args:
            mod: Modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is nonpositive; the current modulus is unchanged.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            Current positive modulus.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def zeta(cls, arr: list[int]) -> list[int]:
        """
        Compute the zeta transform of a sequence.

        The zeta transform converts a sequence to its divisor-sum representation:
        zeta(f)[n] = Σ{d|n} f[d]
        where the sum is over positive divisors d of n.

        Args:
            arr: Input sequence (1-indexed). Slot zero is unused and passed
                through modulo the current modulus; the input is not modified.

        Returns:
            The zeta transform of the input sequence.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        n = len(arr)
        res = [value % cls._mod for value in arr]
        for i in enumerate_primes(n - 1):
            for j in range(1, (n - 1) // i + 1):
                res[i * j] += res[j]
                res[i * j] %= cls._mod
        return res

    @classmethod
    def mobius(cls, arr: list[int]) -> list[int]:
        """
        Compute the Möbius transform (inverse of zeta transform) of a sequence.

        This transform inverts the zeta transform using the Möbius inversion formula:
        f[n] = Σ{d|n} μ(n/d) * g[d]
        where g is the zeta transform of f and μ is the Möbius function.

        Args:
            arr: Input sequence (1-indexed). Slot zero is unused and passed
                through modulo the current modulus; the input is not modified.

        Returns:
            The Möbius transform of the input sequence.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        n = len(arr)
        res = [value % cls._mod for value in arr]
        for i in enumerate_primes(n - 1):
            for j in range((n - 1) // i * i, 0, -i):
                res[j] -= res[j // i]
                res[j] %= cls._mod
        return res

    @classmethod
    def convolution(cls, a: list[int], b: list[int]) -> list[int]:
        """
        Compute the LCM convolution of two sequences.

        For two sequences a and b, computes sequence c where:
        c[k] = Σ{lcm(i,j)=k} a[i] * b[j]
        The sum is taken over all pairs (i,j) whose LCM equals k.

        Args:
            a: First sequence (1-indexed).
            b: Second sequence (1-indexed).

        Returns:
            The LCM convolution of the input sequences.

        Examples:
            >>> a = [0, 1, 1]  # 1-indexed array
            >>> b = [0, 1, 1]
            >>> # Result explanation:
            >>> # c[1] = 1: from pair (1,1) where lcm=1
            >>> # c[2] = 3: from pairs (1,2), (2,1), (2,2) where lcm=2
            >>> LcmConvolution.convolution(a, b)
            [0, 1, 3]

        Raises:
            AssertionError: If ``len(a) == len(b)`` is false.

        Time Complexity:
            O(N log log N)

        Space Complexity:
            O(N)
        """
        assert len(a) == len(b)
        zeta_a = cls.zeta(a)
        zeta_b = cls.zeta(b)
        res = [0] * len(a)
        for i in range(1, len(a)):
            res[i] = zeta_a[i] * zeta_b[i]
            res[i] %= cls._mod
        return cls.mobius(res)
