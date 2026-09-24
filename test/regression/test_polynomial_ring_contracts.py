from random import Random
import unittest

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS, polynomial_product


def trim(a: list[int], mod: int) -> list[int]:
    result = [x % mod for x in a]
    while result and result[-1] == 0:
        result.pop()
    return result


def multiply(a: list[int], b: list[int], mod: int) -> list[int]:
    result = [0] * (len(a)+len(b)-1) if a and b else []
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] = (result[i+j] + x*y) % mod
    return result


def add(a: list[int], b: list[int], mod: int) -> list[int]:
    result = [0] * max(len(a), len(b))
    for i, x in enumerate(a):
        result[i] += x
    for i, x in enumerate(b):
        result[i] += x
    return trim(result, mod)


def remainder(a: list[int], b: list[int], mod: int) -> list[int]:
    result, divisor = trim(a, mod), trim(b, mod)
    if not divisor:
        raise ZeroDivisionError
    inv = pow(divisor[-1], -1, mod)
    while len(result) >= len(divisor):
        shift = len(result)-len(divisor)
        coefficient = result[-1]*inv % mod
        for i, x in enumerate(divisor):
            result[shift+i] = (result[shift+i] - coefficient*x) % mod
        result = trim(result, mod)
    return result


def gcd(a: list[int], b: list[int], mod: int) -> list[int]:
    a, b = trim(a, mod), trim(b, mod)
    while b:
        a, b = b, remainder(a, b, mod)
    if not a:
        return []
    inverse = pow(a[-1], -1, mod)
    return [x*inverse % mod for x in a]


class PolynomialRingContractsTest(unittest.TestCase):
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

    def test_gcd_and_bezout_matrix(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 17, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    a = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(20))]
                    b = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(20))]
                    if rng.randrange(3) == 0:
                        b += [mod, 0, -mod]
                    f, g = FPS(a), FPS(b)
                    expected = gcd(a, b, mod)
                    self.assertEqual(f.gcd(g).coef, expected)
                    common, matrix = FPS.gcd_transform(f, g)
                    self.assertEqual(common.coef, trim(common.coef, mod))
                    self.assertEqual(gcd(common.coef, [], mod), expected)
                    aa, bb, cc, dd = [x.coef for x in matrix]
                    self.assertEqual(add(multiply(aa, a, mod), multiply(bb, b, mod), mod), common.coef)
                    self.assertEqual(add(multiply(cc, a, mod), multiply(dd, b, mod), mod), [])
                    determinant = add(multiply(aa, dd, mod), [-x for x in multiply(bb, cc, mod)], mod)
                    self.assertIn(determinant, ([1], [mod-1]))
                    self.assertEqual((f.coef, g.coef), (a, b))
            self.assertEqual(FPS.gcd_transform(FPS([mod+2]), FPS([]))[0].coef, [2 % mod] if mod != 2 else [])

    def test_large_constructed_common_factor(self) -> None:
        rng = Random(1)
        for mod in (2, 17, 998244353):
            FPS.set_mod(mod)
            FPS.set_sparse_threshold(None)
            for _ in range(8):
                common = [rng.randrange(mod) for _ in range(35)] + [1]
                a = multiply(common, [rng.randrange(mod) for _ in range(65)] + [1], mod)
                b = multiply(common, [rng.randrange(mod) for _ in range(57)] + [1], mod)
                self.assertEqual(FPS(a).gcd(FPS(b)).coef, gcd(a, b, mod))

    def test_modular_power(self) -> None:
        rng = Random(2)
        for mod in (2, 3, 17, 998244353):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    a = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(15))]
                    divisor = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(1, 10))]
                    if not trim(divisor, mod):
                        divisor[0] = 1
                    divisor += [mod, 0]
                    exponent = rng.randrange(13)
                    expected = remainder([1], divisor, mod)
                    for _ in range(exponent):
                        expected = remainder(multiply(expected, a, mod), divisor, mod)
                    f, g = FPS(a), FPS(divisor)
                    self.assertEqual(f.pow_mod(exponent, g).coef, expected, (mod, a, divisor, exponent))
                    self.assertEqual((f.coef, g.coef), (a, divisor))
            for zero in ([], [0], [mod, -mod]):
                with self.assertRaises(ZeroDivisionError):
                    FPS([1]).pow_mod(0, FPS(zero))
            with self.assertRaises(ValueError):
                FPS([1]).pow_mod(-1, FPS([1, 1]))
            exponent = 10**100
            self.assertEqual(FPS([3, 2, 1]).pow_mod(exponent, FPS([-5, 1])).coef, trim([pow(38, exponent, mod)], mod))

    def test_modular_inverse(self) -> None:
        rng = Random(3)
        for mod in (2, 3, 17, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    a = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(16))]
                    divisor = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(1, 12))]
                    if not trim(divisor, mod):
                        divisor[0] = 1
                    divisor += [mod, 0]
                    f, g = FPS(a), FPS(divisor)
                    actual = f.inv_mod_poly(g)
                    if gcd(a, divisor, mod) == [1]:
                        self.assertIsNotNone(actual)
                        assert actual is not None
                        self.assertEqual(actual.coef, trim(actual.coef, mod))
                        self.assertLess(len(actual), len(trim(divisor, mod)))
                        self.assertEqual(remainder(multiply(a, actual.coef, mod), divisor, mod), remainder([1], divisor, mod))
                    else:
                        self.assertIsNone(actual)
                    self.assertEqual((f.coef, g.coef), (a, divisor))
            for zero in ([], [0], [mod, 0]):
                with self.assertRaises(ZeroDivisionError):
                    FPS([1]).inv_mod_poly(FPS(zero))

    def test_product(self) -> None:
        rng = Random(4)
        for mod in (2, 3, 17, 998244353, 1000000007):
            FPS.set_mod(mod)
            for threshold in (None, 100):
                FPS.set_sparse_threshold(threshold)
                for _ in range(100):
                    raw = [[rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(1, 8))] for _ in range(rng.randrange(13))]
                    if raw and rng.randrange(4) == 0:
                        raw[rng.randrange(len(raw))] = []
                    expected = [1]
                    for factor in raw:
                        expected = multiply(expected, factor, mod)
                    originals = [FPS(a) for a in raw]
                    workspace = originals[:]
                    result = polynomial_product(workspace)
                    self.assertEqual(result.coef, expected, (mod, raw))
                    self.assertEqual([f.coef for f in originals], raw)
                    self.assertTrue(all(result is not f for f in originals))
                    self.assertLessEqual(sum(len(f) for f in workspace), sum(map(len, raw)))
            shared = FPS([1, 2])
            self.assertEqual(polynomial_product([shared]*8).coef, polynomial_product([FPS([1, 2]) for _ in range(8)]).coef)
            self.assertEqual(shared.coef, [1, 2])


if __name__ == '__main__':
    unittest.main()
