#!/usr/bin/env python3

from cplib.mathematics.convolution import ConvolutionLargeIntegers


class BigInt:
    """
    Arbitrary precision integer implementation.

    A class for handling integers of arbitrary size using base representation.
    Supports basic arithmetic operations with automatic precision handling.

    Attributes:
        sign: Sign of the stored integer, using ``1`` or ``-1``.
        digits: Base-``BASE`` digits in little-endian order.

    Examples:
        >>> a = BigInt("123456789012345678901234567890")
        >>> b = BigInt("987654321098765432109876543210")
        >>> c = a + b
        >>> print(c)
        1111111110111111111011111111100
        >>> d = a * b
        >>> print(str(d)[:20] + "...")  # First 20 digits
        12193263113702179522...

    Notes:
        The class uses BASE_DIGITS (default 9) for internal representation.
        For numbers with more than 128 total internal limbs in multiplication,
        NTT-based convolution is used when its CRT range can recover every
        coefficient. Wider custom limbs fall back to exact long multiplication.
        The limb size is a class-wide setting; existing objects are not
        converted when it changes. Do not mutate sign or digits directly.

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` and ``m`` are the numbers of internal base-``BASE`` digits in the
        operands, ``N = max(n, m)``, and ``M(N)`` is the multiplication cost for
        ``N`` digits.
    """
    # BASE for internal representation: digits in base BASE
    BASE_DIGITS = 9
    BASE = 10 ** BASE_DIGITS

    @classmethod
    def set_base_digits(cls, base: int) -> None:
        """
        Set the base digits for internal representation.

        Args:
            base (int): Number of decimal digits per internal digit.
                Must be a positive integer.

        Returns:
            None.

        Raises:
            ValueError: If base is not a positive integer.

        Notes:
            Existing instances are not converted. Change the base only before
            constructing values, and discard old values before changing it
            again. The default is 9 decimal digits per limb (base 10^9).

        Time Complexity:
            O(1)
        """
        if base <= 0:
            raise ValueError("Base must be a positive integer")
        cls.BASE_DIGITS = base  # pyright: ignore[reportConstantRedefinition]
        cls.BASE = 10 ** cls.BASE_DIGITS  # pyright: ignore[reportConstantRedefinition]

    def __init__(self, value: 'int | str | BigInt' = 0) -> None:
        """
        Initialize a BigInt from various input types.

        Args:
            value (int | str | BigInt): The value to initialize from.
                Can be an integer, string representation, or another BigInt.
                Defaults to 0. Decimal strings allow surrounding whitespace
                and an optional sign, followed by ASCII digits; no underscores.

        Returns:
            None.

        Raises:
            ValueError: If the string is not a valid decimal integer.

        Time Complexity:
            O(n)

        Examples:
            >>> print(BigInt(123))
            123
            >>> print(BigInt("-456789"))
            -456789
            >>> print(BigInt(BigInt(100)))
            100
        """
        if isinstance(value, BigInt):
            self.sign = value.sign
            self.digits = value.digits.copy()
            return
        self.sign = 1
        if isinstance(value, str):
            s = value.strip()
            if s.startswith(('-', '+')):
                if s[0] == '-':
                    self.sign = -1
                s = s[1:]
            if not s or not s.isascii() or not s.isdecimal():
                raise ValueError('expected decimal digits with an optional sign')
            self.digits: list[int] = []
            for i in range(len(s), 0, -self.BASE_DIGITS):
                start = max(0, i - self.BASE_DIGITS)
                self.digits.append(int(s[start:i]))
        else:
            v = value
            if v < 0:
                self.sign = -1
                v = -v
            self.digits = []
            if v == 0:
                self.digits = [0]
            else:
                while v:
                    self.digits.append(v % self.BASE)
                    v //= self.BASE
        self._normalize()

    @classmethod
    def from_digits(cls, digits: list[int], sign: int = 1) -> 'BigInt':
        """
        Construct BigInt directly from digits list and sign.

        Args:
            digits (list[int]): List of digits in base representation
                (least significant digit first), each in [0, BASE).
                An empty list represents zero.
            sign (int): Sign of the number (1 for positive, -1 for negative).
                Defaults to 1.

        Returns:
            BigInt: A new value that owns a copy of digits; zero has sign 1.

        Raises:
            ValueError: If a digit or sign is outside its domain.

        Examples:
            >>> print(BigInt.from_digits([456, 123], 1))  # 123 * BASE + 456
            123000000456
            >>> print(BigInt.from_digits([789], -1))
            -789

        Time Complexity:
            O(n)
        """
        if sign not in (-1, 1) or any(d < 0 or d >= cls.BASE for d in digits):
            raise ValueError('digits must be in [0, BASE) and sign must be -1 or 1')
        res = BigInt()
        res.sign = sign
        res.digits = digits.copy()
        res._normalize()
        return res

    def copy(self) -> 'BigInt':
        """
        Create a deep copy of this BigInt.

        Returns:
            BigInt: A new BigInt with the same value.

        Time Complexity:
            O(n)
        """
        res = BigInt(self)
        return res

    def _normalize(self) -> None:
        """
        Normalize the internal representation by removing leading zeros.

        Time Complexity:
            O(n)

        Notes:
            This is an internal method that ensures the representation
            is in canonical form (no leading zeros, sign is 1 for zero).
        """
        if not self.digits:
            self.digits = [0]
        while len(self.digits) > 1 and self.digits[-1] == 0:
            self.digits.pop()
        if len(self.digits) == 1 and self.digits[0] == 0:
            self.sign = 1

    def __str__(self):
        """
        Convert BigInt to string representation.

        Returns:
            str: Decimal string representation of the BigInt.

        Time Complexity:
            O(n)
        """
        s = ''.join(str(d).zfill(self.BASE_DIGITS) for d in reversed(self.digits))
        s = s.lstrip('0') or '0'
        return '-' + s if self.sign < 0 else s

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another value.

        Args:
            other (object): Value to compare with.

        Returns:
            bool: True if values are equal, False otherwise.

        Time Complexity:
            O(max(n, m))
        """
        if not isinstance(other, (int, str, BigInt)):
            return NotImplemented
        if not isinstance(other, BigInt):
            other = BigInt(other)
        return self.sign == other.sign and self.digits == other.digits

    def __lt__(self, other: 'int | str | BigInt') -> bool:
        """
        Check if this BigInt is less than another value.

        Args:
            other (int | str | BigInt): Value to compare with.

        Returns:
            bool: True if this < other, False otherwise.

        Time Complexity:
            O(max(n, m))
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if self.sign != other.sign:
            return self.sign < other.sign
        if len(self.digits) != len(other.digits):
            return (len(self.digits) < len(other.digits)) ^ (self.sign < 0)
        for a, b in zip(reversed(self.digits), reversed(other.digits)):
            if a != b:
                return (a < b) ^ (self.sign < 0)
        return False

    def __neg__(self):
        """
        Return the negation of this BigInt.

        Returns:
            BigInt: A new BigInt with opposite sign.

        Time Complexity:
            O(n)
        """
        res = BigInt(self)
        if res != BigInt(0):
            res.sign = -res.sign
        return res

    def __abs__(self):
        """
        Return the absolute value of this BigInt.

        Returns:
            BigInt: A new BigInt with positive sign.

        Time Complexity:
            O(n)
        """
        res = BigInt(self)
        res.sign = 1
        return res

    def __ne__(self, other: object) -> bool:
        return not self == other
    def __le__(self, other: 'int | str | BigInt') -> bool: return self < other or self == other
    def __gt__(self, other: 'int | str | BigInt'): return not self<=other
    def __ge__(self, other: 'int | str | BigInt'): return not self<other

    def __add__(self, other: 'int | str | BigInt') -> 'BigInt':
        """
        Add another value to this BigInt.

        Args:
            other (int | str | BigInt): Value to add.

        Returns:
            BigInt: A new BigInt representing the sum.

        Time Complexity:
            O(max(n, m))

        Examples:
            >>> print(BigInt(123) + BigInt(456))
            579
            >>> print(BigInt("999999999999") + 1)
            1000000000000
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if other == BigInt(0):
            return self.copy()
        if self.sign == other.sign:
            result = BigInt()
            result.sign = self.sign
            carry = 0
            digits: list[int] = []
            n, m = len(self.digits), len(other.digits)
            for i in range(max(n, m)):
                a = self.digits[i] if i < n else 0
                b = other.digits[i] if i < m else 0
                s = a + b + carry
                digits.append(s % self.BASE)
                carry = s // self.BASE
            if carry:
                digits.append(carry)
            result.digits = digits
            result._normalize()
            return result
        else:
            return self - (-other)

    def __sub__(self, other: 'int | str | BigInt') -> 'BigInt':
        """
        Subtract another value from this BigInt.

        Args:
            other (int | str | BigInt): Value to subtract.

        Returns:
            BigInt: A new BigInt representing the difference.

        Time Complexity:
            O(max(n, m))

        Examples:
            >>> print(BigInt(456) - BigInt(123))
            333
            >>> print(BigInt(100) - BigInt(200))
            -100
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if self.sign == other.sign:
            if abs(self) >= abs(other):
                result = BigInt()
                result.sign = self.sign
                carry = 0
                digits: list[int] = []
                for i in range(len(self.digits)):
                    a = self.digits[i]
                    b = other.digits[i] if i < len(other.digits) else 0
                    s = a - b - carry
                    carry = 0
                    if s < 0:
                        s += self.BASE
                        carry = 1
                    digits.append(s)
                result.digits = digits
                result._normalize()
                return result
            else:
                return -(other - self)
        else:
            return self + (-other)

    def _mul_fft(self, other: 'BigInt') -> 'BigInt':
        """
        Multiply using NTT-based convolution for large numbers.

        Args:
            other (BigInt): The multiplicand.

        Returns:
            BigInt: The product.

        Time Complexity:
            O((n + m) log(n + m))

        Notes:
            This method is automatically used for large number multiplication
            to improve performance over the naive O(n^2) algorithm.
        """
        a = self.digits
        b = other.digits
        conv = ConvolutionLargeIntegers.convolution(a, b)
        carry = 0
        for i in range(len(conv)):
            total = conv[i] + carry
            conv[i] = total % self.BASE
            carry = total // self.BASE
        while carry:
            conv.append(carry % self.BASE)
            carry //= self.BASE
        res = BigInt.from_digits(conv, self.sign * other.sign)
        return res

    def __mul__(self, other: 'int | str | BigInt') -> 'BigInt':
        """
        Multiply this BigInt by another value.

        Args:
            other (int | str | BigInt): Value to multiply by.

        Returns:
            BigInt: A new BigInt representing the product.

        Time Complexity:
            O(nm) for small operands or coefficients beyond the CRT range;
            O((n + m) log(n + m)) for supported large products.

        Examples:
            >>> print(BigInt(123) * BigInt(456))
            56088
            >>> print(BigInt("123456789") * 2)
            246913578

        Notes:
            Automatically switches to NTT-based multiplication for
            numbers with more than 128 total internal limbs.
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if len(self.digits) + len(other.digits) > 128:
            return self._mul_fft(other)
        res = [0] * (len(self.digits) + len(other.digits))
        for i in range(len(self.digits)):
            carry = 0
            for j in range(len(other.digits)):
                res[i + j] += self.digits[i] * other.digits[j] + carry
                carry = res[i + j] // self.BASE
                res[i + j] %= self.BASE
            res[i + len(other.digits)] += carry
        result = BigInt.from_digits(res, self.sign * other.sign)
        return result

    def _shift_digits(self, n: int) -> 'BigInt':
        """
        Shift digits left (multiply by BASE^n) or right (divide by BASE^-n).
        """
        if n == 0: return self.copy()
        if self.digits == [0]: return BigInt(0)

        if n > 0:
            res = BigInt()
            res.sign = self.sign
            res.digits = [0] * n + self.digits
            # No normalization needed usually unless self was 0, but we handled that.
            return res
        else:
            # Right shift
            if len(self.digits) <= -n:
                return BigInt(0)
            res = BigInt()
            res.sign = self.sign
            res.digits = self.digits[-n:] # -n is positive index
            # Need to normalize in case of leading zeros?
            # Right shift shouldn't introduce leading zeros if self was normalized.
            return res

    def _inverse(self, n: int) -> 'BigInt':
        """
        Approximate BASE^(2n) / self for an n-limb positive divisor.

        Newton refinement produces an approximation; _div_fft corrects the
        resulting quotient using the exact remainder.
        """
        if n <= 32:
            numerator = BigInt.from_digits([0] * (2 * n) + [1])
            q, _ = numerator._div_naive(self)
            return q

        k = (n + 1) // 2
        # Top k digits.
        # self has n digits. We want top k.
        # shift right by n-k.
        b_high = self._shift_digits(-(n - k))
        x_k = b_high._inverse(k)

        # Newton iteration:
        # x = 2 * x_k * BASE^(n-k) - (self * x_k^2) // BASE^(2k)

        term1 = x_k._shift_digits(n - k) * BigInt(2)
        term2 = (self * x_k * x_k)._shift_digits(-2 * k)

        x = term1 - term2
        return x

    def _div_fft(self, other: 'BigInt') -> tuple['BigInt', 'BigInt']:
        """
        Division using Newton-Raphson and NTT multiplication.
        """
        n = len(self.digits)
        m = len(other.digits)

        if n < m:
            return BigInt(0), self.copy()

        # If n is much larger than m, we can just pad other to size n
        # and compute inverse of size n.
        # This gives 1/other with n digits of precision.

        # Pad other to n digits (shift left by n-m)
        # But we need to be careful: _inverse(n) expects input to have n digits.
        # other << (n-m) has m + n - m = n digits.

        b_shifted = other._shift_digits(n - m)

        # I approx BASE^(2n) / b_shifted = BASE^(2n) / (other * BASE^(n-m))
        #   = BASE^(n+m) / other
        inv = b_shifted._inverse(n)

        # Q = self * inv // BASE^(n+m)
        # self * inv has approx n + n = 2n digits.
        # shift right by n+m.
        # Result has 2n - (n+m) = n - m digits. Correct.

        q = (self * inv)._shift_digits(-(n + m))

        # Fixup
        # q might be off by 1 or 2
        r = self - other * q

        # If r < 0, q is too big
        while r < BigInt(0):
            q = q - BigInt(1)
            r = r + other

        # If r >= other, q is too small
        while r >= other:
            q = q + BigInt(1)
            r = r - other

        return q, r

    def __divmod__(self, other: 'int | str | BigInt') -> tuple['BigInt', 'BigInt']:
        """
        Compute the quotient and remainder of division.

        Args:
            other (int | str | BigInt): The divisor.

        Returns:
            (q, r) with self = other * q + r. The quotient is rounded down,
            and a nonzero remainder has the same sign as other.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
            The limb width is treated as fixed.
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if other.digits == [0]:
            raise ZeroDivisionError('division by zero')
        abs_self, abs_other = abs(self), abs(other)
        if len(abs_other.digits) > 64 and len(abs_self.digits) > 64:
            q, r = abs_self._div_fft(abs_other)
        else:
            q, r = abs_self._div_naive(abs_other)
        if self.sign != other.sign:
            if r.digits != [0]:
                q = q + 1
                r = abs_other - r
            if q.digits != [0]:
                q.sign = -1
        if r.digits != [0]:
            r.sign = other.sign
        return q, r

    def _div_naive(self, other: 'BigInt') -> tuple['BigInt', 'BigInt']:
        """
        Naive O(n^2) division algorithm (Knuth's Algorithm D equivalent).
        Assumes self and other are positive.
        """
        if self < other:
            return BigInt(0), self.copy()

        # Normalize divisor to have high bit set (not strictly needed for base 10^9 but good for estimation)
        # Actually, for base 10^9, we can just do standard long division.

        # We'll use a simple implementation of long division.
        # Work with digits directly.

        a = self.digits.copy()
        b = other.digits
        n = len(a)
        m = len(b)

        # If divisor is single digit, use simpler loop
        if m == 1:
            rem = 0
            quot: list[int] = []
            divisor = b[0]
            for i in range(n - 1, -1, -1):
                cur = a[i] + rem * self.BASE
                q_digit = cur // divisor
                rem = cur % divisor
                quot.append(q_digit)
            quot.reverse()
            return BigInt.from_digits(quot), BigInt.from_digits([rem])

        # For multi-digit divisor, we can use estimation.
        # Or since this is Python, we can cheat a bit for the digit estimation step
        # by using Python's large integer division on the top few digits.

        # But let's implement standard long division properly.
        # Shift a and b so b's most significant digit is large (>= BASE/2)
        # This improves estimation accuracy.

        # Normalization factor d
        # We want b[-1] * d >= BASE // 2
        d = self.BASE // (b[-1] + 1)

        # Multiply a and b by d (only for calculation, doesn't affect result q, but r needs unshift)
        # We can do this by multiplying BigInts or just digits.
        # Let's use BigInt multiplication for simplicity of implementation, though slightly slower.

        big_a = self * d
        big_b = other * d

        a_digits = big_a.digits
        b_digits = big_b.digits

        # Ensure a has enough space (n+1 digits effectively)
        if len(a_digits) < len(a) + 1:
            a_digits.append(0) # Pad with zero if needed

        # Re-read lengths
        n = len(a_digits)
        m = len(b_digits)

        # q will have size n - m + 1 (at most)
        # But since we normalized, a_digits might have grown.
        # Let's just iterate.

        q_digits = [0] * (n - m + 1)

        # Divisor most significant digit
        v1 = b_digits[-1]
        v2 = b_digits[-2] if m > 1 else 0

        # Iterate from most significant position
        # We want to divide a[j:j+m+1] by b
        for j in range(n - m - 1, -1, -1):
            # Estimate qhat
            # dividend top 2 digits: a[j+m]*BASE + a[j+m-1]
            # divisor top 1 digit: v1

            dividend_high = a_digits[j+m] * self.BASE + a_digits[j+m-1]
            qhat = dividend_high // v1
            rhat = dividend_high % v1

            # Refine qhat
            while qhat >= self.BASE or (qhat * v2 > rhat * self.BASE + (a_digits[j+m-2] if j+m-2 >= 0 else 0)):
                qhat -= 1
                rhat += v1
                if rhat >= self.BASE:
                    break

            # Multiply and subtract: a[j:j+m+1] -= qhat * b
            # We do this in place on a_digits
            borrow = 0
            for i in range(m):
                p = qhat * b_digits[i]
                sub = a_digits[j+i] - p - borrow
                a_digits[j+i] = sub % self.BASE
                borrow = -(sub // self.BASE)

            sub = a_digits[j+m] - borrow
            a_digits[j+m] = sub % self.BASE
            borrow = -(sub // self.BASE)

            # If borrow is non-zero, qhat was too large
            if borrow:
                qhat -= 1
                carry = 0
                for i in range(m):
                    s = a_digits[j+i] + b_digits[i] + carry
                    a_digits[j+i] = s % self.BASE
                    carry = s // self.BASE
                a_digits[j+m] = (a_digits[j+m] + carry) % self.BASE

            q_digits[j] = qhat

        q = BigInt.from_digits(q_digits)

        # Remainder is in a_digits, need to unshift by d
        # r = r_normalized // d
        r_normalized = BigInt.from_digits(a_digits)
        r, _ = r_normalized._div_naive(BigInt(d)) # Recursive call but d is small (1 digit)

        return q, r

    def __floordiv__(self, other: 'int | str | BigInt') -> 'BigInt':
        """Divide and round down.

        Args:
            other: Integer, BigInt, or valid decimal string.

        Returns:
            Floor quotient; use trunc_div for rounding toward zero.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
        """
        q, _ = divmod(self, other)
        return q

    def trunc_div(self, other: 'int | str | BigInt') -> 'BigInt':
        """
        Divide by ``other`` and truncate the quotient toward zero.

        Args:
            other: Divisor.

        Returns:
            Quotient rounded toward zero.

        Raises:
            ZeroDivisionError: If ``other`` is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
            The limb width is treated as fixed.

        Space Complexity:
            O(N)
        """
        if not isinstance(other, BigInt):
            other = BigInt(other)
        if other == BigInt(0):
            raise ZeroDivisionError("division by zero")
        abs_self = abs(self)
        abs_other = abs(other)
        q, _ = divmod(abs_self, abs_other)
        if self.sign != other.sign and q != BigInt(0):
            q.sign = -1
        return q

    def __mod__(self, other: 'int | str | BigInt') -> 'BigInt':
        """Return the floor-division remainder.

        Args:
            other: Integer, BigInt, or valid decimal string.

        Returns:
            self - other * (self // other), with the sign of other unless zero.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
        """
        _, r = divmod(self, other)
        return r


class BigIntHex:
    """
    Arbitrary precision integer implementation with hexadecimal representation.

    A class for handling integers of arbitrary size using binary base representation.
    Internally stores digits in base 2^BASE_BITS for efficient operations.

    Attributes:
        sign: Sign of the stored integer, using ``1`` or ``-1``.
        digits: Base-``BASE`` digits in little-endian order.

    Examples:
        >>> a = BigIntHex("0x1234567890abcdef")
        >>> b = BigIntHex("0xfedcba9876543210")
        >>> c = a + b
        >>> print(c)
        0x11111111106ffffff
        >>> d = a * BigIntHex(16)  # Multiply by 16 (0x10)
        >>> print(d)
        0x1234567890abcdef0

    Notes:
        The class uses BASE_BITS (default 32) for internal representation.
        Bitwise operations (&, |, ^, <<, >>) are not currently implemented.
        For numbers with more than 128 total internal limbs in multiplication,
        NTT-based convolution is used when its CRT range can recover every
        coefficient. Wider custom limbs fall back to exact long multiplication.
        The limb size is a class-wide setting; existing objects are not
        converted when it changes. Do not mutate sign or digits directly.

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` and ``m`` are the numbers of internal base-``BASE`` digits in the
        operands, ``N = max(n, m)``, and ``M(N)`` is the multiplication cost for
        ``N`` digits.
    """
    BASE_BITS = 32
    BASE = 1 << BASE_BITS
    BASE_MASK = BASE - 1
    HEX_GROUP = BASE_BITS // 4

    @classmethod
    def set_base_bits(cls, bits: int) -> None:
        """
        Set the number of bits stored in one hexadecimal limb.

        ``bits`` must be a positive multiple of ``4`` so each limb corresponds
        to a whole number of hexadecimal digits. Existing instances are not
        converted; call this before constructing values that should use the new
        limb size.

        Args:
            bits: Limb width in bits.

        Returns:
            None.

        Raises:
            ValueError: If ``bits`` is not a positive multiple of ``4``.

        Time Complexity:
            O(1)
        """
        if bits <= 0 or bits % 4:
            raise ValueError("bits must be positive and a multiple of 4")
        cls.BASE_BITS = bits  # pyright: ignore[reportConstantRedefinition]
        cls.BASE = 1 << bits  # pyright: ignore[reportConstantRedefinition]
        cls.BASE_MASK = cls.BASE - 1  # pyright: ignore[reportConstantRedefinition]
        cls.HEX_GROUP = bits // 4  # pyright: ignore[reportConstantRedefinition]

    def __init__(self, value: 'int | str | BigIntHex' = 0) -> None:
        """
        Initialize a BigIntHex from an integer, hexadecimal string, or BigIntHex.

        Args:
            value: Integer, BigIntHex, or hexadecimal string. Strings allow
                surrounding whitespace, an optional sign, and an optional 0x
                prefix, followed by ASCII hexadecimal digits; no underscores.

        Returns:
            None.

        Raises:
            ValueError: If the string is not a valid hexadecimal integer.

        Time Complexity:
            O(n)
        """
        if isinstance(value, BigIntHex):
            self.sign = value.sign
            self.digits = value.digits.copy()
            return

        self.sign = 1
        if isinstance(value, str):
            s = value.strip()
            if s.startswith(('-', '+')):
                if s[0] == '-':
                    self.sign = -1
                s = s[1:]
            s = s.lower()
            if s.startswith('0x'):
                s = s[2:]
            if not s or any(c not in '0123456789abcdef' for c in s):
                raise ValueError('expected hexadecimal digits with an optional sign and 0x prefix')
            self.digits: list[int] = []
            for i in range(len(s), 0, -self.HEX_GROUP):
                start = max(0, i - self.HEX_GROUP)
                chunk = int(s[start:i], 16) if s[start:i] else 0
                self.digits.append(chunk)
        else:
            v = value
            if v < 0:
                self.sign = -1
                v = -v
            self.digits = []
            if v == 0:
                self.digits = [0]
            else:
                while v:
                    self.digits.append(v & self.BASE_MASK)
                    v >>= self.BASE_BITS

        self._normalize()

    @classmethod
    def from_digits(cls, digits: list[int], sign: int = 1) -> "BigIntHex":
        """
        Construct a hexadecimal integer from little-endian internal limbs.

        Args:
            digits: Limbs in [0, BASE); an empty list represents zero.
            sign: 1 or -1.

        Returns:
            A new value that owns a copy of digits; zero has sign 1.

        Raises:
            ValueError: If a digit or sign is outside its domain.

        Time Complexity:
            O(n)
        """
        if sign not in (-1, 1) or any(d < 0 or d >= cls.BASE for d in digits):
            raise ValueError('digits must be in [0, BASE) and sign must be -1 or 1')
        res = BigIntHex()
        res.sign = sign
        res.digits = digits.copy()
        res._normalize()
        return res

    def copy(self) -> "BigIntHex":
        """
        Return an independent copy with the same value.

        Args:
            None.

        Returns:
            A BigIntHex with its own digits list.

        Time Complexity:
            O(n)
        """
        return BigIntHex(self)

    def _normalize(self) -> None:
        if not self.digits:
            self.digits = [0]
        while len(self.digits) > 1 and self.digits[-1] == 0:
            self.digits.pop()
        if len(self.digits) == 1 and self.digits[0] == 0:
            self.sign = 1

    def __str__(self):
        if not self.digits: return "0x0"
        parts = [format(self.digits[-1], "x")]
        for d in reversed(self.digits[:-1]):
            parts.append(format(d, f"0{self.HEX_GROUP}x"))
        s = "".join(parts) or "0"
        return ("-" if self.sign < 0 else "") + "0x" + s

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (int, str, BigIntHex)):
            return NotImplemented
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)
        return self.sign == other.sign and self.digits == other.digits

    def __lt__(self, other: 'int | str | BigIntHex') -> bool:
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)
        if self.sign != other.sign:
            return self.sign < other.sign
        if len(self.digits) != len(other.digits):
            return (len(self.digits) < len(other.digits)) ^ (self.sign < 0)
        for a, b in zip(reversed(self.digits), reversed(other.digits)):
            if a != b:
                return (a < b) ^ (self.sign < 0)
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other
    def __le__(self, other: 'int | str | BigIntHex') -> bool: return self < other or self == other
    def __gt__(self, other: 'int | str | BigIntHex') -> bool: return not self <= other
    def __ge__(self, other: 'int | str | BigIntHex') -> bool: return not self < other

    def __neg__(self):
        res = self.copy()
        if res != BigIntHex(0):
            res.sign = -res.sign
        return res

    def __abs__(self):
        res = self.copy()
        res.sign = 1
        return res

    def __add__(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """Add another integer.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            self + other.

        Time Complexity:
            O(max(n, m))
        """
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)
        if other == BigIntHex(0):
            return self.copy()

        if self.sign == other.sign:
            carry = 0
            res_digits: list[int] = []
            n, m = len(self.digits), len(other.digits)
            for i in range(max(n, m)):
                a = self.digits[i] if i < n else 0
                b = other.digits[i] if i < m else 0
                s = a + b + carry
                res_digits.append(s & self.BASE_MASK)
                carry = s >> self.BASE_BITS
            if carry:
                res_digits.append(carry)
            return BigIntHex.from_digits(res_digits, self.sign)

        return self - (-other)

    def __sub__(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """Subtract another integer.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            self - other.

        Time Complexity:
            O(max(n, m))
        """
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)

        if self.sign == other.sign:
            if abs(self) >= abs(other):
                carry = 0
                res_digits: list[int] = []
                for i in range(len(self.digits)):
                    a = self.digits[i]
                    b = other.digits[i] if i < len(other.digits) else 0
                    s = a - b - carry
                    carry = 0
                    if s < 0:
                        s += self.BASE
                        carry = 1
                    res_digits.append(s)
                return BigIntHex.from_digits(res_digits, self.sign)
            else:
                return -(other - self)
        else:
            return self + (-other)

    def _mul_fft(self, other: 'BigIntHex') -> 'BigIntHex':
        a, b = self.digits, other.digits
        conv = ConvolutionLargeIntegers.convolution(a, b)
        carry = 0
        for i in range(len(conv)):
            total = conv[i] + carry
            conv[i] = total & self.BASE_MASK
            carry = total >> self.BASE_BITS
        while carry:
            conv.append(carry & self.BASE_MASK)
            carry >>= self.BASE_BITS
        return BigIntHex.from_digits(conv, self.sign * other.sign)

    def __mul__(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """Multiply by another integer.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            self * other.

        Time Complexity:
            O(nm), or O((n + m) log(n + m)) for supported NTT products.
        """
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)

        if len(self.digits) + len(other.digits) > 128:
            return self._mul_fft(other)

        res = [0] * (len(self.digits) + len(other.digits))
        for i in range(len(self.digits)):
            carry = 0
            for j in range(len(other.digits)):
                res[i + j] += self.digits[i] * other.digits[j] + carry
                carry = res[i + j] >> self.BASE_BITS
                res[i + j] &= self.BASE_MASK
            res[i + len(other.digits)] += carry
        return BigIntHex.from_digits(res, self.sign * other.sign)

    def _shift_digits(self, n: int) -> "BigIntHex":
        """
        Shift digits left (multiply by BASE^n) or right (divide by BASE^-n).
        """
        if n == 0:
            return self.copy()
        if self.digits == [0]:
            return BigIntHex(0)
        if n > 0:
            res = BigIntHex()
            res.sign = self.sign
            res.digits = [0] * n + self.digits
            return res
        # Right shift
        if len(self.digits) <= -n:
            return BigIntHex(0)
        res = BigIntHex()
        res.sign = self.sign
        res.digits = self.digits[-n:]
        res._normalize()
        return res

    def _inverse(self, n: int) -> "BigIntHex":
        """
        Approximate BASE^(2n) / self for an n-limb positive divisor.

        Newton refinement produces an approximation; _div_fft corrects the
        resulting quotient using the exact remainder.
        """
        if n <= 32:
            numerator = BigIntHex.from_digits([0] * (2 * n) + [1])
            q, _ = numerator._div_naive(self)
            return q

        k = (n + 1) // 2
        b_high = self._shift_digits(-(n - k))
        x_k = b_high._inverse(k)

        term1 = x_k._shift_digits(n - k) * BigIntHex(2)
        term2 = (self * x_k * x_k)._shift_digits(-2 * k)
        return term1 - term2

    def _div_fft(self, other: "BigIntHex") -> tuple["BigIntHex", "BigIntHex"]:
        """
        Division using Newton-Raphson and NTT multiplication.
        """
        n = len(self.digits)
        m = len(other.digits)
        if n < m:
            return BigIntHex(0), self.copy()

        b_shifted = other._shift_digits(n - m)
        inv = b_shifted._inverse(n)
        q = (self * inv)._shift_digits(-(n + m))

        r = self - other * q
        while r < BigIntHex(0):
            q = q - BigIntHex(1)
            r = r + other
        while r >= other:
            q = q + BigIntHex(1)
            r = r - other
        return q, r

    def __divmod__(self, other: 'int | str | BigIntHex') -> tuple['BigIntHex', 'BigIntHex']:
        """Compute floor quotient and remainder.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            (q, r) with self = other * q + r; q is rounded down and a
            nonzero r has the sign of other.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
        """
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)
        if other.digits == [0]:
            raise ZeroDivisionError('division by zero')
        abs_self, abs_other = abs(self), abs(other)
        if len(abs_other.digits) > 64 and len(abs_self.digits) > 64:
            q, r = abs_self._div_fft(abs_other)
        else:
            q, r = abs_self._div_naive(abs_other)
        if self.sign != other.sign:
            if r.digits != [0]:
                q = q + 1
                r = abs_other - r
            if q.digits != [0]:
                q.sign = -1
        if r.digits != [0]:
            r.sign = other.sign
        return q, r

    def _div_naive(self, other: 'BigIntHex') -> tuple['BigIntHex', 'BigIntHex']:
        """
        Naive long division assuming both operands are positive.
        """
        if self < other:
            return BigIntHex(0), self.copy()

        a = self.digits.copy()
        b = other.digits
        n = len(a)
        m = len(b)

        if m == 1:
            rem = 0
            quot: list[int] = []
            divisor = b[0]
            for i in range(n - 1, -1, -1):
                cur = (rem << self.BASE_BITS) + a[i]
                q_digit = cur // divisor
                rem = cur % divisor
                quot.append(q_digit)
            quot.reverse()
            return BigIntHex.from_digits(quot), BigIntHex.from_digits([rem])

        d = self.BASE // (b[-1] + 1)
        big_a = self * d
        big_b = other * d

        a_digits = big_a.digits
        b_digits = big_b.digits

        if len(a_digits) < len(a) + 1:
            a_digits.append(0)

        n = len(a_digits)
        m = len(b_digits)
        q_digits = [0] * (n - m + 1)

        v1 = b_digits[-1]
        v2 = b_digits[-2] if m > 1 else 0

        for j in range(n - m - 1, -1, -1):
            dividend_high = (a_digits[j + m] << self.BASE_BITS) + a_digits[j + m - 1]
            qhat = dividend_high // v1
            rhat = dividend_high % v1

            while qhat >= self.BASE or (qhat * v2 > (rhat << self.BASE_BITS) + (a_digits[j + m - 2] if j + m - 2 >= 0 else 0)):
                qhat -= 1
                rhat += v1
                if rhat >= self.BASE:
                    break

            borrow = 0
            for i in range(m):
                p = qhat * b_digits[i]
                sub = a_digits[j + i] - p - borrow
                a_digits[j + i] = sub % self.BASE
                borrow = -(sub // self.BASE)

            sub = a_digits[j + m] - borrow
            a_digits[j + m] = sub % self.BASE
            borrow = -(sub // self.BASE)

            if borrow:
                qhat -= 1
                carry = 0
                for i in range(m):
                    s = a_digits[j + i] + b_digits[i] + carry
                    a_digits[j + i] = s % self.BASE
                    carry = s // self.BASE
                a_digits[j + m] = (a_digits[j + m] + carry) % self.BASE

            q_digits[j] = qhat

        q = BigIntHex.from_digits(q_digits)
        r_normalized = BigIntHex.from_digits(a_digits)
        r, _ = r_normalized._div_naive(BigIntHex(d))

        return q, r

    def __floordiv__(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """Divide and round down.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            Floor quotient; use trunc_div for rounding toward zero.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
        """
        q, _ = divmod(self, other)
        return q

    def trunc_div(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """
        Divide by ``other`` and truncate the quotient toward zero.

        Args:
            other: Divisor.

        Returns:
            Quotient rounded toward zero.

        Raises:
            ZeroDivisionError: If ``other`` is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
            The limb width is treated as fixed.

        Space Complexity:
            O(N)
        """
        if not isinstance(other, BigIntHex):
            other = BigIntHex(other)
        if other == BigIntHex(0):
            raise ZeroDivisionError("division by zero")
        abs_self = abs(self)
        abs_other = abs(other)
        q, _ = divmod(abs_self, abs_other)
        if self.sign != other.sign and q != BigIntHex(0):
            q.sign = -1
        return q

    def __mod__(self, other: 'int | str | BigIntHex') -> 'BigIntHex':
        """Return the floor-division remainder.

        Args:
            other: Integer, BigIntHex, or valid hexadecimal string.

        Returns:
            self - other * (self // other), with the sign of other unless zero.

        Raises:
            ZeroDivisionError: If other is zero.

        Time Complexity:
            O(nm) for small operands; O(M(N) log N) for large operands.
        """
        _, r = divmod(self, other)
        return r

    def __int__(self):
        acc = 0
        for d in reversed(self.digits):
            acc = (acc << self.BASE_BITS) | d
        return acc if self.sign > 0 else -acc
