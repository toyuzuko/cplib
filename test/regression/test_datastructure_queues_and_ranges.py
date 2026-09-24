from collections import deque
import random
import unittest

from cplib.datastructure.cumulative import Cumulative, CumulativeSum2D, Imos1D, Imos2D
from cplib.datastructure.intervalset import IntervalSet
from cplib.datastructure.queue import DeletablePriorityQueue, DoubleEndedPriorityQueue, DoubleEndedQueue, OffsetPriorityQueue, PersistentLeftistHeap, PriorityQueue, RadixHeap
from cplib.datastructure.swag import SlidingWindowAggregation


class QueuesAndRangesTest(unittest.TestCase):
    def test_priority_queue_rebuild_and_deletion(self) -> None:
        rng = random.Random(0)
        for ascending in (False, True):
            queue = DeletablePriorityQueue[int](ascending)
            ordinary = PriorityQueue[int](ascending)
            values: list[int] = []
            for _ in range(2000):
                action = rng.randrange(5)
                if action == 0:
                    values = [rng.randrange(-5, 6) for _ in range(rng.randrange(20))]
                    queue.build(values)
                    ordinary.build(values)
                elif action <= 2:
                    value = rng.randrange(-5, 6)
                    values.append(value)
                    queue.push(value)
                    ordinary.push(value)
                elif action == 3:
                    value = rng.randrange(-8, 9)
                    if value in values:
                        queue.remove(value)
                        values.remove(value)
                        ordinary.build(values)
                    else:
                        with self.assertRaises(KeyError):
                            queue.remove(value)
                elif values:
                    expected = min(values) if ascending else max(values)
                    self.assertEqual(queue.pop(), expected)
                    self.assertEqual(ordinary.top(), expected)
                    self.assertEqual(ordinary.pop(), expected)
                    values.remove(expected)
                else:
                    with self.assertRaises(IndexError):
                        queue.pop()
                self.assertEqual(len(queue), len(values))
                self.assertEqual(len(ordinary), len(values))
            queue.build([1])
            queue.build([2])
            with self.assertRaises(KeyError):
                queue.remove(1)
            self.assertEqual(queue.pop(), 2)

    def test_double_ended_priority_queue_rebuild(self) -> None:
        rng = random.Random(0)
        queue = DoubleEndedPriorityQueue[int]()
        values: list[int] = []
        for _ in range(4000):
            action = rng.randrange(5)
            if action == 0:
                values = [rng.randrange(-5, 6) for _ in range(rng.randrange(20))]
                queue.build(values)
            elif action <= 2:
                value = rng.randrange(-5, 6)
                values.append(value)
                queue.push(value)
            elif values:
                expected = min(values) if action == 3 else max(values)
                self.assertEqual(queue.pop_min() if action == 3 else queue.pop_max(), expected)
                values.remove(expected)
            else:
                with self.assertRaises(IndexError):
                    queue.pop_min()
                with self.assertRaises(IndexError):
                    queue.pop_max()
            self.assertEqual(len(queue), len(values))
        for pop_old, pop_new in ((queue.pop_min, queue.pop_max), (queue.pop_max, queue.pop_min)):
            queue.build([1])
            self.assertEqual(pop_old(), 1)
            queue.build([1])
            self.assertEqual(pop_new(), 1)

    def test_offsets_and_meld(self) -> None:
        rng = random.Random(0)
        for ascending in (False, True):
            queues = [OffsetPriorityQueue(ascending) for _ in range(4)]
            values: list[list[int]] = [[] for _ in queues]
            for _ in range(1600):
                i = rng.randrange(4)
                queue = queues[i]
                action = rng.randrange(6)
                if action == 0:
                    values[i] = [rng.randrange(-10, 11) for _ in range(rng.randrange(10))]
                    queue.build(values[i])
                elif action <= 2:
                    value = rng.randrange(-10, 11)
                    values[i].append(value)
                    queue.push(value)
                elif action == 3:
                    delta = rng.randrange(-10, 11)
                    queue.add_offset(delta)
                    values[i] = [value + delta for value in values[i]]
                elif action == 4:
                    j = (i + rng.randrange(1, 4)) % 4
                    queue.meld(queues[j])
                    values[i].extend(values[j])
                    values[j] = []
                    self.assertEqual(len(queues[j]), 0)
                elif values[i]:
                    expected = min(values[i]) if ascending else max(values[i])
                    self.assertEqual(queue.top(), expected)
                    self.assertEqual(queue.pop(), expected)
                    values[i].remove(expected)
                self.assertEqual(len(queue), len(values[i]))
            queue = queues[0]
            queue.build([2, 3])
            with self.assertRaises(ValueError):
                queue.meld(queue)
            with self.assertRaises(ValueError):
                queue.meld(OffsetPriorityQueue(not ascending))
            self.assertEqual(sorted([queue.pop(), queue.pop()]), [2, 3])

    def test_deque_and_noncommutative_swag(self) -> None:
        rng = random.Random(0)
        queue = DoubleEndedQueue[str]()
        swag = SlidingWindowAggregation[str](lambda a, b: a + b)
        expected: deque[str] = deque()
        for _ in range(6000):
            action = rng.randrange(4)
            if action < 2:
                value = rng.choice('abc')
                if action == 0:
                    queue.appendleft(value)
                    swag.push_front(value)
                    expected.appendleft(value)
                else:
                    queue.append(value)
                    swag.push_back(value)
                    expected.append(value)
            elif expected:
                if action == 2:
                    self.assertEqual(queue.popleft(), expected.popleft())
                    swag.pop_front()
                else:
                    self.assertEqual(queue.pop(), expected.pop())
                    swag.pop_back()
            else:
                for operation in (queue.pop, queue.popleft, swag.pop_front, swag.pop_back, swag.all_prod):
                    with self.assertRaises(IndexError):
                        operation()
            self.assertEqual(len(queue), len(expected))
            self.assertEqual([queue[i] for i in range(len(queue))], list(expected))
            self.assertEqual(swag.is_empty(), not expected)
            if expected:
                self.assertEqual(swag.all_prod(), ''.join(expected))

    def test_radix_heap_large_keys(self) -> None:
        rng = random.Random(0)
        heap = RadixHeap[int](2**200 - 1)
        pending: dict[int, int] = {}
        for step in range(1600):
            if not pending or rng.randrange(3):
                key = heap.last() + rng.randrange(0, 40)
                pending[step] = key
                heap.push(key, step)
            else:
                key, value = heap.pop()
                self.assertEqual(key, min(pending.values()))
                self.assertEqual(pending.pop(value), key)
            self.assertEqual(len(heap), len(pending))
            with self.assertRaises(ValueError):
                heap.push(heap.last() - 1, -1)
        while pending:
            key, value = heap.pop()
            self.assertEqual(key, min(pending.values()))
            self.assertEqual(pending.pop(value), key)
        with self.assertRaises(IndexError):
            heap.pop()

    def test_persistent_heaps_share_versions(self) -> None:
        rng = random.Random(0)
        heap = PersistentLeftistHeap[int]()
        versions: list[tuple[int, list[int]]] = [(heap.empty(), [])]
        for _ in range(400):
            root, values = rng.choice(versions)
            action = rng.randrange(3)
            if action == 0:
                value = rng.randrange(-10, 11)
                versions.append((heap.push(root, value), sorted([*values, value])))
            elif action == 1:
                other, other_values = rng.choice(versions)
                if len(values) + len(other_values) < 80:
                    versions.append((heap.meld(root, other), sorted(values + other_values)))
            elif values:
                value, new_root = heap.pop(root)
                self.assertEqual(value, values[0])
                versions.append((new_root, values[1:]))
            for root, values in rng.sample(versions, min(5, len(versions))):
                for expected in values:
                    self.assertEqual(heap.top(root), expected)
                    value, root = heap.pop(root)
                    self.assertEqual(value, expected)
                self.assertTrue(heap.is_empty(root))

    def test_interval_set_matches_integer_set(self) -> None:
        rng = random.Random(0)
        intervals = IntervalSet()
        points: set[int] = set()
        for _ in range(2200):
            l, r = rng.randrange(-20, 21), rng.randrange(-20, 21)
            if rng.randrange(2):
                intervals.add(l, r)
                points.update(range(l, r))
            else:
                intervals.remove(l, r)
                points.difference_update(range(l, r))
            expected: list[tuple[int, int]] = []
            for point in sorted(points):
                if expected and expected[-1][1] == point:
                    expected[-1] = expected[-1][0], point + 1
                else:
                    expected.append((point, point + 1))
            self.assertEqual([intervals.get(i) for i in range(len(intervals))], expected)
            self.assertEqual(intervals.covered_count(), len(points))
            self.assertEqual(intervals.R, dict(expected))
            self.assertEqual(intervals.is_disjoint(l, r), not points.intersection(range(l, r)))
            self.assertIsNone(intervals.get(-1))
            self.assertIsNone(intervals.get(len(expected)))
            for point in range(-21, 22):
                self.assertEqual(intervals.contains(point), point in points)
                mex = point
                while mex in points:
                    mex += 1
                self.assertEqual(intervals.mex(point), mex)
        huge = 10**100
        intervals.add(huge, huge + 10)
        self.assertEqual(intervals.mex(huge), huge + 10)
        intervals.remove(huge + 1, huge + 9)
        self.assertEqual(intervals.mex(huge), huge + 1)

    def test_prefix_cancellation_and_build_validation(self) -> None:
        rng = random.Random(0)
        identity = (0, 1, 2, 3)

        def op(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(a[b[i]] for i in range(4))

        def cancel(whole: tuple[int, ...], prefix: tuple[int, ...]) -> tuple[int, ...]:
            inverse = tuple(prefix.index(i) for i in range(4))
            return op(inverse, whole)

        for n in range(20):
            cumulative = Cumulative(n, identity, op, cancel)
            for _ in range(3):
                values = [tuple(rng.sample(range(4), 4)) for _ in range(n)]
                cumulative.build(values)
                for l in range(n + 1):
                    expected = identity
                    for r in range(l, n + 1):
                        self.assertEqual(cumulative.prod(l, r), expected)
                        if r < n:
                            expected = op(expected, values[r])
                old = cumulative.cum[:]
                for bad in ([identity] * (n + 1), [identity] * (n - 1)):
                    if len(bad) == n:
                        continue
                    with self.assertRaises(ValueError):
                        cumulative.build(bad)
                    self.assertEqual(cumulative.cum, old)
        with self.assertRaises(ValueError):
            Cumulative(-1, 0, int.__add__, int.__sub__)

    def test_difference_arrays_and_rectangle_sums(self) -> None:
        rng = random.Random(0)
        for n in range(12):
            imos = Imos1D(n)
            expected = [0] * n
            for _ in range(60):
                l, r = sorted([rng.randrange(n + 1), rng.randrange(n + 1)])
                value = rng.randrange(-10, 11)
                imos.add(l, r, value)
                for i in range(l, r):
                    expected[i] += value
                self.assertEqual(imos.build(), expected)
                self.assertEqual(imos.build(), expected)
            for l, r in ((-1, n), (0, n + 1), (1, 0)):
                with self.assertRaises(AssertionError):
                    imos.add(l, r, 10)
                self.assertEqual(imos.build(), expected)
        for h, w in ((0, 0), (0, 4), (4, 0), (1, 1), (3, 4), (5, 6)):
            imos2 = Imos2D(h, w)
            cum = CumulativeSum2D(h, w)
            grid = [[0] * w for _ in range(h)]
            for _ in range(60):
                t, b = sorted([rng.randrange(h + 1), rng.randrange(h + 1)])
                l, r = sorted([rng.randrange(w + 1), rng.randrange(w + 1)])
                value = rng.randrange(-10, 11)
                imos2.add(t, l, b, r, value)
                for i in range(t, b):
                    for j in range(l, r):
                        grid[i][j] += value
                self.assertEqual(imos2.build(), grid)
                self.assertEqual(imos2.build(), grid)
                cum.build(grid)
                for _ in range(15):
                    t, b = sorted([rng.randrange(h + 1), rng.randrange(h + 1)])
                    l, r = sorted([rng.randrange(w + 1), rng.randrange(w + 1)])
                    self.assertEqual(cum.rectangle_sum(t, l, b, r), sum(sum(row[l:r]) for row in grid[t:b]))
            for bounds in ((-1, 0, h, w), (0, -1, h, w), (0, 0, h + 1, w), (0, 0, h, w + 1), (1, 0, 0, w), (0, 1, h, 0)):
                with self.assertRaises(AssertionError):
                    imos2.add(*bounds, 10)
                self.assertEqual(imos2.build(), grid)
        for ctor, args in ((Imos1D, (-1,)), (Imos2D, (-1, 2)), (Imos2D, (2, -1)), (CumulativeSum2D, (-1, 2)), (CumulativeSum2D, (2, -1))):
            with self.assertRaises(ValueError):
                ctor(*args)


if __name__ == '__main__':
    unittest.main()
