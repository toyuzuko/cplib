from copy import copy
from itertools import product
from random import Random
import unittest

from cplib.mathematics.matrix import BitSet, MatrixBit, LinearEquationResult


def values(matrix: MatrixBit) -> list[list[int]]:
    return [[matrix[i, j] for j in range(matrix._m)] for i in range(matrix._n)]


def rank_by_span(a: list[list[int]], columns: int) -> int:
    image = {tuple(sum(row[j]*v[j] for j in range(columns)) % 2 for row in a) for v in product(range(2), repeat=columns)}
    return len(image).bit_length()-1


def packed_rows(a: list[list[int]], columns: int) -> list[BitSet]:
    rows: list[BitSet] = []
    widths = (1, 7, 63, 64, 127)
    for i, row in enumerate(a):
        bits = BitSet(columns, widths[i % len(widths)])
        for j, value in enumerate(row):
            if value & 1:
                bits.add(j)
        rows.append(bits)
    return rows


class MatrixBitContractsTest(unittest.TestCase):
    def test_bitset_operations_and_bounds(self) -> None:
        rng = Random(0)
        for n in (0, 1, 2, 62, 63, 64, 65, 126, 127, 128, 257):
            for width in (1, 2, 7, 63, 64, 127, 130):
                bits = BitSet(n, width)
                expected: set[int] = set()
                for _ in range(100):
                    x = rng.randrange(-2, n+3)
                    if rng.randrange(2):
                        if 0 <= x < n:
                            bits.add(x)
                            expected.add(x)
                        else:
                            with self.assertRaises(ValueError):
                                bits.add(x)
                    else:
                        bits.discard(x)
                        expected.discard(x)
                    self.assertEqual(len(bits), len(expected))
                    self.assertEqual(x in bits, x in expected)
                self.assertEqual(str(bits), ''.join('1' if i in expected else '0' for i in range(n)))
                duplicate = copy(bits)
                for x in (-1, n, n+width):
                    self.assertFalse(x in bits)
                    with self.assertRaises(IndexError):
                        bits[x]
                    for v in (False, True):
                        with self.assertRaises(IndexError):
                            bits[x] = v
                if n:
                    bits[0] = not bits[0]
                    self.assertEqual(duplicate[0], 0 in expected)
                for i in range(n):
                    bits[i] = bool(i & 1)
                self.assertEqual(len(bits), n//2)
                if n % width:
                    self.assertEqual(bits.data[-1] >> (n % width), 0)
        for n, width in ((-1, 63), (1, 0), (1, -1)):
            with self.assertRaises(ValueError):
                BitSet(n, width)

    def test_mixed_block_width_bitwise_operations(self) -> None:
        rng = Random(1)
        for n in (0, 1, 3, 62, 63, 64, 65, 126, 127, 128, 513):
            for left_width, right_width in product((1, 7, 63, 64, 127), repeat=2):
                a = {i for i in range(n) if rng.randrange(2)}
                b = {i for i in range(n) if rng.randrange(2)}
                left, right = BitSet(n, left_width), BitSet(n, right_width)
                for i in a:
                    left.add(i)
                for i in b:
                    right.add(i)
                for actual, expected in ((left^right, a^b), (left&right, a&b)):
                    self.assertEqual(actual.n, n)
                    self.assertEqual(actual.bit_size, left_width)
                    self.assertEqual({i for i in range(n) if actual[i]}, expected)
                    self.assertEqual(len(actual), len(expected))
                self.assertEqual({i for i in range(n) if left[i]}, a)
                self.assertEqual({i for i in range(n) if right[i]}, b)
        for op in (lambda: BitSet(1)^BitSet(2), lambda: BitSet(1)&BitSet(2)):
            with self.assertRaises(ValueError):
                op()

    def test_exhaustive_small_matrices_and_solutions(self) -> None:
        for n in range(4):
            for m in range(4):
                for flat in product(range(2), repeat=n*m):
                    a = [list(flat[i*m:(i+1)*m]) for i in range(n)]
                    rows = packed_rows(a, m)
                    matrix = MatrixBit.from_bitset(n, m, rows)
                    expected_rank = rank_by_span(a, m)
                    self.assertEqual(matrix.rank(), expected_rank)
                    self.assertEqual(values(matrix), a)
                    if n == m:
                        self.assertEqual(matrix.determinant(), int(expected_rank == n))
                        if expected_rank == n:
                            inverse = values(~matrix)
                            self.assertEqual([[sum(a[i][k]*inverse[k][j] for k in range(n)) % 2 for j in range(n)] for i in range(n)], [[int(i == j) for j in range(n)] for i in range(n)])
                        else:
                            with self.assertRaises(ValueError):
                                ~matrix
                    for rhs in product(range(2), repeat=n):
                        solutions = {v for v in product(range(2), repeat=m) if all(sum(x*y for x, y in zip(row, v)) % 2 == r for row, r in zip(a, rhs))}
                        if not solutions:
                            with self.assertRaises(ValueError):
                                matrix.linear_equations(list(rhs))
                        else:
                            answer = matrix.linear_equations([x+2 for x in rhs])
                            self.assertIsInstance(answer, LinearEquationResult)
                            dim, particular, basis = answer
                            self.assertEqual(dim, m-expected_rank)
                            generated = {tuple((particular[j]+sum(c*v[j] for c, v in zip(coefficients, basis))) % 2 for j in range(m)) for coefficients in product(range(2), repeat=dim)}
                            self.assertEqual(generated, solutions)
                    self.assertEqual(values(matrix), a)
                    self.assertEqual([[int(bits[j]) for j in range(m)] for bits in rows], a)

    def test_products_transposes_and_word_boundaries(self) -> None:
        rng = Random(2)
        for shared in (0, 1, 3, 62, 63, 64, 65, 126, 127, 128, 131):
            for _ in range(10):
                n, m = rng.randrange(7), rng.randrange(7)
                a = [[rng.randrange(-3, 4) for _ in range(shared)] for _ in range(n)]
                b = [[rng.randrange(-3, 4) for _ in range(m)] for _ in range(shared)]
                left = MatrixBit.from_bitset(n, shared, packed_rows(a, shared))
                right = MatrixBit.from_bitset(shared, m, packed_rows(b, m))
                expected = [[sum(a[i][k]*b[k][j] for k in range(shared)) % 2 for j in range(m)] for i in range(n)]
                self.assertEqual(values(left*right), expected)
                transposed = [[a[i][j] % 2 for i in range(n)] for j in range(shared)]
                self.assertEqual(values(left.transpose()), transposed)
                self.assertEqual(values(MatrixBit(n, shared, transposed, transposed=True)), values(left))
        for n in (1, 62, 63, 64, 65, 126, 127):
            a = [[int(i == j) if i >= j else rng.randrange(2) for j in range(n)] for i in range(n)]
            matrix = MatrixBit.from_bitset(n, n, packed_rows(a, n))
            self.assertEqual(matrix.rank(), n)
            inverse = values(~matrix)
            self.assertEqual([[sum(a[i][k]*inverse[k][j] for k in range(n)) % 2 for j in range(n)] for i in range(n)], [[int(i == j) for j in range(n)] for i in range(n)])

    def test_matrix_validation_and_copying(self) -> None:
        for n, m in ((-1, 0), (0, -1), (-1, -1)):
            with self.assertRaises(ValueError):
                MatrixBit(n, m)
        for operation in (lambda: MatrixBit(1, 2, [[1]]), lambda: MatrixBit(1, 2, [[1, 2]], transposed=True), lambda: MatrixBit.from_bitset(2, 2, [BitSet(2)]), lambda: MatrixBit.from_bitset(1, 2, [BitSet(3)]), lambda: MatrixBit(1, 2)*MatrixBit(3, 1), lambda: MatrixBit(1, 2).determinant(), lambda: ~MatrixBit(1, 2), lambda: MatrixBit(2, 2).linear_equations([1])):
            with self.assertRaises(ValueError):
                operation()
        data = [[1, 0], [0, 1]]
        matrix = MatrixBit(2, 2, data)
        data[0][0] = 0
        self.assertEqual(matrix[0, 0], 1)
        rows = packed_rows([[1, 0], [0, 1]], 2)
        matrix = MatrixBit.from_bitset(2, 2, rows)
        rows[0].discard(0)
        self.assertEqual(matrix[0, 0], 1)
        for i, j in ((-1, -1), (-2, -2), (1, -2), (-2, 1)):
            self.assertEqual(matrix[i, j], matrix[i % 2, j % 2])
            matrix[i, j] = 3
            self.assertEqual(matrix[i % 2, j % 2], 1)
        for i, j in ((-3, 0), (0, -3), (2, 0), (0, 2)):
            with self.assertRaises(IndexError):
                matrix[i, j]
            with self.assertRaises(IndexError):
                matrix[i, j] = 0


if __name__ == '__main__':
    unittest.main()
