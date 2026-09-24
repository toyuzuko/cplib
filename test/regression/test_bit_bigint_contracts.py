import random
import unittest

from cplib.mathematics.bigint import BigInt, BigIntHex
from cplib.mathematics.convolution import ConvolutionLargeIntegers
from cplib.mathematics.bit import (
    bit_reverse, filllower, fillupper, lmbit, lzcount, popcount,
    rmbit, sum_of_all_pairs_of_xor, tzcount,
)


def integer(value: BigInt | BigIntHex) -> int:
    # Read the documented representation without relying on string formatting.
    result = 0
    for digit in reversed(value.digits):
        result = result * value.BASE + digit
    return value.sign * result


class BitContractsTest(unittest.TestCase):
    def test_fixed_width_operations(self) -> None:
        rng = random.Random(0)
        cases = [0, -1, -(1 << 200), 1 << 200]
        cases += [sign * ((1 << bit) + delta) for sign in (-1, 1) for bit in range(66) for delta in (-1, 0, 1)]
        cases += [rng.randrange(-(1 << 200), 1 << 200) for _ in range(1000)]
        for x in cases:
            y = x & 0xffffffff
            bits = f'{y:032b}'
            trailing = len(bits) - len(bits.rstrip('0'))
            leading = len(bits) - len(bits.lstrip('0'))
            self.assertEqual(popcount(x), bits.count('1'))
            self.assertEqual(bit_reverse(x), int(bits[::-1], 2))
            self.assertEqual(tzcount(x), trailing)
            self.assertEqual(lzcount(x), leading)
            self.assertEqual(lmbit(x), 1 << (31 - leading) if y else 0)
            self.assertEqual(filllower(x), (1 << (32 - leading)) - 1)
            self.assertEqual(fillupper(x), ((1 << (32 - trailing)) - 1) << trailing)
            self.assertEqual(rmbit(x), abs(x) & -abs(x))

    def test_xor_pair_sum(self) -> None:
        rng = random.Random(0)
        for _ in range(1000):
            values = [rng.randrange(-(1 << 130), 1 << 130) for _ in range(rng.randrange(21))]
            self.assertEqual(sum_of_all_pairs_of_xor(values), sum(a ^ b for i, a in enumerate(values) for b in values[i + 1:]))
        self.assertEqual(sum_of_all_pairs_of_xor([0, 1 << 1000]), 1 << 1000)


