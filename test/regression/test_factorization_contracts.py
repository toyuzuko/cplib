from math import gcd, isqrt, prod
import random
import unittest
from unittest.mock import patch

import cplib.mathematics.factorization as factorization
from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.sieve import enumerate_primes, enumerate_primes_by_index


def trial_factors(n: int) -> list[int]:
    factors: list[int] = []
    p = 2
    while p * p <= n:
        while n % p == 0:
            factors.append(p)
            n //= p
        p += 1
    if n > 1:
        factors.append(n)
    return factors


def fresh_factor(bound: int) -> type[PrimeFactor]:
    class Factor(PrimeFactor):
        m = 0
        _built = False

    Factor.set_max_value(bound)
    return Factor


class FactorizationContractsTest(unittest.TestCase):
    def test_small_tables_and_domains(self) -> None:
        for bound in (0, 1, 2, 7, 61, 600):
            factor = fresh_factor(bound)
            for n in range(-10, 2001):
                expected = n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))
                self.assertEqual(factor.is_prime(n), expected, (bound, n))
            for n in range(1, 301):
                factors = trial_factors(n)
                self.assertEqual(factor.factorize(n), factors)
                self.assertEqual(factor.divisors(n), [d for d in range(1, n + 1) if n % d == 0])
                self.assertEqual(factor.mobius(n), 0 if len(set(factors)) < len(factors) else (-1) ** len(factors))
                self.assertEqual(factor.totient(n), sum(gcd(n, d) == 1 for d in range(1, n + 1)))
            for n in (-10, -1, 0):
                for method in (factor.factorize, factor.divisors, factor.mobius, factor.totient):
                    with self.assertRaises(ValueError):
                        method(n)
            old_table = factor._isprime
            factor.set_max_value(0)
            self.assertIs(factor._isprime, old_table)
            with self.assertRaises(ValueError):
                factor.set_max_value(-1)
            self.assertIs(factor._isprime, old_table)
            factor.set_max_value(2100)
            self.assertEqual(factor.m, 2100)
            self.assertTrue(factor.is_prime(2089))

    def test_large_factors_and_pseudoprimes(self) -> None:
        factor = fresh_factor(1)
        for n in (561, 1105, 1729, 2465, 2821, 6601, 341550071728321):
            self.assertFalse(factor.is_prime(n), n)
        cases = [
            [2] * 70, [3] * 30, [7] * 12, [10670053, 32010157],
            [1000000007, 1000000009], [3, 5, 17, 257, 641, 65537, 6700417],
        ]
        rng = random.Random(0)
        with patch.object(factorization, 'randint', rng.randint):
            for factors in cases:
                self.assertEqual(factor.factorize(prod(factors)), factors)
            # Lucas-Lehmer independently establishes these Mersenne primes.
            for exponent in (61, 127):
                prime = (1 << exponent) - 1
                value = 4
                for _ in range(exponent - 2):
                    value = (value * value - 2) % prime
                self.assertEqual(value, 0)
                self.assertTrue(factor.is_prime(prime))
                self.assertEqual(factor.factorize(prime), [prime])

    def test_pollard_recovery_and_large_integer_batch(self) -> None:
        for n in (49, 77):
            divisors: list[int] = []

            def observe(a: int, b: int) -> int:
                d = gcd(a, b)
                divisors.append(d)
                return d

            with patch.object(factorization, 'randint', return_value=1), patch.object(factorization, 'gcd', side_effect=observe):
                divisor = PrimeFactor._pollard_rho(n)
            self.assertIn(n, divisors)
            self.assertTrue(1 < divisor < n and n % divisor == 0)
        n = 5 * ((1 << 2048) + 1)
        with patch.object(factorization, 'randint', return_value=1):
            divisor = PrimeFactor._pollard_rho(n)
        self.assertTrue(1 < divisor < n and n % divisor == 0)

    def test_primitive_roots(self) -> None:
        factor = fresh_factor(5)
        for n in range(1, 251):
            units = {x for x in range(1, n) if gcd(x, n) == 1}
            roots = {g for g in units if {pow(g, k, n) for k in range(len(units))} == units}
            root = factor.primitive_root(n)
            if roots:
                self.assertIn(root, roots, n)
            else:
                self.assertEqual(root, -1, n)

    def test_tetration(self) -> None:
        factor = fresh_factor(3000)
        for base in range(6):
            value = 1
            for height in range(4):
                if height:
                    value = pow(base, value)
                for modulus in range(1, 101):
                    self.assertEqual(factor.tetration(base, height, modulus), value % modulus)

        def enough(base: int, height: int, limit: int) -> bool:
            if base == 0:
                return (height + 1) % 2 >= limit
            if base == 1:
                return 1 >= limit
            while limit > 1 and height:
                value = 1
                needed = 0
                while value < limit:
                    value *= base
                    needed += 1
                limit = needed
                height -= 1
            return limit <= 1

        def reference(base: int, height: int, modulus: int) -> int:
            if modulus == 1:
                return 0
            if height == 0:
                return 1
            if base == 0:
                return (height + 1) % 2
            phi = modulus
            for p in set(trial_factors(modulus)):
                phi -= phi // p
            exponent = reference(base, height - 1, phi)
            if enough(base, height - 1, phi):
                exponent += phi
            return pow(base, exponent, modulus)

        rng = random.Random(0)
        for _ in range(5000):
            base, height, modulus = rng.randrange(50), rng.randrange(100), rng.randrange(1, 3001)
            self.assertEqual(factor.tetration(base, height, modulus), reference(base, height, modulus), (base, height, modulus))
        for args in ((-1, 2, 5), (2, -1, 5), (2, 2, 0), (2, 2, -1)):
            with self.assertRaises(ValueError):
                factor.tetration(*args)

        class PowersOfTwo(PrimeFactor):
            @classmethod
            def totient(cls, n: int) -> int:
                assert n > 1 and n & (n - 1) == 0
                return n // 2

        self.assertEqual(PowersOfTwo.tetration(2, 10**10, 1 << 1500), 0)


class SieveContractsTest(unittest.TestCase):
    def test_selection_and_invalid_indices(self) -> None:
        for n in list(range(-3, 100)) + [511, 1024, 5000]:
            primes = [p for p in range(2, n + 1) if all(p % d for d in range(2, isqrt(p) + 1))]
            self.assertEqual(enumerate_primes(n), primes)
            for a in (1, 2, 7, 101):
                for b in set((0, a // 2, a - 1)):
                    self.assertEqual(enumerate_primes_by_index(n, a, b), (len(primes), primes[b::a]))
        for n in (-1, 1, 10):
            for a, b in ((0, 0), (-1, 0), (2, -1), (2, 2)):
                with self.assertRaises(ValueError):
                    enumerate_primes_by_index(n, a, b)

    def test_segment_boundary(self) -> None:
        n = (1 << 23) + 100
        sieve = bytearray(b'\x01') * (n + 1)
        sieve[:2] = b'\x00\x00'
        for p in range(2, isqrt(n) + 1):
            if sieve[p]:
                sieve[p * p::p] = b'\x00' * ((n - p * p) // p + 1)
        primes = [p for p in range(n + 1) if sieve[p]]
        self.assertEqual(enumerate_primes_by_index(n, 997, 411), (len(primes), primes[411::997]))


if __name__ == '__main__':
    unittest.main()
