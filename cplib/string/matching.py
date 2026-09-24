#!/usr/bin/env python3

from array import array
from collections import deque
from collections.abc import Iterator

from cplib.mathematics.convolution import ConvolutionMod


class _WildcardConvolution(ConvolutionMod):
    """Keep matching counts independent of the caller's convolution modulus."""


def z_algorithm(input_string: str) -> list[int]:
    """
    Compute Z-array using Z-algorithm.

    The Z-array Z[i] contains the length of the longest substring starting
    from s[i] which is also a prefix of s.

    Args:
        input_string: The input string.

    Returns:
        Z-array where Z[i] is the length of longest substring starting at i
        that matches a prefix of the string.

    Notes:
        Z[0] is set to the length of the entire string.
        Uses the Z-algorithm with left and right pointers for linear time.

    Examples:
        >>> # Z[0] = 7 (entire string)
        >>> # Z[1] = 0 ('bacaba' has no common prefix with 'abacaba')
        >>> # Z[2] = 1 ('acaba' shares 'a' with 'abacaba')
        >>> # Z[4] = 3 ('aba' matches the prefix 'aba')
        >>> z_algorithm('abacaba')
        [7, 0, 1, 0, 3, 0, 1]

    Time Complexity:
        O(n)

    Space Complexity:
        O(n) in the size of newly allocated output or auxiliary storage
    """
    n = len(input_string)
    s = [ord(c) for c in input_string]
    if n == 0: return []
    z = [0] * n
    j = 0
    for i in range(1, n):
        z[i] = 0 if j + z[j] <= i else min(j + z[j] - i, z[i - j])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if j + z[j] < i + z[i]:
            j = i
    z[0] = n
    return z


