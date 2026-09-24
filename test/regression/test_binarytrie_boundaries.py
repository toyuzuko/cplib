import bisect
import random
import unittest

from cplib.datastructure.binarytrie import BinaryTrie, MergeableBinaryTrie, RangeSortRangeProd


class BinaryTrieBoundariesTest(unittest.TestCase):
    def test_xor_and_order_statistics(self) -> None:
        rng = random.Random(0)
        for bitlen in (0, 1, 3, 7):
            trie = BinaryTrie(bitlen)
            values: set[int] = set()
            limit = 1 << bitlen
            for _ in range(700):
                x = rng.randrange(limit)
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
                self.assertEqual([trie[i] for i in range(len(trie))], ordered)
                for x in (-1, 0, rng.randrange(limit), limit):
                    self.assertEqual(x in trie, x in values)
                    self.assertEqual(trie.bisect_left(x), bisect.bisect_left(ordered, x))
                    self.assertEqual(trie.bisect_right(x), bisect.bisect_right(ordered, x))
                for i in (-1, len(values)):
                    with self.assertRaises(IndexError):
                        trie[i]
                for x in (-1, limit):
                    with self.assertRaises(ValueError):
                        trie.all_xor(x)
                    self.assertEqual([trie[i] for i in range(len(trie))], ordered)
            trie = BinaryTrie(bitlen)
            with self.assertRaises(IndexError):
                trie.min()
            with self.assertRaises(IndexError):
                trie.max()
        with self.assertRaises(ValueError):
            BinaryTrie(-1)

    def test_merge_split_deleted_keys_and_reverse_products(self) -> None:
        rng = random.Random(0)
        for bitlen in (0, 1, 4):
            for reverse in (False, True):
                trie = MergeableBinaryTrie(bitlen, str.__add__, '', calc_reverse=reverse)
                roots = [trie.new_trie() for _ in range(4)]
                maps: list[dict[int, str]] = [{} for _ in roots]
                limit = 1 << bitlen
                for step in range(700):
                    i = rng.randrange(len(roots))
                    root = roots[i]
                    x = rng.randrange(limit)
                    operation = rng.randrange(6)
                    if operation < 2:
                        val = rng.choice('abc')
                        update = bool(operation)
                        self.assertEqual(trie.add(root, x, val, update), x not in maps[i])
                        if update or x not in maps[i]:
                            maps[i][x] = val
                    elif operation == 2:
                        self.assertEqual(trie.discard(root, x), x in maps[i])
                        maps[i].pop(x, None)
                    elif operation == 3 and len(roots) > 1:
                        j = (i + rng.randrange(1, len(roots))) % len(roots)
                        roots[i] = trie.merge(root, roots[j])
                        maps[i] = {**maps[j], **maps[i]}
                        roots.pop(j)
                        maps.pop(j)
                    elif operation >= 4 and len(roots) < 8:
                        boundary = rng.randrange(limit + 1)
                        if operation == 4 and maps[i]:
                            boundary = rng.choice(list(maps[i]))
                            left, right = trie.split(root, boundary)
                        else:
                            left, right = trie.safe_split(root, boundary)
                        roots[i] = left
                        roots.append(right)
                        maps.append({k: v for k, v in maps[i].items() if k >= boundary})
                        maps[i] = {k: v for k, v in maps[i].items() if k < boundary}
                    self.assertEqual(len(trie), sum(len(m) for m in maps))
                    for root, values in zip(roots, maps):
                        items = sorted(values.items())
                        self.assertEqual(trie.size(root), len(items), (bitlen, step))
                        self.assertEqual([trie.get(root, i) for i in range(len(items))], items, (bitlen, step))
                        self.assertEqual(trie.prod(root), (''.join(v for _, v in items), ''.join(v for _, v in reversed(items)) if reverse else ''))
                        self.assertFalse(trie.contains(root, -1))
                        self.assertFalse(trie.contains(root, limit))
                    self.assertEqual(trie.ptr[:3], [0, 0, 0])

    def test_root_validation_and_self_merge(self) -> None:
        trie = MergeableBinaryTrie(3, int.__add__, 0)
        root = trie.new_trie()
        trie.add(root, 2, 9)
        for invalid in (-1, 0, len(trie.cnt_type), len(trie.cnt_type) + 10):
            operations = (lambda: trie.add(invalid, 1, 2), lambda: trie.contains(invalid, 1),
                          lambda: trie.index(invalid, 1), lambda: trie.bisect_left(invalid, 1),
                          lambda: trie.size(invalid), lambda: trie.prod(invalid),
                          lambda: trie.split(invalid, 1), lambda: trie.safe_split(invalid, 1),
                          lambda: trie.get(invalid, 0), lambda: trie.merge(root, invalid),
                          lambda: trie.merge(invalid, root))
            for operation in operations:
                with self.assertRaises(ValueError):
                    operation()
                self.assertEqual(trie.get(root, 0), (2, 9))
        with self.assertRaises(ValueError):
            trie.merge(root, root)
        self.assertEqual(trie.get(root, 0), (2, 9))
        for k in (-1, 1):
            with self.assertRaises(IndexError):
                trie.get(root, k)
        with self.assertRaises(ValueError):
            MergeableBinaryTrie(-1, int.__add__, 0)


