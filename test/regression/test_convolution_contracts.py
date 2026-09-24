from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import BinaryField64, Convolution64bit, ConvolutionBinaryField64, ConvolutionMod
from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS, polynomial_shift_sampling, sum_of_exponential_times_polynomial
from cplib.mathematics.recurrence import evaluate_linear_recurrence, enumerate_linear_recurrence


def multiply(a: list[int], b: list[int], mod: int) -> list[int]:
    if not a or not b:
        return []
    result = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] = (result[i + j] + x * y) % mod
    return result


def binary_multiply(a: int, b: int) -> int:
    mask = (1 << 64) - 1
    a &= mask
    b &= mask
    result = 0
    for _ in range(64):
        if b & 1:
            result ^= a
        b >>= 1
        a = ((a << 1) ^ (0b11011 if a >> 63 else 0)) & mask
    return result


class ConvolutionContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fps_mod = FPS.get_mod()
        self.mod = ConvolutionMod.get_mod()
        self.threshold = FPS._sparse_threshold

    def tearDown(self) -> None:
        if FPS.get_mod() != self.fps_mod:
            FPS.set_mod(self.fps_mod)
        if ConvolutionMod.get_mod() != self.mod:
            ConvolutionMod.set_mod(self.mod)
        FPS.set_sparse_threshold(self.threshold)

    def test_ntt_against_dft(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 17, 97, 257, 998244353, 77309411329):
            ConvolutionMod.set_mod(mod)
            capacity = (mod - 1) & -(mod - 1)
            for length in (1, 2, 4, 8, 16, 32):
                if length > capacity:
                    continue
                values = [rng.randrange(-2 * mod, 2 * mod) for _ in range(length)]
                transformed = values[:]
                self.assertIsNone(ConvolutionMod.butterfly(transformed))
                root = pow(PrimeFactor.primitive_root(mod), (mod - 1) // length, mod)
                dft = [sum(x * pow(root, i*j, mod) for i, x in enumerate(values)) % mod for j in range(length)]
                bits = length.bit_length() - 1
                expected = [dft[int(f'{i:0{bits}b}'[::-1], 2)] for i in range(length)]
                self.assertEqual(transformed, expected, (mod, length))
                ConvolutionMod.butterfly_inv(transformed)
                self.assertEqual(transformed, [x * length % mod for x in values])
            for fn in (ConvolutionMod.butterfly, ConvolutionMod.butterfly_inv):
                empty: list[int] = []
                self.assertIsNone(fn(empty))
                self.assertEqual(empty, [])
                for length in (3, 5, 6):
                    arr = list(range(length))
                    with self.assertRaises(ValueError): fn(arr)
                    self.assertEqual(arr, list(range(length)))
                if capacity < 100:
                    arr = [1] * (2 * capacity)
                    with self.assertRaises(ValueError): fn(arr)
                    self.assertEqual(arr, [1] * (2 * capacity))
        self.assertEqual(ConvolutionMod._rank2, 33)

    def test_convolution_against_product(self) -> None:
        rng = Random(1)
        for mod in (2, 3, 17, 97, 257, 998244353, 77309411329):
            ConvolutionMod.set_mod(mod)
            capacity = (mod - 1) & -(mod - 1)
            for _ in range(100):
                n = rng.randrange(min(35, capacity) + 1)
                m = rng.randrange(min(35, capacity) + 1)
                a = [rng.randrange(-mod, 2 * mod) for _ in range(n)]
                b = [rng.randrange(-mod, 2 * mod) for _ in range(m)]
                original = a[:], b[:]
                if n and m and n + m - 1 > capacity:
                    with self.assertRaises(ValueError): ConvolutionMod.convolution(a, b)
                else:
                    self.assertEqual(ConvolutionMod.convolution(a, b), multiply(a, b, mod))
                if 2 * n - 1 > capacity:
                    with self.assertRaises(ValueError): ConvolutionMod.autoconvolution(a)
                else:
                    self.assertEqual(ConvolutionMod.autoconvolution(a), multiply(a, a, mod))
                self.assertEqual((a, b), original)
            self.assertEqual(ConvolutionMod.convolution([], [1] * 100), [])
            self.assertEqual(ConvolutionMod.convolution([1] * 100, []), [])

    def test_modulus_changes_are_atomic_and_reused(self) -> None:
        FPS.set_mod(17)
        for mod in (-5, 0, 1, 4, 9, 15, 21):
            for setter in (ConvolutionMod.set_mod, FPS.set_mod):
                with self.assertRaises(ValueError): setter(mod)
                self.assertEqual(ConvolutionMod.get_mod(), 17)
                self.assertEqual(FPS.get_mod(), 17)
                self.assertEqual(ConvolutionMod.convolution([1, 2], [3, 4]), [3, 10, 8])
        with patch.object(PrimeFactor, 'primitive_root', side_effect=AssertionError('unnecessary reinitialization')):
            ConvolutionMod.set_mod(17)
            FPS.set_mod(17)
            self.assertEqual((FPS([1, 2]) * FPS([3, 4])).coef, [3, 10, 8])
        with patch.object(ConvolutionMod, 'set_mod', side_effect=AssertionError('unnecessary setter')):
            self.assertEqual((FPS([1, 2]) * FPS([3, 4])).coef, [3, 10, 8])
            self.assertEqual((~FPS([1, -1, 0, 0])).coef, [1, 1, 1, 1])

    def test_fps_transforms_restore_their_modulus(self) -> None:
        FPS.set_mod(998244353)
        FPS.set_sparse_threshold(None)
        ConvolutionMod.set_mod(17)
        self.assertEqual((FPS([16, 1]) * FPS([2, 1])).coef, [32, 18, 1])
        ConvolutionMod.set_mod(17)
        self.assertEqual((~FPS([1, -2, 0, 0, 0, 0])).coef, [1, 2, 4, 8, 16, 32])
        ConvolutionMod.set_mod(17)
        self.assertEqual(evaluate_linear_recurrence([2], [16], 2), 64)
        ConvolutionMod.set_mod(17)
        self.assertEqual(enumerate_linear_recurrence([2], [16], 2, 5), [64, 128, 256, 512, 1024])
        ConvolutionMod.set_mod(17)
        self.assertEqual(polynomial_shift_sampling(3, 5, [0, 1, 4], 3), [9, 16, 25, 36, 49])
        for threshold in (None, 100):
            FPS.set_sparse_threshold(threshold)
            ConvolutionMod.set_mod(17)
            # Compose (1+2x+3x^2) with (2+x+x^2), truncated modulo x^3.
            self.assertEqual(FPS([1, 2, 3]).compose(FPS([2, 1, 1])).coef, [17, 14, 17])
            ConvolutionMod.set_mod(17)
            self.assertEqual(FPS([0, 1, -1, 0, 0, 0]).compositional_inverse().coef, [0, 1, 1, 2, 5, 14])
            for a, b in (([], [1, 2, 3]), ([1, 2, 3], []), ([], [])):
                self.assertEqual((FPS(a) * FPS(b)).coef, [])

    def test_uint64_convolution(self) -> None:
        rng = Random(2)
        cases = [([-1], [1]), ([1 << 200], [1]), ([], [-1]), ([1], []), ([-1, 2], [1, -3])]
        for _ in range(100):
            cases.append(([rng.randrange(-(1 << 200), 1 << 200) for _ in range(rng.randrange(20))], [rng.randrange(-(1 << 200), 1 << 200) for _ in range(rng.randrange(20))]))
        for a, b in cases:
            original = a[:], b[:]
            self.assertEqual(Convolution64bit.convolution(a, b), multiply(a, b, 1 << 64))
            self.assertEqual(Convolution64bit.autoconvolution(a), multiply(a, a, 1 << 64))
            self.assertEqual((a, b), original)

    def test_inverse_cache_after_modulus_changes(self) -> None:
        for mod in (998244353, 17, 97, 17, 998244353):
            FPS.set_mod(mod)
            for d in range(7):
                for r in (-1, 0, 1, 2, 5):
                    for n in (0, 1, 2, 10, 20, 100):
                        expected = sum(pow(r, i, mod) * pow(i, d, mod) for i in range(n)) % mod
                        self.assertEqual(sum_of_exponential_times_polynomial(r, d, n), expected, (mod, r, d, n))
            for r in (0, 2, 3):
                inverse = pow(1 - r, -1, mod)
                expected = [inverse, r * inverse**2 % mod, r * (1 + r) * inverse**3 % mod]
                for d in range(3):
                    self.assertEqual(sum_of_exponential_times_polynomial(r, d), expected[d])

    def test_binary_field(self) -> None:
        rng = Random(3)
        for _ in range(150):
            a, b = (rng.randrange(-(1 << 100), 1 << 100) for _ in range(2))
            self.assertEqual(BinaryField64.multiply(a, b), binary_multiply(a, b))
            self.assertEqual(BinaryField64.add(a, b), (a ^ b) & ((1 << 64) - 1))
            n = rng.randrange(16)
            expected = 1
            for _ in range(n): expected = binary_multiply(expected, a)
            self.assertEqual(BinaryField64.pow(a, n), expected)
            self.assertEqual(binary_multiply(a, BinaryField64.inv(a)), 1)
        for a in (0, 1 << 64, -(1 << 64)):
            with self.assertRaises(ZeroDivisionError): BinaryField64.inv(a)
        with self.assertRaises(ValueError): BinaryField64.pow(2, -1)
        self.assertEqual(BinaryField64.pow(0, 0), 1)

    def test_binary_field_convolution(self) -> None:
        rng = Random(4)
        for n, m in ((0, 3), (3, 0), (1, 1), (10, 7), (140, 140), (141, 143), (280, 75), (81, 249)):
            a = [rng.randrange(-(1 << 70), 1 << 70) for _ in range(n)]
            b = [rng.randrange(-(1 << 70), 1 << 70) for _ in range(m)]
            original = a[:], b[:]
            expected = [0] * (n + m - 1) if n and m else []
            for i, x in enumerate(a):
                for j, y in enumerate(b): expected[i+j] ^= binary_multiply(x, y)
            self.assertEqual(ConvolutionBinaryField64.convolution(a, b), expected, (n, m))
            square = [0] * (2 * n - 1) if n else []
            for i, x in enumerate(a): square[2*i] = binary_multiply(x, x)
            self.assertEqual(ConvolutionBinaryField64.autoconvolution(a), square)
            self.assertEqual((a, b), original)
        with patch.object(ConvolutionBinaryField64, '_pow3', (1, 3, 9)):
            with self.assertRaises(ValueError): ConvolutionBinaryField64.convolution([1] * 150, [2] * 150)
        with patch.object(ConvolutionBinaryField64, '_convolve_aux', side_effect=AssertionError('unnecessary transform for equal operands')):
            a = [rng.getrandbits(64) for _ in range(150)]
            square = [0] * (2 * len(a) - 1)
            for i, x in enumerate(a): square[2*i] = binary_multiply(x, x)
            self.assertEqual(ConvolutionBinaryField64.convolution(a, a), square)
            self.assertEqual(ConvolutionBinaryField64.convolution(a, a[:]), square)
        # Cross a second recursive transform level with an independent sparse product.
        a, b = [0] * 900, [0] * 950
        for i in rng.sample(range(len(a)), 15): a[i] = rng.getrandbits(64)
        for j in rng.sample(range(len(b)), 15): b[j] = rng.getrandbits(64)
        expected = [0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    if y: expected[i+j] ^= binary_multiply(x, y)
        self.assertEqual(ConvolutionBinaryField64.convolution(a, b), expected)


if __name__ == '__main__':
    unittest.main()
