from itertools import permutations, product
from random import Random
import unittest
from unittest.mock import patch

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.matrix import LinearAlgebraFp as Matrix, FrobeniusForm
from cplib.mathematics.polynomial import FormalPowerSeriesMod as FPS


def multiply(a: list[list[int]], b: list[list[int]], mod: int) -> list[list[int]]:
    n = len(a)
    return [[sum(a[i][k]*b[k][j] for k in range(n)) % mod for j in range(n)] for i in range(n)]


def power(a: list[list[int]], exponent: int, mod: int) -> list[list[int]]:
    result = [[int(i == j) for j in range(len(a))] for i in range(len(a))]
    for _ in range(exponent):
        result = multiply(result, a, mod)
    return result


def rank(a: list[list[int]], mod: int) -> int:
    rows = [[x % mod for x in row] for row in a]
    result = 0
    for j in range(len(rows[0]) if rows else 0):
        pivot = next((i for i in range(result, len(rows)) if rows[i][j]), None)
        if pivot is None:
            continue
        rows[result], rows[pivot] = rows[pivot], rows[result]
        inverse = pow(rows[result][j], -1, mod)
        for i in range(result+1, len(rows)):
            factor = rows[i][j]*inverse % mod
            rows[i] = [(x-factor*y) % mod for x, y in zip(rows[i], rows[result])]
        result += 1
    return result


def remainder(a: list[int], b: list[int], mod: int) -> list[int]:
    a = [x % mod for x in a]
    for i in range(len(a)-len(b), -1, -1):
        c = a[i+len(b)-1]*pow(b[-1], -1, mod) % mod
        for j, value in enumerate(b):
            a[i+j] = (a[i+j]-c*value) % mod
    while a and not a[-1]:
        a.pop()
    return a


def determinant(a: list[list[int]], mod: int) -> int:
    result = 0
    for indices in permutations(range(len(a))):
        inversions = sum(indices[i] > indices[j] for i in range(len(a)) for j in range(i+1, len(a)))
        term = -1 if inversions & 1 else 1
        for i, j in enumerate(indices):
            term *= a[i][j]
        result += term
    return result % mod


def hafnian(a: list[list[int]], mod: int) -> int:
    if not a:
        return 1 % mod
    if len(a) & 1:
        return 0
    total = 0
    for j in range(1, len(a)):
        indices = [i for i in range(1, len(a)) if i != j]
        total += a[0][j]*hafnian([[a[x][y] for y in indices] for x in indices], mod)
    return total % mod


class MatrixFormsContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod, self.prime = Matrix._mod, Matrix._is_prime
        self.mod_owned = '_mod' in Matrix.__dict__
        self.prime_owned = '_is_prime' in Matrix.__dict__
        self.fps = FPS.get_mod()
        self.transform = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        Matrix._mod, Matrix._is_prime = self.mod, self.prime
        if not self.mod_owned:
            del Matrix._mod
        if not self.prime_owned:
            del Matrix._is_prime
        if FPS.get_mod() != self.fps:
            FPS.set_mod(self.fps)
        if ConvolutionMod.get_mod() != self.transform:
            ConvolutionMod.set_mod(self.transform)

    def test_companion_and_block_powers(self) -> None:
        rng = Random(0)
        for mod in (2, 3, 5, 17, 998244353):
            Matrix.set_mod(mod)
            for _ in range(70):
                polynomials = [[rng.randrange(-mod, 2*mod) for _ in range(rng.randrange(4))]+[mod+1] for _ in range(rng.randrange(4))]
                matrix = Matrix.block_companion_matrix(polynomials)
                expected = [[0]*matrix._n for _ in range(matrix._n)]
                offset = 0
                for polynomial in polynomials:
                    n = len(polynomial)-1
                    for i in range(n):
                        expected[offset+i][offset+n-1] = -polynomial[i] % mod
                    for j in range(n-1):
                        expected[offset+j+1][offset+j] = 1
                    offset += n
                self.assertEqual(matrix._matrix, expected)
                k = rng.randrange(8)
                self.assertEqual(Matrix.block_companion_power(polynomials, k)._matrix, power(expected, k, mod))
            for polynomials in ([], [[1]]):
                with self.assertRaises(ValueError):
                    Matrix.block_companion_power(polynomials, -1)
            for invalid in ([], [0], [1, 0], [1, mod]):
                with self.assertRaises(ValueError):
                    Matrix.companion_matrix(invalid)
                with self.assertRaises(ValueError):
                    Matrix.block_companion_matrix([invalid])
                with self.assertRaises(ValueError):
                    Matrix.block_companion_power([invalid], 0)

    def test_frobenius_and_krylov_certificates(self) -> None:
        rng = Random(1)
        for mod in (2, 3, 5, 17, 998244353):
            Matrix.set_mod(mod)
            for _ in range(80):
                n = rng.randrange(8)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(n)] for _ in range(n)]
                matrix = Matrix(n, n, a)
                form = matrix.frobenius_form()
                self.assertEqual(rank(form.transform._matrix, mod), n)
                self.assertEqual(multiply(a, form.transform._matrix, mod), multiply(form.transform._matrix, form.frobenius._matrix, mod))
                self.assertEqual(sum(len(f)-1 for f in form.polynomials), n)
                for f in form.polynomials:
                    self.assertEqual(f[-1], 1)
                for f, g in zip(form.polynomials, form.polynomials[1:]):
                    self.assertEqual(remainder(g, f, mod), [])
                self.assertEqual(form.frobenius._matrix, Matrix.block_companion_matrix(form.polynomials)._matrix)
                k = rng.randrange(6)
                self.assertEqual(matrix.pow_by_frobenius_form(form, k)._matrix, power(a, k, mod))
                with patch('cplib.mathematics.matrix.SystemRandom', side_effect=lambda: Random(0)):
                    krylov = matrix.krylov_block_decomposition(max_retry=rng.randrange(3), reverse_basis=bool(rng.randrange(2)), leading_vector=[rng.randrange(mod) for _ in range(n)])
                self.assertEqual(rank(krylov.transform._matrix, mod), n)
                self.assertEqual(multiply(a, krylov.transform._matrix, mod), multiply(krylov.transform._matrix, krylov.action._matrix, mod))
                self.assertEqual([i for l, r in krylov.block_ranges for i in range(l, r)], list(range(n)))
                self.assertEqual(matrix._matrix, a)
            for n in (0, 1, 4):
                zero = Matrix(n, n)
                self.assertEqual(zero.pow_by_frobenius(3)._matrix, [[0]*n for _ in range(n)])

    def test_diagonalization_against_all_eigenvectors(self) -> None:
        rng = Random(2)
        for mod in (2, 3, 5):
            Matrix.set_mod(mod)
            for _ in range(70):
                n = rng.randrange(5)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(n)] for _ in range(n)]
                eigenvectors = [list(v) for root in range(mod) for v in product(range(mod), repeat=n) if all((sum(row[j]*v[j] for j in range(n))-root*v[i]) % mod == 0 for i, row in enumerate(a))]
                expected = rank(eigenvectors, mod) == n
                matrix = Matrix(n, n, a)
                result = matrix.diagonalize()
                self.assertEqual(result is not None, expected, (mod, a))
                if result is not None:
                    self.assertEqual(rank(result.transform._matrix, mod), n)
                    self.assertEqual(multiply(a, result.transform._matrix, mod), multiply(result.transform._matrix, result.diagonal._matrix, mod))
                    self.assertEqual(result.diagonal._matrix, [[result.eigenvalues[i] if i == j else 0 for j in range(n)] for i in range(n)])
                    actual = matrix.pow_by_diagonalization(5)
                    assert actual is not None
                    self.assertEqual(actual._matrix, power(a, 5, mod))
                else:
                    self.assertIsNone(matrix.pow_by_diagonalization(0))

    def test_adjugate_by_minors(self) -> None:
        rng = Random(3)
        for mod in (2, 3, 5, 17, 998244353):
            Matrix.set_mod(mod)
            for _ in range(80):
                n = rng.randrange(6)
                a = [[rng.randrange(-mod, 2*mod) for _ in range(n)] for _ in range(n)]
                matrix = Matrix(n, n, a)
                expected = [[(-1 if (i+j)&1 else 1)*determinant([[a[r][c] for c in range(n) if c != i] for r in range(n) if r != j], mod) % mod for j in range(n)] for i in range(n)]
                self.assertEqual(matrix.adjugate()._matrix, expected, (mod, a))
                self.assertEqual(matrix._matrix, a)

    def test_hafnian_by_matchings(self) -> None:
        rng = Random(4)
        for mod in (1, 2, 3, 4, 6, 17, 998244353):
            Matrix.set_mod(mod)
            for n in range(9):
                for _ in range(8):
                    a = [[0]*n for _ in range(n)]
                    for i in range(n):
                        a[i][i] = rng.randrange(-mod, 2*mod)
                        for j in range(i):
                            a[i][j] = rng.randrange(-mod, 2*mod)
                            a[j][i] = a[i][j]+mod*rng.randrange(-2, 3)
                    matrix = Matrix(n, n, a)
                    self.assertEqual(matrix.hafnian(), hafnian(a, mod), (mod, a))
                    self.assertEqual(matrix._matrix, a)
            if mod > 1:
                with self.assertRaises(ValueError):
                    Matrix(2, 2, [[0, 1], [0, 0]]).hafnian()

    def test_structured_forms_and_large_powers(self) -> None:
        for mod in (2, 3, 998244353):
            Matrix.set_mod(mod)
            matrix = Matrix.block_companion_matrix([[0, 0, 1]]*32+[[1, 1]])
            form = matrix.frobenius_form()
            self.assertEqual(rank(form.transform._matrix, mod), 65)
            self.assertEqual(multiply(matrix._matrix, form.transform._matrix, mod), multiply(form.transform._matrix, form.frobenius._matrix, mod))
            for f, g in zip(form.polynomials, form.polynomials[1:]):
                self.assertEqual(remainder(g, f, mod), [])
            self.assertIsNone(Matrix.identity(3).cyclic_frobenius_form(max_retry=0))
        mod = 998244353
        Matrix.set_mod(mod)
        rng = Random(5)
        n = 7
        transform = [[int(i == j) for j in range(n)] for i in range(n)]
        inverse = [[int(i == j) for j in range(n)] for i in range(n)]
        for _ in range(30):
            i, j = rng.sample(range(n), 2)
            c = rng.randrange(mod)
            transform[i] = [(x+c*y) % mod for x, y in zip(transform[i], transform[j])]
            for row in inverse:
                row[j] = (row[j]-c*row[i]) % mod
        eigenvalues = [0, 1, 1, 2, 3, 5, 8]
        diagonal = [[eigenvalues[i] if i == j else 0 for j in range(n)] for i in range(n)]
        raw = multiply(multiply(transform, diagonal, mod), inverse, mod)
        matrix = Matrix(n, n, [[x+mod*rng.randrange(-2, 3) for x in row] for row in raw])
        FPS.set_mod(17)
        result = matrix.diagonalize()
        assert result is not None
        self.assertEqual(rank(result.transform._matrix, mod), n)
        self.assertEqual(multiply(raw, result.transform._matrix, mod), multiply(result.transform._matrix, result.diagonal._matrix, mod))
        exponent = 10**30
        diagonal_power = [[pow(eigenvalues[i], exponent, mod) if i == j else 0 for j in range(n)] for i in range(n)]
        expected = multiply(multiply(transform, diagonal_power, mod), inverse, mod)
        actual = matrix.pow_by_diagonalization(exponent)
        assert actual is not None
        self.assertEqual(actual._matrix, expected)
        self.assertEqual(matrix.pow_by_frobenius(exponent)._matrix, expected)

    def test_validation_and_random_seed_order(self) -> None:
        Matrix.set_mod(5)
        matrix = Matrix(2, 2, [[1, 0], [0, 2]])
        for operation in (lambda: matrix.cyclic_frobenius_form(max_retry=-1), lambda: matrix.frobenius_form(max_retry=-1), lambda: matrix.krylov_block_decomposition(max_retry=-1), lambda: matrix.krylov_block_decomposition(leading_vector=[1]), lambda: matrix.pow_by_diagonalization(-1), lambda: matrix.pow_by_frobenius(-1)):
            with self.assertRaises(ValueError):
                operation()
        random_source = Random(0)
        with patch('cplib.mathematics.matrix.SystemRandom', return_value=random_source):
            with patch.object(random_source, 'randrange', side_effect=[0, 1]) as draw:
                form = matrix.krylov_block_decomposition(max_retry=1)
                self.assertEqual([row[0] for row in form.transform._matrix], [0, 1])
                self.assertEqual(draw.call_count, 2)
        form = matrix.frobenius_form()
        with self.assertRaises(ValueError):
            Matrix(2, 3).pow_by_frobenius_form(form, 0)
        with self.assertRaises(ValueError):
            matrix.pow_by_frobenius_form(FrobeniusForm(form.polynomials, form.transform, Matrix(1, 1)), 0)
        Matrix.set_mod(6)
        with self.assertRaises(NotImplementedError):
            Matrix.companion_power([1, 1], 2)
        with self.assertRaises(NotImplementedError):
            Matrix.block_companion_power([], 0)


if __name__ == '__main__':
    unittest.main()
