from random import Random
import unittest

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS, sum_of_exponential_times_polynomial


def geometric(r: int, n: int, mod: int) -> int:
    if r % mod == 1:
        return n % mod
    return (1 - pow(r, n, mod)) * pow(1-r, -1, mod) % mod


class PolynomialSumContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        if FPS.get_mod() != self.mod:
            FPS.set_mod(self.mod)
        if ConvolutionMod.get_mod() != self.transform:
            ConvolutionMod.set_mod(self.transform)

    def test_finite_sum_exhaustive_small_fields(self) -> None:
        for mod in (2, 3, 5, 7, 17):
            FPS.set_mod(mod)
            for d in range(2*mod+3):
                for r in range(mod):
                    expected = 0
                    for n in range(2*mod+5):
                        self.assertEqual(sum_of_exponential_times_polynomial(r, d, n), expected, (mod, r, d, n))
                        expected = (expected + pow(r, n, mod)*pow(n, d, mod)) % mod
            for r, d, n in ((2, -1, None), (2, 0, -1), (mod+1, 2, None)):
                with self.assertRaises(ValueError):
                    sum_of_exponential_times_polynomial(r, d, n)
            self.assertEqual(sum_of_exponential_times_polynomial(1, 10**100, 0), 0)

    def test_large_indices_against_period_blocks(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 5, 17, 97):
            FPS.set_mod(mod)
            for _ in range(100):
                r = rng.randrange(-2*mod, 2*mod)
                d = rng.randrange(10**30)
                n = rng.randrange(10**30)
                q, tail = divmod(n, mod)
                block = sum(pow(r, i, mod)*pow(i, d, mod) for i in range(mod)) % mod
                partial = sum(pow(r, i, mod)*pow(i, d, mod) for i in range(tail)) % mod
                ratio = pow(r, mod, mod)
                expected = (block*geometric(ratio, q, mod) + pow(ratio, q, mod)*partial) % mod
                self.assertEqual(sum_of_exponential_times_polynomial(r, d, n), expected, (mod, r, d, n))
        FPS.set_mod(998244353)
        mod = FPS.get_mod()
        n = 10**100
        for d in (mod-1, 2*(mod-1), 10**50*(mod-1)):
            for r in (0, 1, 2, -3):
                expected = (geometric(r, n, mod) - geometric(pow(r, mod, mod), (n+mod-1)//mod, mod)) % mod
                self.assertEqual(sum_of_exponential_times_polynomial(r, d, n), expected)

    def test_generating_function_against_period_and_closed_forms(self) -> None:
        for mod in (2, 3, 5, 17):
            FPS.set_mod(mod)
            for d in list(range(2*mod+3)) + [10**30, 10**30+1]:
                for r in range(mod):
                    if r == 1:
                        continue
                    block = sum(pow(r, i, mod)*pow(i, d, mod) for i in range(mod)) % mod
                    expected = block * pow(1-pow(r, mod, mod), -1, mod) % mod
                    self.assertEqual(sum_of_exponential_times_polynomial(r, d), expected, (mod, r, d))
        for mod in (998244353, 1000000007):
            FPS.set_mod(mod)
            for r in (-5, -1, 0, 2, 3, mod+2):
                numerators = [1, r, r*(1+r), r*(1+4*r+r*r), r*(1+11*r+11*r*r+r**3)]
                for d, numerator in enumerate(numerators):
                    expected = numerator * pow(1-r, -(d+1), mod) % mod
                    self.assertEqual(sum_of_exponential_times_polynomial(r, d), expected)


if __name__ == '__main__':
    unittest.main()
