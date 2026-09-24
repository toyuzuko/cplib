#!/usr/bin/env python3

"""Palindrome algorithms and palindromic tree utilities.

This module provides Manacher's algorithm and a palindromic tree (Eertree)
for distinct palindromic substrings while processing one string online.
"""

from __future__ import annotations


def manacher(input_string: str) -> list[int]:
    """
    Compute longest palindrome lengths using Manacher's algorithm.

    Finds all palindromic substrings in linear time. Returns array of length
    ``2N - 1`` where ``N`` is the input length. Even indices represent
    palindromes centered at characters, odd indices represent palindromes centered
    between characters.

    Args:
        input_string: The input string.

    Returns:
        Array where ``res[i]`` is the length of the longest palindrome centered
        at position ``i / 2``. Even indices are odd-length palindromes; odd
        indices are even-length palindromes.

    Notes:
        Uses sentinel values and expansion around centers with previously
        computed information for linear time complexity.

    Examples:
        >>> # res[0] = 1: 'a' centered at position 0
        >>> # res[2] = 3: 'aba' centered at position 1
        >>> # res[6] = 7: 'abacaba' centered at position 3
        >>> manacher('abacaba')
        [1, 0, 3, 0, 1, 0, 7, 0, 1, 0, 3, 0, 1]

    Time Complexity:
        O(n)

    Space Complexity:
        O(n) in the size of newly allocated output or auxiliary storage
    """

    n = len(input_string) * 2 + 1
    s = [ord(c) for c in input_string]
    res = [0] * n
    arr = [0] * n
    arr[0], arr[-1] = 1, 2 # sentinel values
    for i in range(len(s)):
        arr[i * 2 + 1] = s[i]
    c, r = 1, 0
    while c < n - 1:
        while arr[c - r] == arr[c + r]: r += 1
        res[c] = r
        d = 1
        while d <= r and res[c - d] < r - d:
            res[c + d] = res[c - d]
            d += 1
        c += d
        r = max(r - d, 0)
    for i in range(n):
        res[i] = (res[i] - (i % 2)) // 2 * 2 + (i % 2)
    return res[1 : n - 1]


