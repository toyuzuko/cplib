import math
import random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.factorial import BinomialCoefficient, FactorialMod, LargeFactorialMod, PowMod


class FactorialContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.defaults = (FactorialMod.get_mod(), PowMod.get_mod(), BinomialCoefficient._mod, LargeFactorialMod.get_mod(), ConvolutionMod.get_mod())

    def tearDown(self) -> None:
        factorial, power, binomial, large, convolution = self.defaults
        FactorialMod.set_mod(factorial)
        PowMod.set_mod(power)
        BinomialCoefficient.set_mod(binomial)
        LargeFactorialMod.set_mod(large)
        if ConvolutionMod.get_mod() != convolution:
            ConvolutionMod.set_mod(convolution)

    def test_factorial_tables_and_bounds(self) -> None:
        for modulus in (2, 3, 7, 31, 97):
            FactorialMod.set_mod(modulus)
            for bound in (0, 1, modulus - 1):
                table = FactorialMod(bound)
                for n in range(bound + 1):
                    fact = math.factorial(n) % modulus
                    self.assertEqual(table.factorial(n), fact)
                    self.assertEqual(table.factorial_inv(n), pow(fact, -1, modulus))
                    if n:
                        self.assertEqual(table.inv(n), pow(n, -1, modulus))
                    for k in range(n + 3):
                        self.assertEqual(table.comb(n, k), math.comb(n, k) % modulus)
                        self.assertEqual(table.perm(n, k), math.perm(n, k) % modulus)
                with self.assertRaises(ZeroDivisionError):
                    table.inv(0)
            for bound in (-1, modulus, modulus + 1):
                with self.assertRaises(ValueError):
                    FactorialMod(bound)
            for invalid in (-1, 0, 1):
                with self.assertRaises(ValueError):
                    FactorialMod.set_mod(invalid)
                self.assertEqual(FactorialMod.get_mod(), modulus)

    def test_power_composite_moduli(self) -> None:
        tables: list[tuple[int, int, PowMod]] = []
        for modulus in range(1, 31):
            PowMod.set_mod(modulus)
            for base in range(-10, 11):
                self.assertEqual(PowMod(base, 0).pow(0), 1 % modulus)
                if math.gcd(base, modulus) != 1:
                    with self.assertRaises(ValueError):
                        PowMod(base, 5)
                    continue
                table = PowMod(base, 10)
                for exponent in range(-10, 11):
                    self.assertEqual(table.pow(exponent), pow(base, exponent, modulus))
                tables.append((modulus, base, table))
        PowMod.set_mod(37)
        for modulus, base, table in tables:
            self.assertEqual(table._mod, modulus)
            self.assertEqual(table.pow(-3), pow(base, -3, modulus))
        with self.assertRaises(ValueError):
            PowMod(2, -1)
        for invalid in (0, -1):
            with self.assertRaises(ValueError):
                PowMod.set_mod(invalid)
            self.assertEqual(PowMod.get_mod(), 37)

    def test_binomial_prime_powers_and_modulus_one(self) -> None:
        tables: list[tuple[int, BinomialCoefficient]] = []
        for modulus in list(range(1, 81)) + [128, 243, 360, 1024]:
            BinomialCoefficient.set_mod(modulus)
            table = BinomialCoefficient()
            for n in range(31):
                for k in range(n + 3):
                    self.assertEqual(table.binom(n, k), math.comb(n, k) % modulus, (modulus, n, k))
            self.assertEqual(table.binom(5, -1), 0)
            self.assertEqual(table.binom(-1, 0), 0)
            tables.append((modulus, table))
        BinomialCoefficient.set_mod(13)
        for modulus, table in tables:
            self.assertEqual(table.binom(100, 50), math.comb(100, 50) % modulus)
            self.assertEqual(table.binom(10**30, 3), math.comb(10**30, 3) % modulus)
            self.assertEqual(table.binom(0, 0), 1 % modulus)
        for invalid in (-1, 0):
            with self.assertRaises(ValueError):
                BinomialCoefficient.set_mod(invalid)
            self.assertEqual(BinomialCoefficient._mod, 13)

    def test_large_factorial_blocks(self) -> None:
        rng = random.Random(0)
        for modulus in (2, 3, 7, 17, 31, 97, 257, 998244353, 1000000007):
            LargeFactorialMod.set_mod(modulus)
            maximum = min(modulus + 3, 3000)
            expected = [1]
            for n in range(1, maximum + 1):
                expected.append(expected[-1] * n % modulus)
            queries = [rng.randrange(maximum + 1) for _ in range(100)] + [0, 1, maximum, 2]
            for block in (None, 1, 2, 7, 64, 10000):
                table = LargeFactorialMod(block)
                self.assertEqual(table.factorials(queries), [expected[n] for n in queries], (modulus, block))
                self.assertEqual(table.factorials([]), [])
                self.assertEqual(table.factorial(2), expected[2])
                self.assertEqual(table.factorials([modulus, modulus + 1]), [0, 0])
                with self.assertRaises(ValueError):
                    table.factorials([1, -1])
        for block in (0, -1):
            with self.assertRaises(ValueError):
                LargeFactorialMod(block)
        for invalid in (-1, 0, 1):
            with self.assertRaises(ValueError):
                LargeFactorialMod.set_mod(invalid)
            self.assertEqual(LargeFactorialMod.get_mod(), 1000000007)

    def test_large_modulus_is_current_and_setter_is_lazy(self) -> None:
        old_transform = ConvolutionMod.get_mod()
        helper = LargeFactorialMod(4)
        with patch.object(ConvolutionMod, 'set_mod', side_effect=AssertionError('eager transform initialization')):
            LargeFactorialMod.set_mod(17)
            LargeFactorialMod.set_mod(17)
        self.assertEqual(ConvolutionMod.get_mod(), old_transform)
        self.assertEqual(helper.factorial(5), 120 % 17)
        LargeFactorialMod.set_mod(31)
        self.assertEqual(helper.factorial(5), 120 % 31)


if __name__ == '__main__':
    unittest.main()
