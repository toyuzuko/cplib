#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Sequence

from cplib.datastructure.segtree import SegmentTree


class RollingHashMersenneMod:
    """
    A class implementing rolling hash with Mersenne prime modulo (2^61 - 1).
    Hash equality can have collisions. ``search_substring`` checks the actual
    characters; ``get_hash`` and ``search_hash`` do not guarantee text equality.

    Attributes:
        mod (int): The Mersenne prime modulo (2^61 - 1)
        mask30 (int): Bit mask for 30 bits
        mask31 (int): Bit mask for 31 bits
        str (str): The input string
        n (int): Length of the input string
        base (int): Base for hash calculation
        inv (int): Modular multiplicative inverse of base
        pow (list[int]): Powers of base mod p
        ipow (list[int]): Powers of base inverse mod p
        hash (list[int]): Prefix hashes of the string

    Examples:
        >>> rh = RollingHashMersenneMod("abcabc")
        >>> rh.search_substring("abc")  # Find first occurrence of "abc"
        0
        >>> rh.search_substring("abc", 1)  # Find "abc" starting from index 1
        3

    Args:
        string: Input string.
        base: Hash base in ``[1, mod)``. Defaults to 911382323.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    mod = 2 ** 61 - 1
    mask30 = (1 << 30) - 1
    mask31 = (1 << 31) - 1

    def __init__(self, string: str, base: int = 911382323) -> None:
        """Precompute hashes and powers for a string.

        Args:
            string: Input string.
            base: Hash base in ``[1, mod)``.

        Returns:
            None.

        Raises:
            ValueError: If the base is outside ``[1, mod)``.

        Time Complexity:
            O(n), where n is the string length.

        Space Complexity:
            O(n).
        """
        if not 0 < base < self.mod:
            raise ValueError('base must be in [1, mod)')
        self.str = string
        self.n = n = len(string)
        self.base = base
        self.inv = self._pow(base, self.mod - 2)
        self.pow = [0] * (n + 1)
        self.pow[0] = 1
        self.ipow = [0] * (n + 1)
        self.ipow[0] = 1
        for i in range(1, n + 1):
            self.pow[i] = self._mod(self._mul(self.pow[i - 1], self.base))
        for i in range(1, n + 1):
            self.ipow[i] = self._mod(self._mul(self.ipow[i - 1], self.inv))
        self.hash = [0] * (n + 1)
        for i in range(1, n + 1):
            self.hash[i] = self._mod(self.hash[i - 1] + self._mul(self.pow[i - 1], ord(string[i - 1])))

    @classmethod
    def _mod(cls, x: int) -> int:
        x = (x >> 61) + (x & cls.mod)
        if x >= cls.mod: x -= cls.mod
        return x

    @classmethod
    def _mul(cls, x: int, y: int) -> int:
        x = cls._mod(x)
        y = cls._mod(y)
        xh = x >> 31
        xl = x & cls.mask31
        yh = y >> 31
        yl = y & cls.mask31
        m = xh * yl + xl * yh
        mh = m >> 30
        ml = m & cls.mask30
        return cls._mod(xh * yh * 2 + mh + (ml << 31) + xl * yl)

    @classmethod
    def mul(cls, x: int, y: int) -> int:
        """Multiply arbitrary integers modulo 2**61 - 1.

        Args:
            x: First integer, possibly negative.
            y: Second integer, possibly negative.

        Returns:
            Canonical residue of x * y in [0, mod).

        Time Complexity:
            O(1) for bounded machine-size operands; input reduction depends
            on the bit lengths of larger integers.
        """
        return cls._mul(x % cls.mod, y % cls.mod)

    @classmethod
    def _pow(cls, x: int, n: int) -> int:
        if n == 0: return 1
        y = cls._pow(cls._mod(cls._mul(x, x)), n // 2)
        if n % 2 == 1: y = cls._mod(cls._mul(x, y))
        return y

    def search_substring(self, substring: str, l: int = 0, r: int | None = None) -> int:
        """
        Find an exact substring, checking characters to reject hash collisions.

        Args:
            substring (str): The substring to search for
            l (int, optional): Left boundary of search range. Defaults to 0.
            r (int | None, optional): Right boundary of search range. Defaults to None.

        Returns:
            int: First occurrence fully inside [l, r), or -1 if not found.
                An empty substring matches at l.

        Examples:
            >>> rh = RollingHashMersenneMod("abcabc")
            >>> rh.search_substring("abc")
            0
            >>> rh.search_substring("abc", 1)
            3

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` does not hold.

        Time Complexity:
            O(m + w + c * m), where m is the pattern length,
            w = max(0, r - l - m + 1), and c is the number of hash candidates
            checked before returning. Hash collisions can make this O(w * m + m).

        Space Complexity:
            O(1) auxiliary space
        """
        if r is None: r = self.n
        assert 0 <= l <= r <= self.n
        m = len(substring)
        if m > r - l: return -1
        if m == 0: return l
        subh = 0
        for i in range(m):
            subh += self._mul(self.pow[i], ord(substring[i]))
            subh = self._mod(subh)
        while l + m <= r:
            candidate = self.search_hash(m, subh, l, r)
            if candidate == -1: return -1
            if self.str.startswith(substring, candidate): return candidate
            l = candidate + 1
        return -1

    def get_hash(self, l: int, r: int) -> int:
        """
        Get hash value of substring [l,r).

        Args:
            l (int): Left boundary (inclusive)
            r (int): Right boundary (exclusive)

        Returns:
            int: Hash value of substring [l,r)

        Examples:
            >>> rh = RollingHashMersenneMod("abcabc")
            >>> h1 = rh.get_hash(0, 3)  # hash of "abc"
            >>> h2 = rh.get_hash(3, 6)  # hash of "abc"
            >>> h1 == h2
            True

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= l <= r <= self.n
        return self._mod(self._mul(self._mod(self.hash[r] - self.hash[l]), self.ipow[l]))

    def search_hash(self, substring_length: int, substring_hash: int, l: int = 0, r: int | None = None) -> int:
        """
        Search by hash value without checking character equality.

        Args:
            substring_length (int): Non-negative length of the substring
            substring_hash (int): Hash value of the substring
            l (int, optional): Left boundary of search range. Defaults to 0.
            r (int | None, optional): Right boundary of search range. Defaults to None.

        Returns:
            int: Index of first occurrence of substring with given hash in range [l,r), or -1 if not found

        Examples:
            >>> rh = RollingHashMersenneMod("abcabc")
            >>> h = rh.get_hash(0, 3)  # hash of "abc"
            >>> rh.search_hash(3, h, 1)  # find "abc" by hash starting from index 1
            3

        Raises:
            AssertionError: If the length is negative or ``0 <= l <= r <= n``
                does not hold.

        Time Complexity:
            O(1 + max(0, r - l - substring_length + 1))

        Space Complexity:
            O(1) auxiliary space
        """
        if r is None: r = self.n
        assert 0 <= l <= r <= self.n
        assert substring_length >= 0
        if substring_length == 0: return l if substring_hash == 0 else -1
        if r - l < substring_length: return -1
        p = self.pow[substring_length - 1]
        rol = self._mod(self._mul(self._mod(self.hash[substring_length + l] - self.hash[l]), self.ipow[l]))
        if rol == substring_hash: return l
        for i in range(r - l - substring_length):
            rol = self._mod(rol - ord(self.str[i + l]))
            rol = self._mod(self._mul(rol, self.inv))
            rol = self._mod(rol + self._mul(ord(self.str[i + substring_length + l]), p))
            if rol == substring_hash: return i + l + 1
        return -1


class DynamicRollingHashMersenneMod:
    """
    A class implementing dynamic rolling hash with Mersenne prime modulo (2^61 - 1).
    This implementation allows for character modifications and uses a segment tree
    for efficient updates and range queries.
    It uses the same Unicode code-point encoding as RollingHashMersenneMod,
    so hashes agree when the base and substring are the same.
    Hash equality can have collisions. ``search_substring`` checks the actual
    characters; ``get_hash`` and ``search_hash`` do not guarantee text equality.

    Attributes:
        mod (int): The Mersenne prime modulo (2^61 - 1)
        mask30 (int): Bit mask for 30 bits
        mask31 (int): Bit mask for 31 bits
        str (str): The original input string, before updates
        n (int): Length of the input string
        base (int): Base for hash calculation
        pow (list[int]): Powers of base mod p
        segtree (SegmentTree): Segment tree for maintaining hash values

    Examples:
        >>> drh = DynamicRollingHashMersenneMod("abcabc")
        >>> drh.search_substring("abc")  # Find first occurrence of "abc"
        0
        >>> drh.set_char(0, 'x')  # Change first character to 'x'
        >>> drh.search_substring("abc")  # Now first "abc" starts at index 3
        3

    Args:
        string: Input string.
        base: Hash base in ``[1, mod)``. Defaults to 911382323.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    mod = 2 ** 61 - 1
    mask30 = (1 << 30) - 1
    mask31 = (1 << 31) - 1
    def __init__(self, string: str, base: int = 911382323) -> None:
        """Build a segment tree of hashes for a mutable string.

        Args:
            string: Initial string.
            base: Hash base in ``[1, mod)``.

        Returns:
            None.

        Raises:
            ValueError: If the base is outside ``[1, mod)``.

        Time Complexity:
            O(n), where n is the string length.

        Space Complexity:
            O(n).
        """
        if not 0 < base < self.mod:
            raise ValueError('base must be in [1, mod)')
        self.str = string
        self._chars = list(string)
        self.n = n = len(string)
        self.base = base
        self.pow = [0] * (n + 1)
        self.pow[0] = 1
        for i in range(1, n + 1):
            self.pow[i] = self._mod(self._mul(self.pow[i - 1], self.base))
        self.segtree: SegmentTree[tuple[int, int]] = SegmentTree(self.n, lambda x, y: (self._mod(x[0] + self._mul(y[0], self.pow[x[1]])), x[1] + y[1]), (0, 0))
        self.segtree.build([(ord(c), 1) for c in string])

    @classmethod
    def _mod(cls, x: int) -> int:
        x = (x >> 61) + (x & cls.mod)
        if x >= cls.mod: x -= cls.mod
        return x

    @classmethod
    def _mul(cls, x: int, y: int) -> int:
        x = cls._mod(x)
        y = cls._mod(y)
        xh = x >> 31
        xl = x & cls.mask31
        yh = y >> 31
        yl = y & cls.mask31
        m = xh * yl + xl * yh
        mh = m >> 30
        ml = m & cls.mask30
        return cls._mod(xh * yh * 2 + mh + (ml << 31) + xl * yl)

    def set_char(self, i: int, c: str) -> None:
        """
        Set character at index i to c.

        Args:
            i (int): Index to modify, in [0, n).
            c (str): A string containing exactly one character.

        Returns:
            None. Updates the character and its hash.

        Raises:
            AssertionError: If i is out of range or c is not one character.

        Examples:
            >>> drh = DynamicRollingHashMersenneMod("abcabc")
            >>> drh.set_char(0, 'x')
            >>> drh.search_substring("xbc")
            0

        Time Complexity:
            O(log n)

        Space Complexity:
            O(1) auxiliary space
        """
        assert 0 <= i < self.n and len(c) == 1
        self.segtree.set(i, (ord(c), 1))
        self._chars[i] = c

    def get_hash(self, l: int, r: int) -> int:
        """
        Get hash value of substring [l,r).

        Args:
            l (int): Left boundary (inclusive)
            r (int): Right boundary (exclusive)

        Returns:
            int: Hash value of substring [l,r)

        Examples:
            >>> drh = DynamicRollingHashMersenneMod("abcabc")
            >>> h1 = drh.get_hash(0, 3)  # hash of "abc"
            >>> h2 = drh.get_hash(3, 6)  # hash of "abc"
            >>> h1 == h2
            True

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)

        Space Complexity:
            O(1) auxiliary space
        """
        assert 0 <= l <= r <= self.n
        return self.segtree.prod(l, r)[0]

    def search_substring(self, substring: str, l: int = 0, r: int | None = None) -> int:
        """
        Find an exact substring in the current string, rejecting hash collisions.

        Args:
            substring (str): The substring to search for
            l (int, optional): Left boundary of search range. Defaults to 0.
            r (int | None, optional): Right boundary of search range. Defaults to None.

        Returns:
            int: First occurrence fully inside [l, r), or -1 if not found.
                An empty substring matches at l.

        Examples:
            >>> drh = DynamicRollingHashMersenneMod("abcabc")
            >>> drh.search_substring("abc")
            0
            >>> drh.set_char(0, 'x')
            >>> drh.search_substring("abc")
            3

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` does not hold.

        Time Complexity:
            O(m + w * log(n + 1) + c * m), where m is the pattern length,
            w = max(0, r - l - m + 1), and c is the number of hash candidates
            checked before returning.

        Space Complexity:
            O(1) auxiliary space
        """
        if r is None: r = self.n
        assert 0 <= l <= r <= self.n
        m = len(substring)
        if m > r - l: return -1
        if m == 0: return l
        subh = 0
        for i in range(m):
            subh += self._mul(self.pow[i], ord(substring[i]))
            subh = self._mod(subh)
        while l + m <= r:
            candidate = self.search_hash(m, subh, l, r)
            if candidate == -1: return -1
            if all(self._chars[candidate + j] == c for j, c in enumerate(substring)):
                return candidate
            l = candidate + 1
        return -1

    def search_hash(self, substring_length: int, substring_hash: int, l: int = 0, r: int | None = None) -> int:
        """
        Search by hash value without checking character equality.

        Args:
            substring_length (int): Non-negative length of the substring
            substring_hash (int): Hash value of the substring
            l (int, optional): Left boundary of search range. Defaults to 0.
            r (int | None, optional): Right boundary of search range. Defaults to None.

        Returns:
            int: Index of first occurrence of substring with given hash in range [l,r), or -1 if not found

        Examples:
            >>> drh = DynamicRollingHashMersenneMod("abcabc")
            >>> h = drh.get_hash(0, 3)  # hash of "abc"
            >>> drh.search_hash(3, h, 1)  # find "abc" by hash starting from index 1
            3

        Raises:
            AssertionError: If the length is negative or ``0 <= l <= r <= n``
                does not hold.

        Time Complexity:
            O(1 + max(0, r - l - substring_length + 1) * log(n + 1))

        Space Complexity:
            O(1) auxiliary space
        """
        if r is None: r = self.n
        assert 0 <= l <= r <= self.n
        assert substring_length >= 0
        if substring_length == 0: return l if substring_hash == 0 else -1
        if r - l < substring_length: return -1
        for i in range(r - l - substring_length + 1):
            if self.get_hash(i + l, i + l + substring_length) == substring_hash: return i + l
        return -1


def find_2d_pattern(grid: Sequence[str], pattern: Sequence[str], row_base: int = 972663749, col_base: int = 911382323) -> list[tuple[int, int]]:
    """
    Find all top-left positions where a 2D character pattern appears.

    Args:
        grid: Rectangular text grid.
        pattern: Rectangular pattern grid.
        row_base: Rolling-hash base for the vertical direction, in [1, mod).
        col_base: Rolling-hash base for the horizontal direction, in [1, mod).

    Returns:
        List of exact matching ``(row, column)`` positions in row-major order.
        Horizontal hash candidates are checked against pattern row strings;
        vertical candidates are checked against their row-id sequences.
        Empty grids or zero-width patterns return [].

    Raises:
        ValueError: If ``grid`` or ``pattern`` is not rectangular or either
            base is outside [1, mod).

    Time Complexity:
        O(HW + RC + K_h * C + K_v * R), where H * W is the grid size,
        R * C is the pattern size, and K_h and K_v are the numbers of
        horizontal and vertical hash candidates checked, respectively.

    Space Complexity:
        O(HW)
    """
    mod = RollingHashMersenneMod.mod
    if not (0 < row_base < mod and 0 < col_base < mod):
        raise ValueError('hash bases must be in [1, mod)')
    h, w = len(grid), len(grid[0]) if grid else 0
    r, c = len(pattern), len(pattern[0]) if pattern else 0
    for row in grid:
        if len(row) != w:
            raise ValueError('grid must be rectangular')
    for row in pattern:
        if len(row) != c:
            raise ValueError('pattern must be rectangular')
    if r == 0 or c == 0 or h < r or w < c:
        return []

    row_ids = {row: i + 1 for i, row in enumerate(pattern)}
    row_patterns: dict[int, dict[str, int]] = {}
    for row, label in row_ids.items():
        value = 0
        for ch in row:
            value = (value * col_base + ord(ch) + 1) % mod
        row_patterns.setdefault(value, {})[row] = label
    pattern_ids = [row_ids[row] for row in pattern]

    columns: list[list[int]] = [[] for _ in range(w - c + 1)]
    col_power = pow(col_base, c, mod)
    for row in grid:
        value = 0
        for ch in row[:c]:
            value = (value * col_base + ord(ch) + 1) % mod
        for j in range(w - c + 1):
            candidates = row_patterns.get(value)
            columns[j].append(candidates.get(row[j:j + c], 0) if candidates is not None else 0)
            if j + c < w:
                value = (value * col_base + ord(row[j + c]) + 1 - (ord(row[j]) + 1) * col_power) % mod

    pattern_hash = 0
    for label in pattern_ids:
        pattern_hash = (pattern_hash * row_base + label) % mod
    row_power = pow(row_base, r, mod)
    matches: list[list[int]] = [[] for _ in range(h - r + 1)]
    for j, column in enumerate(columns):
        value = 0
        for label in column[:r]:
            value = (value * row_base + label) % mod
        for i in range(h - r + 1):
            if value == pattern_hash and column[i:i + r] == pattern_ids:
                matches[i].append(j)
            if i + r < h:
                value = (value * row_base + column[i + r] - column[i] * row_power) % mod
    return [(i, j) for i, row in enumerate(matches) for j in row]
