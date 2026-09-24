import random
import unittest

from cplib.datastructure.avltree import ImplicitAVLTree, PersistentImplicitAVLTree
from cplib.datastructure.treap import ImplicitTreap, SegmentedImplicitTreap
from cplib.datastructure.wbtree import ImplicitWeightBalancedTree, PersistentImplicitWeightBalancedTree


IDENTITY = (0, 1, 2)


def mapping(f: tuple[int, ...], value: str) -> str:
    return ''.join('abc'[f[ord(ch) - ord('a')]] for ch in value)


def composition(f: tuple[int, ...], g: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(f[g[i]] for i in range(3))


class ImplicitSequenceContractsTest(unittest.TestCase):
    def test_commutative_fast_path_with_affine_updates(self) -> None:
        mod = 998244353

        def op(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
            return (a[0] + b[0]) % mod, a[1] + b[1]

        def apply(f: tuple[int, int], a: tuple[int, int]) -> tuple[int, int]:
            return (f[0] * a[0] + f[1] * a[1]) % mod, a[1]

        def compose(f: tuple[int, int], g: tuple[int, int]) -> tuple[int, int]:
            return f[0] * g[0] % mod, (f[0] * g[1] + f[1]) % mod

        for cls in (ImplicitTreap, ImplicitAVLTree, ImplicitWeightBalancedTree, PersistentImplicitAVLTree, PersistentImplicitWeightBalancedTree):
            for commutative in (False, True):
                rng = random.Random(0)
                tree = cls(op, (0, 0), apply, compose, (1, 0), commutative=commutative)
                persistent = cls.__name__.startswith('Persistent')
                values = list(range(20))
                if persistent:
                    root = tree.new_root([(v, 1) for v in values])
                else:
                    tree.build([(v, 1) for v in values])
                for _ in range(500):
                    l, r = sorted([rng.randrange(len(values) + 1), rng.randrange(len(values) + 1)])
                    action = rng.randrange(5)
                    if action == 0:
                        value = rng.randrange(10)
                        if persistent:
                            root = tree.insert(root, l, (value, 1))
                        else:
                            tree.insert(l, (value, 1))
                        values.insert(l, value)
                    elif action == 1 and values:
                        pos = rng.randrange(len(values))
                        if persistent:
                            root = tree.erase(root, pos)
                        else:
                            tree.erase(pos)
                        values.pop(pos)
                    elif action == 2:
                        if persistent:
                            root = tree.reverse(root, l, r)
                        else:
                            tree.reverse(l, r)
                        values[l:r] = reversed(values[l:r])
                    elif action == 3:
                        f = rng.randrange(5), rng.randrange(5)
                        if persistent:
                            root = tree.range_apply(root, l, r, f)
                        else:
                            tree.range_apply(l, r, f)
                        values[l:r] = [(f[0] * v + f[1]) % mod for v in values[l:r]]
                    else:
                        result = tree.prod(root, l, r)[0] if persistent else tree.prod(l, r)
                        self.assertEqual(result, (sum(values[l:r]) % mod, r - l))
                    result = tree.prod(root, 0, len(values))[0] if persistent else tree.prod(0, len(values))
                    self.assertEqual(result, (sum(values) % mod, len(values)))
                    self.assertEqual(tree._racc == [], commutative)
                if not persistent:
                    tree.build([])
                    tree.insert(0, (3, 1))
                    self.assertEqual(tree.prod(0, 1), (3, 1))
                    self.assertEqual(tree._racc == [], commutative)

    def test_mutable_reverse_updates_and_build(self) -> None:
        for cls in (ImplicitTreap, ImplicitAVLTree, ImplicitWeightBalancedTree):
            rng = random.Random(0)
            tree = cls(str.__add__, '', mapping, composition, IDENTITY)
            values: list[str] = []
            for step in range(1400):
                operation = rng.randrange(6)
                l, r = sorted([rng.randrange(len(values) + 1), rng.randrange(len(values) + 1)])
                if operation == 0:
                    values = [rng.choice('abc') for _ in range(rng.randrange(35))]
                    tree.build(values)
                elif operation == 1:
                    value = rng.choice('abc')
                    tree.insert(l, value)
                    values.insert(l, value)
                elif operation == 2 and values:
                    pos = rng.randrange(len(values))
                    tree.erase(pos)
                    values.pop(pos)
                elif operation == 3:
                    tree.reverse(l, r)
                    values[l:r] = reversed(values[l:r])
                elif operation == 4:
                    f = tuple(rng.sample(range(3), 3))
                    tree.range_apply(l, r, f)
                    values[l:r] = [mapping(f, v) for v in values[l:r]]
                else:
                    self.assertEqual(tree.prod(l, r), ''.join(values[l:r]), (cls.__name__, step))
                self.assertEqual(tree.size(), len(values))
                self.assertEqual(tree.prod(0, len(values)), ''.join(values), (cls.__name__, step))
                self.assertEqual(list(tree.iter()), values)
                if values:
                    pos = rng.randrange(len(values))
                    self.assertEqual(tree.get(pos), values[pos])
            tree.build([])
            self.assertEqual(tree.size(), 0)
            self.assertEqual(tree.prod(0, 0), '')

    def test_invalid_ranges_leave_mutable_sequences_unchanged(self) -> None:
        for cls in (ImplicitTreap, ImplicitAVLTree, ImplicitWeightBalancedTree):
            tree = cls(str.__add__, '', mapping, composition, IDENTITY)
            tree.build(list('abc'))
            for pos in (-1, 3, 4):
                for operation in (tree.get, tree.erase):
                    with self.assertRaises(IndexError):
                        operation(pos)
            for pos in (-1, 4):
                with self.assertRaises(IndexError):
                    tree.insert(pos, 'a')
            for l, r in ((-1, 2), (0, 4), (2, 1)):
                for operation in (lambda: tree.reverse(l, r), lambda: tree.prod(l, r),
                                  lambda: tree.range_apply(l, r, (2, 1, 0))):
                    with self.assertRaises(IndexError):
                        operation()
                    self.assertEqual(list(tree.iter()), list('abc'))
            for i in range(4):
                tree.reverse(i, i)
                tree.range_apply(i, i, (2, 1, 0))
                self.assertEqual(tree.prod(i, i), '')
            self.assertEqual(tree.prod(0, 3), 'abc')

    def test_persistent_branches_and_allocation_free_iteration(self) -> None:
        for cls in (PersistentImplicitAVLTree, PersistentImplicitWeightBalancedTree):
            rng = random.Random(0)
            tree = cls(str.__add__, '', mapping, composition, IDENTITY)
            root = tree.new_root(list('abcabc'))
            versions = [(root, list('abcabc'))]
            for step in range(500):
                root, old = rng.choice(versions)
                values = old[:]
                l, r = sorted([rng.randrange(len(values) + 1), rng.randrange(len(values) + 1)])
                operation = rng.randrange(7)
                if operation == 0:
                    value = rng.choice('abc')
                    root = tree.insert(root, l, value)
                    values.insert(l, value)
                elif operation == 1 and values:
                    pos = rng.randrange(len(values))
                    root = tree.erase(root, pos)
                    values.pop(pos)
                elif operation == 2:
                    root = tree.reverse(root, l, r)
                    values[l:r] = reversed(values[l:r])
                elif operation == 3:
                    f = tuple(rng.sample(range(3), 3))
                    root = tree.range_apply(root, l, r, f)
                    values[l:r] = [mapping(f, v) for v in values[l:r]]
                elif operation == 4:
                    value, root = tree.prod(root, l, r)
                    self.assertEqual(value, ''.join(values[l:r]), (cls.__name__, step))
                elif operation == 5:
                    a, b = tree.split(root, l)
                    root = tree.merge(b, a)
                    values = values[l:] + values[:l]
                elif values and len(values) < 40:
                    root = tree.merge(root, root)
                    values += values
                versions.append((root, values))
                self.assertEqual(tree.prod(root, 0, len(values))[0], ''.join(values))
                for past_root, expected in rng.sample(versions, min(5, len(versions))):
                    before = len(tree.val)
                    self.assertEqual(list(tree.iter(past_root)), expected)
                    self.assertEqual(tree.to_list(past_root), expected)
                    self.assertEqual(len(tree.val), before)
                    if expected:
                        pos = rng.randrange(len(expected))
                        value, equivalent = tree.get(past_root, pos)
                        self.assertEqual(value, expected[pos])
                        self.assertEqual(tree.to_list(equivalent), expected)

    def test_implicit_treap_reuses_removed_nodes(self) -> None:
        tree = ImplicitTreap(str.__add__, '', mapping, composition, IDENTITY)
        for _ in range(3000):
            tree.insert(0, 'a')
            tree.erase(0)
        self.assertEqual(len(tree.val), 2)
        tree.build([])
        self.assertEqual(len(tree.val), 1)
        tree.insert(0, 'b')
        self.assertEqual(list(tree.iter()), ['b'])

    def test_segmented_split_preserves_heap_and_values(self) -> None:
        rng = random.Random(0)
        tree = SegmentedImplicitTreap(str.__add__, '', lambda n, v: n * v,
                                     lambda f, prod, n, value: (mapping(f, prod), mapping(f, value)), composition, IDENTITY)
        root = tree.new_root(30, 'a')
        values = list('a' * 30)
        for step in range(1200):
            l, r = sorted([rng.randrange(len(values) + 1), rng.randrange(len(values) + 1)])
            operation = rng.randrange(5)
            if operation == 0:
                a, b = tree.split(root, l)
                root = tree.merge(b, a)
                values = values[l:] + values[:l]
            elif operation == 1:
                f = tuple(rng.sample(range(3), 3))
                root = tree.range_apply(root, l, r, f)
                values[l:r] = [mapping(f, v) for v in values[l:r]]
            elif operation == 2 and len(values) < 70:
                n, value = rng.randrange(5), rng.choice('abc')
                a, b = tree.split(root, l)
                root = tree.merge(tree.merge(a, tree.new_root(n, value)), b)
                values[l:l] = [value] * n
            elif operation == 3:
                a, rest = tree.split(root, l)
                _, b = tree.split(rest, r - l)
                root = tree.merge(a, b)
                del values[l:r]
            else:
                result, root = tree.prod(root, l, r)
                self.assertEqual(result, ''.join(values[l:r]))
            self.assertEqual(tree.subtree_prod[root], ''.join(values), step)
            self.assertEqual(tree.subtree_len[root], len(values))
            stack = [root] if root else []
            seen: set[int] = set()
            while stack:
                node = stack.pop()
                self.assertNotIn(node, seen)
                seen.add(node)
                for child in (tree.lc[node], tree.rc[node]):
                    if child:
                        self.assertLessEqual(tree.prio[child], tree.prio[node], step)
                        stack.append(child)
        self.assertEqual(tree.new_root(0, 'a'), 0)
        if root:
            with self.assertRaises(ValueError):
                tree.merge(root, root)


if __name__ == '__main__':
    unittest.main()
