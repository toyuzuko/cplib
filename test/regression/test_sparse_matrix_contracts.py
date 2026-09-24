from itertools import product
from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.matrix import SparseMatrixMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS


def matvec(a: list[list[int]], v: list[int], mod: int) -> list[int]:
    return [sum(x*y for x, y in zip(row, v)) % mod for row in a]


def polynomial_action(a: list[list[int]], coefficients: list[int], v: list[int], mod: int) -> list[int]:
    result = [0]*len(a)
    current = [x % mod for x in v]
    for c in coefficients:
        result = [(x+c*y) % mod for x, y in zip(result, current)]
        current = matvec(a, current, mod)
    return result


def minimum_polynomial(a: list[list[int]], mod: int, vector: list[int] | None = None) -> list[int]:
    n = len(a)
    vectors = [[int(i == j) for i in range(n)] for j in range(n)] if vector is None else [vector]
    powers: list[list[int]] = []
    for _ in range(n+1):
        powers.append([x % mod for v in vectors for x in v])
        vectors = [matvec(a, v, mod) for v in vectors]
    for degree in range(n+1):
        for lower in product(range(mod), repeat=degree):
            if all((powers[degree][i] + sum(c*powers[j][i] for j, c in enumerate(lower))) % mod == 0 for i in range(len(powers[0]))):
                return [*lower, 1]
    raise AssertionError('Cayley-Hamilton bound violated')


class CycleRandom:
    def __init__(self, values: list[int]) -> None:
        self.values = values
        self.index = 0

    def randrange(self, *args: int) -> int:
        result = self.values[self.index % len(self.values)]
        self.index += 1
        return result


class SparseMatrixContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod, self.prime = SparseMatrixMod._mod, SparseMatrixMod._is_prime
        self.fps_mod = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        SparseMatrixMod._mod, SparseMatrixMod._is_prime = self.mod, self.prime
        if FPS.get_mod() != self.fps_mod:
            FPS.set_mod(self.fps_mod)
        if ConvolutionMod.get_mod() != self.transform:
            ConvolutionMod.set_mod(self.transform)

    def test_minimum_polynomials_against_exhaustive_coefficients(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 5):
            SparseMatrixMod.set_mod(mod)
            for case in range(65):
                n = rng.randrange(5)
                a = [[rng.randrange(mod) for _ in range(n)] for _ in range(n)]
                v = [rng.randrange(-mod, 2*mod) for _ in range(n)]
                matrix = SparseMatrixMod(n, n, [(i, j, x) for i, row in enumerate(a) for j, x in enumerate(row)])
                expected = minimum_polynomial(a, mod)
                expected_vector = minimum_polynomial(a, mod, v)
                with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: Random(case)):
                    self.assertEqual(matrix.minimum_polynomial(max_retry=64), expected, (mod, a))
                    self.assertEqual(matrix.vector_minimum_polynomial(v, max_retry=64), expected_vector, (mod, a, v))
                    self.assertEqual(matrix.annihilating_polynomial(v, max_retry=64), list(reversed(expected_vector)))

    def test_bad_projections_are_rejected(self) -> None:
        SparseMatrixMod.set_mod(5)
        identity = SparseMatrixMod(3, 3, [(i, i, 1) for i in range(3)])
        for operation in (lambda: identity.minimum_polynomial(max_retry=0), lambda: identity.annihilating_polynomial([1, 0, 0], max_retry=0)):
            with self.assertRaises(ValueError):
                operation()
        with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: CycleRandom([0])):
            with self.assertRaises(ValueError):
                identity.minimum_polynomial()
            with self.assertRaises(ValueError):
                identity.vector_minimum_polynomial([1, 0, 0])
        matrix = SparseMatrixMod(3, 3, [(0, 0, 1), (1, 1, 2), (2, 2, 3)])
        for values in ([1, 0, 0], [1, 1, 0]):
            with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: CycleRandom(values)):
                with self.assertRaises(ValueError):
                    matrix.minimum_polynomial()
        # A proper divisor of the characteristic polynomial can be the true minimum.
        matrix = SparseMatrixMod(3, 3, [(0, 0, 1), (1, 1, 2), (2, 2, 1)])
        with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: CycleRandom([1, 1, 0])):
            self.assertEqual(matrix.minimum_polynomial(), [2, 2, 1])
        # Separate projections can reveal different factors of a vector's relation.
        matrix = SparseMatrixMod(2, 2, [(0, 0, 1), (1, 1, 2)])
        with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: CycleRandom([1, 0, 0, 1])):
            self.assertEqual(matrix.annihilating_polynomial([1, 1], max_retry=2), [1, 2, 2])

    def test_polynomial_actions_and_powers(self) -> None:
        rng = Random(1)
        for mod in (2, 3, 5):
            SparseMatrixMod.set_mod(mod)
            for _ in range(100):
                n = rng.randrange(5)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(n)] for _ in range(n)]
                v = [rng.randrange(-mod, 2*mod) for _ in range(n)]
                matrix = SparseMatrixMod(n, n, [(i, j, x) for i, row in enumerate(a) for j, x in enumerate(row)])
                relation = minimum_polynomial(a, mod, v)
                coefficients = [rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(16))]
                expected = polynomial_action(a, coefficients, v, mod)
                self.assertEqual(matrix.apply_polynomial_to_vector(coefficients, v, vector_minimum_polynomial=relation), expected)
                scaled = [x*(mod+1)+mod for x in relation] + [mod, 0]
                self.assertEqual(matrix.apply_polynomial_to_vector(coefficients, v, vector_minimum_polynomial=scaled), expected)
                exponent = rng.randrange(20)
                expected_power = [x % mod for x in v]
                for _ in range(exponent):
                    expected_power = matvec(a, expected_power, mod)
                self.assertEqual(matrix.pow_vec(exponent, v, annihilating_polynomial=list(reversed(relation))), expected_power)
        SparseMatrixMod.set_mod(5)
        matrix = SparseMatrixMod(2, 2, [(0, 0, 1), (1, 1, 2)])
        for invalid in ([], [0], [1], [1, 1], [5, 0]):
            with self.assertRaises(ValueError):
                matrix.apply_polynomial_to_vector([1, 2], [1, 1], vector_minimum_polynomial=invalid)
        for invalid in ([], [0], [1], [1, 1], [2, 4, 4]):
            with self.assertRaises(ValueError):
                matrix.pow_vec(10, [1, 1], annihilating_polynomial=invalid)
        with patch.object(matrix, 'vector_minimum_polynomial', side_effect=AssertionError('constant action needs no relation')):
            self.assertEqual(matrix.apply_polynomial_to_vector([3], [2, 4]), [1, 2])
        self.assertEqual(matrix.pow_vec(0, [6, 7], annihilating_polynomial=[]), [1, 2])

    def test_sparse_storage_sequences_and_validation(self) -> None:
        rng = Random(2)
        for mod in (2, 5, 998244353):
            SparseMatrixMod.set_mod(mod)
            for _ in range(100):
                n, m = rng.randrange(5), rng.randrange(5)
                entries = [(i, j, rng.randrange(-mod, 2*mod)) for i in range(n) for j in range(m) for _ in range(2)]
                a = [[0]*m for _ in range(n)]
                for i, j, value in entries:
                    a[i][j] = (a[i][j]+value) % mod
                matrix = SparseMatrixMod(n, m, entries)
                self.assertEqual(matrix.nnz(), sum(x != 0 for row in a for x in row))
                v = [rng.randrange(-mod, mod) for _ in range(m)]
                self.assertEqual(matrix.matvec(v), matvec(a, v, mod))
                left = [rng.randrange(-mod, mod) for _ in range(n)]
                self.assertEqual(matrix.transpose_matvec(left), [sum(a[i][j]*left[i] for i in range(n)) % mod for j in range(m)])
                if n == m:
                    scales = [rng.randrange(mod) for _ in range(n)]
                    expected = []
                    current = [x % mod for x in v]
                    for _ in range(7):
                        expected.append(sum(x*y for x, y in zip(left, current)) % mod)
                        current = [x*y % mod for x, y in zip(matvec(a, current, mod), scales)]
                    self.assertEqual(matrix.scalar_sequence(left, v, 7, scales), expected)
                    with self.assertRaises(ValueError):
                        matrix.scalar_sequence(left, v, -1)
                    with self.assertRaises(ValueError):
                        matrix.scalar_sequence(left, v, 0, scales+[1])
            empty = SparseMatrixMod(0, 0)
            self.assertEqual(empty.minimum_polynomial(max_retry=0), [1])
            self.assertEqual(empty.annihilating_polynomial([], max_retry=0), [1])
            for operation in (lambda: empty.minimum_polynomial(max_retry=-1), lambda: empty.annihilating_polynomial([], max_retry=-1), lambda: empty.determinant(max_retry=-1)):
                with self.assertRaises(ValueError):
                    operation()
            self.assertEqual(empty.scalar_sequence([], [], 3), [0, 0, 0])
            self.assertEqual(empty.scalar_sequence([], [], 0), [])


if __name__ == '__main__':
    unittest.main()
