import bisect
import math
import random
import unittest

from cplib.datastructure.binarytrie import BinaryTrie, RangeSortRangeProd
from cplib.datastructure.treap import Treap
from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.graph.counting import best_theorem
from cplib.graph.matching import MinimumWeightPerfectMatching
from cplib.mathematics.convolution import Convolution64bit, ConvolutionLargeIntegers, ConvolutionMod
from cplib.mathematics.factorial import FactorialMod
from cplib.mathematics.matrix import BitSet, MatrixMod
from cplib.string.hashing import DynamicRollingHashMersenneMod, RollingHashMersenneMod


class BitSetCountTest(unittest.TestCase):
    def test_count_across_bytes_and_words(self) -> None:
        for bit_size in (8, 32, 63, 64, 100):
            with self.subTest(bit_size=bit_size):
                bits = BitSet(201, bit_size)
                self.assertEqual(len(bits), 0)
                for index in (0, 7, 8, 16, 31, 32, 62, 63, 64, 127, 200):
                    bits.add(index)
                    self.assertEqual(len(bits), 1)
                    bits.discard(index)
                    self.assertEqual(len(bits), 0)
                for index in range(201):
                    bits.add(index)
                self.assertEqual(len(bits), 201)

    def test_count_after_set_operations(self) -> None:
        rng = random.Random(0)
        left = BitSet(201)
        right = BitSet(201)
        left_values: set[int] = set()
        right_values: set[int] = set()
        for _ in range(300):
            for bits, values in ((left, left_values), (right, right_values)):
                index = rng.randrange(201)
                if rng.randrange(2):
                    bits.add(index)
                    values.add(index)
                else:
                    bits.discard(index)
                    values.discard(index)
                self.assertEqual(len(bits), len(values))
            self.assertEqual(len(left & right), len(left_values & right_values))
            self.assertEqual(len(left ^ right), len(left_values ^ right_values))


class TreapBoundTest(unittest.TestCase):
    def test_bisect_right_with_right_subtree(self) -> None:
        tree = Treap[int]()
        for value in (1, 2, 3):
            tree.add(value)
        self.assertEqual(tree.bisect_right(2), 2)
        self.assertEqual(tree.get(tree.bisect_right(2)), 3)

    def test_bounds_against_bisect_after_updates(self) -> None:
        rng = random.Random(0)
        tree = Treap[int]()
        values: set[int] = set()
        for _ in range(300):
            value = rng.randrange(32)
            if rng.randrange(2):
                tree.add(value)
                values.add(value)
            else:
                tree.discard(value)
                values.discard(value)
            ordered = sorted(values)
            for query in range(-1, 33):
                for method, bisect_fn in ((tree.bisect_left, bisect.bisect_left),
                                          (tree.bisect_right, bisect.bisect_right)):
                    index = bisect_fn(ordered, query)
                    self.assertEqual(method(query), index)


class BinaryTrieTest(unittest.TestCase):
    def test_reinsert_returns_true(self) -> None:
        trie = BinaryTrie(4)
        self.assertTrue(trie.add(5))
        self.assertTrue(trie.discard(5))
        self.assertTrue(trie.add(5))
        self.assertFalse(trie.add(5))
        self.assertEqual(len(trie), 1)

    def test_order_after_xor(self) -> None:
        trie = BinaryTrie(4)
        trie.add(1)
        trie.add(2)
        trie.all_xor(3)
        self.assertEqual(trie.index(1), 0)
        self.assertEqual(trie.bisect_left(1), 0)

    def test_random_operations_against_set(self) -> None:
        rng = random.Random(0)
        trie = BinaryTrie(6)
        values: set[int] = set()
        for _ in range(500):
            x = rng.randrange(64)
            operation = rng.randrange(3)
            if operation == 0:
                self.assertEqual(trie.add(x), x not in values)
                values.add(x)
            elif operation == 1:
                self.assertEqual(trie.discard(x), x in values)
                values.discard(x)
            else:
                trie.all_xor(x)
                values = {v ^ x for v in values}
            ordered = sorted(values)
            self.assertEqual(len(trie), len(ordered))
            self.assertEqual([trie[i] for i in range(len(trie))], ordered)
            for value in range(64):
                rank = bisect.bisect_left(ordered, value)
                self.assertEqual(trie.bisect_left(value), rank)
                if value in values:
                    self.assertEqual(trie.index(value), rank)
                else:
                    with self.assertRaises(ValueError):
                        trie.index(value)
                self.assertEqual(value in trie, value in values)


