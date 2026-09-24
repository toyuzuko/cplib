"""Deterministic pseudo-random number generators for heuristic search.

This module provides two small contest-friendly generators:

* :class:`SplitMix64` for fast seeding and simple 64-bit generation.
* :class:`XorShift` for a fast xorshift128+ style generator.

Both generators expose a tiny utility surface that is convenient in
competitive programming code: ``next_uint64()``, ``randbits()``,
``randrange()``, ``randint()``, ``choice()``, and ``shuffle()``.

Examples:
    >>> rng = SplitMix64(0)
    >>> value = rng.next_uint64()
    >>> 0 <= value < 2**64
    True
    >>> xs = XorShift(1)
    >>> xs.choice([7])
    7
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from operator import index
from typing import overload

from cplib.tools.type import T

_UINT64_MASK = (1 << 64) - 1
_FLOAT_DENOMINATOR = 1 << 53


class _RandomMixin:
    """Common helpers for the public RNG classes."""

    def _next_uint64(self) -> int:
        raise NotImplementedError

    def next_uint64(self) -> int:
        """
        Return the next 64-bit unsigned integer.

        Returns:
            A value in the range ``[0, 2**64)``.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> value = SplitMix64(0).next_uint64()
            >>> 0 <= value < 2**64
            True
        """

        return self._next_uint64()

    def random(self) -> float:
        """
        Return a floating-point value in ``[0.0, 1.0)``.

        The value is built from the top 53 bits of the next 64-bit word.

        Returns:
            A pseudorandom floating-point value in ``[0.0, 1.0)``.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> value = SplitMix64(1).random()
            >>> 0.0 <= value < 1.0
            True
        """

        return float(self.next_uint64() >> 11) / float(_FLOAT_DENOMINATOR)

    def randbits(self, k: int) -> int:
        """
        Return a non-negative integer with at most ``k`` random bits.

        Args:
            k: Number of random bits to generate.

        Returns:
            A value in ``[0, 2**k)``. Successive 64-bit words fill the result
            from least to most significant bits; unused high bits are dropped.
            Zero bits returns 0 without advancing the generator.

        Raises:
            ValueError: If ``k`` is negative.

        Time Complexity:
            O(1 + k) bit operations, with ceil(k / 64) generator steps.

        Space Complexity:
            O(1 + k) bits, including the result and temporary byte buffer.

        Examples:
            >>> value = SplitMix64(0).randbits(5)
            >>> 0 <= value < 32
            True
        """

        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return 0

        if k <= 64:
            return self.next_uint64() & ((1 << k) - 1)
        words = b''.join(self.next_uint64().to_bytes(8, 'little') for _ in range((k + 63) // 64))
        return int.from_bytes(words, 'little') & ((1 << k) - 1)

    def _randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ValueError("upper must be positive")

        bits = upper.bit_length()
        while True:
            candidate = self.randbits(bits)
            if candidate < upper:
                return candidate

    @overload
    def randrange(self, start: int) -> int: ...

    @overload
    def randrange(self, start: int, stop: int, step: int = 1) -> int: ...

    def randrange(
        self,
        start: int,
        stop: int | None = None,
        step: int = 1,
    ) -> int:
        """
        Return a uniformly chosen element from a numeric range.

        Args:
            start: Range stop if ``stop`` is omitted, otherwise range start.
            stop: Optional range stop.
            step: Step size. May be negative, but must not be zero.

        Returns:
            A uniformly chosen integer from the specified range. Arbitrarily
            large integer endpoints and ranges are supported.

        Raises:
            ValueError: If the range is empty or ``step`` is zero.

        Time Complexity:
            - ``O(1)`` expected for fixed-width integers

        Space Complexity:
            O(1) for fixed-width integers; otherwise proportional to the bit
            lengths of the endpoints, step, and range size.

        Examples:
            >>> value = SplitMix64(0).randrange(3, 10, 2)
            >>> value in range(3, 10, 2)
            True
        """

        start = index(start)
        step = index(step)
        if stop is None:
            start, stop = 0, start
        else:
            stop = index(stop)
        if step == 0:
            raise ValueError("step must not be zero")

        size = (stop - start - 1) // step + 1 if step > 0 else (start - stop - 1) // (-step) + 1
        if size <= 0:
            raise ValueError("empty range")
        return start + step * self._randbelow(size)

    def randint(self, a: int, b: int) -> int:
        """
        Return a uniformly chosen integer in ``[a, b]``.

        Args:
            a: Lower bound.
            b: Upper bound.

        Returns:
            A uniformly chosen integer in the inclusive interval ``[a, b]``.

        Raises:
            ValueError: If ``a > b``.

        Time Complexity:
            - ``O(1)`` expected for fixed-width integers

        Space Complexity:
            O(1) for fixed-width integers; otherwise proportional to the
            endpoints' bit lengths.

        Examples:
            >>> value = SplitMix64(0).randint(4, 7)
            >>> 4 <= value <= 7
            True
        """

        if a > b:
            raise ValueError("a must be <= b")
        return self.randrange(a, b + 1)

    def choice(self, seq: Sequence[T]) -> T:
        """
        Return a uniformly chosen element from a non-empty sequence.

        Args:
            seq: Sequence to sample from.

        Returns:
            One randomly chosen element of ``seq``.

        Raises:
            IndexError: If ``seq`` is empty.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> SplitMix64(0).choice(['x'])
            'x'
        """

        if len(seq) == 0:
            raise IndexError("cannot choose from an empty sequence")
        return seq[self._randbelow(len(seq))]

    def shuffle(self, seq: MutableSequence[T]) -> None:
        """
        Shuffle a mutable sequence in place.

        Args:
            seq: Mutable sequence to be permuted.

        Returns:
            ``None``. ``seq`` is modified in place.

        Time Complexity:
            - ``O(n)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> values = [1, 2, 3]
            >>> SplitMix64(0).shuffle(values)
            >>> sorted(values)
            [1, 2, 3]
        """

        for index in range(len(seq) - 1, 0, -1):
            swap_index = self._randbelow(index + 1)
            seq[index], seq[swap_index] = seq[swap_index], seq[index]


class SplitMix64(_RandomMixin):
    """
    64-bit SplitMix64 pseudo-random number generator.

    Space Complexity:
        - ``O(1)``

    Examples:
        >>> rng = SplitMix64(0)
        >>> value = rng.next_uint64()
        >>> 0 <= value < 2**64
        True
        >>> sample = [1, 2, 3]
        >>> rng.shuffle(sample)
        >>> sorted(sample)
        [1, 2, 3]

    """

    __slots__ = ("_state",)

    def __init__(self, seed: int = 0) -> None:
        """
        Initialize a SplitMix64 generator.

        Args:
            seed: Initial seed. The value is masked to 64 bits.

        Returns:
            None.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> rng = SplitMix64(7)
            >>> isinstance(rng.next_uint64(), int)
            True
        """
        self._state = seed & _UINT64_MASK

    def _next_uint64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _UINT64_MASK
        z = self._state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & _UINT64_MASK
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & _UINT64_MASK
        return z ^ (z >> 31)


class XorShift(_RandomMixin):
    """
    xorshift128+ pseudo-random number generator.

    Space Complexity:
        - ``O(1)``

    Examples:
        >>> rng = XorShift(0)
        >>> rng.choice([7])
        7
    """

    __slots__ = ("_state0", "_state1")

    def __init__(self, seed: int = 0) -> None:
        """
        Initialize a xorshift128+ generator.

        Args:
            seed: Initial seed. The value is expanded into two 64-bit states.

        Returns:
            None.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> rng = XorShift(7)
            >>> isinstance(rng.next_uint64(), int)
            True
        """
        mixer = SplitMix64(seed)
        self._state0 = mixer.next_uint64()
        self._state1 = mixer.next_uint64()
        if self._state0 == 0 and self._state1 == 0:
            self._state1 = 0x9E3779B97F4A7C15

    def _next_uint64(self) -> int:
        s1 = self._state0
        s0 = self._state1
        self._state0 = s0
        s1 ^= (s1 << 23) & _UINT64_MASK
        s1 ^= s1 >> 17
        s1 ^= s0
        s1 ^= s0 >> 26
        self._state1 = s1 & _UINT64_MASK
        return (self._state1 + s0) & _UINT64_MASK


__all__ = ["SplitMix64", "XorShift"]
