import random
import unittest
from fractions import Fraction

from cplib.algorithm import monotone_minima


class LessOnly:
    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: 'LessOnly') -> bool:
        return self.value < other.value

    def __eq__(self, other: object) -> bool:
        raise AssertionError('equality must not be used')

    def __le__(self, other: 'LessOnly') -> bool:
        raise AssertionError('less-or-equal must not be used')


class TestMonotoneMinima(unittest.TestCase):
    def test_empty_and_invalid(self) -> None:
        def unavailable(i: int, j: int) -> int:
            raise AssertionError('callback must not be evaluated')

        self.assertEqual(monotone_minima(0, 0, unavailable), [])
        self.assertEqual(monotone_minima(0, 10, unavailable), [])
        for rows, cols in [(-1, 2), (2, -1), (0, -1), (1, 0)]:
            with self.assertRaises(ValueError):
                monotone_minima(rows, cols, unavailable)

    def test_ties_and_generic_ordering(self) -> None:
        self.assertEqual(monotone_minima(20, 30, lambda i, j: 0), [0] * 20)
        for rows, cols in [(1, 31), (31, 1), (13, 19)]:
            matrix = [[abs(2 * i - j) // 2 for j in range(cols)] for i in range(rows)]
            expected = [min(range(cols), key=row.__getitem__) for row in matrix]
            self.assertEqual(
                monotone_minima(rows, cols, lambda i, j: LessOnly(matrix[i][j])),
                expected,
            )
            self.assertEqual(
                monotone_minima(rows, cols, lambda i, j: Fraction(matrix[i][j], 7)),
                expected,
            )
            self.assertEqual(
                monotone_minima(rows, cols, lambda i, j: (matrix[i][j], j)), expected
            )

    def test_random_rectangular_monge(self) -> None:
        rng = random.Random(348355)
        for _ in range(500):
            rows, cols = rng.randrange(1, 65), rng.randrange(1, 65)
            xs = sorted(rng.randrange(-50, 51) for _ in range(rows))
            ys = sorted(rng.randrange(-50, 51) for _ in range(cols))
            offsets = [rng.randrange(-1000, 1001) for _ in range(cols)]
            matrix = [[(x - y) ** 2 + offsets[j] for j, y in enumerate(ys)] for x in xs]
            expected = [min(range(cols), key=row.__getitem__) for row in matrix]
            self.assertEqual(
                monotone_minima(rows, cols, lambda i, j: matrix[i][j]), expected
            )

    def test_only_monotone_argmins_required(self) -> None:
        rng = random.Random(42)
        for _ in range(100):
            rows, cols = rng.randrange(1, 50), rng.randrange(1, 50)
            expected = sorted(rng.randrange(cols) for _ in range(rows))
            matrix = [[rng.randrange(1, 100) for _ in range(cols)] for _ in range(rows)]
            for i, j in enumerate(expected):
                matrix[i][j] = 0
            self.assertEqual(
                monotone_minima(rows, cols, lambda i, j: matrix[i][j]), expected
            )

    def test_callback_bound_and_domain(self) -> None:
        for rows, cols in [(1, 1000), (1000, 1), (513, 777), (1024, 1024)]:
            seen: set[tuple[int, int]] = set()

            def value(i: int, j: int) -> int:
                self.assertTrue(0 <= i < rows and 0 <= j < cols)
                self.assertNotIn((i, j), seen)
                seen.add((i, j))
                return (i * cols - j * rows) ** 2

            result = monotone_minima(rows, cols, value)
            expected = [
                min(range(cols), key=lambda j: (i * cols - j * rows) ** 2)
                for i in range(rows)
            ]
            self.assertEqual(result, expected)
            self.assertLessEqual(len(seen), rows + (cols - 1) * rows.bit_length())


if __name__ == '__main__':
    unittest.main()
