import random
import unittest

from cplib.datastructure.linkedlist import DoublyLinkedList, SpliceableLinkedLists


class LinkedListContractTests(unittest.TestCase):
    def test_handles_and_mixed_operations(self):
        rng = random.Random(0)
        actual = DoublyLinkedList[int | None]()
        expected: list[tuple[int, int | None]] = []
        erased: list[int] = []
        for _ in range(2500):
            value = rng.choice([None, -2, -1, 0, 1, 2])
            op = rng.randrange(7)
            if op == 0:
                actual.insert_front(value)
                expected.insert(0, (actual.front_node(), value))
            elif op == 1:
                expected.append((actual.append(value), value))
            elif op == 2:
                index = rng.randrange(len(expected) + 1)
                pos = expected[index][0] if index < len(expected) else 0
                handle = actual.insert_before(pos, value)
                expected.insert(index, (handle, value))
            elif op == 3 and expected:
                index = rng.randrange(len(expected))
                node, old = expected.pop(index)
                nxt = expected[index][0] if index < len(expected) else 0
                self.assertEqual(actual.erase(node), (old, nxt))
                erased.append(node)
            elif op in (4, 5):
                if expected:
                    node, old = expected.pop(0 if op == 4 else -1)
                    self.assertEqual(actual.pop_front() if op == 4 else actual.pop_back(), old)
                    erased.append(node)
                else:
                    with self.assertRaises(IndexError):
                        actual.pop_front() if op == 4 else actual.pop_back()
            else:
                index = next((i for i, (_, old) in enumerate(expected) if old == value), -1)
                self.assertEqual(actual.discard_first(value), index >= 0)
                if index >= 0:
                    erased.append(expected.pop(index)[0])
            self.assertEqual(actual.to_list(), [v for _, v in expected])
            self.assertEqual(len(actual), len(expected))
            self.assertEqual(actual.size(), len(expected))
            self.assertEqual(actual.front_node(), expected[0][0] if expected else 0)
            self.assertEqual(actual.back_node(), expected[-1][0] if expected else 0)
            self.assertEqual(actual.next_node(0), actual.front_node())
            self.assertEqual(actual.prev_node(0), actual.back_node())
            for i, (node, old) in enumerate(expected):
                self.assertEqual(actual.value(node), old)
                self.assertEqual(actual.prev_node(node), expected[i - 1][0] if i else 0)
                self.assertEqual(actual.next_node(node), expected[i + 1][0] if i + 1 < len(expected) else 0)
            if erased:
                node = rng.choice(erased)
                before = actual.to_list()
                for method in [actual.value, actual.erase, actual.next_node, actual.prev_node]:
                    with self.assertRaises(ValueError):
                        method(node)
                with self.assertRaises(ValueError):
                    actual.insert_before(node, 7)
                self.assertEqual(actual.to_list(), before)
        for node in [-1, -1000, 10**9]:
            for method in [actual.value, actual.erase, actual.next_node, actual.prev_node]:
                with self.assertRaises(ValueError):
                    method(node)
            with self.assertRaises(ValueError):
                actual.insert_before(node, 7)
        for method in [actual.value, actual.erase]:
            with self.assertRaises(ValueError):
                method(0)

    def test_front_occurrence_and_invalid_values(self):
        rng = random.Random(1)
        actual = DoublyLinkedList[int | None]()
        expected: list[int | None] = []
        for _ in range(4000):
            value = rng.choice([None, -2, -1, 0, 1, 2])
            op = rng.randrange(4)
            if op == 0:
                actual.insert_front(value)
                expected.insert(0, value)
            elif op == 1:
                present = value in expected
                self.assertEqual(actual.discard_first(value), present)
                if present:
                    expected.remove(value)
            elif expected:
                self.assertEqual(actual.pop_front() if op == 2 else actual.pop_back(), expected.pop(0 if op == 2 else -1))
            self.assertEqual(actual.to_list(), expected)
        before = actual.to_list()
        for method in [actual.insert_front, actual.append, lambda v: actual.insert_before(0, v)]:
            with self.assertRaises(TypeError):
                method([])
            self.assertEqual(actual.to_list(), before)
            self.assertEqual(len(actual), len(before))
        actual.insert_front(None)
        self.assertEqual(actual.to_list(), [None] + before)

    def test_splicing(self):
        rng = random.Random(2)
        actual = SpliceableLinkedLists[int | None](8)
        expected: list[list[int | None]] = [[] for _ in range(8)]
        handles: set[int] = set()
        for _ in range(2000):
            index = rng.randrange(8)
            if rng.randrange(2):
                value = rng.choice([None, -1, 0, 1])
                handle = actual.append(index, value)
                self.assertNotIn(handle, handles)
                handles.add(handle)
                expected[index].append(value)
            else:
                target = rng.randrange(8)
                actual.splice_back(index, target)
                if target != index:
                    expected[target].extend(expected[index])
                    expected[index].clear()
            self.assertEqual(len(actual), sum(map(len, expected)))
            for i in range(8):
                self.assertEqual(actual.to_list(i), expected[i])
                self.assertEqual(actual.list_size(i), len(expected[i]))
        for index in [-1, 8, 10**9]:
            for method in [actual.to_list, actual.list_size, lambda i: actual.append(i, None), lambda i: actual.splice_back(i, 0), lambda i: actual.splice_back(0, i)]:
                with self.assertRaises(IndexError):
                    method(index)
                self.assertEqual(len(actual), len(handles))
                self.assertEqual([actual.to_list(i) for i in range(8)], expected)
        with self.assertRaises(ValueError):
            SpliceableLinkedLists(-1)
        empty = SpliceableLinkedLists(0)
        self.assertEqual(len(empty), 0)
        with self.assertRaises(IndexError):
            empty.append(0, 0)
        self.assertEqual(len(empty), 0)


if __name__ == '__main__':
    unittest.main()
