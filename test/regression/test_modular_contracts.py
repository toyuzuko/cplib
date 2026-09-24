from itertools import product
from math import gcd, lcm
import random
import unittest

from cplib.mathematics.modular import batch_inverse_mod, chinese_remainder_theorem, discrete_logarithm, extended_gcd, kth_root_mod, sqrt_mod, tonelli_shanks


class ModularContractTests(unittest.TestCase):
    def test_discrete_logs(self):
        for mod in range(1, 100):
            for base in range(mod):
                seen = {}
                value = 1 % mod
                while value not in seen:
                    seen[value] = len(seen)
                    value = value * base % mod
                for value in range(mod):
                    expected = seen.get(value, -1)
                    self.assertEqual(discrete_logarithm(base, value, mod), expected)
                    self.assertEqual(discrete_logarithm(base - mod, value + 2 * mod, mod), expected)
        for mod in [0, -1]:
            with self.assertRaises(ValueError):
                discrete_logarithm(0, 1, mod)

    def test_gcd_and_crt(self):
        for mod in range(1, 100):
            for a in range(-100, 101):
                g, x = extended_gcd(a, mod)
                self.assertEqual(g, gcd(a, mod))
                self.assertTrue(0 <= x < mod // g)
                self.assertEqual((a * x - g) % mod, 0)
        rng = random.Random(0)
        for _ in range(1000):
            mods = [rng.randrange(1, 10) for _ in range(rng.randrange(5))]
            rems = [rng.randrange(-30, 31) for _ in mods]
            period = lcm(*mods)
            expected = next((x for x in range(period) if all((x - r) % m == 0 for r, m in zip(rems, mods))), None)
            self.assertEqual(chinese_remainder_theorem(rems, mods), (0, 0) if expected is None else (expected, period))
        for mod in [0, -1]:
            with self.assertRaises(ValueError):
                extended_gcd(1, mod)

    def test_modular_roots_and_inverses(self):
        for mod in range(1, 160):
            roots = {x * x % mod for x in range(mod)}
            for value in range(-mod, mod):
                root = sqrt_mod(value, mod)
                if value % mod in roots:
                    self.assertTrue(0 <= root < mod)
                    self.assertEqual(root * root % mod, value % mod)
                else:
                    self.assertEqual(root, -1)
        primes = [p for p in range(2, 100) if all(p % d for d in range(2, p))]
        for mod in primes:
            for k in range(0, 2 * mod):
                roots = {pow(x, k, mod) for x in range(mod)}
                for value in range(mod):
                    root = kth_root_mod(k, value - mod, mod)
                    if value in roots:
                        self.assertTrue(0 <= root < mod)
                        self.assertEqual(pow(root, k, mod), value)
                    else:
                        self.assertEqual(root, -1)
            for value in range(mod):
                root = tonelli_shanks(value - mod, mod)
                self.assertEqual(root >= 0, any(x * x % mod == value for x in range(mod)))
                if root >= 0:
                    self.assertEqual(root * root % mod, value)
        for mod in range(2, 80):
            values = [v for v in range(-mod, mod) if gcd(v, mod) == 1]
            self.assertEqual(batch_inverse_mod(values, mod), [pow(v, -1, mod) for v in values])
            with self.assertRaises(ValueError):
                batch_inverse_mod([1, 0], mod)
        for mod in [0, 1, -1]:
            with self.assertRaises(ValueError):
                tonelli_shanks(0, mod)
            with self.assertRaises(ValueError):
                kth_root_mod(0, 1, mod)
        with self.assertRaises(ValueError):
            kth_root_mod(-1, 1, 7)


if __name__ == '__main__':
    unittest.main()