class PalindromicTree:
    """
    Palindromic tree for distinct palindromic substrings.

    The implementation keeps two roots:

    - node ``0`` with length ``-1``
    - node ``1`` with length ``0``

    Every other node represents one distinct palindrome.

    Attributes:
        next: Outgoing transitions by added character.
        link: Suffix link of each node.
        length: Palindrome length of each node.
        occurrence_count: Number of times each node was the longest palindromic
            suffix during online construction.
        first_pos: End position of the first occurrence of each palindrome.
        parent: Creation parent in the palindromic tree.
        last: Node of the longest palindromic suffix of the current string.

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> tree = PalindromicTree("ababa")
        >>> tree.count_distinct_palindromes()
        5
        >>> tree.palindrome(tree.transition(2, "b"))
        'bab'

    Args:
        string: Input string.
    """

    def __init__(self, string: str = "") -> None:
        """Initialize a palindromic tree and optionally build a string.

        Args:
            string: Initial string to insert.

        Returns:
            None.

        Raises:
            ValueError: If ``string`` is not a string.

        Time Complexity:
            - ``O(len(string))`` amortized

        Examples:
            >>> tree = PalindromicTree("aaa")
            >>> tree.count_distinct_palindromes()
            3
        """
        string = self._validate_string(string)
        self._chars: list[str] = []
        self.next: list[dict[str, int]] = [{}, {}]
        self.link: list[int] = [0, 0]
        self.length: list[int] = [-1, 0]
        self.occurrence_count: list[int] = [0, 0]
        self.first_pos: list[int] = [-1, -1]
        self.parent: list[int] = [-1, -1]
        self.last = 1
        for char in string:
            self.extend(char)

    def _validate_string(self, string: object) -> str:
        if not isinstance(string, str):
            raise ValueError("string must be a str")
        return string

    @property
    def string(self) -> str:
        """
        Return the processed string.

        Returns:
            Processed string.

        Time Complexity:
            - ``O(n)``
        """
        return "".join(self._chars)

    def __len__(self) -> int:
        """Return the number of states, including the two roots.

        Returns:
            Number of states.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``
        """
        return len(self.length)

    def _validate_char(self, char: object) -> str:
        if not isinstance(char, str) or len(char) != 1:
            raise ValueError("char must be a single-character string")
        return char

    def _validate_node(self, node: int) -> None:
        if not 0 <= node < len(self.length):
            raise IndexError("node index out of range")

    def _find_suffix(self, node: int, pos: int, char: str) -> int:
        while True:
            palindrome_length = self.length[node]
            if pos - palindrome_length - 1 >= 0 and self._chars[pos - palindrome_length - 1] == char:
                return node
            node = self.link[node]

    def extend(self, char: str) -> int:
        """
        Append one character and return the longest suffix-palindrome node.

        Args:
            char: Character to append.

        Returns:
            Node index representing the longest palindromic suffix after the
            insertion.

        Time Complexity:
            - ``O(1)`` amortized

        Examples:
            >>> tree = PalindromicTree()
            >>> node = tree.extend("a")
            >>> tree.palindrome(node)
            'a'
        """
        char = self._validate_char(char)
        self._chars.append(char)
        pos = len(self._chars) - 1
        node = self._find_suffix(self.last, pos, char)
        nxt = self.next[node].get(char)
        if nxt is not None:
            self.last = nxt
            self.occurrence_count[nxt] += 1
            return nxt

        new_node = len(self.length)
        self.next.append({})
        self.link.append(0)
        self.length.append(self.length[node] + 2)
        self.occurrence_count.append(1)
        self.first_pos.append(pos)
        self.parent.append(node)
        self.next[node][char] = new_node

        if self.length[new_node] == 1:
            self.link[new_node] = 1
        else:
            suffix = self._find_suffix(self.link[node], pos, char)
            self.link[new_node] = self.next[suffix][char]

        self.last = new_node
        return new_node

    def add(self, char: str) -> int:
        """
        Alias for :meth:`extend`.

        Args:
            char: Character to append.

        Returns:
            Node index representing the longest palindromic suffix.

        Time Complexity:
            O(1) amortized
        """
        return self.extend(char)

    def transition(self, node: int, char: str) -> int:
        """
        Follow one outgoing transition from a node.

        Args:
            node: Source node.
            char: Transition character.

        Returns:
            Destination node, or ``-1`` if the transition does not exist.

        Time Complexity:
            - ``O(1)`` average
        """
        self._validate_node(node)
        char = self._validate_char(char)
        return self.next[node].get(char, -1)

    def palindrome(self, node: int) -> str:
        """
        Reconstruct the palindrome represented by one node.

        Args:
            node: Node index.

        Returns:
            Palindrome string for the given node. Root nodes return ``""``.

        Time Complexity:
            - ``O(length[node])``
        """
        self._validate_node(node)
        if node < 2:
            return ""
        end = self.first_pos[node]
        start = end - self.length[node] + 1
        return "".join(self._chars[start : end + 1])

    def longest_suffix_node(self) -> int:
        """
        Return the node of the current longest palindromic suffix.

        Returns:
            Node index of the current longest suffix palindrome.

        Time Complexity:
            - ``O(1)``
        """
        return self.last

    def longest_suffix_palindrome(self) -> str:
        """
        Return the current longest palindromic suffix.

        Returns:
            Longest palindrome that is also a suffix of the processed string.

        Time Complexity:
            - ``O(length[last])``
        """
        return self.palindrome(self.last)

    def count_distinct_palindromes(self) -> int:
        """
        Return the number of distinct palindromic substrings.

        Returns:
            Number of distinct palindromes found so far.

        Time Complexity:
            - ``O(1)``
        """
        return len(self.length) - 2

    def build_occurrence_counts(self) -> list[int]:
        """
        Compute total occurrence counts for every palindrome node.

        The online ``occurrence_count`` array stores how often a node appeared
        as the longest suffix palindrome. This method propagates those counts
        along suffix links and returns the total number of occurrences of each
        palindrome in the whole string.

        Returns:
            Total occurrence count for every node index.

        Time Complexity:
            - ``O(|nodes| log |nodes|)``

        Space Complexity:
            - ``O(|nodes|)``

        Examples:
            >>> tree = PalindromicTree("aaa")
            >>> counts = tree.build_occurrence_counts()
            >>> counts[2]
            3
        """
        counts = self.occurrence_count[:]
        order = sorted(range(2, len(self.length)), key=self.length.__getitem__, reverse=True)
        for node in order:
            counts[self.link[node]] += counts[node]
        return counts


def count_distinct_palindromes(input_string: str) -> int:
    """
    Count distinct palindromic substrings of a string.

    Args:
        input_string: Input string.

    Returns:
        Number of distinct palindromic substrings.

    Time Complexity:
        - ``O(len(input_string))`` amortized

    Space Complexity:
        - ``O(len(input_string))``
    """
    return PalindromicTree(input_string).count_distinct_palindromes()


__all__ = ["PalindromicTree", "count_distinct_palindromes"]
