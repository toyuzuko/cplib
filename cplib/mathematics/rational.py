#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Sequence
from math import gcd



class Rational:
    """
    Exact rational number with lazy normalization.

    The class stores a numerator and denominator and delays normalization until
    it is required for comparison, hashing, or display. A zero denominator is
    used to represent signed infinity. Denominator signs and infinities are
    normalized immediately; gcd reduction may be deferred. Treat num and den
    as read-only attributes to preserve normalization and hash invariants.
    Python integers are unbounded: the internal size threshold merely triggers
    gcd reduction and is not a numeric limit.

    Attributes:
        num: Numerator.
        den: Denominator, with ``0`` representing signed infinity.
        _normalized: Whether ``num`` and ``den`` are in canonical form.

    Space Complexity:
        - ``O(1)``

    Complexity Notation:
        Arithmetic operation costs assume Python integer arithmetic is treated
        as constant time. Normalization itself uses one gcd computation.

    Examples:
        >>> Rational(1, 2) + Rational(1, 3)
        Rational(5, 6)
        >>> str(Rational(6, 8))
        '3/4'

    """

    _MAX_SAFE_INT = (1 << 63) - 1

    def __init__(self, num: int, den: int, _should_normalize: bool = True) -> None:
        """
        Initialize a rational number.

        Args:
            num: Numerator.
            den: Denominator. ``0`` represents signed infinity.
            _should_normalize: Whether to normalize immediately.

        Returns:
            None.

        Time Complexity:
            ``O(log min(abs(num), abs(den)))`` when normalization is requested;
            otherwise ``O(1)``.
        """
        if den < 0:
            num, den = -num, -den
        self.num: int = num
        self.den: int = den
        self._normalized: bool = False
        if _should_normalize or den == 0:
            self._normalize()

    def _normalize(self) -> None:
        if self.den == 0:
            if self.num == 0:
                raise ValueError("0/0 is undefined")
            self.num = 1 if self.num > 0 else -1
            self._normalized = True
            return

        if self.num == 0:
            self.den = 1
            self._normalized = True
            return

        if self.den < 0:
            self.num, self.den = -self.num, -self.den

        g = gcd(abs(self.num), abs(self.den))
        self.num //= g
        self.den //= g
        self._normalized = True

    def ensure_normalized(self) -> None:
        """
        Ensure this rational is normalized, doing so if necessary.

        This method checks if the rational is already normalized and only
        performs normalization if needed. This is more efficient than
        calling the internal normalization routine directly when you're not sure if normalization
        is needed.

        Use this method when:
        - You need to access num/den attributes reliably
        - You want to ensure canonical form before comparison
        - You're unsure if the rational is already normalized


        Returns:
            None; num and den are put in canonical form.

        Time Complexity:
            ``O(log min(abs(num), abs(den)))`` if normalization is needed;
            otherwise ``O(1)``.
        """
        if not self._normalized:
            self._normalize()

    def _check_overflow(self) -> bool:
        """Check if the numbers are getting too large and normalize if needed."""
        if (abs(self.num) > self._MAX_SAFE_INT or abs(self.den) > self._MAX_SAFE_INT):
            if not self._normalized:
                self._normalize()
            return True
        return False

    def sign(self) -> int:
        """
        Get the sign of the rational number.

        Returns:
            -1 if negative, 0 if zero, 1 if positive.

        Time Complexity:
            O(1)
        """
        return (self.num > 0) - (self.num < 0)

    @staticmethod
    def _bounded_nonnegative(bound: int, num: int, den: int) -> tuple['Rational', 'Rational']:
        if num == 0:
            zero = Rational(0, 1)
            return zero, zero
        if den == 0:
            inf = Rational(1, 0)
            return inf, inf

        p, q = 0, 1
        r, s = 1, 0
        is_left = False

        while True:
            steps: int = num // den
            if is_left:
                if p > 0:
                    steps = min(steps, (bound - r) // p)
                steps = min(steps, (bound - s) // q)
                r += steps * p
                s += steps * q
            else:
                steps = min(steps, (bound - p) // r)
                if s > 0:
                    steps = min(steps, (bound - q) // s)
                p += steps * r
                q += steps * s

            if is_left and steps == 0:
                break

            num -= steps * den
            if num == 0:
                if is_left:
                    exact = Rational(r, s)
                else:
                    exact = Rational(p, q)
                return exact, exact

            num, den = den, num
            is_left = not is_left

        return Rational(p, q), Rational(r, s)

    def bounded_floor(self, bound: int) -> 'Rational':
        """
        Find the maximum bounded rational not greater than this value.

        Args:
            bound: Upper bound for ``abs(num)`` and ``abs(den)`` of the answer.

        Returns:
            The largest rational ``r`` such that ``r <= self`` and
            ``abs(r.num), abs(r.den) <= bound``.

        Raises:
            ValueError: If bound < 1. Signed infinities are valid answers.

        Time Complexity:
            ``O(log max(abs(num), den))``
        """
        if bound < 1:
            raise ValueError('bound must be positive')
        self.ensure_normalized()
        if self.num < 0:
            return -(-self).bounded_ceil(bound)
        floor, _ = self._bounded_nonnegative(bound, self.num, self.den)
        return floor

    def bounded_ceil(self, bound: int) -> 'Rational':
        """
        Find the minimum bounded rational not less than this value.

        Args:
            bound: Upper bound for ``abs(num)`` and ``abs(den)`` of the answer.

        Returns:
            The smallest rational ``r`` such that ``self <= r`` and
            ``abs(r.num), abs(r.den) <= bound``.

        Raises:
            ValueError: If bound < 1. Signed infinities are valid answers.

        Time Complexity:
            ``O(log max(abs(num), den))``
        """
        if bound < 1:
            raise ValueError('bound must be positive')
        self.ensure_normalized()
        if self.num < 0:
            return -(-self).bounded_floor(bound)
        _, ceil = self._bounded_nonnegative(bound, self.num, self.den)
        return ceil

    def __add__(self, other: 'Rational') -> 'Rational':
        """Return the exact sum.

        Args:
            other: Rational operand.

        Returns:
            A new Rational, possibly signed infinity.

        Raises:
            ValueError: Opposite signed infinities are added.

        Time Complexity:
            O(1) integer operations, plus one gcd if the intermediate numerator
            or denominator exceeds the size threshold.
        """
        if self.den == 0 and other.den == 0 and self.num * other.num < 0:
            raise ValueError("inf + (-inf) is undefined")
        if self.den == 0:
            result = Rational(self.num, 0, _should_normalize=True)
            return result
        if other.den == 0:
            result = Rational(other.num, 0, _should_normalize=True)
            return result

        new_num = self.num * other.den + other.num * self.den
        new_den = self.den * other.den
        result = Rational(new_num, new_den, _should_normalize=False)
        result._check_overflow()
        return result

    def __sub__(self, other: 'Rational') -> 'Rational':
        """Return the exact difference.

        Args:
            other: Rational operand.

        Returns:
            A new Rational, possibly signed infinity.

        Raises:
            ValueError: Equal signed infinities are subtracted.

        Time Complexity:
            O(1) integer operations, plus one gcd if the intermediate numerator
            or denominator exceeds the size threshold.
        """
        if self.den == 0 and other.den == 0 and self.num * other.num > 0:
            raise ValueError("inf - inf is undefined")
        if self.den == 0:
            result = Rational(self.num, 0, _should_normalize=True)
            return result
        if other.den == 0:
            result = Rational(-other.num, 0, _should_normalize=True)
            return result

        new_num = self.num * other.den - other.num * self.den
        new_den = self.den * other.den
        result = Rational(new_num, new_den, _should_normalize=False)
        result._check_overflow()
        return result

    def __mul__(self, other: 'Rational') -> 'Rational':
        """Return the exact product.

        Args:
            other: Rational operand.

        Returns:
            A new Rational, possibly signed infinity.

        Raises:
            ValueError: Zero is multiplied by infinity.

        Time Complexity:
            O(1) integer operations, plus one gcd if the intermediate numerator
            or denominator exceeds the size threshold.
        """
        if (self.num == 0 and other.den == 0) or (self.den == 0 and other.num == 0):
            raise ValueError("0 * inf is undefined")
        new_num = self.num * other.num
        new_den = self.den * other.den
        result = Rational(new_num, new_den, _should_normalize=False)
        result._check_overflow()
        return result

    def __truediv__(self, other: 'Rational') -> 'Rational':
        """Return the exact quotient.

        Args:
            other: Rational operand.

        Returns:
            A new Rational, possibly signed infinity. Finite nonzero division by
            zero returns signed infinity.

        Raises:
            ValueError: The operation is 0/0, inf/0 or inf/inf.

        Time Complexity:
            O(1) integer operations, plus one gcd if the intermediate numerator
            or denominator exceeds the size threshold.
        """
        if other.num == 0:
            if self.num == 0:
                raise ValueError("0/0 is undefined")
            if self.den == 0:
                raise ValueError("inf/0 is undefined")
            result = Rational(self.num * other.den, 0, _should_normalize=True)
            return result

        if self.den == 0 and other.den == 0:
            raise ValueError("inf/inf is undefined")
        if self.den == 0:
            return Rational(self.num * other.num, 0)

        new_num = self.num * other.den
        new_den = self.den * other.num
        result = Rational(new_num, new_den, _should_normalize=False)
        result._check_overflow()
        return result

    def __eq__(self, other: object) -> bool:
        """Compare two values using ==.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations, plus gcd normalization when needed.
        """
        if not isinstance(other, Rational):
            return NotImplemented
        self.ensure_normalized()
        other.ensure_normalized()
        return self.num == other.num and self.den == other.den

    def __lt__(self, other: 'Rational') -> bool:
        """Compare two values using <.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations.
        """
        if self.den == 0 and other.den == 0:
            return self.num < other.num
        if self.den == 0:
            return self.num < 0
        if other.den == 0:
            return other.num > 0
        return self.num * other.den < other.num * self.den

    def __le__(self, other: 'Rational') -> bool:
        """Compare two values using <=.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations, plus gcd normalization when needed.
        """
        return self == other or self < other

    def __gt__(self, other: 'Rational') -> bool:
        """Compare two values using >.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations.
        """
        return other < self

    def __ge__(self, other: 'Rational') -> bool:
        """Compare two values using >=.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations, plus gcd normalization when needed.
        """
        return other <= self

    def __ne__(self, other: object) -> bool:
        """Compare two values using !=.

        Args:
            other: Other operand.

        Returns:
            The comparison result. Signed infinities are ordered outside finite values.

        Time Complexity:
            O(1) integer operations, plus gcd normalization when needed.
        """
        return not self == other

    def __neg__(self) -> 'Rational':
        """Negate this value.

        Returns:
            A new Rational with the opposite sign.

        Time Complexity:
            O(1) integer operations.
        """
        return Rational(-self.num, self.den, _should_normalize=False)

    def __str__(self) -> str:
        """Format the canonical rational value.

        Returns:
            An integer, numerator/denominator, inf or -inf as text.

        Time Complexity:
            O(1) integer operations plus gcd normalization when needed; text formatting
            additionally depends on the number of digits.
        """
        self.ensure_normalized()
        if self.den == 0:
            return "inf" if self.num > 0 else "-inf"
        if self.den == 1:
            return str(self.num)
        return f"{self.num}/{self.den}"

    def __repr__(self) -> str:
        """Format the canonical constructor representation.

        Returns:
            Text of the form Rational(numerator, denominator).

        Time Complexity:
            O(1) integer operations plus gcd normalization when needed; text formatting
            additionally depends on the number of digits.
        """
        self.ensure_normalized()
        return f"Rational({self.num}, {self.den})"

    def is_inf(self) -> bool:
        """
        Return whether this value is signed infinity.

        Returns:
            True for either signed infinity.

        Time Complexity:
            O(1)
        """
        return self.den == 0

    def is_zero(self) -> bool:
        """
        Return whether this value is zero.

        Returns:
            True for finite zero.

        Time Complexity:
            O(1)
        """
        return self.num == 0 and self.den != 0

    def __hash__(self) -> int:
        """Hash the canonical rational value.

        Returns:
            An integer hash; equal Rational values have equal hashes.

        Time Complexity:
            O(1) integer operations, plus gcd normalization when needed.
        """
        self.ensure_normalized()
        u = self.num * 2 if self.num >= 0 else -self.num * 2 - 1
        v = self.den * 2 if self.den >= 0 else -self.den * 2 - 1
        s = u + v
        return (s * (s + 1) // 2) + v


class SternBrocotTree:
    """
    Node on the Stern-Brocot tree of positive rational numbers.

    The root is ``1/1``. Each node stores the open rational interval occupied by
    its subtree and the run-length encoded path from the root.

    Attributes:
        _left: Left boundary of the open interval of the subtree.
        _right: Right boundary of the open interval of the subtree.
        _path: Run-length encoded path from the root.
        _depth: Total path length from the root.

    Space Complexity:
        ``O(k)`` where ``k`` is the number of direction runs in the path.

    Complexity Notation:
        ``k`` is the number of run-length encoded direction blocks in a path,
        and ``d`` is the total depth from the root.
    """

    def __init__(self, num: int | Rational = 1, den: int = 1) -> None:
        """
        Initialize a Stern-Brocot node from a positive finite rational.

        Args:
            num: Numerator, or a ``Rational`` value.
            den: Denominator when ``num`` is an integer.

        Returns:
            None.

        Time Complexity:
            ``O(log max(num, den))``
        """
        self._left = Rational(0, 1)
        self._right = Rational(1, 0)
        self._path: list[tuple[str, int]] = []
        self._depth = 0

        if isinstance(num, Rational):
            num.ensure_normalized()
            num, den = num.num, num.den
        self._set_from_fraction(num, den)

    @staticmethod
    def from_path(path: Sequence[tuple[str, int]]) -> 'SternBrocotTree':
        """
        Build a node from a run-length encoded path.

        Args:
            path: List of ``('L' or 'R', count)`` moves from the root.

        Returns:
            The node reached by following ``path``.

        Time Complexity:
            ``O(len(path))``
        """
        node = SternBrocotTree()
        for direction, count in path:
            node.move_down(direction, count)
        return node

    def _set_from_fraction(self, num: int, den: int) -> None:
        if num <= 0 or den <= 0:
            raise ValueError('Stern-Brocot tree nodes must be positive finite rationals')

        direction = 'L' if num < den else 'R'
        if direction == 'L':
            num, den = den, num
        while den:
            q, r = divmod(num, den)
            self.move_down(direction, q - (1 if r == 0 else 0))
            num, den = den, r
            direction = 'R' if direction == 'L' else 'L'

    def value(self) -> Rational:
        """
        Return the rational number corresponding to this node.

        Returns:
            The mediant of the current subtree bounds.

        Time Complexity:
            ``O(1)``
        """
        return Rational(self._left.num + self._right.num, self._left.den + self._right.den, _should_normalize=False)

    def range(self) -> tuple[Rational, Rational]:
        """
        Return the open interval occupied by this node's subtree.

        Returns:
            The left and right endpoints of the subtree interval.

        Time Complexity:
            ``O(1)``
        """
        return Rational(self._left.num, self._left.den, _should_normalize=False), Rational(self._right.num, self._right.den, _should_normalize=False)

    def path(self) -> list[tuple[str, int]]:
        """
        Return the run-length encoded path from the root.

        Returns:
            List of ``('L' or 'R', count)`` moves from ``1/1``.

        Time Complexity:
            ``O(k)`` where ``k`` is the number of direction runs.
        """
        return [(direction, count) for direction, count in self._path]

    def depth(self) -> int:
        """
        Return the distance from the root ``1/1``.

        Returns:
            The number of edge moves from the root.

        Time Complexity:
            ``O(1)``
        """
        return self._depth

    def move_down(self, direction: str, count: int = 1) -> None:
        """
        Move this node downward by repeating one direction.

        Args:
            direction: ``'L'`` for left child or ``'R'`` for right child.
            count: Number of repeated moves.


        Returns:
            None.

        Raises:
            ValueError: If direction is not L or R, or count is negative.

        Time Complexity:
            ``O(1)``
        """
        if direction not in ('L', 'R'):
            raise ValueError("direction must be 'L' or 'R'")
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return
        direction_value: str = 'L' if direction == 'L' else 'R'
        count_value: int = count

        if self._path and self._path[-1][0] == direction_value:
            prev_path: tuple[str, int] = self._path[-1]
            self._path[-1] = (prev_path[0], prev_path[1] + count_value)
        else:
            self._path.append((direction_value, count_value))
        self._depth += count_value

        if direction_value == 'L':
            self._right = Rational(
                self._right.num + self._left.num * count_value,
                self._right.den + self._left.den * count_value,
                _should_normalize=False,
            )
        else:
            self._left = Rational(
                self._left.num + self._right.num * count_value,
                self._left.den + self._right.den * count_value,
                _should_normalize=False,
            )

    def move_up(self, count: int = 1) -> bool:
        """
        Move this node toward the root.

        Args:
            count: Number of upward moves.

        Returns:
            ``True`` if the move was valid, otherwise ``False`` and this node is
            left unchanged.

        Time Complexity:
            ``O(k)`` where ``k`` is the number of removed direction runs.
        """
        if count < 0 or count > self._depth:
            return False

        while count:
            last_path = self._path.pop()
            direction: str = last_path[0]
            path_count: int = last_path[1]
            move_count: int = min(count, path_count)
            count -= move_count
            self._depth -= move_count

            if direction == 'L':
                self._right = Rational(
                    self._right.num - self._left.num * move_count,
                    self._right.den - self._left.den * move_count,
                    _should_normalize=False,
                )
            else:
                self._left = Rational(
                    self._left.num - self._right.num * move_count,
                    self._left.den - self._right.den * move_count,
                    _should_normalize=False,
                )

            remaining_count: int = path_count - move_count
            if remaining_count:
                self._path.append((direction, remaining_count))
        return True

    def ancestor(self, depth: int) -> 'SternBrocotTree | None':
        """
        Return the ancestor at a given depth from the root.

        Args:
            depth: Target depth, where the root ``1/1`` has depth ``0``.

        Returns:
            The ancestor node, or ``None`` if ``depth`` is outside this path.

        Time Complexity:
            ``O(k)`` where ``k`` is the number of direction runs in this path.
        """
        node = SternBrocotTree.from_path(self._path)
        if node.move_up(node.depth() - depth):
            return node
        return None

    @staticmethod
    def lca(a: 'SternBrocotTree', b: 'SternBrocotTree') -> 'SternBrocotTree':
        """
        Find the lowest common ancestor of two Stern-Brocot nodes.

        Args:
            a: First node.
            b: Second node.

        Returns:
            The lowest common ancestor of ``a`` and ``b``.

        Time Complexity:
            ``O(k)`` where ``k`` is the common path run length.
        """
        node = SternBrocotTree()
        for (dir_a, count_a), (dir_b, count_b) in zip(a._path, b._path):
            if dir_a != dir_b:
                break
            count = min(count_a, count_b)
            node.move_down(dir_a, count)
            if count_a != count_b:
                break
        return node

    def is_ancestor_of(self, other: 'SternBrocotTree') -> bool:
        """
        Check whether this node is an ancestor of ``other``.

        Args:
            other: Candidate descendant.

        Returns:
            ``True`` if ``other`` is in this node's subtree.

        Time Complexity:
            ``O(1)``
        """
        value = other.value()
        return self._left < value and value < self._right

    def is_descendant_of(self, other: 'SternBrocotTree') -> bool:
        """
        Check whether this node is a descendant of ``other``.

        Args:
            other: Candidate ancestor.

        Returns:
            ``True`` if this node is in ``other``'s subtree.

        Time Complexity:
            ``O(1)``
        """
        return other.is_ancestor_of(self)

    @staticmethod
    def hops(a: 'SternBrocotTree', b: 'SternBrocotTree') -> int:
        """
        Return the tree distance between two nodes.

        Args:
            a: First node.
            b: Second node.

        Returns:
            Number of edges on the path between ``a`` and ``b``.

        Time Complexity:
            ``O(k)`` where ``k`` is the common path run length.
        """
        c = SternBrocotTree.lca(a, b)
        return a.depth() + b.depth() - c.depth() * 2
