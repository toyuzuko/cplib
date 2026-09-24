from collections import Counter
import itertools
import random
import unittest

from cplib.sequence.alignment import edit_distance, longest_common_subsequence_length
from cplib.sequence.cartesian import cartesian_tree
from cplib.sequence.grid import count_rectangles_in_grid, count_squares_in_grid, largest_rectangle_area_in_grid, largest_square_area_in_grid
from cplib.sequence.histogram import largest_rectangle_area
from cplib.sequence.permutation import count_inversions, next_permutation, prev_permutation
from cplib.sequence.rangestat import OfflineStaticRangeInversionsQuery, OfflineStaticRangeMexQuery, StaticRangeCountDistinctQuery, StaticRangeLISQuery, StaticRangeMajorityQuery, StaticRangeModeQuery, StaticRangeOrderQuery
from cplib.sequence.window import count_subarrays_with_sum, count_subarrays_with_sum_at_most_nonnegative, minimum_subarray_length_with_sum_at_least_nonnegative, minimum_window_covering_multiset


class SequenceRangesTest(unittest.TestCase):
    def test_range_statistics_against_slices(self) -> None:
        rng = random.Random(0)
        self.assertEqual(StaticRangeModeQuery(1, [-1]).range_mode(0, 1), (-1, 1))
        for _ in range(65):
            n = rng.randrange(35)
            arr = [rng.randrange(-3, 8) for _ in range(n)]
            mode = StaticRangeModeQuery(n, arr)
            majority = StaticRangeMajorityQuery(arr)
            distinct = StaticRangeCountDistinctQuery(arr)
            queries = [(l, r) for l in range(n + 1) for r in range(l, n + 1)]
            rng.shuffle(queries)
            queries = queries[:80]
            inversions: list[int] = []
            mex: list[int] = []
            for l, r in queries:
                values = arr[l:r]
                counts = Counter(values)
                self.assertEqual(distinct.count_distinct(l, r), len(counts))
                inversions.append(sum(a > b for i, a in enumerate(values) for b in values[i + 1:]))
                missing = 0
                while missing in counts:
                    missing += 1
                mex.append(missing)
                if l < r:
                    value, count = mode.range_mode(l, r)
                    self.assertEqual(counts[value], count)
                    self.assertEqual(count, max(counts.values()))
                    expected_majority = next((value for value, count in counts.items() if count * 2 > r - l), None)
                    self.assertEqual(majority.range_majority(l, r), expected_majority)
                else:
                    with self.assertRaises(ValueError):
                        mode.range_mode(l, r)
            inv_solver = OfflineStaticRangeInversionsQuery(arr)
            mex_solver = OfflineStaticRangeMexQuery(n, arr)
            for _ in range(2):
                self.assertEqual(inv_solver.solve(queries), inversions)
                self.assertEqual(mex_solver.solve(queries), mex)

    def test_range_order_and_lis(self) -> None:
        rng = random.Random(0)
        for _ in range(60):
            n = rng.randrange(25)
            arr = [rng.randrange(20) for _ in range(n)]
            order = StaticRangeOrderQuery(arr)
            perm = rng.sample(range(n), n)
            lis = StaticRangeLISQuery(perm)
            for l in range(n + 1):
                for r in range(l, n + 1):
                    values = arr[l:r]
                    self.assertEqual(order.range_sum(l, r), sum(values))
                    x = rng.randrange(-2, 35)
                    self.assertEqual(order.freq(l, r, x), values.count(x))
                    self.assertEqual(order.count_lt(l, r, x), sum(v < x for v in values))
                    self.assertEqual(order.count_le(l, r, x), sum(v <= x for v in values))
                    self.assertEqual(order.sum_lt(l, r, x), sum(v for v in values if v < x))
                    self.assertEqual(order.sum_le(l, r, x), sum(v for v in values if v <= x))
                    y = rng.randrange(-2, 35)
                    self.assertEqual(order.count_between(l, r, x, y), sum(x <= v < y for v in values))
                    self.assertEqual(order.sum_between(l, r, x, y), sum(v for v in values if x <= v < y))
                    if values:
                        k = rng.randrange(len(values))
                        self.assertEqual(order.kth_smallest(l, r, k), sorted(values)[k])
                        self.assertEqual(order.quantile(l, r, k), sorted(values)[k])
                    lengths = [1] * (r - l)
                    for i in range(r - l):
                        for j in range(i):
                            if perm[l + j] < perm[l + i]:
                                lengths[i] = max(lengths[i], lengths[j] + 1)
                    self.assertEqual(lis.range_lis(l, r), max(lengths, default=0))

    def test_window_queries(self) -> None:
        rng = random.Random(0)
        for _ in range(180):
            arr = [rng.randrange(-3, 5) for _ in range(rng.randrange(12))]
            target = rng.randrange(-5, 12)
            ranges = [(l, r) for l in range(len(arr)) for r in range(l + 1, len(arr) + 1)]
            self.assertEqual(count_subarrays_with_sum(arr, target), sum(sum(arr[l:r]) == target for l, r in ranges))
            positive = [abs(v) for v in arr]
            self.assertEqual(count_subarrays_with_sum_at_most_nonnegative(positive, target), sum(sum(positive[l:r]) <= target for l, r in ranges))
            expected = 0 if target <= 0 else min((r - l for l, r in ranges if sum(positive[l:r]) >= target), default=0)
            self.assertEqual(minimum_subarray_length_with_sum_at_least_nonnegative(positive, target), expected)
            required = [rng.randrange(-3, 5) for _ in range(rng.randrange(5))]
            need = Counter(required)
            expected = min((r - l for l, r in ranges if Counter(arr[l:r]) >= need), default=0) if required else 0
            self.assertEqual(minimum_window_covering_multiset(arr, iter(required)), expected)
        for bound in (-1, 0, 1):
            with self.assertRaises(ValueError):
                count_subarrays_with_sum_at_most_nonnegative([-1], bound)
            with self.assertRaises(ValueError):
                minimum_subarray_length_with_sum_at_least_nonnegative([-1], bound)

    def test_grid_and_histogram_against_rectangles(self) -> None:
        rng = random.Random(0)
        for _ in range(100):
            h, w = rng.randrange(6), rng.randrange(6)
            grid = [[rng.randrange(2) for _ in range(w)] for _ in range(h)]
            rectangle_areas: list[int] = []
            square_areas: list[int] = []
            for top in range(h):
                for bottom in range(top + 1, h + 1):
                    for left in range(w):
                        for right in range(left + 1, w + 1):
                            if all(grid[i][j] == 0 for i in range(top, bottom) for j in range(left, right)):
                                area = (bottom - top) * (right - left)
                                rectangle_areas.append(area)
                                if bottom - top == right - left:
                                    square_areas.append(area)
            self.assertEqual(count_rectangles_in_grid(grid), len(rectangle_areas))
            self.assertEqual(count_squares_in_grid(grid), len(square_areas))
            self.assertEqual(largest_rectangle_area_in_grid(grid), max(rectangle_areas, default=0))
            self.assertEqual(largest_square_area_in_grid(grid), max(square_areas, default=0))
            histogram = [rng.randrange(10) for _ in range(rng.randrange(15))]
            expected = max((min(histogram[l:r]) * (r - l) for l in range(len(histogram)) for r in range(l + 1, len(histogram) + 1)), default=0)
            self.assertEqual(largest_rectangle_area(histogram), expected)

    def test_cartesian_tree_and_permutations(self) -> None:
        rng = random.Random(0)
        with self.assertRaises(ValueError):
            cartesian_tree([])
        for _ in range(100):
            arr = [rng.randrange(-3, 5) for _ in range(rng.randrange(1, 25))]
            tree = cartesian_tree(arr)
            pending = [(0, len(arr), -1)]
            while pending:
                l, r, parent = pending.pop()
                if l == r:
                    continue
                root = min(range(l, r), key=lambda i: arr[i])
                self.assertEqual(tree.par_v[root], parent)
                pending.extend(((l, root, root), (root + 1, r, root)))
            self.assertEqual(count_inversions(arr), sum(a > b for i, a in enumerate(arr) for b in arr[i + 1:]))
        for arr in ([], [0], [0, 0, 1, 2], [0, 1, 2, 3]):
            permutations = sorted(set(itertools.permutations(arr)))
            for i, p in enumerate(permutations):
                values = list(p)
                self.assertEqual(next_permutation(values), i + 1 < len(permutations))
                self.assertEqual(values, list(permutations[min(i + 1, len(permutations) - 1)]))
                values = list(p)
                self.assertEqual(prev_permutation(values), i > 0)
                self.assertEqual(values, list(permutations[max(0, i - 1)]))

    def test_alignment_against_full_tables(self) -> None:
        rng = random.Random(0)
        for _ in range(100):
            s = [rng.randrange(3) for _ in range(rng.randrange(9))]
            t = [rng.randrange(3) for _ in range(rng.randrange(9))]
            ins, delete, replace = [rng.randrange(5) for _ in range(3)]
            dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]
            for i in range(len(s) + 1):
                dp[i][0] = i * delete
            for j in range(len(t) + 1):
                dp[0][j] = j * ins
            for i in range(1, len(s) + 1):
                for j in range(1, len(t) + 1):
                    dp[i][j] = min(dp[i - 1][j] + delete, dp[i][j - 1] + ins, dp[i - 1][j - 1] + (replace if s[i - 1] != t[j - 1] else 0))
            self.assertEqual(edit_distance(s, t, ins, delete, replace), dp[-1][-1])
            subsequences_s = {tuple(x for i, x in enumerate(s) if mask >> i & 1) for mask in range(1 << len(s))}
            subsequences_t = {tuple(x for i, x in enumerate(t) if mask >> i & 1) for mask in range(1 << len(t))}
            self.assertEqual(longest_common_subsequence_length(s, t), max(map(len, subsequences_s & subsequences_t)))


if __name__ == '__main__':
    unittest.main()
