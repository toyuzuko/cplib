#!/usr/bin/env python3

from __future__ import annotations

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.modular import batch_inverse_mod, sqrt_mod
from cplib.mathematics.utility import xorshift64
from collections.abc import Iterable, Sequence

from typing import TypeAlias, overload
from itertools import zip_longest
import heapq

FPS: TypeAlias = 'FormalPowerSeriesMod'
PolynomialLike: TypeAlias = 'Sequence[int] | FormalPowerSeriesMod'


def _polynomial_coefficients(poly: PolynomialLike) -> Sequence[int]:
    if isinstance(poly, FormalPowerSeriesMod):
        return poly.coef
    return poly


def polynomial_trim(coeffs: PolynomialLike, mod: int | None = None) -> list[int]:
    """
    Normalize a low-to-high polynomial coefficient list by reducing modulo
    ``mod`` and removing trailing zeros.

    Args:
        coeffs: Coefficients in ascending-degree order, or a
            ``FormalPowerSeriesMod``.
        mod: Positive modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is used.

    Returns:
        Trimmed coefficient list. The zero polynomial is returned as ``[0]``.

    Raises:
        ValueError: If mod is not positive.

    Time Complexity:
        ``O(n)``

    Space Complexity:
        ``O(n)``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    coeffs = _polynomial_coefficients(coeffs)
    res = [c % mod for c in coeffs]
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    if not res:
        return [0]
    return res


def polynomial_normalize_monic(coeffs: PolynomialLike, mod: int | None = None) -> list[int]:
    """
    Normalize a non-zero polynomial to monic form.

    Args:
        coeffs: Coefficients in ascending-degree order, or a
            ``FormalPowerSeriesMod``.
        mod: Prime modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is
            used.

    Returns:
        Monic polynomial with the same roots. The zero polynomial is returned
        as ``[0]``.

    Raises:
        ValueError: If mod is not positive, or an inverse required by the
            operation does not exist modulo mod.

    Time Complexity:
        ``O(n)``

    Space Complexity:
        ``O(n)``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    res = polynomial_trim(coeffs, mod)
    if len(res) == 1 and res[0] == 0:
        return [0]
    inv = pow(res[-1], -1, mod)
    return [(c * inv) % mod for c in res]


def polynomial_add(left: PolynomialLike, right: PolynomialLike, mod: int | None = None) -> list[int]:
    """
    Add two low-to-high polynomials.

    Args:
        left: Left polynomial as coefficients or ``FormalPowerSeriesMod``.
        right: Right polynomial as coefficients or ``FormalPowerSeriesMod``.
        mod: Positive modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is used.

    Returns:
        ``left + right`` in trimmed low-to-high form; [0] for zero.

    Raises:
        ValueError: If mod is not positive.

    Time Complexity:
        ``O(max(n, m))``

    Space Complexity:
        ``O(max(n, m))``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    left = _polynomial_coefficients(left)
    right = _polynomial_coefficients(right)
    size = max(len(left), len(right))
    res = [0] * size
    left_len = len(left)
    right_len = len(right)
    for i in range(size):
        value = 0
        if i < left_len:
            value += left[i]
        if i < right_len:
            value += right[i]
        res[i] = value % mod
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res or [0]


def polynomial_sub(left: PolynomialLike, right: PolynomialLike, mod: int | None = None) -> list[int]:
    """
    Subtract two low-to-high polynomials.

    Args:
        left: Left polynomial as coefficients or ``FormalPowerSeriesMod``.
        right: Right polynomial as coefficients or ``FormalPowerSeriesMod``.
        mod: Positive modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is used.

    Returns:
        ``left - right`` in trimmed low-to-high form; [0] for zero.

    Raises:
        ValueError: If mod is not positive.

    Time Complexity:
        ``O(max(n, m))``

    Space Complexity:
        ``O(max(n, m))``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    left = _polynomial_coefficients(left)
    right = _polynomial_coefficients(right)
    size = max(len(left), len(right))
    res = [0] * size
    left_len = len(left)
    right_len = len(right)
    for i in range(size):
        value = 0
        if i < left_len:
            value += left[i]
        if i < right_len:
            value -= right[i]
        res[i] = value % mod
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res or [0]


def polynomial_mul_naive(left: PolynomialLike, right: PolynomialLike, mod: int | None = None) -> list[int]:
    """
    Multiply two low-to-high polynomials by the quadratic algorithm.

    Args:
        left: Left polynomial as coefficients or ``FormalPowerSeriesMod``.
        right: Right polynomial as coefficients or ``FormalPowerSeriesMod``.
        mod: Positive modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is used.

    Returns:
        Product polynomial in trimmed low-to-high form.

    Raises:
        ValueError: If mod is not positive.

    Time Complexity:
        ``O(nm)``

    Space Complexity:
        ``O(n + m)``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    left = polynomial_trim(left, mod)
    right = polynomial_trim(right, mod)
    if len(left) == 1 and left[0] == 0:
        return [0]
    if len(right) == 1 and right[0] == 0:
        return [0]
    res = [0] * (len(left) + len(right) - 1)
    for i, li in enumerate(left):
        if li == 0:
            continue
        for j, rj in enumerate(right):
            res[i + j] += li * rj
            res[i + j] %= mod
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res


def polynomial_divmod_naive(left: PolynomialLike, right: PolynomialLike, mod: int | None = None) -> tuple[list[int], list[int]]:
    """
    Divide low-to-high polynomials by the quadratic algorithm.

    Args:
        left: Dividend polynomial as coefficients or ``FormalPowerSeriesMod``.
        right: Divisor polynomial as coefficients or ``FormalPowerSeriesMod``.
        mod: Prime modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is
            used.

    Returns:
        Pair ``(quotient, remainder)`` in trimmed low-to-high form.

    Raises:
        ZeroDivisionError: If ``right`` is the zero polynomial.
        ValueError: If mod is not positive, or an inverse required by the
            operation does not exist modulo mod.

    Time Complexity:
        ``O((n - m + 1) m)``

    Space Complexity:
        ``O(n + m)``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    rem = polynomial_trim(left, mod)
    divisor = polynomial_trim(right, mod)
    if len(divisor) == 1 and divisor[0] == 0:
        raise ZeroDivisionError('polynomial division by zero')
    if len(rem) < len(divisor):
        return [0], rem
    quotient = [0] * (len(rem) - len(divisor) + 1)
    inv_lead = pow(divisor[-1], -1, mod)
    divisor_degree = len(divisor) - 1
    while len(rem) >= len(divisor) and not (len(rem) == 1 and rem[0] == 0):
        degree_diff = len(rem) - len(divisor)
        coeff = rem[-1] * inv_lead % mod
        quotient[degree_diff] = coeff
        if coeff:
            for i in range(divisor_degree + 1):
                rem[degree_diff + i] -= coeff * divisor[i]
                rem[degree_diff + i] %= mod
        while len(rem) > 1 and rem[-1] == 0:
            rem.pop()
    while len(quotient) > 1 and quotient[-1] == 0:
        quotient.pop()
    return quotient, rem


def polynomial_is_zero(coeffs: PolynomialLike, mod: int | None = None) -> bool:
    """
    Return whether all coefficients are zero modulo ``mod``.

    Args:
        coeffs: Coefficients in ascending-degree order, or a
            ``FormalPowerSeriesMod``.
        mod: Positive modulus. If omitted, ``FormalPowerSeriesMod.get_mod()`` is used.

    Returns:
        True exactly when the polynomial is zero modulo mod, including empty input.

    Raises:
        ValueError: If mod is not positive.

    Time Complexity:
        ``O(n)``

    Space Complexity:
        ``O(1)``
    """
    mod = FormalPowerSeriesMod.get_mod() if mod is None else mod
    if mod <= 0:
        raise ValueError('mod must be positive')
    coeffs = _polynomial_coefficients(coeffs)
    return all(c % mod == 0 for c in coeffs)


