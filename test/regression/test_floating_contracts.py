from decimal import Decimal, localcontext
from fractions import Fraction
import math
import operator
import random
import unittest

from cplib.mathematics.floating import FloatDouble


def exact(value: FloatDouble) -> Fraction:
    return Fraction(value.hi) + Fraction(value.lo)


class FloatingContractsTest(unittest.TestCase):
    def assert_close(self, actual: FloatDouble, expected: Fraction, factor: int = 1) -> None:
        self.assertTrue(math.isfinite(actual.hi), (actual, expected))
        self.assertTrue(math.isfinite(actual.lo))
        error = abs(exact(actual) - expected)
        limit = abs(expected) * Fraction(factor, 1 << 101) + Fraction(1, 1 << 1073)
        self.assertLessEqual(error, limit, (actual, float(error / abs(expected)) if expected else error))
        if actual.hi:
            self.assertLessEqual(abs(actual.lo), math.ulp(actual.hi) / 2)
        else:
            self.assertEqual(actual.lo, 0.0)

    def test_construction_and_integer_comparison(self) -> None:
        for n in [0, -1, 1, 2**60 + 1, -(2**60 + 1), 2**106 - 1, 2**200 + 1, 2**200 + 2**100 + 1, 2**1023 - 1]:
            value = FloatDouble(n)
            self.assert_close(value, Fraction(n))
            for other in (n - 1, n, n + 1, 1 << 2000, -(1 << 2000)):
                for compare in (operator.eq, operator.lt, operator.le, operator.gt, operator.ge):
                    self.assertEqual(compare(value, other), compare(exact(value), other), (n, other, compare))
            copy = FloatDouble(value, 1.0)
            self.assertEqual((copy.hi, copy.lo), (value.hi, value.lo))
        self.assertEqual(exact(FloatDouble(2**60 + 1) - 2**60), 1)
        self.assertEqual(exact(FloatDouble(2**60 + 1, 0.25)), Fraction(2**60 + 1) + Fraction(1, 4))
        with self.assertRaises(OverflowError):
            FloatDouble(1 << 2000)
        for hi, lo in ((1e100, -1e100), (1e-100, 1e100), (1, 2**-54), (-0.0, 0.0), (0.0, -1.0)):
            self.assert_close(FloatDouble.from_parts(hi, lo), Fraction(hi) + Fraction(lo))

    def test_arithmetic_and_cancellation(self) -> None:
        rng = random.Random(0)
        for _ in range(1500):
            ae, be = rng.randrange(-450, 451), rng.randrange(-450, 451)
            ah = math.ldexp(rng.uniform(-2, 2), ae)
            bh = math.ldexp(rng.uniform(-2, 2), be)
            a = FloatDouble.from_parts(ah, math.ldexp(rng.uniform(-1, 1), ae - 55))
            b = FloatDouble.from_parts(bh, math.ldexp(rng.uniform(-1, 1), be - 55))
            x, y = exact(a), exact(b)
            self.assert_close(a + b, x + y)
            self.assert_close(a - b, x - y)
            self.assert_close(a * b, x * y)
            self.assert_close(a / b, x / y)
            self.assertEqual(exact(-a), -x)
            self.assertEqual(exact(abs(a)), abs(x))
            for compare in (operator.eq, operator.lt, operator.le, operator.gt, operator.ge):
                self.assertEqual(compare(a, b), compare(x, y))
        a = FloatDouble.from_parts(1, 2**-54)
        b = FloatDouble.from_parts(-1, 2**-108)
        self.assertEqual(exact(a + b), exact(a) + exact(b))
        self.assertEqual(exact(a - (-b)), exact(a) + exact(b))
        self.assertEqual(exact(3 + a), 3 + exact(a))
        self.assertEqual(exact(3 - a), 3 - exact(a))
        self.assert_close(3 * a, 3 * exact(a))
        self.assert_close(3 / a, 3 / exact(a))

    def test_extreme_exponents(self) -> None:
        largest = float.fromhex('0x1.fffffffffffffp+1023')
        smallest = math.ulp(0.0)
        values = [largest, 1e308, 1e300, 1e-300, float.fromhex('0x1p-1022'), 1e-320, smallest]
        for x in values:
            value = FloatDouble(x)
            self.assert_close(value * 1, Fraction(x))
            self.assert_close(value / value, Fraction(1))
            self.assert_close(value * -1, -Fraction(x))
            for y in values:
                expected = Fraction(x) / Fraction(y)
                if abs(expected) <= Fraction(largest):
                    self.assert_close(value / y, expected)
                expected = Fraction(x) * Fraction(y)
                if abs(expected) <= Fraction(largest):
                    self.assert_close(value * y, expected)
        self.assert_close(FloatDouble.from_parts(largest, -2.0**969) + 2.0**970, Fraction(largest) + Fraction(2)**969)
        self.assert_close(FloatDouble.from_parts(largest, -2.0**969) - (-2.0**970), Fraction(largest) + Fraction(2)**969)
        ulp = math.ulp(largest)
        a = FloatDouble.from_parts(largest - ulp, -ulp / 4)
        b = FloatDouble.from_parts(1 + 2**-52, -2**-54)
        self.assertTrue(math.isinf(a.hi * b.hi))
        self.assert_close(a * b, exact(a) * exact(b))
        self.assertLess(FloatDouble(-largest), FloatDouble(largest))
        self.assertTrue(math.isinf(float(FloatDouble(largest) * 2)))
        self.assertTrue(math.isinf(float(FloatDouble(largest) / smallest)))
        self.assert_close(FloatDouble(1e155) ** -2, Fraction(1) / Fraction(1e155) ** 2)

    def test_square_roots_and_powers(self) -> None:
        rng = random.Random(0)
        with localcontext() as context:
            context.prec = 1000
            for _ in range(250):
                x = math.ldexp(rng.uniform(0.5, 1), rng.randrange(-1073, 1024))
                value = FloatDouble(x)
                root = value.sqrt()
                expected = Decimal.from_float(x).sqrt()
                actual = Decimal.from_float(root.hi) + Decimal.from_float(root.lo)
                self.assertLessEqual(abs(actual - expected), expected * Decimal(2) ** -100)
        for x in (-3.25, -0.1, 0.1, 1.01, 2.5):
            for exponent in range(-15, 16):
                self.assert_close(FloatDouble(x) ** exponent, Fraction(x) ** exponent, 20)
        for exponent in (0.0, 1.0, 1.5, '2', None):
            with self.assertRaises(TypeError):
                FloatDouble(2) ** exponent
        with self.assertRaises(ZeroDivisionError):
            FloatDouble(0) ** -1
        with self.assertRaises(ValueError):
            FloatDouble(-1).sqrt()

    def test_nonfinite_and_signed_zero(self) -> None:
        infinity = FloatDouble(float('inf'))
        nan = FloatDouble(float('nan'))
        self.assertEqual(infinity, float('inf'))
        self.assertEqual(-infinity, -float('inf'))
        for x in (nan, 0, 1e308, -(1 << 2000), infinity):
            for compare in (operator.eq, operator.lt, operator.le, operator.gt, operator.ge):
                self.assertFalse(compare(nan, x))
                self.assertFalse(compare(x, nan))
            self.assertNotEqual(nan, x)
        self.assertEqual(infinity.sqrt(), infinity)
        self.assertTrue(math.isnan(float(nan.sqrt())))
        with self.assertRaises(ValueError):
            (-infinity).sqrt()
        cases = ((infinity + 1, math.inf), (infinity * 2, math.inf), (infinity / 2, math.inf), (FloatDouble(2) / infinity, 0.0), (infinity - infinity, math.nan), (infinity * 0, math.nan), (infinity / infinity, math.nan))
        for value, expected in cases:
            if math.isnan(expected):
                self.assertTrue(math.isnan(float(value)))
            else:
                self.assertEqual(float(value), expected)
            self.assertEqual(value.lo, 0.0)
        for x in (0.0, -0.0):
            value = FloatDouble(x)
            self.assertFalse(value)
            self.assertEqual(math.copysign(1, float(value.sqrt())), math.copysign(1, x))
            self.assertEqual(math.copysign(1, float(abs(value))), 1)
            with self.assertRaises(ZeroDivisionError):
                FloatDouble(1) / value
        self.assertEqual(FloatDouble(0), FloatDouble(-0.0))

    def test_unsupported_operands_and_reflection(self) -> None:
        value = FloatDouble(2)
        for other in (object(), '3', None):
            self.assertNotEqual(value, other)
            for operation in (operator.add, operator.sub, operator.mul, operator.truediv, operator.lt, operator.le, operator.gt, operator.ge):
                with self.assertRaises(TypeError):
                    operation(value, other)

        class Reflected:
            def __radd__(self, other: object) -> str:
                return 'reflected'

            def __gt__(self, other: object) -> bool:
                return True

        self.assertEqual(value + Reflected(), 'reflected')
        self.assertTrue(value < Reflected())


if __name__ == '__main__':
    unittest.main()
