from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS


def multiply(a: list[int], b: list[int], n: int, mod: int) -> list[int]:
    result = [0] * n
    for i, x in enumerate(a[:n]):
        for j, y in enumerate(b[:n-i]):
            result[i+j] = (result[i+j] + x*y) % mod
    return result


def compose(a: list[int], b: list[int], n: int, mod: int) -> list[int]:
    result = [0] * n
    power = [1] + [0] * (n-1) if n else []
    for coefficient in a:
        result = [(x + coefficient*y) % mod for x, y in zip(result, power)]
        power = multiply(power, b, n, mod)
    return result


def inverse(a: list[int], mod: int) -> list[int]:
    result = [0] * len(a)
    result[1] = pow(a[1], -1, mod)
    for degree in range(2, len(a)):
        coefficient = compose(a[:degree+1], result[:degree+1], degree+1, mod)[degree]
        result[degree] = -coefficient * result[1] % mod
    return result


class PolynomialCompositionContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()
        self.threshold = FPS._sparse_threshold

    def tearDown(self) -> None:
        if FPS.get_mod() != self.mod:
            FPS.set_mod(self.mod)
        if ConvolutionMod.get_mod() != self.transform:
            ConvolutionMod.set_mod(self.transform)
        FPS.set_sparse_threshold(self.threshold)

    def test_composition_against_powers(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 5, 17, 97, 257, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    a = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(19))]
                    b = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(19))]
                    n = max(len(a), len(b))
                    f, g = FPS(a), FPS(b)
                    self.assertEqual(f.compose(g).coef, compose(a, b, n, mod), (mod, a, b))
                    self.assertEqual((f.coef, g.coef), (a, b))
            for a, b in (([], []), ([mod], []), ([1], []), ([], [1, 2]), ([mod, 2*mod], [1, 2, 3])):
                self.assertEqual(FPS(a).compose(FPS(b)).coef, compose(a, b, max(len(a), len(b)), mod))

    def test_inverse_against_coefficient_solving(self) -> None:
        rng = Random(1)
        for mod in (2, 3, 5, 17, 97, 257, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(45):
                    n = rng.randrange(2, 20)
                    a = [mod*rng.randrange(-2, 3), rng.randrange(1, mod)]
                    a += [rng.randrange(-mod, 2*mod) for _ in range(n-2)]
                    f = FPS(a)
                    actual = f.compositional_inverse().coef
                    expected = inverse(a, mod)
                    self.assertEqual(actual, expected, (mod, a))
                    identity = [0, 1] + [0] * (n-2)
                    self.assertEqual(compose(a, actual, n, mod), identity)
                    self.assertEqual(compose(actual, a, n, mod), identity)
                    self.assertEqual(f.coef, a)
            self.assertEqual(FPS([]).compositional_inverse().coef, [])
            for a in ([0], [mod], [1, 1], [mod, mod], [0, 0, 1]):
                with self.assertRaises(ValueError):
                    FPS(a).compositional_inverse()

    def test_transform_capacity_boundaries(self) -> None:
        rng = Random(2)
        FPS.set_sparse_threshold(None)
        # Sizes on either side of the flattened 2D / middle-product capacity.
        for mod in (17, 97, 257):
            FPS.set_mod(mod)
            for n in range(2, 38):
                a = [rng.randrange(mod) for _ in range(n)]
                b = [rng.randrange(mod) for _ in range(n)]
                self.assertEqual(FPS(a).compose(FPS(b)).coef, compose(a, b, n, mod))
                a[0], a[1] = 0, 1
                result = FPS(a).compositional_inverse().coef
                self.assertEqual(compose(a, result, n, mod), [0, 1] + [0] * (n-2))

    def test_default_fast_path_and_modulus_switch(self) -> None:
        FPS.set_mod(998244353)
        FPS.set_sparse_threshold(None)
        a = [0, 2, 3, 4, 5, 6, 7, 8]
        b = [7, 6, 5, 4, 3, 2, 1, 0]
        expected_composition = compose(a, b, len(a), FPS.get_mod())
        expected_inverse = inverse(a, FPS.get_mod())
        with patch.object(FPS, '_compose_impl', wraps=FPS._compose_impl) as fast:
            with patch.object(ConvolutionMod, 'set_mod', side_effect=AssertionError('unnecessary modulus reset')):
                self.assertEqual(FPS(a).compose(FPS(b)).coef, expected_composition)
            self.assertEqual(fast.call_count, 1)
        with patch.object(FPS, '_compositional_inverse_impl', wraps=FPS._compositional_inverse_impl) as fast:
            self.assertEqual(FPS(a).compositional_inverse().coef, expected_inverse)
            self.assertEqual(fast.call_count, 1)
        ConvolutionMod.set_mod(17)
        self.assertEqual(FPS(a).compose(FPS(b)).coef, expected_composition)
        ConvolutionMod.set_mod(17)
        self.assertEqual(FPS(a).compositional_inverse().coef, expected_inverse)


if __name__ == '__main__':
    unittest.main()