class RollingHashTest(unittest.TestCase):
    def test_collision_does_not_count_as_occurrence(self) -> None:
        for cls in (RollingHashMersenneMod, DynamicRollingHashMersenneMod):
            with self.subTest(cls=cls.__name__):
                rh = cls('daab', base=3)
                self.assertEqual(rh.get_hash(0, 2), rh.get_hash(2, 4))
                self.assertEqual(rh.search_hash(2, rh.get_hash(2, 4)), 0)
                self.assertEqual(rh.search_substring('ab'), 2)
                self.assertEqual(rh.search_substring('ab', 0, 2), -1)

    def test_search_boundaries(self) -> None:
        for cls in (RollingHashMersenneMod, DynamicRollingHashMersenneMod):
            for text in ('', 'a', 'abcabc'):
                rh = cls(text)
                for l in range(len(text) + 1):
                    for r in range(l, len(text) + 1):
                        for pattern in ('', 'a', 'abc', 'bc', 'x', 'abcabcabc'):
                            with self.subTest(cls=cls.__name__, text=text, pattern=pattern, l=l, r=r):
                                self.assertEqual(rh.search_substring(pattern, l, r), text.find(pattern, l, r))
                        self.assertEqual(rh.search_hash(0, 0, l, r), l)
                        self.assertEqual(rh.search_hash(0, 1, l, r), -1)
                with self.assertRaises(AssertionError):
                    rh.search_hash(-1, 0)

    def test_default_base_avoids_small_alphabet_collision(self) -> None:
        for cls in (RollingHashMersenneMod, DynamicRollingHashMersenneMod):
            rh = cls('daab')
            self.assertNotEqual(rh.get_hash(0, 2), rh.get_hash(2, 4))

    def test_invalid_base(self) -> None:
        for cls in (RollingHashMersenneMod, DynamicRollingHashMersenneMod):
            for base in (0, -1, cls.mod, cls.mod + 1):
                with self.subTest(cls=cls.__name__, base=base):
                    with self.assertRaises(ValueError):
                        cls('abc', base=base)

    def test_static_hashes_and_search_against_string(self) -> None:
        rng = random.Random(0)
        for base in (1, 3, 911382323, RollingHashMersenneMod.mod - 1):
            text = ''.join(rng.choice('abcdA\x00あ') for _ in range(30))
            rh = RollingHashMersenneMod(text, base=base)
            for _ in range(100):
                l = rng.randrange(len(text) + 1)
                r = rng.randrange(l, len(text) + 1)
                expected_hash = sum(ord(c) * pow(base, j, rh.mod) for j, c in enumerate(text[l:r])) % rh.mod
                self.assertEqual(rh.get_hash(l, r), expected_hash)
                pattern = ''.join(rng.choice('abcdA\x00あ') for _ in range(rng.randrange(6)))
                for pattern in (pattern, text[l:r]):
                    self.assertEqual(rh.search_substring(pattern), text.find(pattern))
                    self.assertEqual(rh.search_substring(pattern, l, r), text.find(pattern, l, r))

    def test_dynamic_updates_and_hashes(self) -> None:
        rng = random.Random(0)
        alphabet = 'abcdA\x00あ'
        for base in (1, 3, 911382323):
            chars = list('daabcabc')
            rh = DynamicRollingHashMersenneMod(''.join(chars), base=base)
            for _ in range(80):
                i = rng.randrange(len(chars))
                chars[i] = rng.choice(alphabet)
                rh.set_char(i, chars[i])
                text = ''.join(chars)
                l = rng.randrange(len(chars) + 1)
                r = rng.randrange(l, len(chars) + 1)
                expected_hash = sum(ord(c) * pow(base, j, rh.mod) for j, c in enumerate(chars[l:r])) % rh.mod
                self.assertEqual(rh.get_hash(l, r), expected_hash)
                for pattern in ('', 'ab', text[l:r], 'a' * 12):
                    self.assertEqual(rh.search_substring(pattern, l, r), text.find(pattern, l, r))


class FactorialModTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_mod = FactorialMod.get_mod()
        self.matrix_mod = MatrixMod(0, 0).get_mod()

    def tearDown(self) -> None:
        FactorialMod.set_mod(self.original_mod)
        if MatrixMod(0, 0).get_mod() != self.matrix_mod:
            MatrixMod.set_mod(self.matrix_mod)

    def test_instances_keep_their_precomputed_modulus(self) -> None:
        tables = []
        for mod in (5, 7, 11):
            FactorialMod.set_mod(mod)
            tables.append((mod, FactorialMod(mod - 1)))
        FactorialMod.set_mod(13)
        self.assertEqual(FactorialMod.get_mod(), 13)
        for mod, table in tables:
            for n in range(mod):
                self.assertEqual(table.factorial(n), math.factorial(n) % mod)
                self.assertEqual(table.factorial_inv(n) * math.factorial(n) % mod, 1)
                for k in range(mod + 1):
                    self.assertEqual(table.comb(n, k), math.comb(n, k) % mod)
                    self.assertEqual(table.perm(n, k), math.perm(n, k) % mod)
                if n:
                    self.assertEqual(table.inv(n) * n % mod, 1)

    def test_best_theorem_sets_modulus_before_precomputation(self) -> None:
        FactorialMod.set_mod(7)
        graph = Graph(2, is_directed=True)
        for _ in range(5):
            graph.add_edge(Node(0), Node(1))
            graph.add_edge(Node(1), Node(0))
        for mod in (11, 7, 13):
            self.assertEqual(best_theorem(graph, mod), 5 * math.factorial(4) ** 2 % mod)


