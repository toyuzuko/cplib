import random
import unittest

from cplib.datastructure.range2d import CompressedFenwickTree2D, KDTree2D, LazyKDTree2D, PointAddRectangleSum, RectangleAddPointGet, static_rectangle_add_rectangle_sum, static_rectangle_union_area


class Range2DContractTests(unittest.TestCase):
    def test_compressed_updates_and_invalid_points(self):
        rng = random.Random(0)
        points = sorted({(rng.randrange(-4, 5), rng.randrange(-4, 5)) for _ in range(25)}) + [(1 << 100, -(1 << 100))]
        actual = CompressedFenwickTree2D(iter(points + points))
        wrapper = PointAddRectangleSum(points)
        expected = dict.fromkeys(points, 0)
        for _ in range(1000):
            x, y = rng.choice(points)
            delta = rng.choice([rng.randrange(-20, 21), 1 << 100, -(1 << 100)])
            actual.add(x, y, delta)
            wrapper.add_point(x, y, delta)
            expected[x, y] += delta
            a, b = rng.randrange(-6, 7), rng.randrange(-6, 7)
            self.assertEqual(actual.prefix_sum_lt(a, b), sum(w for (x, y), w in expected.items() if x < a and y < b))
            self.assertEqual(actual.prefix_sum_leq(a, b), sum(w for (x, y), w in expected.items() if x <= a and y <= b))
            l, d, r, u = [rng.randrange(-6, 7) for _ in range(4)]
            self.assertEqual(wrapper.rectangle_sum(l, d, r, u), sum(w for (x, y), w in expected.items() if l <= x < r and d <= y < u))
        for x in range(-5, 6):
            for y in range(-5, 6):
                if (x, y) not in expected:
                    with self.assertRaises(ValueError):
                        actual.add(x, y, 7)
        for x in range(-6, 7):
            for y in range(-6, 7):
                self.assertEqual(actual.prefix_sum_lt(x, y), sum(w for (a, b), w in expected.items() if a < x and b < y))
        empty = CompressedFenwickTree2D([])
        self.assertEqual(empty.prefix_sum_lt(0, 0), 0)
        with self.assertRaises(ValueError):
            empty.add(0, 0, 0)

    def test_rectangle_updates_are_atomic(self):
        rng = random.Random(1)
        rectangles = [tuple(rng.randrange(-4, 5) for _ in range(4)) for _ in range(30)]
        actual = RectangleAddPointGet(iter(rectangles))
        updates = []
        for _ in range(350):
            l, d, r, u = rng.choice(rectangles)
            weight = rng.choice([rng.randrange(-20, 21), 1 << 100])
            actual.add_rectangle(l, d, r, u, weight)
            updates.append((l, d, r, u, weight))
            for _ in range(10):
                x, y = rng.randrange(-6, 7), rng.randrange(-6, 7)
                self.assertEqual(actual.point_get(x, y), sum(w for l, d, r, u, w in updates if l <= x < r and d <= y < u))
        actual = RectangleAddPointGet([(0, 0, 1, 1)])
        actual.add_rectangle(0, 0, 1, 1, 3)
        for rectangle in [(0, 0, 2, 1), (0, 0, 1, 2), (-1, 0, 1, 1)]:
            with self.assertRaises(ValueError):
                actual.add_rectangle(*rectangle, 8)
            for x in range(-2, 4):
                for y in range(-2, 4):
                    self.assertEqual(actual.point_get(x, y), 3 if (x, y) == (0, 0) else 0)
        actual.add_rectangle(100, 100, 0, 0, 7)
        actual.add_rectangle(100, 0, 100, 100, 7)
        self.assertEqual(actual.point_get(0, 0), 3)
        empty = RectangleAddPointGet([])
        self.assertEqual(empty.point_get(0, 0), 0)

    def test_kd_trees_against_points(self):
        rng = random.Random(2)
        mod = 97
        for n in [0, 1, 2, 30, 65]:
            points = [(rng.randrange(-5, 6), rng.randrange(-5, 6)) for _ in range(n)]
            values = [rng.randrange(mod) for _ in points]
            kd = KDTree2D(iter(points), iter(values))
            lazy = LazyKDTree2D(iter(points), iter(values), lambda a, b: (a + b) % mod, 0, lambda f, total, count: (f[0] * total + f[1] * count) % mod, lambda f, v: (f[0] * v + f[1]) % mod, lambda f, g: (f[0] * g[0] % mod, (f[0] * g[1] + f[1]) % mod), (1, 0))
            expected = values.copy()
            for _ in range(400):
                l, d, r, u = [rng.randrange(-7, 8) for _ in range(4)]
                selected = [i for i, (x, y) in enumerate(points) if l <= x < r and d <= y < u]
                if rng.randrange(3) == 0:
                    f = (rng.randrange(4), rng.randrange(-5, 6))
                    lazy.rectangle_apply(l, d, r, u, f)
                    for i in selected:
                        expected[i] = (f[0] * expected[i] + f[1]) % mod
                        kd.set(i, expected[i])
                elif n:
                    i = rng.randrange(n)
                    expected[i] = rng.randrange(mod)
                    lazy.set(i, expected[i])
                    kd.set(i, expected[i])
                self.assertEqual(kd.rectangle_sum(l, d, r, u), sum(expected[i] for i in selected))
                self.assertEqual(sorted(kd.rectangle_indices(l, d, r, u)), selected)
                self.assertEqual(lazy.rectangle_prod(l, d, r, u), sum(expected[i] for i in selected) % mod)
                self.assertEqual([lazy.get(i) for i in range(n)], expected)
                self.assertEqual([kd.get(i) for i in range(n)], expected)
            for bad in [-1, n, 10**9]:
                for tree in [kd, lazy]:
                    with self.assertRaises(IndexError):
                        tree.get(bad)
                    with self.assertRaises(IndexError):
                        tree.set(bad, 0)
                self.assertEqual([kd.get(i) for i in range(n)], expected)
                self.assertEqual([lazy.get(i) for i in range(n)], expected)
        with self.assertRaises(ValueError):
            KDTree2D([(0, 0)], [])

    def test_noncommutative_kd_order(self):
        points = [(x, 0) for x in range(7)]
        values = [chr(65 + i) for i in range(7)]
        tree = LazyKDTree2D(points, values, lambda a, b: a + b, '', lambda f, s, n: s.swapcase() if f else s, lambda f, s: s.swapcase() if f else s, lambda f, g: f ^ g, False)
        # The median splits produce the preorder 3, 1, 0, 2, 5, 4, 6.
        order = [3, 1, 0, 2, 5, 4, 6]
        for l in range(8):
            for r in range(l, 8):
                self.assertEqual(tree.rectangle_prod(l, -1, r, 1), ''.join(values[i] for i in order if l <= i < r))
        tree.rectangle_apply(1, -1, 6, 1, True)
        for i in range(1, 6):
            values[i] = values[i].swapcase()
        tree.set(2, '!')
        values[2] = '!'
        for l in range(8):
            for r in range(l, 8):
                self.assertEqual(tree.rectangle_prod(l, -1, r, 1), ''.join(values[i] for i in order if l <= i < r))

    def test_static_rectangles(self):
        rng = random.Random(3)
        for _ in range(150):
            rectangles = [tuple(rng.randrange(-4, 5) for _ in range(4)) for _ in range(rng.randrange(15))]
            weighted = [(*rect, rng.randrange(-8, 9)) for rect in rectangles]
            queries = [tuple(rng.randrange(-5, 6) for _ in range(4)) for _ in range(15)]
            cells = {(x, y) for l, d, r, u in rectangles for x in range(l, r) for y in range(d, u)}
            self.assertEqual(static_rectangle_union_area(iter(rectangles)), len(cells))
            expected = [sum(w * max(0, min(r, qr) - max(l, ql)) * max(0, min(u, qu) - max(d, qd)) for l, d, r, u, w in weighted) for ql, qd, qr, qu in queries]
            for mod in [None, 1, 7, 998244353]:
                self.assertEqual(static_rectangle_add_rectangle_sum(iter(weighted), iter(queries), mod), expected if mod is None else [v % mod for v in expected])
        huge = 1 << 100
        self.assertEqual(static_rectangle_union_area([(0, 0, huge, huge), (huge - 1, 0, huge + 1, huge)]), (huge + 1) * huge)
        self.assertEqual(static_rectangle_add_rectangle_sum([(0, 0, huge, huge, huge)], [(0, 0, huge, huge)]), [huge ** 3])
        for mod in [0, -1]:
            with self.assertRaises(ValueError):
                static_rectangle_add_rectangle_sum([], [], mod)


if __name__ == '__main__':
    unittest.main()