class FormalPowerSeriesMod:
    """
    Formal power series with modular arithmetic.

    Represents a formal power series f(x) = a_0 + a_1*x + a_2*x^2 + ... + a_n*x^n
    with coefficients in Z/modZ. The series is stored as a finite list of coefficients,
    effectively representing a polynomial of degree n.

    Attributes:
        coef: Coefficient list ``[a_0, a_1, ..., a_n]``.
        _mod: Modulus used for arithmetic.
        _sparse_threshold: Threshold for sparse algorithm selection.

    Notes:
        - Arithmetic results are reduced modulo ``_mod``; zero/one tests use
          residues even when coefficients were stored without normalization.
        - Series operations preserve the stored length unless stated otherwise.
          Polynomial division ignores trailing zero coefficients instead.
        - Multiplication and multiplicative inversion use quadratic methods if
          the modulus has insufficient NTT capacity.
        - The stored length can exceed degree() + 1 because of trailing zeros.
        - Sparse algorithms are used when non-zero terms <= _sparse_threshold
        - For sparse polynomials, multiplication is ``O((s + 1) n)``, where ``s`` is
          the number of non-zero terms in the sparse operand.
        - Most operations preserve the degree of the input series unless specified otherwise

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` and ``m`` are the numbers of coefficients of the operands, and
        ``s`` is the number of non-zero coefficients in a sparse polynomial.
    """
    _mod = 998244353
    _sparse_threshold = None

    def __init__(self, coef: Iterable[int]):
        """Initialize formal power series with coefficients.

        Args:
            coef: Coefficients [a_0, a_1, ..., a_n] for polynomial a_0 + a_1*x + ... + a_n*x^n

        Returns:
            None.

        Time Complexity:
            O(n)

        Notes:
            - Coefficients are stored as supplied; arithmetic operations reduce
              their results modulo ``_mod``.
            - Empty list creates the zero polynomial
            - The highest stored index is len(coef) - 1; degree() ignores trailing
              zero residues.
        """
        self.coef = list(coef)

    def __len__(self) -> int:
        return len(self.coef)

    def __str__(self) -> str:
        return ' '.join(map(str, self.coef))

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set modulus for all operations.

        Args:
            mod: Prime modulus (998244353 is recommended)

        Returns:
            None.

        Raises:
            ValueError: If mod is not prime. Above 64 bits, primality testing
                is probabilistic.

        Notes:
            Applies to existing and future series. Multiplication and
            multiplicative inversion fall back to quadratic methods when NTT
            capacity is insufficient. Other direct transforms may still require
            a suitable modulus; integration/log/exp require length <= mod.
            998244353 is recommended.

        Time Complexity:
            Same as ConvolutionMod.set_mod if the transform modulus differs;
            O(1) otherwise.
        """
        if ConvolutionMod.get_mod() != mod:
            ConvolutionMod.set_mod(mod)
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            The prime modulus used by existing and future series.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def set_sparse_threshold(cls, threshold: int | None) -> None:
        """
        Set threshold for sparse algorithm usage.

        Args:
            threshold: Use sparse algorithms if non-zero terms <= threshold
                      None to disable automatic sparse selection. Must be
                      non-negative when specified. Capacity fallbacks still apply.

        Returns:
            None.

        Raises:
            ValueError: If threshold is negative.

        Time Complexity:
            O(1)
        """
        if threshold is not None and threshold < 0:
            raise ValueError('threshold must be non-negative or None')
        cls._sparse_threshold = threshold

    @overload
    def __getitem__(self, key: int) -> int:
        ...

    @overload
    def __getitem__(self, key: slice) -> FPS:
        ...

    def __getitem__(self, key: int | slice) -> int | FPS:
        if isinstance(key, slice):
            return FormalPowerSeriesMod(self.coef[key])
        if key < 0:
            raise IndexError('index must be non-negative')
        if key >= len(self.coef):
            return 0
        return self.coef[key]

    def __setitem__(self, key: int, value: int) -> None:
        if key < 0:
            raise IndexError('index must be non-negative')
        if key >= len(self.coef):
            self.coef += [0] * (key - len(self) + 1)
        self.coef[key] = value

    def nzcount(self) -> int:
        """
        Count non-zero coefficients.

        Returns:
            Number of coefficients that are nonzero modulo get_mod().

        Time Complexity:
            ``O(n)``
        """
        return sum(1 for x in self.coef if x % self._mod != 0)

    def shrink(self) -> None:
        """
        Remove trailing coefficients that are zero modulo get_mod(), in-place.

        Returns:
            None. Retained coefficients keep their original integer values.

        Time Complexity:
            O(n)
        """
        while self.coef and self.coef[-1] % self._mod == 0:
            self.coef.pop()

    def resize(self, n: int) -> FPS:
        """
        Resize to exactly n coefficients.

        Args:
            n: Target number of coefficients

        Returns:
            New FPS truncated or padded with zeros to size n; coefficients
            are retained as supplied, without reducing them modulo the modulus.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            ``O(n)``
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        if n < len(self):
            new_coef = self.coef[:n]
        else:
            new_coef = self.coef + [0] * (n - len(self))
        return FormalPowerSeriesMod(new_coef)

    def __pos__(self) -> FPS:
        return self

    def __neg__(self) -> FPS:
        return FormalPowerSeriesMod([-x % self._mod for x in self.coef])

    def __add__(self, other: int | FPS) -> FPS:
        if isinstance(other, int):
            other = FormalPowerSeriesMod([other])
        return FormalPowerSeriesMod([(x + y) % self._mod for x, y in zip_longest(self.coef, other.coef, fillvalue=0)])

    def __radd__(self, other: int | FPS) -> FPS:
        return self + other

    def __sub__(self, other: int | FPS) -> FPS:
        if isinstance(other, int):
            other = FormalPowerSeriesMod([other])
        return FormalPowerSeriesMod([(x - y) % self._mod for x, y in zip_longest(self.coef, other.coef, fillvalue=0)])

    def __rsub__(self, other: int | FPS) -> FPS:
        return -self + other

    def is_sparse(self) -> bool:
        """
        Return whether sparse algorithms should be selected by coefficient count.

        Returns:
            True if the configured threshold includes the number of nonzero
            residues. False if automatic sparse selection is disabled.

        Time Complexity:
            ``O(n)`` if sparse algorithms are enabled, because non-zero
            coefficients are counted; otherwise ``O(1)``.
        """
        return self._sparse_threshold is not None and self.nzcount() <= self._sparse_threshold

    def __mul__(self, other: int | FPS) -> FPS:
        """Multiply by scalar or another formal power series.

        Args:
            other: Scalar integer or FormalPowerSeriesMod

        Returns:
            FormalPowerSeriesMod: Product of self and other
            - Scalar multiplication preserves the stored length.
            - Nonempty series operands produce len(self) + len(other) - 1 coefficients.

        Time Complexity:
            - Scalar multiplication: O(n)
            - FPS multiplication: O((n + m) log(n + m)) using NTT
            - Insufficient NTT capacity: O(nm)
            - Sparse multiplication: O(n + (s + 1) m), where s is the number of non-zero
              terms in the sparse operand and m is the size of the other operand

        Notes:
            - Uses FFT-based convolution for general case
            - Automatically uses sparse algorithm if either operand is sparse
            - Nonempty FPS operands produce len(self) + len(other) - 1
              coefficients; if either is empty, the result is empty.
        """
        if isinstance(other, int):
            return FormalPowerSeriesMod([x * other % self._mod for x in self.coef])
        if not self.coef or not other.coef:
            return FormalPowerSeriesMod([])
        if self.is_sparse():
            return self._sparse_mul(other)
        if other.is_sparse():
            return other._sparse_mul(self)
        capacity = (self._mod - 1) & -(self._mod - 1)
        if len(self) + len(other) - 1 > capacity:
            return self._sparse_mul(other)
        if ConvolutionMod.get_mod() != self._mod:
            ConvolutionMod.set_mod(self._mod)
        return FormalPowerSeriesMod(ConvolutionMod.convolution(self.coef, other.coef))

    def __rmul__(self, other: int | FPS) -> FPS:
        return self * other

    def _sparse_mul(self, other: FPS) -> FPS:
        new_coef = [0] * (len(self) + len(other) - 1)
        nz = [i for i, x in enumerate(self.coef) if x % self._mod]
        for i, c in enumerate(other.coef):
            if not c % self._mod: continue
            for j in nz:
                new_coef[i + j] += c * self[j]
                new_coef[i + j] %= self._mod
        return FormalPowerSeriesMod(new_coef)

    def __invert__(self) -> FPS:
        """Compute multiplicative inverse (1/f).

        Returns:
            FormalPowerSeriesMod: Inverse g such that f * g ≡ 1 (mod x^n)
            - The result contains len(self) coefficients.

        Time Complexity:
            - General case: O(n log n) using Newton's method
            - Sparse case: O((s + 1) n), where s is the number of non-zero terms
            - Insufficient NTT capacity: O(n**2)

        Raises:
            ZeroDivisionError: If the constant term is zero modulo the modulus,
                including an empty input.

        Notes:
            - Can be called with ~f syntax
            - The inverse is computed modulo x^n where n = len(self)
            - For sparse polynomials, uses iterative method instead of FFT
        """
        if self[0] % self._mod == 0:
            raise ZeroDivisionError('Cannot invert power series with zero constant term')
        if self.is_sparse() or len(self) > ((self._mod - 1) & -(self._mod - 1)):
            return self._sparse_inv()
        return self._inv()

    def _sparse_inv(self) -> FPS:
        inv0 = pow(self[0], -1, self._mod)
        nz = [i for i, x in enumerate(self.coef) if x % self._mod]
        new_coef = [0] * len(self)
        new_coef[0] = inv0
        for i in range(1, len(self)):
            s = 0
            for j in nz:
                if j == 0: continue
                if j > i: break
                s -= new_coef[i - j] * self[j]
                s %= self._mod
            new_coef[i] = s * inv0 % self._mod
        return FormalPowerSeriesMod(new_coef)

    def _inv(self) -> FPS:
        if ConvolutionMod.get_mod() != self._mod:
            ConvolutionMod.set_mod(self._mod)
        n = len(self)
        r = pow(self[0], -1, self._mod)
        m = 1
        res = [r]
        while m < n:
            f = [0] * (2 * m)
            g = [0] * (2 * m)
            for i in range(2 * m):
                f[i] = self[i]
            for i in range(m):
                g[i] = res[i]
            ConvolutionMod.butterfly(f)
            ConvolutionMod.butterfly(g)
            for i in range(2 * m):
                f[i] *= g[i]
                f[i] %= self._mod
            ConvolutionMod.butterfly_inv(f)
            inv = pow(2 * m, -1, self._mod)
            for i in range(m):
                f[i] = 0
            for i in range(m, 2 * m):
                f[i] *= inv
                f[i] %= self._mod
            ConvolutionMod.butterfly(f)
            for i in range(2 * m):
                f[i] *= g[i]
                f[i] %= self._mod
            ConvolutionMod.butterfly_inv(f)
            res += [0] * m
            for i in range(m, 2 * m):
                res[i] -= f[i] * inv
                res[i] %= self._mod
            m <<= 1
        return FormalPowerSeriesMod(res).resize(n)

    def inv(self) -> FPS:
        """
        Alias for multiplicative inverse.

        Returns:
            Same as ~self

        Time Complexity:
            Same as :meth:`__invert__`.
        """
        return ~self

    def __truediv__(self, other: int | FPS) -> FPS:
        """Division by scalar or formal power series.

        Args:
            other: Scalar integer or FormalPowerSeriesMod

        Returns:
            FormalPowerSeriesMod: Quotient f/g
            - Degree of result is max(len(self), len(other)) - 1

        Time Complexity:
            - Scalar division: O(n)
            - FPS division: O(n log n), or O(n**2) without sufficient NTT capacity
            - Sparse divisor: O((s + 1) n), where s is the number of non-zero terms
              in the divisor

        Raises:
            ZeroDivisionError: If the scalar or the divisor's constant term is
                zero modulo the modulus.

        Notes:
            - For FPS division, computes f * g^(-1) modulo x^n
            - Result is truncated to max(len(self), len(other)) coefficients
        """
        if isinstance(other, int):
            if other % self._mod == 0:
                raise ZeroDivisionError('Cannot divide by zero')
            return self * pow(other, -1, self._mod)
        if other.is_sparse():
            return self._sparse_truediv(other)
        n = max(len(self), len(other))
        return (self.resize(n) * ~other.resize(n)).resize(n)

    def _sparse_truediv(self, other: FPS) -> FPS:
        if other[0] % self._mod == 0:
            raise ZeroDivisionError('Cannot divide by power series with zero constant term')
        n = max(len(self), len(other))
        inv0 = pow(other[0], -1, self._mod)
        nz = [(i, c) for i, c in enumerate(other.coef) if i > 0 and c % self._mod != 0]
        coef = [0] * n
        for i in range(n):
            s = self[i]
            for j, c in nz:
                if j > i:
                    break
                s -= c * coef[i - j]
                s %= self._mod
            coef[i] = s * inv0 % self._mod
        return FormalPowerSeriesMod(coef)

    def __rtruediv__(self, other: int | FPS) -> FPS:
        if isinstance(other, int):
            return FormalPowerSeriesMod([other])._sparse_truediv(self) if self.is_sparse() else (FormalPowerSeriesMod([other]).resize(len(self)) * ~self.resize(len(self))).resize(len(self))
        if self.is_sparse():
            return other._sparse_truediv(self)
        n = max(len(self), len(other))
        return (other.resize(n) * ~self.resize(n)).resize(n)

    def derivative(self) -> FPS:
        """
        Compute formal derivative.

        Returns:
            FormalPowerSeriesMod: Derivative f'(x) where (x^n)' = n*x^(n-1)
            - The result contains len(self) coefficients.

        Notes:
            - The constant term of the result is the coefficient of x in self
            - Preserves the stored length by padding the last coefficient with zero.

        Time Complexity:
            O(n)
        """
        coef = [0] * len(self)
        for i in range(1, len(self)):
            coef[i - 1] = self[i] * i % self._mod
        return FormalPowerSeriesMod(coef)

    def integral(self) -> FPS:
        """
        Compute formal integral with zero constant term.

        Returns:
            FormalPowerSeriesMod: Integral ∫f(x)dx where ∫x^n dx = x^(n+1)/(n+1)
            - The result contains len(self) coefficients.

        Notes:
            - The constant term of integration is always set to 0
            - Returns exactly len(self) coefficients, discarding the integrated
              term of degree len(self). Empty input returns an empty series.
            - Requires all index denominators 1..len(self)-1 to be invertible.

        Raises:
            ValueError: If len(self) > get_mod().

        Time Complexity:
            O(n)
        """
        if len(self) > self._mod:
            raise ValueError('integration requires len(self) <= mod')
        coef = [0] * len(self)
        inv = [1] * len(self)
        for i in range(2, len(self)):
            inv[i] = (self._mod - self._mod // i) * inv[self._mod % i] % self._mod
        for i in range(1, len(self)):
            coef[i] = self[i - 1] * inv[i] % self._mod
        return FormalPowerSeriesMod(coef)

    def log(self) -> FPS:
        """
        Compute formal logarithm.

        Returns:
            FormalPowerSeriesMod: log(f(x)) as formal power series
            - The result contains len(self) coefficients.

        Raises:
            ValueError: If a nonempty input's constant term is not congruent to
                one, or len(self) > get_mod().

        Notes:
            - Uses the formula log(f) = ∫(f'/f)dx
            - The constant term of the result is always 0
            - Empty input returns an empty series.
            - Multiplication and inversion may use sparse or quadratic fallbacks.

        Time Complexity:
            O(n log n) with sufficient NTT capacity, otherwise O(n**2).
        """
        if not self.coef:
            return FormalPowerSeriesMod([])
        if len(self) > self._mod:
            raise ValueError('log requires len(self) <= mod')
        if self[0] % self._mod != 1:
            raise ValueError('log of power series with constant term not equal to 1 is undefined')
        return (self.derivative() / self).integral()

    def exp(self) -> FPS:
        """
        Compute formal exponential.

        Returns:
            FormalPowerSeriesMod: exp(f(x)) as formal power series
            - The result contains len(self) coefficients.

        Time Complexity:
            - General case: O(n log n) using Newton's method
            - Sparse case: O((s + 1) n), where s is the number of non-zero terms

        Raises:
            ValueError: If the constant term is not congruent to zero,
                or len(self) > get_mod().

        Notes:
            - Computes e^f(x) using Newton's method for general case
            - For sparse polynomials, uses iterative method based on derivative
            - The constant term is one for nonempty input; empty input returns [].
            - Insufficient NTT capacity selects the O(n**2) coefficient recurrence.

        """
        if not self.coef:
            return FormalPowerSeriesMod([])
        if len(self) > self._mod:
            raise ValueError('exp requires len(self) <= mod')
        if self[0] % self._mod != 0:
            raise ValueError('exp of power series with constant term not equal to 0 is undefined')
        capacity = (self._mod - 1) & -(self._mod - 1)
        if self.is_sparse() or (2 << (len(self) - 1).bit_length()) > capacity:
            return self._sparse_exp()
        return self._exp()

    def _sparse_exp(self) -> FPS:
        inv = [1] * len(self)
        for i in range(2, len(self)):
            inv[i] = (self._mod - self._mod // i) * inv[self._mod % i] % self._mod
        coef = [0] * len(self)
        coef[0] = 1
        f = self.derivative()
        nz_coef = [(i, c) for i, c in enumerate(f.coef) if c != 0]
        for i in range(len(self) - 1):
            for j, v in nz_coef:
                if i - j < 0: continue
                coef[i + 1] += coef[i - j] * v
                coef[i + 1] %= self._mod
            coef[i + 1] *= inv[i + 1]
            coef[i + 1] %= self._mod
        return FormalPowerSeriesMod(coef)

    def _exp(self) -> FPS:
        m = 1
        n = len(self)
        res = FormalPowerSeriesMod([1])
        g = FormalPowerSeriesMod([1])
        q = self.derivative()
        m = 1
        while m < n:
            g = g * 2 - res * (g * g).resize(m)
            res = res.resize(2 * m)
            m *= 2
            w = q.resize(m) + (g * (res.derivative() - (res * q.resize(m)).resize(m))).resize(m)
            res = res + (res * (self.resize(m) - w.integral())).resize(m)
        return res.resize(n)

    def __pow__(self, k: int) -> FPS:
        """Compute k-th power of formal power series.

        Args:
            k: Non-negative exponent

        Returns:
            FormalPowerSeriesMod: f(x)^k as formal power series
            - The result contains len(self) coefficients.

        Time Complexity:
            - General case: O(n log n) using exp(k * log(f)), or O(n**2)
              if the modulus has insufficient NTT capacity.
            - If n > mod: O(n**2 log(k + 1)) by repeated squaring.
            - Sparse case: O((s + 1) n), where s is the number of non-zero terms

        Raises:
            ValueError: If k < 0

        Notes:
            - Empty input returns an empty series for every non-negative k.
            - For k = 0 and nonempty input, returns [1, 0, ..., 0] of the same length.
            - If f(x) = x^m * g(x) where g(0) ≠ 0, optimizes by factoring out x^m
            - For sparse polynomials, uses iterative method instead of exp/log
            - If the lowest degree term is x^m and k*m >= len(self), returns zero polynomial
        """
        if k < 0:
            raise ValueError('pow of power series with negative exponent is not supported')
        if not self.coef:
            return FormalPowerSeriesMod([])
        if k == 0:
            return FormalPowerSeriesMod([1] + [0] * (len(self) - 1))
        if k == 1:
            return self * 1
        if len(self) > self._mod:
            # Integer powers still exist when integration-based formulas do not.
            result = FormalPowerSeriesMod([1])
            base = self * 1
            exponent = k
            while exponent:
                if exponent & 1:
                    result = (result * base).resize(len(self))
                exponent >>= 1
                if exponent:
                    base = (base * base).resize(len(self))
            return result.resize(len(self))
        if self.is_sparse():
            return self._sparse_pow(k)
        else:
            return self._pow(k)

    def _sparse_pow(self, k: int) -> FPS:
        min_nz = len(self)
        for i, c in enumerate(self.coef):
            if c % self._mod != 0:
                min_nz = i
                break
        if k * min_nz >= len(self):
            return FormalPowerSeriesMod([0] * len(self))
        p = self.coef[min_nz]
        p_inv = pow(p, self._mod - 2, self._mod)
        g = FormalPowerSeriesMod([0] * (len(self) - min_nz * k))
        nz_coef = [(i, c) for i, c in enumerate(self.coef) if c % self._mod != 0]
        for i, c in nz_coef:
            if 0 <= i - min_nz < len(g):
                g[i - min_nz] = c * p_inv % self._mod
        g = g._sparse_pow_reg(k)
        res = FormalPowerSeriesMod([0] * len(self))
        p_pow = pow(p, k, self._mod)
        for i, c in enumerate(g.coef):
            if i < len(self) - min_nz * k:
                res[i + min_nz * k] = c * p_pow % self._mod
        return res

    def _sparse_pow_reg(self, k: int) -> FPS:
        assert self[0] == 1
        res = FormalPowerSeriesMod([0] * len(self))
        res[0] = 1
        inv = [1] * len(self)
        for i in range(2, len(self)):
            inv[i] = (self._mod - self._mod // i) * inv[self._mod % i] % self._mod
        nz_coef = [(i, c) for i, c in enumerate(self.coef) if c % self._mod != 0]
        for i in range(1, len(self)):
            for j, v in nz_coef:
                if i - j < 0: continue
                res[i] += res[i - j] * (k * j - i + j) * v
                res[i] %= self._mod
            res[i] *= inv[i]
            res[i] %= self._mod
        return res

    def _pow(self, k: int) -> FPS:
        for i, c in enumerate(self.coef):
            if c % self._mod != 0:
                min_nz = i
                min_nz_c = c
                break
        else:
            return FormalPowerSeriesMod([0] * len(self))
        res = FormalPowerSeriesMod([0] * len(self))
        length = len(self) - min_nz * k
        if length <= 0:
            return res
        g = ((self[min_nz:].resize(length) / min_nz_c).log() * k).exp()
        for i in range(max(0, len(self) - min_nz * k)):
            res[i + min_nz * k] = g[i]
        res *= pow(min_nz_c, k, self._mod)
        return res

    def __floordiv__(self, other: int | FPS) -> FPS:
        """Polynomial division (quotient).

        Args:
            other: Divisor (scalar or polynomial)

        Returns:
            FormalPowerSeriesMod: Quotient q where f = q*g + r and deg(r) < deg(g)
            - Degree of result is deg(f) - deg(g) if deg(f) >= deg(g), otherwise empty

        Time Complexity:
            - Scalar division: O(n)
            - Polynomial division: O(n log n), or O(n**2) without sufficient NTT capacity
            - Sparse division: O((s + 1) n), where s is the number of non-zero terms
              in the divisor

        Raises:
            ZeroDivisionError: If the divisor is zero modulo the modulus.

        Notes:
            - Returns empty polynomial if deg(f) < deg(g)
            - For polynomials, computes exact quotient (not truncated power series)
            - Sparse algorithm available when divisor is sparse
        """
        if isinstance(other, int):
            return self / other
        dividend = self.trimmed()
        divisor = other.trimmed()
        if not divisor.coef:
            raise ZeroDivisionError('polynomial division by zero')
        if divisor.is_sparse():
            return dividend._sparse_floordiv(divisor)
        return dividend._floordiv(divisor)

    def _sparse_floordiv(self, other: FPS) -> FPS:
        n = len(self)
        m = len(other)
        if n < m:
            return FormalPowerSeriesMod([])
        l = n - m + 1
        arr = [0] * l
        inv = pow(other[m - 1], -1, self._mod)
        tmp = self[::-1]
        nonzero = [(j, c % self._mod) for j, c in enumerate(reversed(other.coef)) if c % self._mod]
        for i in range(l):
            arr[i] = tmp[i] * inv % self._mod
            for j, c in nonzero:
                tmp[i + j] -= c * arr[i]
                tmp[i + j] %= self._mod
        return FormalPowerSeriesMod(arr[::-1])

    def _floordiv(self, other: FPS) -> FPS:
        n = len(self)
        m = len(other)
        if n < m:
            return FormalPowerSeriesMod([])
        l = n - m + 1
        res = (self[n - l:][::-1] * ~(other[::-1].resize(l))).resize(l)[::-1]
        return res

    def __rfloordiv__(self, other: int) -> FPS:
        return FormalPowerSeriesMod([other]) // self

    def __mod__(self, other: int | FPS) -> FPS:
        """Polynomial division (remainder).

        Args:
            other: Divisor (scalar or polynomial)

        Returns:
            FormalPowerSeriesMod: Remainder r where f = q*g + r and deg(r) < deg(g)
            - Degree of result is at most deg(g) - 1

        Time Complexity:
            - General case: O(n log n), or O(n**2) without sufficient NTT capacity
            - Sparse divisor: O((s + 1) n), where s is the number of non-zero terms
              in the divisor

        Raises:
            ZeroDivisionError: If the divisor is zero modulo the modulus.

        Notes:
            - For scalar divisor, always returns zero polynomial
            - Returns a normalized, trimmed copy of self if deg(f) < deg(g)
            - Trailing zeros are removed from the result
        """
        if isinstance(other, int):
            if other % self._mod == 0:
                raise ZeroDivisionError('polynomial division by zero')
            return FormalPowerSeriesMod([0])
        return self.divmod_poly(other)[1]

    def trimmed(self) -> FPS:
        """
        Return a copy with trailing zero residues removed.

        Returns:
            A new series with retained coefficients unchanged; [] for zero.

        Time Complexity:
            ``O(n)``
        """
        res = FormalPowerSeriesMod(self.coef[:])
        res.shrink()
        return res

    def degree(self) -> int:
        """
        Return the degree after ignoring trailing zero residues.

        Returns:
            Largest index with a nonzero residue, or -1 for the zero polynomial.

        Time Complexity:
            O(n)
        """
        for i in range(len(self.coef) - 1, -1, -1):
            if self.coef[i] % self._mod != 0:
                return i
        return -1

    def is_zero(self) -> bool:
        """
        Return whether all coefficients are zero modulo get_mod().

        Returns:
            True for a zero polynomial, including an empty series.

        Time Complexity:
            O(n)
        """
        return self.degree() == -1

    def div_xk(self, k: int) -> FPS:
        """
        Divide by x^k and discard negative-degree terms.

        Args:
            k: Non-negative number of low-degree coefficients to remove.

        Returns:
            A new series containing the coefficients from index k onward.

        Raises:
            ValueError: If k is negative.

        Time Complexity:
            ``O(n)``
        """
        if k < 0:
            raise ValueError('k must be non-negative')
        if k == 0:
            return FormalPowerSeriesMod(self.coef[:])
        if k >= len(self.coef):
            return FormalPowerSeriesMod([])
        return FormalPowerSeriesMod(self.coef[k:])

    def divmod_poly(self, other: FPS) -> tuple[FPS, FPS]:
        """
        Return the quotient and remainder of polynomial division.

        Args:
            other: Nonzero divisor polynomial modulo get_mod().

        Returns:
            Quotient and remainder, ignoring trailing zero residues. The zero
            polynomial is represented by an empty coefficient list.

        Raises:
            ZeroDivisionError: If other is zero modulo the modulus.

        Time Complexity:
            One polynomial division plus one multiplication/subtraction.
        """
        quotient = self // other
        remainder = (self - quotient * other).trimmed()
        return quotient, remainder

    @classmethod
    def _mat_identity(cls) -> tuple[FPS, FPS, FPS, FPS]:
        one = FormalPowerSeriesMod([1])
        zero = FormalPowerSeriesMod([0])
        return one, zero, zero, one

    @classmethod
    def _mat_step(cls, quot: FPS) -> tuple[FPS, FPS, FPS, FPS]:
        return FormalPowerSeriesMod([0]), FormalPowerSeriesMod([1]), FormalPowerSeriesMod([1]), -quot

    @classmethod
    def _mat_mul(cls, left: tuple[FPS, FPS, FPS, FPS], right: tuple[FPS, FPS, FPS, FPS]) -> tuple[FPS, FPS, FPS, FPS]:
        left_a, left_b, left_c, left_d = left
        right_a, right_b, right_c, right_d = right
        return (
            left_a * right_a + left_b * right_c,
            left_a * right_b + left_b * right_d,
            left_c * right_a + left_d * right_c,
            left_c * right_b + left_d * right_d,
        )

    @classmethod
    def _mat_apply(cls, mat: tuple[FPS, FPS, FPS, FPS], left: FPS, right: FPS) -> tuple[FPS, FPS]:
        mat_a, mat_b, mat_c, mat_d = mat
        return (mat_a * left + mat_b * right).trimmed(), (mat_c * left + mat_d * right).trimmed()

    @classmethod
    def _half_gcd(cls, left: FPS, right: FPS) -> tuple[FPS, FPS, FPS, FPS]:
        left = left.trimmed()
        right = right.trimmed()
        if left.degree() < right.degree():
            raise ValueError('half_gcd requires deg(left) >= deg(right)')
        m = len(left) >> 1
        if right.degree() < m:
            return cls._mat_identity()
        quot, rem = left.divmod_poly(right)
        mat = cls._mat_step(quot)
        left = right
        right = rem
        first = cls._half_gcd(left.div_xk(m), right.div_xk(m))
        mat = cls._mat_mul(first, mat)
        left, right = cls._mat_apply(first, left, right)
        shift = max(0, 2 * m - left.degree())
        second = cls._half_gcd(left.div_xk(shift), right.div_xk(shift))
        return cls._mat_mul(second, mat)

    @classmethod
    def gcd_transform(cls, left: FPS, right: FPS) -> tuple[FPS, tuple[FPS, FPS, FPS, FPS]]:
        """
        Compute the polynomial gcd and the associated Bezout transform.

        Args:
            left: First polynomial.
            right: Second polynomial.

        Returns:
            A pair (g, (a, b, c, d)) satisfying a*left + b*right = g and
            c*left + d*right = 0 over the current field. g is a greatest common
            divisor, not necessarily monic, with normalized coefficients and
            no trailing zeros. If both inputs are zero, g is empty and the
            matrix is the identity. Neither input is modified.

        Time Complexity:
            O(M(n) log(n + 1)), where n = max(len(left), len(right)) and M(n)
            is the multiplication cost: O(n log n) with sufficient NTT capacity,
            otherwise O(n**2).

        Space Complexity:
            O(n log(n + 1)).
        """
        left = left.trimmed()
        right = right.trimmed()
        mat = cls._mat_identity()
        while not right.is_zero():
            quot, rem = left.divmod_poly(right)
            step = cls._mat_step(quot)
            mat = cls._mat_mul(step, mat)
            left, right = right, rem
            half = cls._half_gcd(left, right)
            mat = cls._mat_mul(half, mat)
            left, right = cls._mat_apply(half, left, right)
        return left * 1, mat

    def gcd(self, other: FPS) -> FPS:
        """
        Compute the monic greatest common divisor.

        Args:
            other: Polynomial to compare with ``self``.

        Returns:
            The monic gcd with normalized coefficients and no trailing zeros.
            Two zero inputs give an empty polynomial. Neither input is modified.

        Time Complexity:
            O(M(n) log(n + 1)), where n = max(len(self), len(other)) and M(n)
            is the multiplication cost, up to O(n**2) without NTT capacity.

        Space Complexity:
            O(n log(n + 1)).
        """
        left = self.trimmed()
        right = other.trimmed()
        if left.is_zero():
            if right.is_zero():
                return FormalPowerSeriesMod([])
            return (right * pow(right[right.degree()], -1, self._mod)).trimmed()
        if right.is_zero():
            return (left * pow(left[left.degree()], -1, self._mod)).trimmed()
        gcd_poly, _ = self.gcd_transform(left, right)
        return (gcd_poly * pow(gcd_poly[gcd_poly.degree()], -1, self._mod)).trimmed()

    def pow_mod(self, exponent: int, mod_poly: FPS) -> FPS:
        """
        Compute ``self ** exponent`` modulo a polynomial.

        Args:
            exponent: Non-negative integer exponent.
            mod_poly: Nonzero polynomial modulus; trailing zero residues are ignored.

        Returns:
            The normalized remainder of self ** exponent divided by mod_poly,
            with no trailing zeros. For a nonzero constant modulus, returns an
            empty polynomial. Exponent zero gives 1 modulo mod_poly, including
            when self is zero. Neither input is modified.

        Raises:
            ValueError: If exponent is negative.
            ZeroDivisionError: If mod_poly is the zero polynomial.

        Time Complexity:
            One initial reduction of self, then O(log(exponent + 1)) polynomial
            multiplications and reductions with O(deg(mod_poly)) coefficients.
            Each multiplication/reduction uses O(m log m) time with sufficient
            NTT capacity, otherwise O(m**2). Exponent zero and constant moduli
            require only scanning the modulus.

        Space Complexity:
            O(len(self) + len(mod_poly)).
        """
        if exponent < 0:
            raise ValueError('pow_mod requires a non-negative exponent')
        mod_poly = mod_poly.trimmed()
        if mod_poly.is_zero():
            raise ZeroDivisionError('Cannot take a polynomial modulo the zero polynomial')
        if len(mod_poly) == 1:
            return FormalPowerSeriesMod([])
        res = FormalPowerSeriesMod([1])
        if exponent == 0:
            return res
        base = self % mod_poly
        while exponent > 0:
            if exponent & 1:
                res = (res * base) % mod_poly
            exponent >>= 1
            if exponent:
                base = (base * base) % mod_poly
        return res

    def inv_mod_poly(self, mod_poly: FPS) -> FPS | None:
        """
        Compute the inverse modulo another polynomial.

        Args:
            mod_poly: Nonzero modulus polynomial g(x); trailing zeros are ignored.

        Returns:
            FormalPowerSeriesMod | None: Polynomial h(x) with degree < deg(g) such that
            self(x) * h(x) ≡ 1 (mod g(x)), or None if the monic gcd is not 1.
            Coefficients are normalized and trailing zeros removed. A nonzero
            constant modulus gives the empty polynomial (the only residue).
            Neither input is modified.

        Time Complexity:
            O(M(n) log(n + 1)), where n = max(len(self), len(mod_poly)) and M(n)
            is the multiplication cost, up to O(n**2) without NTT capacity.

        Space Complexity:
            O(n log(n + 1)).

        Raises:
            ZeroDivisionError: If mod_poly is the zero polynomial

        Notes:
            - This is polynomial modular inverse, not FPS inverse modulo x^n
            - Invertibility is equivalent to gcd(self, mod_poly) being a non-zero constant

        """
        mod_poly = mod_poly.trimmed()
        if mod_poly.is_zero():
            raise ZeroDivisionError('Cannot take inverse modulo the zero polynomial')
        if len(mod_poly) == 1:
            return FormalPowerSeriesMod([])
        gcd_poly, mat = self.gcd_transform(mod_poly, self.trimmed())
        if gcd_poly.degree() != 0:
            return None
        _, bezout_self, _, _ = mat
        inv_const = pow(gcd_poly[0], -1, self._mod)
        res = (bezout_self % mod_poly) * inv_const
        res.shrink()
        return res

    @classmethod
    def _pow_unit_scalar(cls, poly: list[int], exponent: int) -> list[int]:
        if len(poly) == 0:
            return []
        fps = cls(poly)
        if fps[0] != 1:
            raise ValueError('_pow_unit_scalar requires constant term 1')
        return ((fps.log() * exponent).exp()).coef

    @classmethod
    def _coef_of_powers(cls, base: list[int], k: int, n: int, weight: list[int] | None = None) -> list[int]:
        if len(base) != k + 1:
            raise ValueError('base must have length k + 1')
        if weight is None:
            weight = [1]
        p = [[0, 0] for _ in range(k + 1)]
        q = [[0, 0] for _ in range(k + 1)]
        p[0][0] = 1
        q[0][0] = 1
        for i in range(min(len(weight), k + 1)):
            p[i][0] = weight[i]
        mod = cls.get_mod()
        if ConvolutionMod.get_mod() != mod:
            ConvolutionMod.set_mod(mod)
        for i in range(min(len(base), k + 1)):
            q[i][1] = (-base[i]) % mod
        while k > 0:
            q_neg = [row[:] for row in q]
            for i in range(1, len(q_neg), 2):
                row = q_neg[i]
                for j in range(len(row)):
                    row[j] = (-row[j]) % mod
            p_conv = ConvolutionMod.convolution2d(p, q_neg)
            q_conv = ConvolutionMod.convolution2d(q, q_neg)
            next_k = k // 2
            p = [p_conv[2 * i | (k & 1)] for i in range(next_k + 1)]
            q = [q_conv[2 * i] for i in range(next_k + 1)]
            k = next_k
            limit = n + 1
            for i in range(len(p)):
                if len(p[i]) > limit:
                    p[i] = p[i][:limit]
            for i in range(len(q)):
                if len(q[i]) > limit:
                    q[i] = q[i][:limit]
        numer = cls(p[0]).resize(n + 1)
        denom = cls(q[0]).resize(n + 1)
        return (numer / denom).coef

    @classmethod
    def _composition_ntt_fits(cls, n: int) -> bool:
        """Check the flattened transforms used by composition and reversion."""
        capacity = (cls._mod - 1) & -(cls._mod - 1)
        degree_x, degree_y = n - 1, 1
        while degree_x > 0:
            # The middle product needs more space than either 2D convolution.
            if 3 * (degree_x + 1) * (2 * degree_y + 1) - 2 > capacity:
                return False
            degree_x //= 2
            degree_y *= 2
        return True

    @classmethod
    def _compose_impl(cls, left: list[int], right: list[int]) -> list[int]:
        n = len(left) - 1
        if n < 0:
            return []
        shift = right[0]
        shifted = polynomial_shift(cls(left), shift).coef
        right = right[:]
        right[0] = 0
        mod = cls.get_mod()
        if ConvolutionMod.get_mod() != mod:
            ConvolutionMod.set_mod(mod)

        poly2d = [[0, 0] for _ in range(n + 1)]
        poly2d[0][0] = 1
        for i in range(n + 1):
            poly2d[i][1] = (-right[i]) % mod
        result_stack: list[list[list[int]]] = []
        frame_stack: list[tuple[int, list[list[int]], list[list[int]] | None, int, int]] = [(0, poly2d, None, 0, 0)]
        while frame_stack:
            phase, current, neg, degree_x, degree_y = frame_stack.pop()
            if phase == 0:
                degree_x = len(current) - 1
                degree_y = len(current[0]) - 1
                if degree_x == 0:
                    result_stack.append([shifted[:degree_y + 1]])
                    continue
                neg = [row[:] for row in current]
                for i in range(1, degree_x + 1, 2):
                    row = neg[i]
                    for j in range(degree_y + 1):
                        row[j] = (-row[j]) % mod
                squared = ConvolutionMod.convolution2d(current, neg)
                reduced = [squared[2 * i] for i in range(degree_x // 2 + 1)]
                frame_stack.append((1, current, neg, degree_x, degree_y))
                frame_stack.append((0, reduced, None, 0, 0))
                continue
            assert neg is not None
            down = result_stack.pop()
            width = 2 * degree_y + 1
            flat = [0] * (2 * (degree_x + 1) * width - 1)
            for i in range(len(down)):
                target_x = 2 * i + (degree_x & 1)
                offset = target_x * width
                row = down[i]
                for j in range(len(row)):
                    flat[offset + j] = row[j]
            kernel = [0] * ((degree_x + 1) * width)
            for i in range(degree_x + 1):
                offset = i * width
                row = neg[i]
                for j in range(degree_y + 1):
                    kernel[offset + j] = row[j]
            middle = ConvolutionMod.middle_product(flat, kernel)
            result_stack.append([middle[i * width:i * width + degree_y + 1] for i in range(degree_x + 1)])
        res2d = result_stack.pop()
        ans = [res2d[i][0] for i in range(n + 1)]
        ans.reverse()
        return ans

    @classmethod
    def _compositional_inverse_impl(cls, poly: list[int]) -> list[int]:
        n = len(poly) - 1
        if n < 0:
            return []
        if n == 0:
            return poly[:]
        mod = cls.get_mod()
        linear = poly[1]
        linear_inv = pow(linear, -1, mod)
        normalized = [value * linear_inv % mod for value in poly]
        coef = cls._coef_of_powers(normalized, n, n)
        base = [0] * n
        for i in range(1, n + 1):
            base[n - i] = n * coef[i] % mod * pow(i, -1, mod) % mod
        inv_n = pow(n, -1, mod)
        inner = cls._pow_unit_scalar(base, (-inv_n) % mod)
        res = [0] + inner
        scale = 1
        for i in range(len(res)):
            res[i] = res[i] * scale % mod
            scale = scale * linear_inv % mod
        return res

    def compose(self, other: FPS) -> FPS:
        """
        Compose the stored polynomials f(g(x)) modulo x^n.

        Args:
            other: Polynomial g(x); its constant term need not be zero.

        Returns:
            FormalPowerSeriesMod: First n coefficients of f(g(x))
            where n = max(len(self), len(other)). Neither input is modified.
            Two empty inputs give an empty result.

        Notes:
            Uses the finite polynomial represented by all stored coefficients
            of f, including when g has a nonzero constant term. With insufficient
            NTT capacity, uses truncated Horner evaluation instead.

        Time Complexity:
            O(n log^2 n) with sufficient NTT capacity. Otherwise O(n M(n)),
            up to O(n**3), where M(n) is the cost of polynomial multiplication.

        Space Complexity:
            O(n log n) for the transform algorithm; O(n) for Horner evaluation.
        """
        n = max(len(self), len(other))
        if n == 0:
            return FormalPowerSeriesMod([])
        if not self._composition_ntt_fits(n):
            result = FormalPowerSeriesMod([])
            for value in reversed(self.trimmed().coef):
                result = (result * other).resize(n)
                result.coef[0] = (result.coef[0] + value) % self._mod
            return result.resize(n)
        return FormalPowerSeriesMod(self._compose_impl(self.resize(n).coef, other.resize(n).coef))

    def compositional_inverse(self) -> FPS:
        """
        Compute the compositional inverse modulo x^n.

        Returns:
            FormalPowerSeriesMod: g(x) with zero constant term such that
            self(g(x)) ≡ x (mod x^n), where n = len(self). Returns exactly
            n normalized coefficients without modifying self. Empty input
            gives an empty result.

        Raises:
            ValueError: If the constant term is not congruent to zero or the
                linear term is congruent to zero (including a length-one input).

        Time Complexity:
            O(n log^2 n) with sufficient NTT capacity and n <= mod. Otherwise
            uses Newton reversion with O(n M(n)) time, up to O(n**3), where
            M(n) is the cost of polynomial multiplication.

        Space Complexity:
            O(n log n), or O(n) when every Newton step uses Horner evaluation.

        Notes:
            The fallback also works in small characteristic: it divides only
            by series with invertible constant term, not by degree indices.
        """
        if len(self) == 0:
            return FormalPowerSeriesMod([])
        if self[0] % self._mod != 0:
            raise ValueError('compositional inverse requires zero constant term')
        if len(self) == 1 or self[1] % self._mod == 0:
            raise ValueError('compositional inverse requires a non-zero linear term')
        if len(self) > self._mod or not self._composition_ntt_fits(len(self)):
            result = FormalPowerSeriesMod([0, pow(self[1], -1, self._mod)])
            while len(result) < len(self):
                size = min(2 * len(result), len(self))
                current = self.resize(size)
                result = result.resize(size)
                error = current.compose(result)
                error.coef[1] = (error.coef[1] - 1) % self._mod
                slope = current.derivative().compose(result)
                result = (result - error / slope).resize(size)
            return result
        return FormalPowerSeriesMod(self._compositional_inverse_impl(self.coef))

    def sqrt(self) -> FPS:
        """
        Compute square root of formal power series.

        Returns:
            FormalPowerSeriesMod: Square root g such that g^2 ≡ f (mod x^n)
            - The result contains len(self) coefficients.

        Time Complexity:
            O(n log n) with sufficient NTT capacity, otherwise O(n**2).
            O(n) in characteristic two.

        Raises:
            ValueError: If no square root exists modulo x**len(self).

        Notes:
            - Uses Newton's method for odd prime moduli. In characteristic two,
              all odd-indexed coefficients must be zero and a root is obtained
              by halving the exponents of the even-indexed coefficients.
            - No specialized implementation for sparse polynomials
            - Requires first non-zero coefficient to be a quadratic residue
            - First non-zero coefficient must be at an even index

        """
        if self._mod == 2:
            result = [0] * len(self)
            for i, c in enumerate(self.coef):
                c %= 2
                if i & 1:
                    if c:
                        raise ValueError('Square root does not exist')
                else:
                    result[i // 2] = c
            return FormalPowerSeriesMod(result)
        return self._sqrt()

    def _sqrt(self) -> FPS:
        """Compute square root using Newton's method with O(n log n) complexity."""
        if len(self) == 0:
            return FormalPowerSeriesMod([])
        for i, c in enumerate(self.coef):
            if c % self._mod != 0:
                min_nz = i
                break
        else:
            return FormalPowerSeriesMod([0] * len(self))
        if min_nz % 2 != 0:
            raise ValueError('Square root does not exist')
        sqrt_c = sqrt_mod(c, self._mod)
        if sqrt_c == -1:
            raise ValueError('Square root does not exist')
        if min_nz > 0:
            g = self[min_nz:]
            sqrt_g = g._sqrt()
            res = FormalPowerSeriesMod([0] * len(self))
            shift = min_nz // 2
            for i, coeff in enumerate(sqrt_g.coef):
                if i + shift < len(self):
                    res[i + shift] = coeff
            return res

        n = len(self)
        res = FormalPowerSeriesMod([sqrt_c])
        m = 1

        while m < n:
            next_m = min(2 * m, n)
            f_trunc = self.resize(next_m)
            res_extended = res.resize(next_m)
            res = ((res_extended + f_trunc / res_extended) * pow(2, -1, self._mod)).resize(next_m)
            m = next_m

        return res


def polynomial_product(polys: list[FPS]) -> FPS:
    """
    Compute product of multiple polynomials efficiently.

    Args:
        polys: List of polynomials, used as workspace for intermediate products.
            Individual input polynomial objects are not modified.

    Returns:
        A new polynomial with normalized coefficients. An empty input list gives
        [1]; any empty coefficient list gives []. Otherwise the result has
        1 + sum(len(poly) - 1 for poly in polys) coefficients, including trailing
        zeros. A singleton input also gives a normalized copy.

    Notes:
        - Uses divide-and-conquer with heap to minimize intermediate sizes
        - Always multiplies smallest polynomials first for efficiency
        - Empty input list returns the multiplicative identity [1]
        - Replaces list entries with intermediate products and empty polynomials
          to release consumed storage. The final list layout is unspecified.
        - Empty input, an empty factor, and a singleton input return immediately
          without modifying the input list.

    Time Complexity:
        O(M(S) log(k + 1) + k log(k + 1)), where k is the number of factors,
        S is the total input coefficient count, and M(S) is the multiplication
        cost: O(S log S) with sufficient NTT capacity, otherwise O(S**2).

    Space Complexity:
        O(S + k), including intermediate polynomials and the heap.
    """
    if len(polys) == 0:
        return FormalPowerSeriesMod([1])
    if any(len(poly) == 0 for poly in polys):
        return FormalPowerSeriesMod([])
    if len(polys) == 1:
        return polys[0] * 1
    n = len(polys)
    heap: list[int] = []
    for i, poly in enumerate(polys):
        heap.append(len(poly) * n + i)
    heapq.heapify(heap)
    i1 = None
    for _ in range(n - 1):
        d1, i1 = divmod(heapq.heappop(heap), n)
        d2, i2 = divmod(heapq.heappop(heap), n)
        f1 = polys[i1]
        f2 = polys[i2]
        polys[i1] = f1 * f2
        polys[i2] = FormalPowerSeriesMod([])
        d = d1 + d2 - 1
        heapq.heappush(heap, d * n + i1)
    assert i1 is not None
    return polys[i1]


def coefficient_of_rational_polynomial(numer: FPS, denom: FPS, k: int) -> int:
    """
    Find k-th coefficient of rational function P(x)/Q(x).

    Args:
        numer: Numerator polynomial P(x)
        denom: Denominator polynomial Q(x) with invertible constant term.
        k: Non-negative index of coefficient to find

    Returns:
        int: Coefficient of x^k in P(x)/Q(x), reduced modulo
        FormalPowerSeriesMod.get_mod().

    Raises:
        ValueError: If k is negative or Q(0) is not invertible modulo the modulus.

    Notes:
        - Uses Bostan-Mori algorithm for efficient computation
        - Does not compute the full power series, only the k-th coefficient
        - Requires Q(0) to be invertible; it need not equal one.
        - Uses the configured prime modulus; polynomial products fall back to
          quadratic multiplication if NTT capacity is insufficient.

    Time Complexity:
        O(d log(d + 1) log(k + 2)) with NTT, otherwise O(d**2 log(k + 2)),
        where d = max(len(numer), len(denom)).

    Space Complexity:
        ``O(d)``
    """
    if k < 0:
        raise ValueError('k must be non-negative')
    mod = FormalPowerSeriesMod.get_mod()
    constant = denom[0] % mod
    inverse = 1 if constant == 1 else pow(constant, -1, mod)
    if k == 0:
        return numer[0] * inverse % mod
    if not numer.coef:
        return 0
    p = FormalPowerSeriesMod([x * inverse % mod for x in numer.coef])
    q = FormalPowerSeriesMod([x * inverse % mod for x in denom.coef])
    while k:
        r = FormalPowerSeriesMod([-q if i & 1 else q for i, q in enumerate(q.coef)])
        p *= r
        q *= r
        p = p[(k & 1)::2]
        q = q[::2]
        k >>= 1
    return p[0] % FormalPowerSeriesMod.get_mod()


def multipoint_evaluation(poly: FPS, xs: list[int]) -> list[int]:
    """
    Evaluate polynomial at multiple points.

    Args:
        poly: Polynomial f(x) to evaluate
        xs: List of evaluation points

    Returns:
        list[int]: Values [f(xs[0]), f(xs[1]), ..., f(xs[n-1])]

    Notes:
        - Uses divide-and-conquer with polynomial remainder tree
        - More efficient than n individual evaluations for large n
        - All evaluations are performed modulo FormalPowerSeriesMod._mod

    Time Complexity:
        ``O((n + m) log^2(n + m))``, where ``n = len(poly)`` and
        ``m = len(xs)``.

    Space Complexity:
        ``O(n + m log m)``
    """
    n = len(xs)
    if n == 0:
        return []
    sz = 1 << (n - 1).bit_length()
    g = [FormalPowerSeriesMod([1]) for _ in range(2 * sz)]
    for i in range(n):
        g[i + sz] = FormalPowerSeriesMod([-xs[i], 1])
    for i in range(1, sz)[::-1]:
        g[i] = g[2 * i] * g[2 * i + 1]
    g[1] = poly % g[1]
    for i in range(2, 2 * sz):
        g[i] = g[i >> 1] % g[i]
    res = [g[i + sz][0] for i in range(n)]
    return res


def polynomial_interpolation(xs: list[int], ys: list[int]) -> FPS:
    """
    Find polynomial through given points.

    Args:
        xs: x-coordinates (must be distinct)
        ys: y-coordinates where ys[i] = f(xs[i])

    Returns:
        FormalPowerSeriesMod: Unique polynomial f of degree < n where f(xs[i]) = ys[i]
        - Degree of result is at most len(xs) - 1

    Raises:
        ValueError: If lengths differ or two coordinates are congruent modulo
            the current modulus.

    Notes:
        - Uses divide-and-conquer approach with Lagrange interpolation
        - All x-coordinates must be distinct modulo FormalPowerSeriesMod._mod
        - Returns the unique polynomial of minimal degree through all points

    Time Complexity:
        ``O(n log^2 n)``, where ``n = len(xs)``.

    Space Complexity:
        ``O(n log n)``
    """
    if len(xs) != len(ys):
        raise ValueError('xs and ys must have equal lengths')
    n = len(xs)
    if n == 0:
        return FormalPowerSeriesMod([])
    mod = FormalPowerSeriesMod.get_mod()
    if len({x % mod for x in xs}) != n:
        raise ValueError('xs must be distinct modulo the modulus')
    sz = 1 << (n - 1).bit_length()
    f = [FormalPowerSeriesMod([1]) for _ in range(2 * sz)]
    for i in range(n):
        f[i + sz] = FormalPowerSeriesMod([-xs[i], 1])
    for i in range(1, sz)[::-1]:
        f[i] = f[2 * i] * f[2 * i + 1]
    g = [FormalPowerSeriesMod([0]) for _ in range(2 * sz)]
    g[1] = f[1].derivative() % f[1]
    for i in range(2, n + sz):
        g[i] = g[i >> 1] % f[i]
    for i in range(n):
        g[i + sz] = FormalPowerSeriesMod([ys[i] * pow(g[i + sz][0], -1, mod) % mod])
    for i in range(1, sz)[::-1]:
        g[i] = g[2 * i] * f[2 * i + 1] + g[2 * i + 1] * f[2 * i]
    return g[1][:n]


def polynomial_shift_sampling(n: int, m: int, ys: list[int], c: int) -> list[int]:
    """
    Evaluate polynomial at shifted consecutive points using sampling.

    Given polynomial values f(0), f(1), ..., f(n-1), computes the values
    f(c), f(c+1), ..., f(c+m-1) where f is the unique polynomial of degree < n
    interpolating the given points.

    Args:
        n: Number of known sample points, with 0 <= n <= get_mod().
        m: Non-negative number of evaluation points to compute.
        ys: Known values [f(0), f(1), ..., f(n-1)]
        c: Starting point for evaluation; reduced modulo the modulus.

    Returns:
        Values [f(c), f(c+1), ..., f(c+m-1)] modulo get_mod(). Empty samples
        define the zero polynomial and return m zeros; m=0 returns [].
        The supplied samples are not modified.

    Time Complexity:
        O(m) for direct lookup or a constant polynomial. Otherwise, with
        t = min(m, mod), O((n+t) log(n+t) + m + log mod) using NTT,
        or O(n(n+t) + m + log mod) with direct multiplication.

    Space Complexity:
        O(n + m)

    Raises:
        ValueError: If n or m is negative, n exceeds the modulus, or len(ys) != n.

    Notes:
        - Uses Lagrange interpolation formula with optimizations
        - Handles large c values by taking c modulo _mod
        - Special cases for when evaluation points overlap with known points
        - Splits at sample boundaries and modular wraparound without recursion.
        - Evaluates at most one period, then repeats it for outputs longer than mod.
        - Uses batch inversion and convolution for intervals outside the samples.

    Examples:
        >>> # f(x) = x^2, known values f(0)=0, f(1)=1, f(2)=4
        >>> # f(3)=9, f(4)=16, f(5)=25
        >>> polynomial_shift_sampling(3, 3, [0, 1, 4], 3)
        [9, 16, 25]

        >>> # Direct lookup when c < n
        >>> # f(2)=5, f(3)=10
        >>> polynomial_shift_sampling(5, 2, [1, 2, 5, 10, 17], 2)
        [5, 10]

    """
    mod = FormalPowerSeriesMod.get_mod()
    if n < 0 or n > mod or len(ys) != n or m < 0:
        raise ValueError('require 0 <= n <= mod, len(ys) == n, and m >= 0')
    if m == 0:
        return []
    if n == 0:
        return [0] * m
    if n == 1:
        return [ys[0] % mod] * m
    c %= mod
    length = min(m, mod)
    result: list[int] = []
    while len(result) < length:
        if c < n:
            count = min(n - c, length - len(result))
            result.extend(value % mod for value in ys[c:c + count])
        else:
            count = min(mod - c, length - len(result))
            result.extend(_shift_sampling_block(ys, c, count, mod))
        c = (c + count) % mod
    if m > length:
        return result * (m // length) + result[:m % length]
    return result


def _shift_sampling_block(ys: list[int], c: int, m: int, mod: int) -> list[int]:
    """Evaluate one block with len(ys) <= c < c+m <= mod."""
    n = len(ys)
    inv = [1] * n
    factorial = 1
    for i in range(1, n):
        factorial = factorial * i % mod
    inv[-1] = pow(factorial, -1, mod)
    for i in range(n - 1, 0, -1):
        inv[i - 1] = inv[i] * i % mod
    weights = [0] * n
    for i in range(n):
        value = inv[i] * inv[n - 1 - i] % mod * ys[i] % mod
        weights[i] = value if (n - i) & 1 else -value % mod
    inverses = batch_inverse_mod(list(range(c - n + 1, c + m)), mod)
    product = (FormalPowerSeriesMod(weights) * FormalPowerSeriesMod(inverses)).coef
    result = [0] * m
    falling = 1
    for i in range(n):
        falling = falling * (c - i) % mod
    for i in range(m):
        result[i] = falling * product[n - 1 + i] % mod
        falling = falling * (c + i + 1) % mod * inverses[i] % mod
    return result


_mod_inverses = [0, 1]
_mod_inverses_mod = 998244353


def _ensure_inverses(n: int) -> list[int]:
    global _mod_inverses_mod
    mod = FormalPowerSeriesMod.get_mod()
    if _mod_inverses_mod != mod:
        _mod_inverses[:] = [0, 1]
        _mod_inverses_mod = mod
    if len(_mod_inverses) <= n:
        start = len(_mod_inverses)
        _mod_inverses.extend([0] * (n + 1 - start))
        for i in range(max(2, start), n + 1):
            _mod_inverses[i] = mod - mod // i * _mod_inverses[mod % i] % mod
    return _mod_inverses


def _sum_of_exponential_times_polynomial_samples(r: int, ys: list[int], n: int | None = None) -> int:
    mod = FormalPowerSeriesMod.get_mod()
    r %= mod
    values = [y % mod for y in ys]
    if not values:
        return 0
    if n is None:
        if r == 1:
            raise ValueError('infinite sum requires r != 1')
        if len(values) == 1:
            return values[0] * pow((1 - r) % mod, -1, mod) % mod
        d = len(values) - 1
        prefix = values[:]
        rp = 1
        for i in range(1, len(prefix)):
            rp = rp * r % mod
            prefix[i] = (prefix[i] * rp + prefix[i - 1]) % mod
        inv = _ensure_inverses(d + 1)
        ret = 0
        comb = 1
        rp = 1
        neg_r = (-r) % mod
        for i in range(d + 1):
            ret = (ret + prefix[d - i] * comb % mod * rp) % mod
            rp = rp * neg_r % mod
            comb = comb * (d + 1 - i) % mod * inv[i + 1] % mod
        return ret * pow((1 - r) % mod, -(d + 1), mod) % mod

    if n <= 0:
        return 0
    if len(values) == 1:
        if r == 1:
            return values[0] * (n % mod) % mod
        return values[0] * (1 - pow(r, n, mod)) % mod * pow((1 - r) % mod, -1, mod) % mod
    if r == 0:
        return values[0]
    d = len(values) - 1
    if n <= d + 1:
        ret = 0
        rp = 1
        for i in range(n):
            ret = (ret + rp * values[i]) % mod
            rp = rp * r % mod
        return ret

    inv = _ensure_inverses(d + 1)
    c1 = [0] * (d + 2)
    c1[d] = 1
    for i in range(d - 1, -1, -1):
        c1[i] = c1[i + 1] * ((n - 1 - i) % mod) % mod * inv[d - i] % mod

    c0 = 1
    if r == 1:
        for i in range(1, d + 1):
            c0 = c0 * ((n + 1 - i) % mod) % mod * inv[i] % mod
        b = c0 * ((n - d) % mod) % mod * inv[d + 1] % mod
    else:
        rinv = pow(r, -1, mod)
        a1 = pow(r, n, mod)
        b = 1
        for i in range(d + 1):
            term = c0 * c1[i] % mod * a1 % mod
            if (d - i) & 1:
                b = (b + term) % mod
            else:
                b = (b - term) % mod
            c0 = c0 * ((n - i) % mod) % mod * inv[i + 1] % mod
            a1 = a1 * rinv % mod
        b = b * pow((1 - r) % mod, -(d + 1), mod) % mod

    ret = 0
    prefix = 0
    c0 = n % mod
    choose = (d + 1) % mod
    rp = 1
    if r == 1:
        rinv = -1 # not used
        desc = 1
        a1 = 1
    else:
        rinv = pow(r, -1, mod)
        desc = pow(r, d, mod)
        a1 = pow(r, n - 1, mod)
    for i in range(1, d + 2):
        prefix = (prefix + rp * values[i - 1]) % mod
        first = b * choose % mod * desc % mod
        if (d + 1 - i) & 1:
            first = (-first) % mod
        second = c0 * c1[i] % mod * a1 % mod
        if (d - i) & 1:
            second = (-second) % mod
        ret = (ret + (first + second) * prefix) % mod
        rp = rp * r % mod
        if i <= d:
            c0 = c0 * ((n - i) % mod) % mod * inv[i + 1] % mod
            choose = choose * (d + 1 - i) % mod * inv[i + 1] % mod
        if r != 1:
            desc = desc * rinv % mod
            a1 = a1 * rinv % mod
    return ret


def sum_of_exponential_times_polynomial(r: int, d: int, n: int | None = None) -> int:
    """
    Compute a finite exponential-polynomial sum or its generating function.

    This function computes:

    - ``sum_{i=0}^{n-1} r^i i^d`` when ``n`` is an integer.
    - The rational generating function of ``i^d``, evaluated at ``r``, when
      ``n is None``. This is not a convergent infinite sum in a finite field.

    Args:
        r: Common ratio of the geometric factor.
        d: Non-negative exponent of the monomial ``i^d``; ``0**0`` is 1.
        n: Non-negative number of terms, or ``None`` for the generating function.

    Returns:
        int: The requested sum modulo ``FormalPowerSeriesMod._mod``.

    Raises:
        ValueError: If d or a supplied n is negative, or if n is None and r is
            congruent to 1 modulo the current modulus.

    Notes:
        - For positive d, the exponent can be reduced to
          ``e = 1 + (d - 1) % (mod - 1)``; for d = 0, e = 0.
        - Builds e + 1 samples and uses polynomial summation. When e = mod - 1,
          uses the indicator of indices not divisible by mod and geometric sums
          instead, avoiding division by the modulus.

    Time Complexity:
        O((e + 1) log(e + 2) + log(n + 1)) modular operations for finite n,
        with the last term omitted for n = None. When e = mod - 1, O(log(n + 1))
        for finite n and O(1) for n = None, excluding integer exponent reduction.

    Space Complexity:
        O(e + 1), or O(1) when e = mod - 1.
    """
    if d < 0:
        raise ValueError('d must be non-negative')
    if n is not None and n < 0:
        raise ValueError('n must be non-negative')
    mod = FormalPowerSeriesMod.get_mod()
    r %= mod
    if n is None and r == 1:
        raise ValueError('generating function requires r != 1 modulo mod')
    if n == 0:
        return 0
    if d:
        d = 1 + (d - 1) % (mod - 1)
    if d == mod - 1:
        if n is None:
            return 0
        multiples = (n + mod - 1) // mod
        if r == 1:
            return (n - multiples) % mod
        return (pow(r, multiples, mod) - pow(r, n, mod)) * pow(1 - r, -1, mod) % mod
    samples = [pow(i, d, mod) for i in range(d + 1)]
    return _sum_of_exponential_times_polynomial_samples(r, samples, n)


def polynomial_shift(poly: FPS, c: int) -> FPS:
    """
    Compute Taylor shift P(x+c).

    Args:
        poly: Input polynomial P(x)
        c: Shift amount

    Returns:
        FormalPowerSeriesMod: Polynomial P(x+c) expanded in powers of x
        - Contains len(poly) coefficients; empty input returns an empty series.
        - The input polynomial is not modified.

    Notes:
        - Computes the polynomial P(x+c) = Σ P^(k)(c)/k! * x^k
        - Uses NTT convolution and factorials when possible. If the stored
          length exceeds the modulus, uses Horner expansion without division.
        - All computations are performed modulo FormalPowerSeriesMod._mod

    Time Complexity:
        O(n log n) with suitable NTT capacity and invertible factorials,
        otherwise O(n**2). O(n) if the shift is zero modulo the modulus.

    Space Complexity:
        ``O(n)``, where ``n = len(poly)``.
    """
    n = len(poly)
    if n == 0:
        return FormalPowerSeriesMod([])
    mod = FormalPowerSeriesMod.get_mod()
    c %= mod
    if c == 0:
        return poly * 1
    if n > mod:
        # Horner expansion avoids factorial inverses in small characteristic.
        coefficients: list[int] = []
        for value in reversed(poly.coef):
            coefficients.append(0)
            for i in range(len(coefficients) - 1, 0, -1):
                coefficients[i] = (coefficients[i - 1] + c * coefficients[i]) % mod
            coefficients[0] = (c * coefficients[0] + value) % mod
        return FormalPowerSeriesMod(coefficients)
    factorials = [1] * n
    inverses = [1] * n
    for i in range(1, n):
        factorials[i] = factorials[i - 1] * i % mod
    inverses[n - 1] = pow(factorials[n - 1], -1, mod)
    for i in range(n - 1, 0, -1):
        inverses[i - 1] = inverses[i] * i % mod
    powers = [1] * n
    for i in range(1, n):
        powers[i] = powers[i - 1] * c % mod
    left = FormalPowerSeriesMod([poly[i] * factorials[i] % mod for i in range(n)])
    right = FormalPowerSeriesMod([powers[n - 1 - i] * inverses[n - 1 - i] % mod for i in range(n)])
    product = left * right
    return FormalPowerSeriesMod([product[n - 1 + i] * inverses[i] % mod for i in range(n)])


def polynomial_roots(poly: FPS) -> list[int]:
    """
    Find all roots of a polynomial over F_p.

    Args:
        poly: Nonzero polynomial over ``FormalPowerSeriesMod.get_mod()``.

    Returns:
        All distinct roots in ascending order as integers in [0, mod).
        A nonzero constant polynomial has no roots and returns [].

    Raises:
        ValueError: If poly is zero modulo the modulus; all field elements would
            be roots.

    Time Complexity:
        Expected ``O(M(n) log(mod) log(n))`` where ``n`` is the polynomial
        degree and ``M(n)`` is the cost of multiplying degree-``n``
        polynomials. O(n) in characteristic two, by evaluating zero and one.

    Space Complexity:
        ``O(n log(n))`` for polynomial remainders and the randomized splitting
        stack.
    """
    poly = poly.trimmed()
    if not poly.coef:
        raise ValueError('the zero polynomial has every field element as a root')
    if len(poly) == 1:
        return []

    mod = FormalPowerSeriesMod.get_mod()
    if mod == 2:
        binary_roots: list[int] = []
        if poly[0] % 2 == 0:
            binary_roots.append(0)
        if sum(poly.coef) % 2 == 0:
            binary_roots.append(1)
        return binary_roots

    rng_state = 10150724397891781847

    x_poly = FormalPowerSeriesMod([0, 1])
    frobenius = x_poly.pow_mod(mod, poly)
    if len(frobenius) < 2:
        frobenius = frobenius.resize(2)
    frobenius[1] = (frobenius[1] - 1) % mod
    squarefree_linear = poly.gcd(frobenius)

    roots: list[int] = []
    stack = [squarefree_linear]
    while stack:
        current = stack.pop()
        current = current.trimmed()
        if len(current) <= 1:
            continue
        if len(current) == 2:
            roots.append((-current[0]) * pow(current[1], -1, mod) % mod)
            continue
        while True:
            rng_state = xorshift64(rng_state)
            affine = FormalPowerSeriesMod([rng_state % mod, 1])
            split = affine.pow_mod((mod - 1) // 2, current)
            split = split.trimmed()
            if split.is_zero():
                continue
            split[0] = (split[0] - 1) % mod
            split = split.trimmed()
            if split.is_zero():
                continue
            left = current.gcd(split)
            if len(left) == 1 or len(left) == len(current):
                continue
            right = (current // left).trimmed()
            stack.append(left)
            stack.append(right)
            break
    roots.sort()
    return roots
