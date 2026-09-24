#!/usr/bin/env python3

from __future__ import annotations

from math import copysign, frexp, isfinite, isnan, ldexp, sqrt
from operator import index
from types import NotImplementedType


_SPLITTER = 134217729.0


def _two_sum(a: float, b: float) -> tuple[float, float]:
    s = a + b
    if not isfinite(s):
        return s, 0.0
    bb = s - a
    err = (a - (s - bb)) + (b - bb)
    return s, err


def _split(a: float) -> tuple[float, float]:
    c = _SPLITTER * a
    hi = c - (c - a)
    lo = a - hi
    return hi, lo


def _two_prod(a: float, b: float) -> tuple[float, float]:
    p = a * b
    if not isfinite(p) or p == 0.0:
        return p, 0.0
    # Split bounded mantissas so the splitter and partial products cannot overflow.
    am, ae = frexp(a)
    bm, be = frexp(b)
    a_hi, a_lo = _split(am)
    b_hi, b_lo = _split(bm)
    product = am * bm
    err = ((a_hi * b_hi - product) + a_hi * b_lo + a_lo * b_hi) + a_lo * b_lo
    return p, ldexp(err, ae + be)


class FloatDouble:
    """Double-double floating-point number.

    A value is represented as ``hi + lo`` where both parts are Python floats.
    This improves precision over a single float while keeping the same basic
    exponent range. Operations aim for roughly 106 bits of significand
    precision away from overflow and underflow; they are not guaranteed to be
    correctly rounded. Subnormal results gradually lose this extra precision.
    Overflow produces signed infinity. NaN is unequal to every value and all
    ordered comparisons with NaN are false. Division by zero raises an error.

    Integer construction keeps a rounded high part and a rounded residual.
    Arithmetic converts integer operands this way, while comparisons with
    integers compare the exact represented sum without rounding the operand.
    A pair of floats still has finite precision, so arbitrary integers need
    not be represented exactly. float() and str() return single-float precision;
    repr() includes both parts. Do not mutate hi or lo directly.

    Complexity notes below count fixed-width floating-point operations.
    Converting or comparing arbitrarily large integers also depends on their
    bit length.

    Attributes:
        hi: Main floating-point part.
        lo: Error-correction floating-point part.

    Space Complexity:
        O(1)
    """

    __slots__ = ('hi', 'lo')

    def __init__(self, value: float | int | 'FloatDouble' = 0.0, lo: float = 0.0) -> None:
        """Initialize a double-double number.

        Args:
            value: Float, integer, or another FloatDouble. Integer residuals
                are retained to the precision available in two floats.
            lo: Additional floating-point low part. Ignored when value is
                FloatDouble. Infinities and NaN follow float addition.

        Returns:
            None.

        Raises:
            OverflowError: If an integer value is too large to convert to float.

        Time Complexity:
            O(1) for float inputs; integer conversion depends on its bit length.
        """
        if isinstance(value, FloatDouble):
            self.hi = value.hi
            self.lo = value.lo
            return
        hi = float(value)
        correction = float(value - int(hi)) if isinstance(value, int) else 0.0
        self.hi, self.lo = _two_sum(hi, correction) if correction else (hi, 0.0)
        if lo:
            hi, correction = _two_sum(self.hi, float(lo))
            self.hi, self.lo = _two_sum(hi, correction + self.lo)

    @classmethod
    def from_parts(cls, hi: float, lo: float) -> 'FloatDouble':
        """Construct a value from high and low parts.

        Args:
            hi: Main floating-point part.
            lo: Error-correction floating-point part.

        Returns:
            Normalized double-double value.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return cls(hi, lo)

    def __float__(self) -> float:
        """Return the nearest Python float value.

        Args:
            None.

        Returns:
            The rounded sum of hi and lo, preserving the sign of zero.
        """
        return self.hi + self.lo if self.lo else self.hi

    def __repr__(self) -> str:
        """Represent both floating-point components.

        Args:
            None.

        Returns:
            FloatDouble(hi, lo) text preserving the components' precision.
        """
        return f'FloatDouble({self.hi!r}, {self.lo!r})'

    def __str__(self) -> str:
        """Format the value at ordinary float precision.

        Args:
            None.

        Returns:
            str(float(self)); use repr(self) to inspect both components.
        """
        return str(float(self))

    def __bool__(self) -> bool:
        """Test whether the value is nonzero.

        Args:
            None.

        Returns:
            False for either signed zero; True otherwise, including NaN.
        """
        return self.hi != 0.0 or self.lo != 0.0

    @staticmethod
    def _coerce(value: object) -> FloatDouble | NotImplementedType:
        if isinstance(value, FloatDouble):
            return value
        if isinstance(value, int | float):
            return FloatDouble(value)
        return NotImplemented

    def _scale(self, exponent: int) -> FloatDouble:
        try:
            hi = ldexp(self.hi, exponent)
        except OverflowError:
            return FloatDouble(copysign(float('inf'), self.hi))
        return FloatDouble.from_parts(hi, ldexp(self.lo, exponent))

    def __pos__(self) -> 'FloatDouble':
        return FloatDouble(self)

    def __neg__(self) -> 'FloatDouble':
        return FloatDouble.from_parts(-self.hi, -self.lo)

    def __abs__(self) -> 'FloatDouble':
        return -self if copysign(1.0, self.hi) < 0.0 else FloatDouble(self)

    def __add__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        """Return the sum.

        Args:
            other: Value to add.

        Returns:
            ``self + other``.

        Time Complexity:
            O(1)
        """
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        hi, correction = _two_sum(self.hi, value.hi)
        if not isfinite(hi) and isfinite(self.hi) and isfinite(value.hi):
            return (self._scale(-1) + value._scale(-1))._scale(1)
        lo, tail = _two_sum(self.lo, value.lo)
        hi, correction = _two_sum(hi, correction + lo)
        return FloatDouble.from_parts(hi, correction + tail)

    def __radd__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        return self.__add__(other)

    def __sub__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        """Return the difference.

        Args:
            other: Value to subtract.

        Returns:
            ``self - other``.

        Time Complexity:
            O(1)
        """
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        hi, correction = _two_sum(self.hi, -value.hi)
        if not isfinite(hi) and isfinite(self.hi) and isfinite(value.hi):
            return (self._scale(-1) - value._scale(-1))._scale(1)
        lo, tail = _two_sum(self.lo, -value.lo)
        hi, correction = _two_sum(hi, correction + lo)
        return FloatDouble.from_parts(hi, correction + tail)

    def __rsub__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        return value - self

    def __mul__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        """Return the product.

        Args:
            other: Value to multiply by.

        Returns:
            ``self * other``.

        Time Complexity:
            O(1)
        """
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        hi, lo = _two_prod(self.hi, value.hi)
        if not isfinite(hi):
            if isfinite(self.hi) and isfinite(value.hi):
                ah, ae = frexp(self.hi)
                bh, be = frexp(value.hi)
                left = FloatDouble.from_parts(ah, ldexp(self.lo, -ae))
                right = FloatDouble.from_parts(bh, ldexp(value.lo, -be))
                return (left * right)._scale(ae + be)
            return FloatDouble(hi)
        lo += self.hi * value.lo + self.lo * value.hi + self.lo * value.lo
        return FloatDouble.from_parts(hi, lo)

    def __rmul__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        return self.__mul__(other)

    def __truediv__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        """Return the quotient.

        Args:
            other: Divisor.

        Returns:
            ``self / other``.

        Raises:
            ZeroDivisionError: If ``other`` is zero.

        Time Complexity:
            O(1)
        """
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        if not value:
            raise ZeroDivisionError('division by zero')
        if not isfinite(self.hi) or not isfinite(value.hi) or self.hi == 0.0:
            return FloatDouble(self.hi / value.hi)
        ah, ae = frexp(self.hi)
        bh, be = frexp(value.hi)
        left = FloatDouble.from_parts(ah, ldexp(self.lo, -ae))
        right = FloatDouble.from_parts(bh, ldexp(value.lo, -be))
        q1 = ah / bh
        residual = left - right * q1
        q2 = residual.hi / bh
        quotient = FloatDouble.from_parts(q1, q2)
        residual = left - right * quotient
        quotient += residual.hi / bh
        return quotient._scale(ae - be)

    def __rtruediv__(self, other: float | int | 'FloatDouble') -> 'FloatDouble':
        value = self._coerce(other)
        if isinstance(value, NotImplementedType):
            return NotImplemented
        return value / self

    def __pow__(self, exponent: int) -> 'FloatDouble':
        """Return an integer power.

        Args:
            exponent: Integer exponent.

        Returns:
            ``self ** exponent``.

        Raises:
            TypeError: If exponent does not support integer indexing.
            ZeroDivisionError: If the base is zero and exponent is negative.

        Time Complexity:
            O(log(abs(exponent) + 1))
        """
        exponent = index(exponent)
        base = FloatDouble(self)
        if exponent < 0:
            base = FloatDouble(1.0) / base
            exponent = -exponent
        result = FloatDouble(1.0)
        while exponent:
            if exponent & 1:
                result *= base
            exponent >>= 1
            if exponent:
                base *= base
        return result

    def sqrt(self) -> 'FloatDouble':
        """Return the square root.

        Args:
            None.

        Returns:
            Square root of this value. Positive infinity and NaN propagate;
            signed zero is preserved.

        Raises:
            ValueError: If this value is negative.

        Time Complexity:
            O(1)
        """
        if self.hi < 0.0:
            raise ValueError('cannot take square root of a negative value')
        if not isfinite(self.hi) or self.hi == 0.0:
            return FloatDouble(self)
        hi, exponent = frexp(self.hi)
        if exponent & 1:
            hi *= 2.0
            exponent -= 1
        value = FloatDouble.from_parts(hi, ldexp(self.lo, -exponent))
        y = FloatDouble(sqrt(hi))
        result = y + (value - y * y) / (y * 2.0)
        return result._scale(exponent // 2)

    def _compare(self, other: object) -> int | None | NotImplementedType:
        if isinstance(other, int):
            if isnan(self.hi):
                return None
            if not isfinite(self.hi):
                return 1 if self.hi > 0.0 else -1
            # Compare exact represented values without rounding the integer operand.
            hn, hd = self.hi.as_integer_ratio()
            ln, ld = self.lo.as_integer_ratio()
            left = hn * ld + ln * hd
            right = other * hd * ld
            return (left > right) - (left < right)
        if isinstance(other, FloatDouble):
            hi, lo = other.hi, other.lo
        elif isinstance(other, float):
            hi, lo = other, 0.0
        else:
            return NotImplemented
        if isnan(self.hi) or isnan(hi):
            return None
        if self.hi != hi:
            return 1 if self.hi > hi else -1
        return (self.lo > lo) - (self.lo < lo)

    def __eq__(self, other: object) -> bool:
        result = self._compare(other)
        if isinstance(result, NotImplementedType):
            return NotImplemented
        return result is not None and result == 0

    def __lt__(self, other: float | int | FloatDouble) -> bool:
        result = self._compare(other)
        if isinstance(result, NotImplementedType):
            return NotImplemented
        return result is not None and result < 0

    def __le__(self, other: float | int | FloatDouble) -> bool:
        result = self._compare(other)
        if isinstance(result, NotImplementedType):
            return NotImplemented
        return result is not None and result <= 0

    def __gt__(self, other: float | int | FloatDouble) -> bool:
        result = self._compare(other)
        if isinstance(result, NotImplementedType):
            return NotImplemented
        return result is not None and result > 0

    def __ge__(self, other: float | int | FloatDouble) -> bool:
        result = self._compare(other)
        if isinstance(result, NotImplementedType):
            return NotImplemented
        return result is not None and result >= 0


__all__ = ['FloatDouble']
