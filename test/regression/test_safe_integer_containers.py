import copy
import random
import sys
import unittest

from cplib.datastructure.hash import SafeIntegerDict, SafeIntegerSet


class SafeIntegerContainerTests(unittest.TestCase):
    def test_mapping_operations_and_views(self):
        rng = random.Random(0)
        actual = SafeIntegerDict[int]()
        expected: dict[int, int] = {}
        keys = actual.keys()
        items = actual.items()
        values = actual.values()
        domain = list(range(-25, 26)) + [-(1 << 1000), 1 << 1000]
        for _ in range(1500):
            key = rng.choice(domain)
            value = rng.randrange(1000)
            op = rng.randrange(8)
            if op == 0:
                actual[key] = expected[key] = value
            elif op == 1:
                actual.update({key: value})
                expected.update({key: value})
            elif op == 2:
                self.assertEqual(actual.setdefault(key, value), expected.setdefault(key, value))
            elif op == 3:
                self.assertEqual(actual.pop(key, None), expected.pop(key, None))
            elif op == 4:
                if key in expected:
                    del actual[key]
                    del expected[key]
                else:
                    with self.assertRaises(KeyError) as error:
                        del actual[key]
                    self.assertEqual(error.exception.args, (key,))
            elif op == 5:
                actual |= [(key, value)]
                expected |= [(key, value)]
            elif op == 6:
                if expected:
                    self.assertEqual(actual.popitem(), expected.popitem())
                else:
                    with self.assertRaises(KeyError):
                        actual.popitem()
            else:
                self.assertEqual(actual.get(key), expected.get(key))
                if key not in expected:
                    with self.assertRaises(KeyError) as error:
                        actual.pop(key)
                    self.assertEqual(error.exception.args, (key,))
            self.assertEqual(actual, expected)
            self.assertEqual(expected, actual)
            self.assertEqual(list(keys), list(expected))
            self.assertEqual(list(items), list(expected.items()))
            self.assertEqual(list(values), list(expected.values()))
            self.assertEqual(list(reversed(actual)), list(reversed(expected)))
        for clone in [actual.copy(), copy.copy(actual), SafeIntegerDict(actual), SafeIntegerDict(actual.items())]:
            self.assertEqual(clone, expected)
            clone.clear()
            self.assertEqual(actual, expected)
        self.assertEqual(actual | {123: 7}, expected | {123: 7})
        self.assertEqual({123: 7} | actual, {123: 7} | expected)
        self.assertEqual(SafeIntegerDict.fromkeys([1, 2]), {1: None, 2: None})
        shared = []
        by_keys = SafeIntegerDict.fromkeys([1, 2, 1], shared)
        self.assertIs(by_keys[1], shared)
        self.assertIs(by_keys[2], shared)
        self.assertEqual(dict(actual), expected)
        self.assertEqual(repr(actual), repr(expected))
        self.assertNotIsInstance(actual, dict)
        self.assertNotIn('1', actual)
        with self.assertRaises(TypeError):
            actual['1'] = 2
        recursive = SafeIntegerDict[object]()
        recursive[0] = recursive
        self.assertEqual(repr(recursive), '{0: {...}}')

    def test_set_operations(self):
        rng = random.Random(1)
        actual = SafeIntegerSet()
        expected: set[int] = set()
        domain = list(range(-25, 26)) + [-(1 << 1000), 1 << 1000]
        for _ in range(1500):
            key = rng.choice(domain)
            other = rng.choices(domain, k=rng.randrange(15))
            op = rng.randrange(9)
            if op == 0:
                self.assertIsNone(actual.add(key))
                expected.add(key)
            elif op == 1:
                self.assertIsNone(actual.discard(key))
                expected.discard(key)
            elif op == 2:
                if key in expected:
                    self.assertIsNone(actual.remove(key))
                    expected.remove(key)
                else:
                    with self.assertRaises(KeyError) as error:
                        actual.remove(key)
                    self.assertEqual(error.exception.args, (key,))
            elif op == 3:
                actual.update(other)
                expected.update(other)
            elif op == 4:
                actual.intersection_update(iter(other))
                expected.intersection_update(other)
            elif op == 5:
                actual.difference_update(iter(other))
                expected.difference_update(other)
            elif op == 6:
                actual.symmetric_difference_update(iter(other))
                expected.symmetric_difference_update(other)
            elif op == 7:
                if expected:
                    removed = actual.pop()
                    self.assertIn(removed, expected)
                    expected.remove(removed)
                else:
                    with self.assertRaises(KeyError):
                        actual.pop()
            else:
                actual |= SafeIntegerSet(other)
                expected |= set(other)
            self.assertEqual(actual, expected)
            self.assertEqual(expected, actual)
            self.assertEqual(set(actual), expected)
            safe_other = SafeIntegerSet(other)
            ordinary = set(other)
            self.assertEqual(actual | safe_other, expected | ordinary)
            self.assertEqual(actual & safe_other, expected & ordinary)
            self.assertEqual(actual - safe_other, expected - ordinary)
            self.assertEqual(actual ^ safe_other, expected ^ ordinary)
            self.assertEqual(ordinary | actual, ordinary | expected)
            self.assertEqual(ordinary & actual, ordinary & expected)
            self.assertEqual(ordinary - actual, ordinary - expected)
            self.assertEqual(ordinary ^ actual, ordinary ^ expected)
            self.assertEqual(actual <= safe_other, expected <= ordinary)
            self.assertEqual(actual >= safe_other, expected >= ordinary)
            self.assertEqual(actual < safe_other, expected < ordinary)
            self.assertEqual(actual > safe_other, expected > ordinary)
            self.assertEqual(actual.issubset(iter(other)), expected.issubset(other))
            self.assertEqual(actual.issuperset(iter(other)), expected.issuperset(other))
            self.assertEqual(actual.isdisjoint(iter(other)), expected.isdisjoint(other))
            self.assertEqual(actual.union(other), expected.union(other))
            self.assertEqual(actual.intersection(other), expected.intersection(other))
            self.assertEqual(actual.difference(other), expected.difference(other))
            self.assertEqual(actual.symmetric_difference(other), expected.symmetric_difference(other))
            for name in ['__ior__', '__iand__', '__isub__', '__ixor__']:
                changed = actual.copy()
                reference = expected.copy()
                self.assertIs(getattr(changed, name)(safe_other), changed)
                getattr(reference, name)(ordinary)
                self.assertEqual(changed, reference)
        cloned = copy.copy(actual)
        cloned.clear()
        self.assertEqual(actual, expected)
        self.assertNotIsInstance(actual, set)
        for method in ['update', 'intersection_update']:
            s = SafeIntegerSet([1, 2, 3])
            getattr(s, method)(s)
            self.assertEqual(s, {1, 2, 3})
        for method in ['difference_update', 'symmetric_difference_update']:
            s = SafeIntegerSet([1, 2, 3])
            getattr(s, method)(s)
            self.assertEqual(s, set())
        self.assertIsNone(actual.discard('1'))
        self.assertEqual(actual.union(), actual)
        self.assertEqual(actual.intersection(), actual)
        self.assertEqual(actual.difference(), actual)

    def test_hash_collisions_and_encoding(self):
        old_keys = [i * sys.hash_info.modulus * (1 << 31) for i in range(100)]
        self.assertEqual(len({hash(key ^ 12345) for key in old_keys}), 1)
        domain = old_keys + [sign * (1 << bits) + delta for bits in [0, 7, 8, 15, 16, 63, 64, 1000, 20000] for sign in [-1, 1] for delta in [-1, 0, 1]]
        mapping = SafeIntegerDict((key, i) for i, key in enumerate(domain))
        elements = SafeIntegerSet(domain)
        self.assertEqual(dict(mapping), dict((key, i) for i, key in enumerate(domain)))
        self.assertEqual(set(elements), set(domain))
        self.assertGreater(len({hash(encoded) for encoded in mapping._data}), 90)
        self.assertGreater(len({hash(encoded) for encoded in elements._data}), 90)
        for sign in [-1, 1]:
            for offset in range(-3, 4):
                key = (sign * sys.hash_info.modulus + offset) ^ mapping.b
                mapping[key] = key
                self.assertEqual(mapping[key], key)
                key = (sign * sys.hash_info.modulus + offset) ^ elements.b
                elements.add(key)
                self.assertIn(key, elements)
                elements.remove(key)
                self.assertNotIn(key, elements)
        mapping[True] = -1
        elements.add(True)
        self.assertEqual(mapping[1], -1)
        self.assertIn(1, elements)
        for container in [mapping, elements]:
            self.assertEqual(copy.deepcopy(container), container)


if __name__ == '__main__':
    unittest.main()
