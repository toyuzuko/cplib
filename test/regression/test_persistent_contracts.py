import random
import unittest

from cplib.datastructure.persistent import (
    PartiallyPersistentArray, FullyPersistentArray, FullyPersistentDSU,
    FullyPersistentSegmentTree, FullyPersistentLazySegmentTree,
)


class PersistentContractsTest(unittest.TestCase):
    def test_partial_array_timestamps_and_boundaries(self) -> None:
        for n in (0, 1, 7):
            for automatic in (False, True):
                rng = random.Random(n)
                tree = PartiallyPersistentArray[int | None](n, auto_update=automatic)
                tree.build(tuple([None] * n))
                states: list[list[int | None]] = [[None] * n, [None] * n]
                last = 0
                for step in range(250):
                    if not n or step % 7 == 0:
                        last += 1
                        states.append(states[-1][:])
                        self.assertEqual(tree.update(), last)
                    else:
                        i = rng.randrange(n)
                        x = rng.choice([None, -1, 0, 5])
                        states[last + 1][i] = x
                        if automatic:
                            last += 1
                            states.append(states[-1][:])
                        self.assertEqual(tree.set(i, x), last)
                    t = rng.randrange(-1, last + 1)
                    self.assertEqual([tree.get(i, t) for i in range(n)], states[t + 1])
                for i in (-1, n):
                    with self.assertRaises(AssertionError):
                        tree.set(i, 3)
                    with self.assertRaises(AssertionError):
                        tree.get(i, last)
                if n:
                    for t in (-2, last + 1):
                        with self.assertRaises(AssertionError):
                            tree.get(0, t)
                with self.assertRaises(AssertionError):
                    tree.build([None] * n)
                self.assertEqual([tree.get(i, last) for i in range(n)], states[last + 1])
        tree = PartiallyPersistentArray(1, auto_update=False, init_val=0)
        for i in range(1000):
            tree.set(0, i)
        self.assertEqual(tree.get(0, -1), 0)
        self.assertEqual(tree.get(0, 0), 999)
        self.assertEqual(len(tree.data[0]), 2)

    def test_full_array_branching_and_none(self) -> None:
        for n in (0, 1, 2, 7, 65):
            for branching in (2, 3, 64):
                for automatic in (False, True):
                    rng = random.Random(n)
                    tree = FullyPersistentArray[int | None](n, branching, automatic)
                    initial: list[int | None] = [None] * n
                    tree.build(tuple(initial))
                    states = [initial[:], initial[:]]
                    last = 0
                    for step in range(180):
                        if not n or step % 11 == 0:
                            states.append(states[-1][:])
                            last += 1
                            self.assertEqual(tree.update(), last)
                        else:
                            t = rng.randrange(-1, last + 1)
                            i = rng.randrange(n)
                            x = rng.choice([None, -1, 0, 5])
                            changed = states[t + 1][:]
                            changed[i] = x
                            states[last + 1] = changed
                            if automatic:
                                last += 1
                                states.append(changed[:])
                            self.assertEqual(tree.set(i, x, t), last)
                        t = rng.randrange(-1, last + 1)
                        self.assertEqual([tree.get(i, t) for i in range(n)], states[t + 1])
                    for i in (-1, n):
                        with self.assertRaises(AssertionError):
                            tree.set(i, 3, last)
                    if n:
                        for t in (-2, last + 1):
                            before = len(tree.data), tree.roots[:]
                            with self.assertRaises(AssertionError):
                                tree.set(0, 3, t)
                            with self.assertRaises(AssertionError):
                                tree.get(0, t)
                            self.assertEqual((len(tree.data), tree.roots), before)

    def test_dsu_noop_branches(self) -> None:
        for automatic in (False, True):
            n = 8
            rng = random.Random(0)
            tree = FullyPersistentDSU(n, automatic)
            states = [list(range(n)), list(range(n))]
            last = 0
            for step in range(450):
                if step % 17 == 0:
                    states.append(states[-1][:])
                    last += 1
                    self.assertEqual(tree.update(), last)
                else:
                    t = rng.randrange(-1, last + 1)
                    x, y = rng.randrange(n), rng.randrange(n)
                    changed = states[t + 1][:]
                    a, b = changed[x], changed[y]
                    success = a != b
                    changed = [a if v == b else v for v in changed]
                    states[last + 1] = changed
                    if automatic:
                        states.append(changed[:])
                        last += 1
                    self.assertEqual(tree.merge(x, y, t), (success, last))
                for t in (-1, last, rng.randrange(-1, last + 1)):
                    roots = [tree.leader(i, t) for i in range(n)]
                    for i in range(n):
                        for j in range(n):
                            self.assertEqual(roots[i] == roots[j], states[t + 1][i] == states[t + 1][j])
            before = tree.last, tree.par_size.roots[:], len(tree.par_size.data)
            for x, y, t in ((-1, 0, last), (0, n, last), (0, 1, -2), (0, 1, last + 1)):
                with self.assertRaises(AssertionError):
                    tree.merge(x, y, t)
                self.assertEqual((tree.last, tree.par_size.roots, len(tree.par_size.data)), before)

    def test_persistent_segment_branches(self) -> None:
        for n in (0, 1, 2, 7, 17):
            for automatic in (False, True):
                rng = random.Random(n)
                tree = FullyPersistentSegmentTree(n, str.__add__, '', automatic)
                initial = [rng.choice('abc') for _ in range(n)]
                tree.build(tuple(initial))
                states = [initial[:], initial[:]]
                last = 0
                for step in range(300):
                    if not n or step % 11 == 0:
                        states.append(states[-1][:])
                        last += 1
                        self.assertEqual(tree.update(), last)
                    else:
                        t = rng.randrange(-1, last + 1)
                        p = rng.randrange(n)
                        value = rng.choice('abc')
                        changed = states[t + 1][:]
                        changed[p] = value
                        states[last + 1] = changed
                        if automatic:
                            states.append(changed[:])
                            last += 1
                        self.assertEqual(tree.set(p, value, t), last)
                    t = rng.randrange(-1, last + 1)
                    l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                    self.assertEqual(tree.prod(l, r, t), ''.join(states[t + 1][l:r]))
                    if n:
                        i = rng.randrange(n)
                        self.assertEqual(tree.get(i, t), states[t + 1][i])
                before = len(tree.data), tree.roots[:]
                with self.assertRaises(AssertionError):
                    tree.set(n, 'x', last)
                with self.assertRaises(AssertionError):
                    tree.prod(0, n, -2)
                with self.assertRaises(AssertionError):
                    tree.build(initial)
                self.assertEqual((len(tree.data), tree.roots), before)

    def test_lazy_copy_composition_and_readonly_queries(self) -> None:
        identity = (0, 1, 2)

        def mapping(f: tuple[int, ...], value: str) -> str:
            return ''.join('abc'[f[ord(c) - ord('a')]] for c in value)

        def composition(f: tuple[int, ...], g: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(f[g[i]] for i in range(3))

        for n in (0, 1, 2, 7, 17):
            for automatic in (False, True):
                rng = random.Random(n)
                tree = FullyPersistentLazySegmentTree(n, str.__add__, '', mapping, composition, identity, automatic)
                initial = [rng.choice('abc') for _ in range(n)]
                tree.build(tuple(initial))
                states = [initial[:], initial[:]]
                last = 0
                for step in range(450):
                    l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                    t = rng.randrange(-1, last + 1)
                    source = rng.randrange(-1, last + 1)
                    if step % 3 == 0:
                        states.append(states[-1][:])
                        last += 1
                        self.assertEqual(tree.update(), last)
                    else:
                        changed = states[t + 1][:]
                        f = tuple(rng.sample(range(3), 3))
                        if step % 3 == 1:
                            changed[l:r] = [mapping(f, x) for x in changed[l:r]]
                        else:
                            changed[l:r] = states[source + 1][l:r]
                        states[last + 1] = changed
                        if automatic:
                            states.append(changed[:])
                            last += 1
                        result = tree.range_apply(l, r, f, t) if step % 3 == 1 else tree.range_copy(l, r, t, source)
                        self.assertEqual(result, last)
                    before = len(tree.data), len(tree.lazy), len(tree.lt), len(tree.rt), tree.roots[:]
                    for t in (-1, last, rng.randrange(-1, last + 1)):
                        self.assertEqual(tree.prod(l, r, t), ''.join(states[t + 1][l:r]))
                    self.assertEqual((len(tree.data), len(tree.lazy), len(tree.lt), len(tree.rt), tree.roots), before)
                before = len(tree.data), tree.roots[:]
                for method, args in ((tree.range_apply, (-1, n, identity, last)), (tree.range_copy, (0, n, -2, last)), (tree.range_copy, (0, n, last, last + 1))):
                    with self.assertRaises(AssertionError):
                        method(*args)
                self.assertEqual((len(tree.data), tree.roots), before)

    def test_invalid_construction_and_unbuilt(self) -> None:
        for create in (lambda: PartiallyPersistentArray(-1), lambda: FullyPersistentArray(-1), lambda: FullyPersistentDSU(-1), lambda: FullyPersistentSegmentTree(-1, int.__add__, 0), lambda: FullyPersistentLazySegmentTree(-1, int.__add__, 0, int.__mul__, int.__mul__, 1)):
            with self.assertRaises(ValueError):
                create()
        for branching in (-1, 0, 1):
            with self.assertRaises(ValueError):
                FullyPersistentArray(2, branching)
        for tree in (PartiallyPersistentArray[int](1), FullyPersistentArray[int](1), FullyPersistentSegmentTree(1, int.__add__, 0), FullyPersistentLazySegmentTree(1, int.__add__, 0, int.__mul__, int.__mul__, 1)):
            with self.assertRaises(AssertionError):
                tree.update()
            with self.assertRaises(AssertionError):
                tree.build([])
            self.assertFalse(tree.built)
            tree.build([4])
            self.assertEqual(tree.last, 0)


if __name__ == '__main__':
    unittest.main()