class RangeSortDistinctKeysTest(unittest.TestCase):
    def test_unique_key_validation_and_atomic_updates(self) -> None:
        for n, keys, vals, bits in ((2, [1, 1], ['a', 'b'], 3), (2, [1], ['a', 'b'], 3),
                                   (2, [1, 2], ['a'], 3), (1, [-1], ['a'], 3),
                                   (1, [8], ['a'], 3), (-1, [], [], 3), (0, [], [], -1)):
            with self.assertRaises(ValueError):
                RangeSortRangeProd(n, keys, vals, bits, str.__add__, '')
        tree = RangeSortRangeProd(4, [3, 1, 4, 2], ['c', 'a', 'd', 'b'], 3, str.__add__, '')
        tree.sort(0, 4, reverse=True)
        expected = [(4, 'd'), (3, 'c'), (2, 'b'), (1, 'a')]
        node_count = len(tree.trie.cnt_type)
        for key in (-1, 8, 3):
            with self.assertRaises(ValueError):
                tree.set(0, key, 'X')
            self.assertEqual([tree.get(i) for i in range(4)], expected)
            self.assertEqual(tree.all_prod(), 'dcba')
            self.assertEqual(len(tree.trie.cnt_type), node_count)
        tree.set(0, 4, 'X')
        self.assertEqual(tree.all_prod(), 'Xcba')
        tree.set(0, 7, 'Y')
        tree.set(3, 4, 'Z')
        self.assertEqual([tree.get(i) for i in range(4)], [(7, 'Y'), (3, 'c'), (2, 'b'), (4, 'Z')])
        tree.sort(0, 4)
        self.assertEqual(tree.all_prod(), 'bcZY')

    def test_updates_sorts_and_noncommutative_products(self) -> None:
        rng = random.Random(0)
        for n in (0, 1, 2, 10, 30):
            keys = rng.sample(range(128), n)
            expected = [(key, rng.choice('abc')) for key in keys]
            tree = RangeSortRangeProd(n, keys, [v for _, v in expected], 7, str.__add__, '')
            for _ in range(600):
                operation = rng.randrange(4)
                l, r = sorted([rng.randrange(n + 1), rng.randrange(n + 1)])
                if operation == 0 and n:
                    i = rng.randrange(n)
                    used = {k for k, _ in expected}
                    key = rng.choice([k for k in range(128) if k not in used] + [expected[i][0]])
                    val = rng.choice('abc')
                    tree.set(i, key, val)
                    expected[i] = key, val
                elif operation == 1:
                    reverse = bool(rng.randrange(2))
                    tree.sort(l, r, reverse)
                    expected[l:r] = sorted(expected[l:r], reverse=reverse)
                else:
                    self.assertEqual(tree.prod(l, r), ''.join(v for _, v in expected[l:r]))
                self.assertEqual(tree.all_prod(), ''.join(v for _, v in expected))
                self.assertEqual([tree.get(i) for i in range(n)], expected)
        tree = RangeSortRangeProd(1, [0], ['a'], 0, str.__add__, '')
        tree.set(0, 0, 'b')
        tree.sort(0, 1, True)
        self.assertEqual(tree.prod(0, 1), 'b')

    def test_replacing_singletons_reuses_nodes(self) -> None:
        tree = RangeSortRangeProd(1, [0], [1], 12, int.__add__, 0)
        initial_size = len(tree.trie.cnt_type)
        for key in range(1, 2000):
            tree.set(0, key, key)
            self.assertEqual(tree.get(0), (key, key))
            self.assertEqual(tree.all_prod(), key)
            self.assertEqual(len(tree.trie.cnt_type), initial_size)


if __name__ == '__main__':
    unittest.main()