def knuth_morris_pratt(text: str, pattern: str) -> list[int]:
    """
    Find all occurrences of pattern in text using KMP algorithm.

    Args:
        text: The text to search in.
        pattern: The pattern to search for.

    Returns:
        List of starting indices of all pattern occurrences in text. An empty
        pattern matches every position from 0 through len(text).

    Notes:
        Uses failure function (prefix function) to avoid re-examining
        characters. The failure function pi[i] is the length of the longest
        proper prefix of pattern[0..i] that is also a suffix.

    Examples:
        >>> # Pattern 'aba' occurs at positions 0 and 4
        >>> knuth_morris_pratt('abacaba', 'aba')
        [0, 4]

        >>> knuth_morris_pratt('aabaacaadaabaaba', 'aaba')
        [0, 9, 12]

    Time Complexity:
        O(n + m), where n is ``len(text)`` and m is ``len(pattern)``

    Space Complexity:
        O(m + k), where k is the number of reported matches.
    """

    n, m = len(text), len(pattern)
    if m == 0: return list(range(n + 1))
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    res: list[int] = []
    j = 0
    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = pi[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            res.append(i - m + 1)
            j = pi[j - 1]
    return res


def wildcard_pattern_matching(text: str, pattern: str) -> list[bool]:
    """
    Find all positions where pattern matches text with wildcard support.

    Performs pattern matching where '*' in either text or pattern acts as a wildcard
    that can match any single character. Uses exact NTT-based convolution for efficient
    matching of all positions simultaneously.

    Args:
        text: The text string to search in (may contain wildcards)
        pattern: The pattern string to search for (may contain wildcards)

    Returns:
        list[bool]: Boolean array of length (n - m + 1) where result[i] is True
                   if pattern matches text starting at position i. An empty
                   pattern matches all n + 1 positions.

    Raises:
        ValueError: If pattern length is greater than text length or the
            required NTT length exceeds 2**23.

    Notes:
        - '*' is the wildcard character that matches any single character
        - Both text and pattern can contain wildcards
        - Uses convolution to count matching characters at each position
        - A position matches if all non-wildcard pairs match
        - Algorithm:
          1. Count total non-wildcard pairs for each position
          2. For each distinct character, count matching pairs
          3. Position matches if matching pairs equals non-wildcard pairs

    Examples:
        >>> wildcard_pattern_matching("abacaba", "aba")
        [True, False, False, False, True]

        >>> wildcard_pattern_matching("ab*cab*", "a*a")
        [True, False, True, False, True]

    Space Complexity:
        O(n) in the size of newly allocated output or auxiliary storage

    Time Complexity:
        O(sigma * (n + m) log(n + m)), where sigma is the number of distinct
        non-``'*'`` characters appearing in ``text`` or ``pattern``
    """
    n, m = len(text), len(pattern)
    if m > n:
        raise ValueError("Pattern length cannot be greater than text length")
    if m == 0:
        return [True] * (n + 1)
    if n + m - 1 > 1 << 23:
        raise ValueError('convolution length must be at most 2**23')
    if _WildcardConvolution.get_mod() != 998244353:
        _WildcardConvolution.set_mod(998244353)

    non_ast_t = [1 if c != '*' else 0 for c in text]
    non_ast_p = [1 if c != '*' else 0 for c in pattern]
    conv_non = _WildcardConvolution.convolution(non_ast_t, non_ast_p[::-1])
    total_non_ast_pairs = conv_non[m - 1: n]

    letters = sorted((set(text) | set(pattern)) - {'*'})
    equal_counts = [0] * (n - m + 1)

    for ch in letters:
        ch_t = [1 if c == ch else 0 for c in text]
        ch_p = [1 if c == ch else 0 for c in pattern]
        conv_eq = _WildcardConvolution.convolution(ch_t, ch_p[::-1])
        for i in range(n - m + 1):
            equal_counts[i] += conv_eq[m - 1 + i]

    return [(total_non_ast_pairs[i] - equal_counts[i] == 0) for i in range(n - m + 1)]


class AhoCorasick:
    """
    Aho-Corasick automaton for multi-pattern matching on lowercase ASCII.

    The trie stores inserted patterns, ``build`` adds failure links, and
    ``search`` streams all matched patterns together with their start indices.
    All inserted patterns and searched texts must contain only lowercase
    ``'a'`` through ``'z'`` characters.

    Let ``L`` be the total length of inserted patterns, ``V`` the number of
    trie nodes, ``Z`` the total number of propagated output pattern ids stored
    over all nodes, and ``A = 26``.

    Args:
        None.

    Space Complexity:
        ``O(L + V * A + Z)``.

    Examples:
        >>> ac = AhoCorasick()
        >>> _ = ac.insert('he')
        >>> _ = ac.insert('she')
        >>> ac.build()
        >>> list(ac.search('ushers'))
        [('she', 1), ('he', 2)]
    """
    alphabet_size = 26
    alphabet_base = ord('a')

    def __init__(self) -> None:
        """Initialize the empty automaton.

        Returns:
            None.

        Time Complexity:
            ``O(A)``.

        Space Complexity:
            ``O(A)``.
        """
        self.trie = [array('i', [-1]) * self.alphabet_size]
        self.fail = array('i', [0])
        self.par  = array('i', [-1])
        self.output: list[array[int]] = [array('i')]
        self.word_pool = bytearray()
        self.word_start = array('i')
        self.word_len   = array('i')
        self.built = False

    def _char_id(self, char: int | str) -> int:
        if isinstance(char, int):
            return char - self.alphabet_base
        return ord(char) - self.alphabet_base

    def insert(self, word: str) -> int:
        """
        Insert a lowercase ASCII pattern into the trie.

        Args:
            word: Pattern to insert. The empty pattern matches every position,
                including the start and end of the text.

        Returns:
            The terminal trie node for ``word``. Pattern ids used by
            search_ids are assigned separately in insertion order, starting
            at zero. Duplicate insertions receive separate pattern ids.

        Raises:
            RuntimeError: If build has already been called.
            ValueError: If word contains a character outside 'a' through 'z'.

        Time Complexity:
            ``O(len(word))``.

        Space Complexity:
            ``O(len(word) * A)`` in the worst case for newly added trie nodes,
            plus ``O(len(word))`` for stored pattern bytes.
        """
        if self.built:
            raise RuntimeError('cannot insert after build')
        node = 0
        wb = word.encode('ascii')
        if wb and not (wb.isalpha() and wb.islower()):
            raise ValueError('word must contain only lowercase ASCII letters')
        for b in wb:
            c = self._char_id(b)
            if self.trie[node][c] == -1:
                self.trie[node][c] = len(self.trie)
                self.trie.append(array('i', [-1]) * self.alphabet_size)
                self.fail.append(0)
                self.par.append(node)
                self.output.append(array('i'))
            node = self.trie[node][c]
        idx = len(self.word_start)
        self.word_start.append(len(self.word_pool))
        self.word_len.append(len(wb))
        self.word_pool.extend(wb)
        self.output[node].append(idx)
        return node

    def build(self) -> None:
        """
        Build failure links and propagate pattern outputs.

        Let ``V`` be the number of trie nodes before the call, ``Z`` the total
        number of propagated output pattern ids copied into nodes, and
        ``A = 26``.

        Returns:
            None.

        Time Complexity:
            ``O(V * A + Z)``.

        Space Complexity:
            ``O(V)`` for the BFS queue, plus ``O(Z)`` for propagated outputs.
        """
        if self.built:
            return
        queue: deque[int] = deque()
        for char, nxt in enumerate(self.trie[0]):
            if nxt != -1:
                self.fail[nxt] = 0
                queue.append(nxt)
            else:
                self.trie[0][char] = 0
        while queue:
            v = queue.popleft()
            self.output[v].extend(self.output[self.fail[v]])
            for char, next_node in enumerate(self.trie[v]):
                if next_node != -1 and self.par[next_node] == v:
                    self.fail[next_node] = self.trie[self.fail[v]][char]
                    queue.append(next_node)
                else:
                    self.trie[v][char] = self.trie[self.fail[v]][char]
        self.built = True

    def _word_at(self, idx: int) -> str:
        """Return the stored pattern by id.

        Time Complexity:
            ``O(pattern length)``.

        Space Complexity:
            ``O(pattern length)`` for the decoded string.
        """
        s = self.word_start[idx]
        e = s + self.word_len[idx]
        return self.word_pool[s:e].decode('ascii')

    def search_ids(self, text: str) -> Iterator[tuple[int, int]]:
        """
        Yield all matched pattern ids in ``text``.

        Args:
            text: Lowercase ASCII text to scan.

        Yields:
            Pairs ``(pattern_id, start_index)`` for each match.

        Let ``R`` be the number of reported matches.

        Raises:
            ValueError: If text contains a character outside 'a' through 'z'.

        Time Complexity:
            ``O(len(text) + R)`` after build. The first search also builds
            failure links if needed.

        Space Complexity:
            ``O(1)`` besides the yielded output.
        """
        if not self.built:
            self.build()
        node = 0
        for j in self.output[0]:
            yield j, 0
        for i, char in enumerate(text):
            c = self._char_id(char)
            if not 0 <= c < self.alphabet_size:
                raise ValueError('text must contain only lowercase ASCII letters')
            node = self.trie[node][c]
            for j in self.output[node]:
                yield j, i - self.word_len[j] + 1

    def search(self, text: str) -> Iterator[tuple[str, int]]:
        """
        Yield all matches of the inserted patterns in ``text``.

        Args:
            text: Lowercase ASCII text to scan.

        Yields:
            Pairs ``(pattern, start_index)`` for each match.

        Let ``R`` be the number of reported matches and ``M`` the total length
        of reported pattern strings decoded for output.

        Time Complexity:
            ``O(len(text) + R + M)``.

        Space Complexity:
            ``O(max matched pattern length)`` for each yielded decoded string.
        """
        for j, start in self.search_ids(text):
            yield self._word_at(j), start
