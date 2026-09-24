import math
import random
import unittest

from cplib.algorithm import hilbert_order
from cplib.graph import LowLinkAnalysisResult, analyze_lowlink
from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.mathematics import batch_inverse_mod
from cplib.mathematics.convolution import ConvolutionMod


class HilbertOrderTest(unittest.TestCase):
    def test_grid_is_a_continuous_bijection(self) -> None:
        for power in range(6):
            side = 1 << power
            points = [(x, y) for x in range(side) for y in range(side)]
            points.sort(key=lambda point: hilbert_order(*point, power))
            self.assertEqual([hilbert_order(*point, power) for point in points], list(range(side * side)))
            for (x, y), (u, v) in zip(points, points[1:]):
                self.assertEqual(abs(x - u) + abs(y - v), 1)

    def test_bounds(self) -> None:
        self.assertEqual(hilbert_order(0, 0, 0), 0)
        for x, y, power in ((0, 0, -1), (-1, 0, 2), (0, -1, 2), (4, 0, 2), (0, 4, 2), (1, 0, 0)):
            with self.subTest(x=x, y=y, power=power), self.assertRaises(ValueError):
                hilbert_order(x, y, power)


class BatchInverseTest(unittest.TestCase):
    def test_prime_and_composite_moduli(self) -> None:
        rng = random.Random(0)
        for mod in (2, 7, 15, 16, 35, 998244353):
            values = [rng.randrange(-2 * mod, 2 * mod) for _ in range(100)]
            values = [value for value in values if math.gcd(value, mod) == 1]
            original = values[:]
            self.assertEqual(batch_inverse_mod(values, mod), [pow(value, -1, mod) for value in values])
            self.assertEqual(values, original)
            self.assertEqual(batch_inverse_mod([], mod), [])

    def test_invalid_inputs(self) -> None:
        for mod in (-1, 0, 1):
            with self.assertRaises(ValueError):
                batch_inverse_mod([], mod)
        for values, mod in (([1, 0, 2], 7), ([2, 3, 4], 15)):
            original = values[:]
            with self.assertRaises(ValueError):
                batch_inverse_mod(values, mod)
            self.assertEqual(values, original)


class ConvolutionHelpersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_mod = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        if ConvolutionMod.get_mod() != self.original_mod:
            ConvolutionMod.set_mod(self.original_mod)

    def test_two_dimensional_against_direct_product(self) -> None:
        rng = random.Random(0)
        for mod in (998244353, 97):
            ConvolutionMod.set_mod(mod)
            for _ in range(30):
                h1, w1, h2, w2 = [rng.randrange(1, 4) for _ in range(4)]
                left = [[rng.randrange(-mod, mod) for _ in range(w1)] for _ in range(h1)]
                right = [[rng.randrange(-mod, mod) for _ in range(w2)] for _ in range(h2)]
                saved_left = [row[:] for row in left]
                saved_right = [row[:] for row in right]
                expected = [[0] * (w1 + w2 - 1) for _ in range(h1 + h2 - 1)]
                for i, row in enumerate(left):
                    for j, x in enumerate(row):
                        for k, other in enumerate(right):
                            for l, y in enumerate(other):
                                expected[i + k][j + l] = (expected[i + k][j + l] + x * y) % mod
                self.assertEqual(ConvolutionMod.convolution2d(left, right), expected)
                self.assertEqual(left, saved_left)
                self.assertEqual(right, saved_right)

    def test_two_dimensional_shapes_and_transform_limit(self) -> None:
        empty_shapes: list[tuple[list[list[int]], list[list[int]]]] = [
            ([], [[1]]), ([[], []], [[1]]), ([[1]], []), ([[1]], [[], []]),
        ]
        for left, right in empty_shapes:
            self.assertEqual(ConvolutionMod.convolution2d(left, right), [])
        invalid_shapes: list[tuple[list[list[int]], list[list[int]]]] = [
            ([[1], [2, 3]], [[1]]), ([], [[1], []]),
        ]
        for left, right in invalid_shapes:
            with self.assertRaises(ValueError):
                ConvolutionMod.convolution2d(left, right)
        ConvolutionMod.set_mod(17)
        self.assertEqual(ConvolutionMod.convolution2d([[1] * 3] * 2, [[1] * 3] * 2), [[1, 2, 3, 2, 1], [2, 4, 6, 4, 2], [1, 2, 3, 2, 1]])
        with self.assertRaises(ValueError):
            ConvolutionMod.convolution2d([[1] * 3] * 3, [[1] * 3] * 3)

    def test_middle_product_against_sliding_dot_products(self) -> None:
        rng = random.Random(0)
        for mod in (998244353, 97):
            ConvolutionMod.set_mod(mod)
            for _ in range(50):
                n = rng.randrange(16)
                m = rng.randrange(n + 1)
                left = [rng.randrange(-mod, mod) for _ in range(n)]
                right = [rng.randrange(-mod, mod) for _ in range(m)]
                saved_left, saved_right = left[:], right[:]
                expected = [sum(left[i + j] * right[j] for j in range(m)) % mod for i in range(n - m + 1)]
                self.assertEqual(ConvolutionMod.middle_product(left, right), expected)
                self.assertEqual(left, saved_left)
                self.assertEqual(right, saved_right)
        with self.assertRaises(ValueError):
            ConvolutionMod.middle_product([], [1])
        ConvolutionMod.set_mod(17)
        with self.assertRaises(ValueError):
            ConvolutionMod.middle_product([1] * 16, [1, 1])


class LowLinkAnalysisTest(unittest.TestCase):
    def test_public_result_includes_components_and_isolated_vertices(self) -> None:
        graph = Graph(5)
        for u, v in ((0, 1), (1, 2), (2, 0), (2, 3)):
            graph.add_edge(Node(u), Node(v))
        result = analyze_lowlink(graph)
        self.assertIsInstance(result, LowLinkAnalysisResult)
        self.assertEqual(result.articulation, [False, False, True, False, False])
        self.assertEqual(result.bridges, [3])
        self.assertEqual({frozenset(component) for component in result.biconnected_components}, {frozenset((0, 1, 2)), frozenset((2, 3)), frozenset((4,))})
        with self.assertRaises(ValueError):
            analyze_lowlink(Graph(2, is_directed=True))


if __name__ == '__main__':
    unittest.main()
