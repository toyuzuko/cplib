from itertools import permutations, product
from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.matrix import MatrixMod, LinearAlgebraFp, SparseMatrixMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS


def determinant(a: list[list[int]], mod: int) -> int:
    n = len(a)
    result = 0
    for order in permutations(range(n)):
        term = 1
        for i, j in enumerate(order):
            term *= a[i][j]
        inversions = sum(order[i] > order[j] for i in range(n) for j in range(i+1, n))
        result += -term if inversions & 1 else term
    return result % mod


def multiply(a: list[list[int]], b: list[list[int]], columns: int, mod: int) -> list[list[int]]:
    return [[sum(a[i][k]*b[k][j] for k in range(len(b))) % mod for j in range(columns)] for i in range(len(a))]


def pfaffian(a: list[list[int]], mod: int) -> int:
    if not a:
        return 1
    result = 0
    for partner in range(1, len(a)):
        remaining = [i for i in range(1, len(a)) if i != partner]
        minor = [[a[i][j] for j in remaining] for i in remaining]
        result += (-1 if partner % 2 == 0 else 1)*a[0][partner]*pfaffian(minor, mod)
    return result % mod


class MatrixBasicContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = [(cls, cls._mod, cls._is_prime) for cls in (MatrixMod, LinearAlgebraFp, SparseMatrixMod)]
        self.fp_owned = '_mod' in LinearAlgebraFp.__dict__
        self.prime_owned = '_is_prime' in LinearAlgebraFp.__dict__
        self.fps_mod = FPS.get_mod()
        self.transform_mod = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        for cls, mod, prime in self.settings:
            cls._mod, cls._is_prime = mod, prime
        if not self.fp_owned:
            del LinearAlgebraFp._mod
        if not self.prime_owned:
            del LinearAlgebraFp._is_prime
        if FPS.get_mod() != self.fps_mod:
            FPS.set_mod(self.fps_mod)
        if ConvolutionMod.get_mod() != self.transform_mod:
            ConvolutionMod.set_mod(self.transform_mod)

    def test_dimensions_copy_and_modulus(self) -> None:
        for cls in (MatrixMod, LinearAlgebraFp, SparseMatrixMod):
            for n, m in ((-1, 0), (0, -1), (-2, -3)):
                with self.assertRaises(ValueError):
                    cls(n, m)
        for cls in (MatrixMod, LinearAlgebraFp):
            cls.set_mod(7)
            for mod in (0, -1):
                with self.assertRaises(ValueError):
                    cls.set_mod(mod)
                self.assertEqual((cls._mod, cls._is_prime), (7, True))
            for data in ([[1]], [[1, 2], [3]]):
                with self.assertRaises(ValueError):
                    cls(2, 2, data)
            raw = [[-1, 14], [9, 2]]
            a = cls(2, 2, raw)
            b = +a
            self.assertIs(type(b), cls)
            self.assertEqual(b._matrix, raw)
            b[0, 0] = 123
            self.assertEqual(a[0, 0], -1)
            self.assertEqual(raw[0][0], -1)
            for operation in (lambda: a+cls(2, 1), lambda: a-cls(1, 2), lambda: a*cls(1, 2), lambda: a**-1, lambda: cls(2, 1)**0):
                with self.assertRaises(ValueError):
                    operation()
        MatrixMod.set_mod(1)
        self.assertFalse(MatrixMod._is_prime)
        self.assertEqual(MatrixMod.identity(2)._matrix, [[0, 0], [0, 0]])
        self.assertEqual(MatrixMod(0, 0).determinant(), 0)
        MatrixMod.set_mod((1 << 61)-1)
        self.assertTrue(MatrixMod._is_prime)
        MatrixMod.set_mod(((1 << 61)-1)*3)
        self.assertFalse(MatrixMod._is_prime)

    def test_dense_arithmetic_and_determinant(self) -> None:
        rng = Random(0)
        for mod in (1, 2, 3, 4, 6, 17, 998244353):
            MatrixMod.set_mod(mod)
            for _ in range(100):
                n, m, k = (rng.randrange(5) for _ in range(3))
                a = [[rng.randrange(-2*mod, 2*mod) for _ in range(m)] for _ in range(n)]
                b = [[rng.randrange(-2*mod, 2*mod) for _ in range(k)] for _ in range(m)]
                c = [[rng.randrange(-2*mod, 2*mod) for _ in range(m)] for _ in range(n)]
                f, g, h = MatrixMod(n, m, a), MatrixMod(m, k, b), MatrixMod(n, m, c)
                self.assertEqual((f*g)._matrix, multiply(a, b, k, mod))
                self.assertEqual((f+h)._matrix, [[(a[i][j]+c[i][j]) % mod for j in range(m)] for i in range(n)])
                self.assertEqual((f-h)._matrix, [[(a[i][j]-c[i][j]) % mod for j in range(m)] for i in range(n)])
                self.assertEqual(f.transpose()._matrix, [[a[i][j] for i in range(n)] for j in range(m)])
                self.assertEqual(f.times(-3)._matrix, [[-3*x % mod for x in row] for row in a])
                vector = [rng.randrange(-mod, mod) for _ in range(m)]
                self.assertEqual(f.matvec(vector), [sum(x*y for x, y in zip(row, vector)) % mod for row in a])
                square = [[rng.randrange(-2*mod, 2*mod) for _ in range(n)] for _ in range(n)]
                matrix = MatrixMod(n, n, square)
                self.assertEqual(matrix.determinant(), determinant(square, mod))
                expected = [[int(i == j) % mod for j in range(n)] for i in range(n)]
                exponent = rng.randrange(7)
                for _ in range(exponent):
                    expected = multiply(expected, square, n, mod)
                self.assertEqual((matrix**exponent)._matrix, expected)
                self.assertEqual(matrix._matrix, square)
            with self.assertRaises(ValueError):
                MatrixMod(1, 2).determinant()

    def test_rank_and_linear_solutions_by_enumeration(self) -> None:
        rng = Random(1)
        for mod in (2, 3, 5):
            LinearAlgebraFp.set_mod(mod)
            for _ in range(100):
                n, m = rng.randrange(4), rng.randrange(4)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(m)] for _ in range(n)]
                b = [rng.randrange(-mod, 2*mod) for _ in range(n)]
                matrix = LinearAlgebraFp(n, m, a)
                image = {tuple(sum(row[j]*vector[j] for j in range(m)) % mod for row in a) for vector in product(range(mod), repeat=m)}
                rank, count = 0, 1
                while count < len(image):
                    rank += 1
                    count *= mod
                self.assertEqual(matrix.rank(), rank)
                solutions = {vector for vector in product(range(mod), repeat=m) if all(sum(row[j]*vector[j] for j in range(m)) % mod == rhs % mod for row, rhs in zip(a, b))}
                if not solutions:
                    with self.assertRaises(ValueError):
                        matrix.linear_equations(b)
                else:
                    result = matrix.linear_equations(b)
                    self.assertEqual(result.dimension, m-rank)
                    generated = {tuple((result.particular_solution[j]+sum(c*v[j] for c, v in zip(coefficients, result.basis_vectors))) % mod for j in range(m)) for coefficients in product(range(mod), repeat=result.dimension)}
                    self.assertEqual(generated, solutions)
                self.assertEqual(matrix._matrix, a)

    def test_inverse_hessenberg_and_characteristic_polynomial(self) -> None:
        rng = Random(2)
        for mod in (2, 3, 17, 998244353):
            LinearAlgebraFp.set_mod(mod)
            for _ in range(70):
                n = rng.randrange(5)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(n)] for _ in range(n)]
                matrix = LinearAlgebraFp(n, n, a)
                if determinant(a, mod):
                    inverse = ~matrix
                    identity = [[int(i == j) for j in range(n)] for i in range(n)]
                    self.assertEqual(multiply(a, inverse._matrix, n, mod), identity)
                    self.assertEqual(multiply(inverse._matrix, a, n, mod), identity)
                else:
                    with self.assertRaises(ValueError):
                        ~matrix
                h, transform = matrix.hessenberg_decomposition()
                self.assertEqual(multiply(a, transform._matrix, n, mod), multiply(transform._matrix, h._matrix, n, mod))
                self.assertNotEqual(determinant(transform._matrix, mod), 0)
                self.assertTrue(all(h[i, j] == 0 for i in range(n) for j in range(i-1)))
                coefficients = matrix.characteristic_polynomial()
                self.assertEqual(len(coefficients), n+1)
                self.assertEqual(coefficients[-1], 1)
                for x in range(min(mod, n+2)):
                    expected = determinant([[(x if i == j else 0)-a[i][j] for j in range(n)] for i in range(n)], mod)
                    self.assertEqual(sum(c*pow(x, i, mod) for i, c in enumerate(coefficients)) % mod, expected)
                self.assertEqual(matrix._matrix, a)
        LinearAlgebraFp.set_mod(5)
        matrix = LinearAlgebraFp(2, 2, [[5, 1], [1, 0]])
        LinearAlgebraFp.set_mod(3)
        self.assertEqual(matrix.determinant(), 2)

    def test_skew_symmetry_and_pfaffian(self) -> None:
        rng = Random(3)
        for mod in (2, 3, 17):
            LinearAlgebraFp.set_mod(mod)
            for n in (0, 2, 4, 6, 8):
                for _ in range(15):
                    a = [[0]*n for _ in range(n)]
                    for i in range(n):
                        a[i][i] = mod*rng.randrange(-2, 3)
                        for j in range(i):
                            a[i][j] = rng.randrange(-mod, 2*mod)
                            a[j][i] = -a[i][j] + mod*rng.randrange(-2, 3)
                    matrix = LinearAlgebraFp(n, n, a)
                    self.assertTrue(matrix.is_skew_symmetric())
                    actual = matrix.pfaffian()
                    self.assertEqual(actual, pfaffian(a, mod))
                    self.assertEqual(actual*actual % mod, matrix.determinant())
            invalid = LinearAlgebraFp(2, 2, [[1, 0], [0, 0]])
            self.assertEqual(invalid.is_skew_symmetric(), mod == 2)
            with self.assertRaises(ValueError):
                invalid.pfaffian()
            self.assertEqual(LinearAlgebraFp(3, 3).pfaffian(), 0)

    def test_sparse_modulus_and_shared_helpers(self) -> None:
        SparseMatrixMod.set_mod(5)
        matrix = SparseMatrixMod(2, 2, [(0, 0, 2), (0, 1, 1), (1, 1, 3)])
        FPS.set_mod(7)
        for mod in (0, 1, -1, 6):
            with self.assertRaises(ValueError):
                SparseMatrixMod.set_mod(mod)
            self.assertEqual((SparseMatrixMod._mod, SparseMatrixMod._is_prime), (5, True))
            self.assertEqual(FPS.get_mod(), 7)
        vector = [1, 2]
        expected = vector[:]
        for _ in range(10):
            expected = matrix.matvec(expected)
        self.assertEqual(matrix.pow_vec(10, vector, annihilating_polynomial=[1, -5, 6]), expected)
        FPS.set_mod(7)
        actual = matrix.apply_polynomial_to_vector([4, 2, 1], vector, vector_minimum_polynomial=[6, -5, 1])
        av = matrix.matvec(vector)
        aav = matrix.matvec(av)
        self.assertEqual(actual, [(4*v+2*a+b) % 5 for v, a, b in zip(vector, av, aav)])
        MatrixMod.set_mod(7)
        dense = matrix.to_dense()
        self.assertEqual(dense.get_mod(), 5)
        self.assertEqual(dense.matvec(vector), matrix.matvec(vector))
        with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: Random(0)):
            FPS.set_mod(7)
            coefficients = matrix.annihilating_polynomial(vector)
            self.assertEqual(coefficients, [1, 0, 1])
            FPS.set_mod(7)
            self.assertEqual(matrix.minimum_polynomial(), [1, 0, 1])
            FPS.set_mod(7)
            self.assertEqual(matrix.determinant(), 1)
        with patch.object(FPS, 'set_mod', side_effect=AssertionError('unnecessary modulus reset')):
            self.assertEqual(matrix.pow_vec(10, vector, annihilating_polynomial=[1, -5, 6]), expected)
            SparseMatrixMod.set_mod(5)


if __name__ == '__main__':
    unittest.main()