class BigIntContractsTest(unittest.TestCase):
    def assert_canonical(self, value: BigInt | BigIntHex) -> None:
        self.assertTrue(value.digits)
        self.assertIn(value.sign, (-1, 1))
        self.assertTrue(all(0 <= digit < value.BASE for digit in value.digits))
        self.assertTrue(value.digits[-1] or len(value.digits) == 1)
        if integer(value) == 0:
            self.assertEqual(value.sign, 1)
            self.assertEqual(value, 0)

    def test_construction_and_zero(self) -> None:
        for cls in (BigInt, BigIntHex):
            for digits in ([], [0], [0, 0, 0]):
                for sign in (-1, 1):
                    value = cls.from_digits(digits, sign)
                    self.assert_canonical(value)
                    self.assertEqual(integer(value), 0)
                    with self.assertRaises(ZeroDivisionError):
                        divmod(cls(1), value)
            for text in ('', ' ', '+', '-', '1_000', '1 0', '--1', '+-1', '1+23456789', '１'):
                with self.assertRaises(ValueError, msg=(cls, text)):
                    cls(text)
            if cls is BigIntHex:
                for text in ('0x', '-0x', '0xx1', '0x-1', '0x+1', '0x0x1'):
                    with self.assertRaises(ValueError):
                        cls(text)
            for n in (0, -1, 1, 10**100 + 123, -(10**100 + 123)):
                text = hex(n) if cls is BigIntHex else str(n)
                for source in (n, text, '  ' + text + '  ', cls(n)):
                    value = cls(source)
                    self.assert_canonical(value)
                    self.assertEqual(integer(value), n)
                    self.assertEqual(int(str(value), 16 if cls is BigIntHex else 10), n)
                    copy = value.copy()
                    copy.digits[0] = (copy.digits[0] + 1) % cls.BASE
                    self.assertEqual(integer(value), n)
            for digits, sign in (([-1], 1), ([cls.BASE], 1), ([1], 0), ([1], 2)):
                with self.assertRaises(ValueError):
                    cls.from_digits(digits, sign)
            digits = [2, 3]
            value = cls.from_digits(digits)
            digits[0] = 7
            self.assertEqual(value.digits, [2, 3])

    def test_signed_arithmetic(self) -> None:
        rng = random.Random(0)
        cases = [(a, b) for a in range(-15, 16) for b in range(-15, 16)]
        cases += [(rng.randrange(-(1 << 200), 1 << 200), rng.randrange(-(1 << 100), 1 << 100)) for _ in range(1500)]
        for cls in (BigInt, BigIntHex):
            for a, b in cases:
                left, right = cls(a), cls(b)
                for result, expected in ((left + right, a + b), (left - right, a - b), (left * right, a * b), (-left, -a), (abs(left), abs(a))):
                    self.assertEqual(integer(result), expected)
                    self.assert_canonical(result)
                self.assertEqual((left == right, left < right, left <= right, left > right, left >= right), (a == b, a < b, a <= b, a > b, a >= b))
                if b:
                    q, r = divmod(left, right)
                    self.assertEqual((integer(q), integer(r)), divmod(a, b))
                    self.assert_canonical(q)
                    self.assert_canonical(r)
                    self.assertEqual(integer(left // right), a // b)
                    self.assertEqual(integer(left % right), a % b)
                    self.assertEqual(integer(left.trunc_div(right)), (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1))
                else:
                    with self.assertRaises(ZeroDivisionError):
                        divmod(left, right)
                self.assertEqual((integer(left), integer(right)), (a, b))

    def test_large_products_and_division(self) -> None:
        rng = random.Random(0)
        for cls in (BigInt, BigIntHex):
            for n, m in ((63, 64), (64, 65), (65, 65), (129, 65), (190, 100), (256, 257), (300, 65)):
                for top in (1, cls.BASE - 1):
                    left = cls.from_digits([rng.randrange(cls.BASE) for _ in range(n - 1)] + [top])
                    right = cls.from_digits([rng.randrange(cls.BASE) for _ in range(m - 1)] + [top])
                    a, b = integer(left), integer(right)
                    self.assertEqual(integer(left * right), a * b)
                    for sa, sb in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                        left.sign, right.sign = sa, sb
                        q, r = divmod(left, right)
                        self.assertEqual((integer(q), integer(r)), divmod(sa * a, sb * b))
                        self.assert_canonical(q)
                        self.assert_canonical(r)

    def test_custom_radices(self) -> None:
        old_decimal, old_hex = BigInt.BASE_DIGITS, BigIntHex.BASE_BITS
        rng = random.Random(0)
        try:
            for cls, configure, widths in ((BigInt, BigInt.set_base_digits, (1, 3, 9, 30)), (BigIntHex, BigIntHex.set_base_bits, (4, 12, 32, 160))):
                for width in widths:
                    configure(width)
                    for n, m in ((10, 5), (70, 69)):
                        a, b = rng.randrange(cls.BASE ** (n - 1), cls.BASE ** n), rng.randrange(cls.BASE ** (m - 1), cls.BASE ** m)
                        left, right = cls(a), cls(b)
                        self.assertEqual(integer(left * right), a * b)
                        self.assertEqual(tuple(map(integer, divmod(left, right))), divmod(a, b))
                        self.assertEqual(integer(cls(str(left))), a)
                before = cls.BASE
                for width in (0, -1):
                    with self.assertRaises(ValueError):
                        configure(width)
                    self.assertEqual(cls.BASE, before)
            with self.assertRaises(ValueError):
                BigIntHex.set_base_bits(7)
        finally:
            BigInt.set_base_digits(old_decimal)
            BigIntHex.set_base_bits(old_hex)


class IntegerConvolutionContractsTest(unittest.TestCase):
    def test_signed_and_wide_coefficients(self) -> None:
        rng = random.Random(0)
        for width in (3, 16, 30, 50, 65, 100, 200):
            for _ in range(20):
                a = [rng.randrange(-(1 << width), 1 << width) for _ in range(rng.randrange(1, 20))]
                b = [rng.randrange(-(1 << width), 1 << width) for _ in range(rng.randrange(1, 20))]
                expected = [sum(a[j] * b[i - j] for j in range(len(a)) if 0 <= i - j < len(b)) for i in range(len(a) + len(b) - 1)]
                square = [sum(a[j] * a[i - j] for j in range(len(a)) if 0 <= i - j < len(a)) for i in range(2 * len(a) - 1)]
                for modulus in (0, 1, 10**9 + 7, 1 << 300):
                    self.assertEqual(ConvolutionLargeIntegers.convolution(a, b, modulus), [x % modulus for x in expected] if modulus else expected)
                    self.assertEqual(ConvolutionLargeIntegers.autoconvolution(a, modulus), [x % modulus for x in square] if modulus else square)
        self.assertEqual(ConvolutionLargeIntegers.convolution([], [1]), [])
        self.assertEqual(ConvolutionLargeIntegers.autoconvolution([]), [])
        with self.assertRaises(ValueError):
            ConvolutionLargeIntegers.convolution([], [], -1)
        with self.assertRaises(ValueError):
            ConvolutionLargeIntegers.autoconvolution([], -1)


if __name__ == '__main__':
    unittest.main()