class RangeSortRangeProdTest(unittest.TestCase):
    def test_get_after_reverse_sort(self) -> None:
        values = RangeSortRangeProd(4, [3, 1, 4, 2], ['c', 'a', 'd', 'b'], 3, str.__add__, '')
        values.sort(0, 4, reverse=True)
        self.assertEqual([values.get(i) for i in range(4)], [(4, 'd'), (3, 'c'), (2, 'b'), (1, 'a')])

    def test_empty_sort_preserves_order(self) -> None:
        values = RangeSortRangeProd(4, [1, 2, 3, 4], ['a', 'b', 'c', 'd'], 3, str.__add__, '')
        values.sort(0, 4, reverse=True)
        values.sort(2, 2)
        self.assertEqual(values.all_prod(), 'dcba')

    def test_random_operations_against_list(self) -> None:
        rng = random.Random(0)
        keys = rng.sample(range(64), 10)
        expected = [(key, chr(ord('a') + i)) for i, key in enumerate(keys)]
        values = RangeSortRangeProd(10, keys, [v for _, v in expected], 6, str.__add__, '')
        for step in range(100):
            l = rng.randrange(11)
            r = rng.randrange(l, 11)
            if step % 3 == 0:
                i = rng.randrange(10)
                key = rng.choice(sorted(set(range(64)) - {key for key, _ in expected}))
                expected[i] = (key, str(step))
                values.set(i, *expected[i])
            else:
                reverse = bool(rng.randrange(2))
                expected[l:r] = sorted(expected[l:r], reverse=reverse)
                values.sort(l, r, reverse=reverse)
            self.assertEqual([values.get(i) for i in range(10)], expected)
            self.assertEqual(values.all_prod(), ''.join(v for _, v in expected))
            self.assertEqual(values.prod(l, r), ''.join(v for _, v in expected[l:r]))


class DocumentationAuditBugTest(unittest.TestCase):
    def test_perfect_matching_prioritizes_cardinality(self) -> None:
        matching = MinimumWeightPerfectMatching(4)
        for u, v, cost in ((0, 1, 0), (0, 2, 100), (1, 3, 100)):
            matching.add_edge(u, v, cost)
        result = matching.solve()
        self.assertTrue(result.success)
        self.assertEqual(result.weight, 200)
        self.assertEqual(sorted(result.edges), [(0, 2), (1, 3)])

    def test_perfect_matching_against_exhaustive_search(self) -> None:
        rng = random.Random(0)

        def solve_naively(vertices, costs):
            if not vertices:
                return 0
            u = vertices[0]
            answers = []
            for i, v in enumerate(vertices[1:], 1):
                if (u, v) in costs:
                    rest = solve_naively(vertices[1:i] + vertices[i + 1:], costs)
                    if rest is not None:
                        answers.append(costs[u, v] + rest)
            return min(answers) if answers else None

        for n in (2, 4, 6, 8):
            for _ in range(25):
                costs = {(u, v): rng.choice((0, 1, 100, 10000)) for u in range(n) for v in range(u + 1, n) if rng.randrange(3)}
                matching = MinimumWeightPerfectMatching(n)
                for (u, v), cost in costs.items():
                    matching.add_edge(u, v, cost)
                expected = solve_naively(list(range(n)), costs)
                result = matching.solve()
                self.assertEqual(result.success, expected is not None)
                self.assertEqual(result.weight, expected)

    def test_self_convolution_against_naive_product(self) -> None:
        rng = random.Random(0)
        original_mod = ConvolutionMod.get_mod()
        try:
            for mod in (17, 998244353):
                ConvolutionMod.set_mod(mod)
                for n in range(9):
                    values = [rng.randrange(-10, 11) for _ in range(n)]
                    original = values[:]
                    expected = [0] * max(0, 2 * n - 1)
                    for i, x in enumerate(values):
                        for j, y in enumerate(values):
                            expected[i + j] = (expected[i + j] + x * y) % mod
                    self.assertEqual(ConvolutionMod.autoconvolution(values), expected)
                    self.assertEqual(values, original)
            ConvolutionMod.set_mod(17)
            with self.assertRaises(ValueError):
                ConvolutionMod.autoconvolution([1] * 9)
        finally:
            ConvolutionMod.set_mod(original_mod)

    def test_self_convolution_crt_variants(self) -> None:
        for values in ([], [3], [1, 2], [10 ** 12, 7, 10 ** 12 + 1]):
            expected = [0] * max(0, 2 * len(values) - 1)
            for i, x in enumerate(values):
                for j, y in enumerate(values):
                    expected[i + j] += x * y
            self.assertEqual(ConvolutionLargeIntegers.autoconvolution(values), expected)
            self.assertEqual(ConvolutionLargeIntegers.autoconvolution(values, 1000000007), [x % 1000000007 for x in expected])
            self.assertEqual(Convolution64bit.autoconvolution(values), [x % (1 << 64) for x in expected])


if __name__ == '__main__':
    unittest.main()
