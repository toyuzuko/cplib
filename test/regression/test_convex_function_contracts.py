import random
import unittest

from cplib.datastructure.convex import LiChaoTree, MonotoneConvexHullTrick
from cplib.datastructure.slopetrick import SlopeTrick


class ConvexFunctionContractsTest(unittest.TestCase):
    def test_li_chao_large_values_and_segments(self) -> None:
        huge = 1 << 100
        for xs in ([], [0], [-huge, 0, huge], [-huge, -3, 0, 1, 1 << 63, huge, huge + 1], list(range(-10, 11))):
            rng = random.Random(len(xs))
            original = xs[:]
            tree = LiChaoTree(original)
            original.append(999)
            lines: list[tuple[int, int, int | None, int | None]] = []
            pool = [-huge * 2, -huge, -1, 0, 1, 10, (1 << 63) - 1, huge, huge * 2]
            for step in range(350):
                a, b = rng.choice(pool), rng.choice(pool)
                if step % 5 == 0:
                    tree.add_line(a, b)
                    lines.append((a, b, None, None))
                else:
                    l, r = sorted((rng.choice(pool), rng.choice(pool)))
                    tree.add_segment(a, b, l, r)
                    lines.append((a, b, l, r))
                for x in xs:
                    expected = min((a * x + b for a, b, l, r in lines if l is None or l <= x < r), default=None)
                    self.assertEqual(tree.get_min(x), expected)
            before = tree.a[:], tree.b[:], tree._used[:]
            with self.assertRaises(ValueError):
                tree.add_segment(0, 0, 1, -1)
            self.assertEqual((tree.a, tree.b, tree._used), before)
            with self.assertRaises(AssertionError):
                tree.get_min(3 * huge)
        for invalid in ([1, 1], [1, 0]):
            with self.assertRaises(ValueError):
                LiChaoTree(invalid)
        tree = LiChaoTree([0, 1, huge])
        tree.add_line(0, 0)
        tree.add_line(-1, 1 << 80)
        self.assertEqual(tree.get_min(huge), (1 << 80) - huge)
        tree = LiChaoTree([0, 1, 2])
        self.assertIsNone(tree.get_min(1))
        tree.add_segment(0, huge, 1, 2)
        self.assertIsNone(tree.get_min(0))
        self.assertEqual(tree.get_min(1), huge)
        self.assertIsNone(tree.get_min(2))

    def test_li_chao_missing_lines_are_distinct_from_integer_results(self) -> None:
        for value in (0, (1 << 63) - 1, 1 << 100, -(1 << 100)):
            tree = LiChaoTree([0, 1, 2])
            self.assertIsNone(tree.get_min(1))
            tree.add_segment(0, value, 1, 2)
            self.assertIsNone(tree.get_min(0))
            self.assertEqual(tree.get_min(1), value)
            self.assertIsNone(tree.get_min(2))
            tree.add_line(0, value + 1)
            self.assertEqual([tree.get_min(x) for x in range(3)], [value + 1, value, value + 1])

    def test_monotone_interleaved_lines_queries(self) -> None:
        huge = 1 << 100
        for direction in (1, -1):
            rng = random.Random(0)
            tree = MonotoneConvexHullTrick(slope_increasing=direction < 0, query_increasing=direction > 0)
            with self.assertRaises(ValueError):
                tree.get_min(huge)
            lines: list[tuple[int, int]] = []
            slope, x = huge, -huge
            for step in range(1800):
                if step % 3 != 2:
                    slope -= rng.randrange(6)
                    b = rng.randrange(-huge, huge)
                    tree.add_line(direction * slope, b)
                    lines.append((direction * slope, b))
                else:
                    x += rng.randrange(10**30)
                    coordinate = direction * x
                    self.assertEqual(tree.get_min(coordinate), min(a * coordinate + b for a, b in lines))
                    before = list(tree.lines), tree._last_x
                    with self.assertRaises(ValueError):
                        tree.get_min(coordinate - direction)
                    self.assertEqual((list(tree.lines), tree._last_x), before)
                before = list(tree.lines)
                with self.assertRaises(ValueError):
                    tree.add_line(direction * (slope + 1), 0)
                self.assertEqual(list(tree.lines), before)
        for direction in (False, True):
            with self.assertRaises(ValueError):
                MonotoneConvexHullTrick(direction, direction)

    def test_slope_trick_against_grid_dp(self) -> None:
        for seed in range(30):
            rng = random.Random(seed)
            constant = rng.randrange(-10, 11)
            tree = SlopeTrick(constant)
            lo, hi = -400, 400
            values = [constant] * (hi - lo + 1)
            for _ in range(90):
                operation = rng.randrange(8)
                a = rng.randrange(-8, 9)
                if operation == 0:
                    tree.add_const(a)
                    values = [v + a for v in values]
                elif operation == 1:
                    tree.add_abs(a)
                    values = [v + abs(x - a) for x, v in enumerate(values, lo)]
                elif operation == 2:
                    tree.add_x_minus_a(a)
                    values = [v + max(x - a, 0) for x, v in enumerate(values, lo)]
                elif operation == 3:
                    tree.add_a_minus_x(a)
                    values = [v + max(a - x, 0) for x, v in enumerate(values, lo)]
                elif operation == 4:
                    tree.shift(a)
                    lo += a
                    hi += a
                elif operation == 5:
                    left, right = sorted((rng.randrange(-3, 4), rng.randrange(-3, 4)))
                    tree.sliding_window_min(left, right)
                    values = [min(values[i:i + right - left + 1]) for i in range(len(values) - (right - left))]
                    lo += right
                    hi += left
                elif operation == 6:
                    tree.prefix_min()
                    current = values[0]
                    for i, value in enumerate(values):
                        current = min(current, value)
                        values[i] = current
                else:
                    tree.suffix_min()
                    current = values[-1]
                    for i in range(len(values) - 1, -1, -1):
                        current = min(current, values[i])
                        values[i] = current
                minimum = min(values)
                self.assertEqual(tree.minimum(), minimum)
                positions = [i + lo for i, v in enumerate(values) if v == minimum]
                left = None if positions[0] == lo else positions[0]
                right = None if positions[-1] == hi else positions[-1]
                self.assertEqual(tree.minimum_interval(), (left, right))
                for x in range(-30, 31):
                    self.assertEqual(tree.evaluate(x), values[x - lo])
            before = tree.minimum(), tree.minimum_interval(), [tree.evaluate(x) for x in range(-10, 11)]
            with self.assertRaises(ValueError):
                tree.sliding_window_min(2, 1)
            self.assertEqual((tree.minimum(), tree.minimum_interval(), [tree.evaluate(x) for x in range(-10, 11)]), before)
        huge = 1 << 100
        tree = SlopeTrick(-huge)
        tree.add_abs(huge)
        tree.shift(huge)
        self.assertEqual(tree.minimum_interval(), (2 * huge, 2 * huge))
        self.assertEqual(tree.evaluate(0), huge)


if __name__ == '__main__':
    unittest.main()
