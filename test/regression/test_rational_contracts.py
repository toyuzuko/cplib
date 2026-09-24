from fractions import Fraction
from itertools import product
import random
import unittest

from cplib.mathematics.rational import Rational, SternBrocotTree


def as_fraction(value):
    value.ensure_normalized()
    return Fraction(value.num, value.den) if value.den else (float('inf') if value.num > 0 else -float('inf'))


class RationalContractTests(unittest.TestCase):
    def test_finite_arithmetic(self):
        rng = random.Random(0)
        for _ in range(2500):
            a, b, c, d = [rng.randrange(-100, 101) for _ in range(4)]
            b = b or 1
            d = d or 1
            left = Rational(a, b, _should_normalize=False)
            right = Rational(c, d, _should_normalize=False)
            x, y = Fraction(a, b), Fraction(c, d)
            added, subtracted, multiplied = left + right, left - right, left * right
            self.assertEqual(added.sign(), (x + y > 0) - (x + y < 0))
            self.assertEqual(subtracted.sign(), (x - y > 0) - (x - y < 0))
            self.assertEqual(multiplied.sign(), (x * y > 0) - (x * y < 0))
            self.assertEqual(as_fraction(added), x + y)
            self.assertEqual(as_fraction(subtracted), x - y)
            self.assertEqual(as_fraction(multiplied), x * y)
            if c:
                quotient = left / right
                self.assertEqual(quotient.sign(), (x / y > 0) - (x / y < 0))
                self.assertEqual(as_fraction(quotient), x / y)
            self.assertEqual(left < right, x < y)
            self.assertEqual(left <= right, x <= y)
            self.assertEqual(left > right, x > y)
            self.assertEqual(left >= right, x >= y)
            self.assertEqual(left == right, x == y)
            self.assertEqual(left != right, x != y)
            self.assertEqual(hash(left), hash(Rational(a * 3, b * 3)))
            self.assertEqual(str(left), str(x))
            self.assertEqual(as_fraction(-left), -x)
        huge = 1 << 1000
        self.assertEqual(as_fraction(Rational(huge, 3) / Rational(-huge, 7)), Fraction(-7, 3))
        self.assertFalse(Rational(1, 2) == object())

    def test_infinities_and_zero(self):
        for normalize in [False, True]:
            with self.assertRaises(ValueError):
                Rational(0, 0, _should_normalize=normalize)
        inf, neg_inf, zero = Rational(1, 0), Rational(-1, 0), Rational(0, -5, _should_normalize=False)
        self.assertTrue(zero.is_zero())
        self.assertFalse(zero.is_inf())
        self.assertEqual(zero.sign(), 0)
        self.assertTrue(inf.is_inf())
        self.assertTrue(neg_inf < zero < inf)
        for a, b in product([-1, 1], repeat=2):
            infinite = Rational(a * 7, 0, _should_normalize=False)
            finite = Rational(-3 * b, -2, _should_normalize=False)
            self.assertEqual((infinite * finite).sign(), a * b)
            self.assertEqual((finite * infinite).sign(), a * b)
            self.assertEqual((infinite / finite).sign(), a * b)
            self.assertEqual(as_fraction(finite / infinite), 0)
            self.assertEqual((finite / zero).sign(), b)
            self.assertEqual((infinite + finite).sign(), a)
            self.assertEqual((finite - infinite).sign(), -a)
        for operation in [lambda: inf - inf, lambda: inf + neg_inf, lambda: zero * inf, lambda: inf * zero, lambda: inf / inf, lambda: zero / zero, lambda: inf / zero]:
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(as_fraction(inf + inf), float('inf'))
        self.assertEqual(as_fraction(neg_inf - inf), -float('inf'))

    def test_bounded_approximations(self):
        for bound in range(1, 8):
            choices = {Fraction(p, q) for p in range(-bound, bound + 1) for q in range(1, bound + 1)}
            for p, q in product(range(-12, 13), range(1, 11)):
                x = Fraction(p, q)
                value = Rational(p, q)
                floor = max((v for v in choices if v <= x), default=-float('inf'))
                ceil = min((v for v in choices if v >= x), default=float('inf'))
                self.assertEqual(as_fraction(value.bounded_floor(bound)), floor)
                self.assertEqual(as_fraction(value.bounded_ceil(bound)), ceil)
            for s in [-1, 1]:
                value = Rational(s, 0)
                self.assertEqual(value.bounded_floor(bound), value)
                self.assertEqual(value.bounded_ceil(bound), value)
        for bound in [0, -1]:
            with self.assertRaises(ValueError):
                Rational(1, 2).bounded_floor(bound)
            with self.assertRaises(ValueError):
                Rational(1, 2).bounded_ceil(bound)

    def test_stern_brocot_paths(self):
        queue = [('', (0, 1), (1, 0))]
        nodes = []
        for path, left, right in queue:
            value = (left[0] + right[0], left[1] + right[1])
            node = SternBrocotTree(*value)
            expanded = ''.join(direction * count for direction, count in node.path())
            self.assertEqual(expanded, path)
            self.assertEqual(node.depth(), len(path))
            self.assertEqual(as_fraction(node.value()), Fraction(*value))
            self.assertEqual(tuple(as_fraction(v) for v in node.range()), (Fraction(*left), Fraction(*right) if right[1] else float('inf')))
            for depth in range(-1, len(path) + 2):
                ancestor = node.ancestor(depth)
                if not 0 <= depth <= len(path):
                    self.assertIsNone(ancestor)
                else:
                    self.assertIsNotNone(ancestor)
                    self.assertEqual(''.join(d * n for d, n in ancestor.path()), path[:depth])
            nodes.append((path, node))
            if len(path) < 6:
                queue.extend([(path + 'L', left, value), (path + 'R', value, right)])
        for path, node in nodes:
            for other_path, other in nodes:
                common = 0
                while common < min(len(path), len(other_path)) and path[common] == other_path[common]:
                    common += 1
                self.assertEqual(SternBrocotTree.lca(node, other).depth(), common)
                self.assertEqual(SternBrocotTree.hops(node, other), len(path) + len(other_path) - 2 * common)
                self.assertEqual(node.is_ancestor_of(other), other_path.startswith(path))
                self.assertEqual(node.is_descendant_of(other), path.startswith(other_path))
        huge = 1 << 100
        node = SternBrocotTree.from_path([('L', huge), ('R', huge)])
        before = node.path()
        self.assertFalse(node.move_up(2 * huge + 1))
        self.assertEqual(node.path(), before)
        self.assertTrue(node.move_up(huge))
        self.assertEqual(node.value(), Rational(1, huge + 1))
        self.assertTrue(node.move_up(huge))
        self.assertEqual(node.value(), Rational(1, 1))


if __name__ == '__main__':
    unittest.main()
