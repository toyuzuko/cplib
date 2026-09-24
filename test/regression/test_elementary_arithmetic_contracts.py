from itertools import product
from math import gcd, isqrt, lcm
import random
import unittest

from cplib.mathematics.arithmetic import GaussianInteger, GcdConvolution, LcmConvolution, NimProduct64, linear_congruence, linear_indeterminate_equation, linear_indeterminate_equation_min_abs_sum, linear_indeterminate_equation_with_limits, two_square_sum
from cplib.mathematics.interval import interval_union, interval_intersection, range_mod
from cplib.mathematics.utility import absolute, clamp, generate_quotient, sign, xorshift64


class ElementaryArithmeticContractTests(unittest.TestCase):
    def test_integer_helpers(self):
        values = [0, -1, 1, -(1 << 31), (1 << 31) - 1, -(1 << 1000), 1 << 1000]
        for x in values:
            self.assertEqual(absolute(x), abs(x))
            self.assertEqual(sign(x), (x > 0) - (x < 0))
            for a, b in product(values, repeat=2):
                if a <= b:
                    self.assertEqual(clamp(x, a, b), min(max(x, a), b))
                else:
                    with self.assertRaises(ValueError):
                        clamp(x, a, b)
        for n in range(300):
            pieces = list(generate_quotient(n))
            covered = [0] * (n + 1)
            self.assertEqual([q for q, _, _ in pieces], sorted({n // i for i in range(1, n + 1)}))
            for q, l, r in pieces:
                self.assertTrue(1 <= l < r <= n + 1)
                for i in range(l, r):
                    self.assertEqual(n // i, q)
                    covered[i] += 1
            self.assertEqual(covered[1:], [1] * n)
        with self.assertRaises(ValueError):
            list(generate_quotient(-1))
        for state in [0, 1, (1 << 63), (1 << 64) - 1]:
            expected = state
            expected ^= expected << 7
            expected &= (1 << 64) - 1
            expected ^= expected >> 9
            self.assertEqual(xorshift64(state), expected)
        for state in [-1, 1 << 64]:
            with self.assertRaises(ValueError):
                xorshift64(state)

    def test_diophantine_equations(self):
        rng = random.Random(0)
        for a, b, c in product(range(-5, 6), range(-5, 6), range(-12, 13)):
            possible = c == 0 if a == b == 0 else c % gcd(a, b) == 0
            found, x, y = linear_indeterminate_equation(a, b, c)
            self.assertEqual(found, possible)
            if found:
                self.assertEqual(a * x + b * y, c)
            else:
                self.assertEqual((x, y), (0, 0))
            found, x, y = linear_indeterminate_equation_min_abs_sum(a, b, c)
            self.assertEqual(found, possible)
            if found:
                self.assertEqual(a * x + b * y, c)
                choices = [(abs(u) + abs(v), u > v) for u in range(-30, 31) for v in range(-30, 31) if a * u + b * v == c]
                self.assertEqual((abs(x) + abs(y), x > y), min(choices))
            xl, xr = sorted([rng.randrange(-5, 6), rng.randrange(-5, 6)])
            yl, yr = sorted([rng.randrange(-5, 6), rng.randrange(-5, 6)])
            expected = any(a * u + b * v == c for u in range(xl, xr + 1) for v in range(yl, yr + 1))
            found, x, y = linear_indeterminate_equation_with_limits(a, b, c, xl, xr, yl, yr)
            self.assertEqual(found, expected, (a, b, c, xl, xr, yl, yr))
            if found:
                self.assertTrue(xl <= x <= xr and yl <= y <= yr)
                self.assertEqual(a * x + b * y, c)
            else:
                self.assertEqual((x, y), (0, 0))
        large = 1 << 1000
        for a, b in [(-3, 7), (0, 3), (5, 0), (2, -4)]:
            c = a * large + b * (-large)
            found, x, y = linear_indeterminate_equation_with_limits(a, b, c, large, large + 4, -large - 4, -large)
            self.assertTrue(found)
            self.assertEqual(a * x + b * y, c)
            self.assertTrue(large <= x <= large + 4 and -large - 4 <= y <= -large)
        for mod in range(1, 35):
            for a, b in product(range(-10, 11), repeat=2):
                roots = [x for x in range(mod) if (a * x - b) % mod == 0]
                found, x = linear_congruence(a, b, mod)
                self.assertEqual(found, bool(roots))
                self.assertEqual(x, min(roots) if roots else 0)

    def test_gaussian_and_two_squares(self):
        rng = random.Random(1)
        for _ in range(1000):
            a = GaussianInteger(rng.randrange(-1000, 1001), rng.randrange(-1000, 1001))
            b = GaussianInteger(rng.randrange(-1000, 1001), rng.randrange(-1000, 1001))
            if b.norm() == 0:
                continue
            q, r = GaussianInteger.divmod(a, b)
            prod = b * q
            self.assertEqual((prod.real + r.real, prod.imag + r.imag), a.to_tuple())
            self.assertLess(r.norm(), b.norm())
            g = GaussianInteger.gcd(a, b)
            self.assertEqual(GaussianInteger.divmod(a, g)[1].norm(), 0)
            self.assertEqual(GaussianInteger.divmod(b, g)[1].norm(), 0)
            n = rng.randrange(8)
            expected = GaussianInteger(1, 0)
            for _ in range(n):
                expected = expected * a
            self.assertEqual((a ** n).to_tuple(), expected.to_tuple())
            rotated = a.rotate_first_quadrant()
            self.assertGreaterEqual(rotated.real, 0)
            self.assertGreaterEqual(rotated.imag, 0)
            self.assertEqual(rotated.norm(), a.norm())
        with self.assertRaises(ValueError):
            GaussianInteger(1) ** -1
        with self.assertRaises(ZeroDivisionError):
            GaussianInteger.divmod(GaussianInteger(1), GaussianInteger(0))
        for n in range(500):
            expected = [(x, isqrt(n - x * x)) for x in range(isqrt(n) + 1) if isqrt(n - x * x) ** 2 == n - x * x]
            self.assertEqual(two_square_sum(n), expected)
        self.assertEqual(two_square_sum(-1), [])
        # Mex is an independent definition of small nim products.
        nim = [[0] * 16 for _ in range(16)]
        for a in range(16):
            for b in range(16):
                excluded = {nim[x][b] ^ nim[a][y] ^ nim[x][y] for x in range(a) for y in range(b)}
                value = 0
                while value in excluded:
                    value += 1
                nim[a][b] = value
                self.assertEqual(NimProduct64.multiply(a, b), value)
        for a, b in [(-1, 0), (0, -1), (1 << 64, 0)]:
            with self.assertRaises(ValueError):
                NimProduct64.multiply(a, b)

    def test_divisor_transforms(self):
        rng = random.Random(2)
        for cls, operation in [(GcdConvolution, gcd), (LcmConvolution, lcm)]:
            old = cls.get_mod()
            try:
                for mod in [1, 6, 998244353]:
                    cls.set_mod(mod)
                    for n in range(35):
                        a = [rng.randrange(-10**12, 10**12) for _ in range(n)]
                        b = [rng.randrange(-100, 100) for _ in range(n)]
                        expected = [0] * n
                        for i in range(1, n):
                            for j in range(1, n):
                                k = operation(i, j)
                                if k < n:
                                    expected[k] = (expected[k] + a[i] * b[j]) % mod
                        self.assertEqual(cls.convolution(a, b), expected)
                        self.assertEqual(cls.mobius(cls.zeta(a)), [v % mod for v in a])
                        zeta = [a[0] % mod] if n else []
                        for i in range(1, n):
                            zeta.append(sum(a[j] for j in range(1, n) if (j % i == 0 if cls is GcdConvolution else i % j == 0)) % mod)
                        self.assertEqual(cls.zeta(a), zeta)
                for mod in [0, -1]:
                    with self.assertRaises(ValueError):
                        cls.set_mod(mod)
                    self.assertEqual(cls.get_mod(), 998244353)
            finally:
                cls.set_mod(old)

    def test_interval_helpers(self):
        rng = random.Random(3)
        for _ in range(500):
            groups = [[tuple(sorted((rng.randrange(-10, 11), rng.randrange(-10, 11)))) for _ in range(rng.randrange(8))] for _ in range(rng.randrange(5))]
            unions = [interval_union(group) for group in groups]
            sets = [{x for l, r in group for x in range(l, r)} for group in groups]
            for group, expected in zip(unions, sets):
                self.assertEqual({x for l, r in group for x in range(l, r)}, expected)
                self.assertTrue(all(l < r for l, r in group))
            intersection = interval_intersection(unions)
            expected = set.intersection(*sets) if sets else set()
            self.assertEqual({x for l, r in intersection for x in range(l, r)}, expected)
        self.assertEqual(interval_intersection([[(0, 2), (2, 4)], [(1, 3)]]), [(1, 3)])
        self.assertEqual(interval_union([(0, 0)]), [])
        for groups in [[[(2, 1)]], [[], [(2, 1)]], [[(0, 3), (2, 4)]]]:
            with self.assertRaises(ValueError):
                interval_intersection(groups)
        for l in range(-20, 21):
            for r in range(l, 22):
                for mod in range(1, 8):
                    counts = [0] * mod
                    for a, b, count in range_mod(l, r, mod):
                        self.assertTrue(0 <= a < b <= mod)
                        for i in range(a, b):
                            counts[i] += count
                    self.assertEqual(counts, [sum(x % mod == i for x in range(l, r)) for i in range(mod)])


if __name__ == '__main__':
    unittest.main()
