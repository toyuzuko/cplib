from itertools import islice, product
from math import isqrt
from random import Random
import unittest

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS, coefficient_of_rational_polynomial
from cplib.mathematics.recurrence import berlekamp_massey, evaluate_linear_recurrence, enumerate_linear_recurrence, find_linear_recurrence
from cplib.mathematics.subset import (
    BitFlagSet, BitwiseAndConvolution, BitwiseOrConvolution, BitwiseXorConvolution,
    SubsetConvolution, bitmask_from_indices, bitmask_indices, enumerate_bitmasks,
    enumerate_combinations, enumerate_subsets_descending, enumerate_subsets_ascending,
    enumerate_supersets, format_bitmask,
)
from cplib.mathematics.summatory import count_primes, count_squarefrees, sum_of_primes


class SubsetContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.classes = (BitwiseAndConvolution, BitwiseOrConvolution, BitwiseXorConvolution, SubsetConvolution)
        self.moduli = [cls.get_mod() for cls in self.classes]

    def tearDown(self) -> None:
        for cls, mod in zip(self.classes, self.moduli):
            cls.set_mod(mod)

    def test_mask_enumeration(self) -> None:
        for width in range(9):
            masks = list(range(1 << width))
            self.assertEqual(list(enumerate_bitmasks(width)), masks)
            for mask in masks:
                indices = [i for i in range(width) if mask & (1 << i)]
                self.assertEqual(list(bitmask_indices(mask)), indices)
                self.assertEqual(bitmask_from_indices(indices + indices), mask)
                subsets = [x for x in masks if x & mask == x]
                self.assertEqual(list(enumerate_subsets_ascending(mask)), subsets)
                self.assertEqual(list(enumerate_subsets_descending(mask)), subsets[::-1])
                self.assertEqual(list(enumerate_supersets(mask, width)), [x for x in masks if x & mask == mask])
                self.assertEqual(format_bitmask(mask, width), ''.join(str(mask >> i & 1) for i in reversed(range(width))))
            for size in range(-1, width + 2):
                self.assertEqual(list(enumerate_combinations(width, size)), [x for x in masks if x.bit_count() == size])
        # Taking a short prefix must not materialize exponentially many masks.
        self.assertEqual(list(islice(enumerate_subsets_ascending((1 << 100) - 1), 5)), list(range(5)))
        self.assertEqual(list(islice(enumerate_supersets(1 << 100, 101), 5)), [(1 << 100) + i for i in range(5)])
        self.assertEqual(list(enumerate_subsets_descending((1 << 100) | 1)), [(1 << 100) | 1, 1 << 100, 1, 0])
        self.assertEqual(format_bitmask(-2, 4), '1110')
        for make in (lambda: bitmask_indices(-1), lambda: enumerate_subsets_descending(-1), lambda: enumerate_subsets_ascending(-1), lambda: enumerate_supersets(-1, 3), lambda: enumerate_supersets(8, 3), lambda: enumerate_supersets(0, -1), lambda: enumerate_bitmasks(-1), lambda: enumerate_combinations(-1, 0)):
            with self.assertRaises(ValueError):
                next(make())
        with self.assertRaises(ValueError):
            bitmask_from_indices([1, -1])
        with self.assertRaises(ValueError):
            format_bitmask(0, -1)

    def test_flags(self) -> None:
        rng = Random(0)
        for width in (0, 1, 10, 100):
            flags = BitFlagSet(width)
            expected: set[int] = set()
            for _ in range(300):
                mask = rng.getrandbits(width)
                selected = {i for i in range(width) if mask >> i & 1}
                operation = rng.randrange(3)
                if operation == 0:
                    flags.set_mask(mask)
                    expected |= selected
                elif operation == 1:
                    flags.clear_mask(mask)
                    expected -= selected
                else:
                    flags.flip_mask(mask)
                    expected ^= selected
                self.assertEqual(flags.val(), sum(1 << i for i in expected))
                self.assertEqual(flags.count(mask), len(expected & selected))
                self.assertEqual(flags.all(mask), selected <= expected)
                self.assertEqual(flags.any(mask), bool(selected & expected))
                self.assertEqual(flags.none(mask), not selected & expected)
                self.assertEqual(flags.complement_value(), ((1 << width) - 1) ^ flags.val())
                self.assertEqual(flags.to_binary(), format_bitmask(flags.val(), width))
                for shift in (0, 1, width, width + 1, 10**30):
                    self.assertEqual(flags.logical_left_shift_value(shift), 0 if shift >= width else flags.val() * 2**shift % (1 << width))
                    self.assertEqual(flags.logical_right_shift_value(shift), 0 if shift >= width else flags.val() // 2**shift)
            for i in range(width):
                flags.set_bit(i)
                self.assertTrue(flags.test(i))
                flags.clear_bit(i)
                self.assertFalse(flags.test(i))
                flags.flip_bit(i)
                self.assertTrue(flags.test(i))
            before = flags.val()
            for fn in (flags.test, flags.set_bit, flags.clear_bit, flags.flip_bit):
                for invalid in (-1, width):
                    with self.assertRaises(ValueError): fn(invalid)
            for fn in (flags.set_mask, flags.clear_mask, flags.flip_mask, flags.val, flags.count, flags.all, flags.any, flags.none):
                for invalid in (-1, 1 << width):
                    with self.assertRaises(ValueError): fn(invalid)
            self.assertEqual(flags.val(), before)
            for fn in (flags.logical_left_shift_value, flags.logical_right_shift_value):
                with self.assertRaises(ValueError): fn(-1)
        for width, value in ((-1, 0), (0, 1), (3, 8), (3, -1)):
            with self.assertRaises(ValueError): BitFlagSet(width, value)

    def test_transforms_and_convolutions(self) -> None:
        rng = Random(1)
        for mod in (1, 2, 4, 9, 17, 998244353):
            for cls in self.classes: cls.set_mod(mod)
            for n in range(6):
                size = 1 << n
                for _ in range(5):
                    a = [rng.randrange(-2 * mod - 10, 2 * mod + 10) for _ in range(size)]
                    b = [rng.randrange(-2 * mod - 10, 2 * mod + 10) for _ in range(size)]
                    original = a[:], b[:]
                    results = [[0] * size for _ in self.classes]
                    for i, j in product(range(size), repeat=2):
                        results[0][i & j] += a[i] * b[j]
                        results[1][i | j] += a[i] * b[j]
                        results[2][i ^ j] += a[i] * b[j]
                        if i & j == 0: results[3][i | j] += a[i] * b[j]
                    for cls, expected in zip(self.classes, results):
                        if cls is BitwiseXorConvolution and n and mod % 2 == 0:
                            with self.assertRaises(ValueError): cls.convolution(n, a, b)
                        else:
                            self.assertEqual(cls.convolution(n, a, b), [x % mod for x in expected])
                    for cls, supersets in ((BitwiseAndConvolution, True), (BitwiseOrConvolution, False)):
                        zeta = [sum(a[j] for j in range(size) if (i & j == i if supersets else i & j == j)) % mod for i in range(size)]
                        mobius = [sum(a[j] * (-1)**abs(i.bit_count() - j.bit_count()) for j in range(size) if (i & j == i if supersets else i & j == j)) % mod for i in range(size)]
                        self.assertEqual(cls.zeta(n, a), zeta)
                        self.assertEqual(cls.mobius(n, a), mobius)
                        self.assertEqual(cls.mobius(n, cls.zeta(n, a)), [x % mod for x in a])
                    hadamard = [sum(a[j] * (-1)**((i & j).bit_count()) for j in range(size)) % mod for i in range(size)]
                    self.assertEqual(BitwiseXorConvolution.hadamard(n, a), hadamard)
                    self.assertEqual((a, b), original)
        for cls in self.classes:
            before = cls.get_mod()
            for mod in (0, -1):
                with self.assertRaises(ValueError): cls.set_mod(mod)
                self.assertEqual(cls.get_mod(), before)
            for n, a, b in ((-1, [], []), (0, [], [1]), (1, [1, 2], [1]), (2, [1, 2, 3], [1, 2, 3, 4])):
                with self.assertRaises(ValueError): cls.convolution(n, a, b)
        for fn in (BitwiseAndConvolution.zeta, BitwiseAndConvolution.mobius, BitwiseOrConvolution.zeta, BitwiseOrConvolution.mobius, BitwiseXorConvolution.hadamard):
            for n, arr in ((-1, []), (0, []), (1, [1]), (2, [1, 2, 3])):
                with self.assertRaises(ValueError): fn(n, arr)


class RecurrenceContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        if FPS.get_mod() != self.mod: FPS.set_mod(self.mod)
        if ConvolutionMod.get_mod() != self.transform: ConvolutionMod.set_mod(self.transform)

    def test_recurrence_against_iteration(self) -> None:
        rng = Random(2)
        for mod in (257, 998244353):
            FPS.set_mod(mod)
            for _ in range(500):
                n = rng.randrange(13)
                coef = [rng.randrange(-mod, mod) for _ in range(n)]
                init = [rng.randrange(-mod, mod) for _ in range(n)]
                k, m = rng.randrange(100), rng.randrange(25)
                seq = [x % mod for x in init]
                for i in range(n, max(n, k + m + 1)):
                    seq.append(sum(coef[j] * seq[i - j - 1] for j in range(n)) % mod)
                self.assertEqual(evaluate_linear_recurrence(coef, init, k), seq[k])
                self.assertEqual(enumerate_linear_recurrence(coef, init, k, m), seq[k:k + m])
            k = 10**30
            self.assertEqual(evaluate_linear_recurrence([3], [2], k), 2 * pow(3, k, mod) % mod)
            self.assertEqual(enumerate_linear_recurrence([3], [2], k, 20), [2 * pow(3, k + i, mod) % mod for i in range(20)])
            for coef in ([0, 0, 0], [2, 0, 0], [0, 2, 0]):
                seq = [3, 4, 5]
                for i in range(3, 30):
                    seq.append(sum(coef[j] * seq[i-j-1] for j in range(3)) % mod)
                for start in range(10):
                    self.assertEqual(evaluate_linear_recurrence(coef, [3, 4, 5], start), seq[start])
                    self.assertEqual(enumerate_linear_recurrence(coef, [3, 4, 5], start, 10), seq[start:start+10])
        for coef, init, k in (([], [1], 0), ([1], [], 0), ([1], [1], -1)):
            with self.assertRaises(ValueError): evaluate_linear_recurrence(coef, init, k)
            with self.assertRaises(ValueError): enumerate_linear_recurrence(coef, init, k, 0)
        with self.assertRaises(ValueError): enumerate_linear_recurrence([1], [1], 0, -1)

    def test_rational_coefficients(self) -> None:
        rng = Random(3)
        for mod in (257, 998244353):
            FPS.set_mod(mod)
            for _ in range(300):
                numer = [rng.randrange(-mod, mod) for _ in range(rng.randrange(15))]
                denom = [rng.randrange(1, mod)] + [rng.randrange(-mod, mod) for _ in range(rng.randrange(10))]
                inverse = pow(denom[0], -1, mod)
                seq: list[int] = []
                for i in range(51):
                    seq.append(((numer[i] if i < len(numer) else 0) - sum(denom[j] * seq[i - j] for j in range(1, min(len(denom), i + 1)))) * inverse % mod)
                for k in (0, 1, 2, 15, 50):
                    self.assertEqual(coefficient_of_rational_polynomial(FPS(numer), FPS(denom), k), seq[k])
            self.assertEqual(coefficient_of_rational_polynomial(FPS([1]), FPS([2, -2]), 10**30), pow(2, -1, mod))
            for denom in ([], [0], [mod], [0, 1]):
                with self.assertRaises(ValueError): coefficient_of_rational_polynomial(FPS([1]), FPS(denom), 0)
            with self.assertRaises(ValueError): coefficient_of_rational_polynomial(FPS([1]), FPS([1, -1]), -1)

    def test_berlekamp_massey_minimality(self) -> None:
        rng = Random(4)
        for mod in (2, 3, 17, 998244353):
            FPS.set_mod(mod)
            for _ in range(200):
                n = rng.randrange(1, 12)
                coef = [rng.randrange(mod) for _ in range(n)]
                seq = [rng.randrange(mod) for _ in range(n)]
                for i in range(n, 4 * n): seq.append(sum(coef[j] * seq[i-j-1] for j in range(n)) % mod)
                found = find_linear_recurrence(seq[:2*n])
                self.assertLessEqual(len(found), n)
                for i in range(len(found), len(seq)):
                    self.assertEqual(seq[i], sum(found[j] * seq[i-j-1] for j in range(len(found))) % mod)
                signed = berlekamp_massey([x - mod for x in seq[:2*n]])
                self.assertEqual(signed, [1] + [-x % mod for x in found])
            self.assertEqual(berlekamp_massey([]), [1])
            self.assertEqual(find_linear_recurrence([0] * 10), [])
        FPS.set_mod(2)
        for length in range(7):
            for seq_tuple in product(range(2), repeat=length):
                seq = list(seq_tuple)
                found = find_linear_recurrence(seq)
                for degree in range(len(found)):
                    self.assertFalse(any(all(seq[i] == sum(c[j] * seq[i-j-1] for j in range(degree)) % 2 for i in range(degree, length)) for c in product(range(2), repeat=degree)))


class SummatoryContractsTest(unittest.TestCase):
    def test_prime_prefixes(self) -> None:
        limit = 200000
        prime = [True] * (limit + 1)
        prime[0] = prime[1] = False
        for p in range(2, isqrt(limit) + 1):
            if prime[p]:
                for i in range(p*p, limit + 1, p): prime[i] = False
        count, total = [0], [0]
        for i in range(1, limit + 1):
            count.append(count[-1] + prime[i])
            total.append(total[-1] + i * prime[i])
        rng = Random(5)
        for n in list(range(1000)) + [rng.randrange(limit + 1) for _ in range(200)] + [limit]:
            self.assertEqual(count_primes(n), count[n])
            self.assertEqual(sum_of_primes(n), total[n])
        for n in (-10, -1, 0):
            self.assertEqual(count_primes(n), 0)
            self.assertEqual(sum_of_primes(n), 0)

    def test_squarefree_prefixes(self) -> None:
        limit = 100000
        mu = [1] * (limit + 1)
        prime = [True] * (limit + 1)
        for p in range(2, limit + 1):
            if prime[p]:
                for i in range(p, limit + 1, p):
                    if i > p: prime[i] = False
                    mu[i] *= -1
                for i in range(p*p, limit + 1, p*p): mu[i] = 0
        squarefree = [True] * (limit + 1)
        for i in range(2, isqrt(limit) + 1):
            for j in range(i*i, limit + 1, i*i): squarefree[j] = False
        count = 0
        for n in range(1, 3000):
            count += squarefree[n]
            self.assertEqual(count_squarefrees(n), count)
        rng = Random(6)
        cases = [rng.randrange(1, limit**2) for _ in range(100)]
        cases += [k**5 + delta for k in range(2, 40) for delta in (-1, 0, 1)]
        for n in cases:
            self.assertEqual(count_squarefrees(n), sum(mu[i] * (n // (i*i)) for i in range(1, isqrt(n) + 1)), n)
        for n in (-10, -1, 0): self.assertEqual(count_squarefrees(n), 0)


if __name__ == '__main__':
    unittest.main()
