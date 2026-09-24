#!/usr/bin/env python3

from __future__ import annotations

from array import array

from cplib.datastructure.sparsetable import SparseTable


class SuffixArray:
    """
    A class implementing suffix array with SA-IS algorithm.
    Provides efficient string processing capabilities including longest common prefix computation.

    Attributes:
        n (int): Length of the input string
        str (list[int]): Input string converted to integer array
        arr (list[int]): Suffix array
        lcp (list[int]): LCP (Longest Common Prefix) array
        rnk (list[int]): Rank array (inverse of suffix array)
        rmq (SparseTable): Range Minimum Query structure for LCP array

    Examples:
        >>> sa = SuffixArray("banana")
        >>> sa.arr  # Suffix array
        [5, 3, 1, 0, 4, 2]
        >>> sa.lcp  # LCP array
        [1, 3, 0, 0, 2]

    Args:
        string: Input string.

    Space Complexity:
        O(n) after construction; O(n log n) after an LCP query builds the
        sparse table.
    """
    def __init__(self, string: str) -> None:
        '''
        Initialize SuffixArray with a string.

        Args:
            string (str): Input string to build suffix array for

        Returns:
            None.

        Time Complexity:
            O(n) for byte-range characters; O(n + sigma log sigma) otherwise,
            where sigma is the number of distinct characters.
        '''
        self.n = len(string)
        self.str = [ord(c) for c in string]
        self.arr = self.build_sa()
        self.lcp, self.rnk = self.build_lcp()
        self.rmq: SparseTable[int] | None = None

    def build_sa(self) -> list[int]:
        """
        Build suffix array using SA-IS algorithm.
        Implementation includes three methods:
        - sa_naive: Simple O(n^2 log n) implementation for small strings
        - sa_doubling: O(n (log n)^2) implementation for medium strings
        - sa_is: O(n) implementation for large strings

        Returns:
            list[int]: Suffix array of the string

        Notes:
            This method automatically chooses the best algorithm based on string length:
            - n < 10: sa_naive
            - n < 100: sa_doubling
            - n >= 100: sa_is

        Time Complexity:
            O(n) for byte-range characters; O(n + sigma log sigma) otherwise.
        """
        def sa_naive(s: list[int]) -> list[int]:
            """Sort suffix copies; used only for fewer than ten characters."""
            n = len(s)
            sa = list(range(n))
            sa.sort(key=lambda x: s[x:])
            return sa

        def sa_doubling(s: list[int]) -> list[int]:
            """Rank doubling with O(n log^2 n) time and O(n) space."""
            n = len(s)
            sa = list(range(n))
            rnk = s
            tmp = [0] * n
            k = 1
            while k < n:
                sa.sort(key=lambda x: (rnk[x], rnk[x + k]) if x + k < n else (rnk[x], -1))
                tmp[sa[0]] = 0
                for i in range(1, n):
                    tmp[sa[i]] = tmp[sa[i - 1]]
                    x = (rnk[sa[i - 1]], rnk[sa[i - 1] + k]) if sa[i - 1] + k < n else (rnk[sa[i - 1]], -1)
                    y = (rnk[sa[i]], rnk[sa[i] + k]) if sa[i] + k < n else (rnk[sa[i]], -1)
                    if x < y: tmp[sa[i]] += 1
                k *= 2
                tmp, rnk = rnk, tmp
            return sa

        def sa_is(s: list[int], upper: int) -> list[int]:
            """Induced sorting in O(n + upper) time and space."""
            n = len(s)
            if n == 0: return []
            if n == 1: return [0]
            if n == 2:
                if s[0] < s[1]: return [0, 1]
                else: return [1, 0]
            if n < 10:
                return sa_naive(s)
            if n < 100:
                return sa_doubling(s)
            ls = [0] * n
            for i in range(n - 1)[::-1]:
                ls[i] = ls[i + 1] if s[i] == s[i + 1] else s[i] < s[i + 1]
            sum_l = [0] * (upper + 1)
            sum_s = [0] * (upper + 1)
            for i in range(n):
                if ls[i]:
                    sum_l[s[i] + 1] += 1
                else:
                    sum_s[s[i]] += 1
            for i in range(upper):
                sum_s[i] += sum_l[i]
                if i < upper:
                    sum_l[i + 1] += sum_s[i]
            lms_map = [-1] * (n + 1)
            m = 0
            for i in range(1, n):
                if not ls[i - 1] and ls[i]:
                    lms_map[i] = m
                    m += 1
            lms: list[int] = []
            for i in range(1, n):
                if not ls[i - 1] and ls[i]:
                    lms.append(i)
            sa = [-1] * n
            buf = sum_s.copy()
            for d in lms:
                if d == n: continue
                sa[buf[s[d]]] = d
                buf[s[d]] += 1
            buf = sum_l.copy()
            sa[buf[s[n - 1]]] = n - 1
            buf[s[n - 1]] += 1
            for i in range(n):
                v = sa[i]
                if v >= 1 and not ls[v - 1]:
                    sa[buf[s[v - 1]]] = v - 1
                    buf[s[v - 1]] += 1
            buf = sum_l.copy()
            for i in range(n)[::-1]:
                v = sa[i]
                if v >= 1 and ls[v - 1]:
                    buf[s[v - 1] + 1] -= 1
                    sa[buf[s[v - 1] + 1]] = v - 1
            if m == 0: return sa
            sorted_lms: list[int] = []
            for v in sa:
                if lms_map[v] != -1: sorted_lms.append(v)
            rec_s = [0] * m
            rec_upper = 0
            rec_s[lms_map[sorted_lms[0]]] = 0
            for i in range(1, m):
                l = sorted_lms[i - 1]
                r = sorted_lms[i]
                end_l = lms[lms_map[l] + 1] if lms_map[l] + 1 < m else n
                end_r = lms[lms_map[r] + 1] if lms_map[r] + 1 < m else n
                same = True
                if end_l - l != end_r - r:
                    same = False
                else:
                    while l < end_l:
                        if s[l] != s[r]:
                            break
                        l += 1
                        r += 1
                    if l == n or s[l] != s[r]:
                        same = False
                if not same:
                    rec_upper += 1
                rec_s[lms_map[sorted_lms[i]]] = rec_upper
            rec_sa = sa_is(rec_s, rec_upper) #recursive call
            for i in range(m):
                sorted_lms[i] = lms[rec_sa[i]]
            sa = [-1] * n
            buf = sum_s.copy()
            for d in sorted_lms:
                if d == n: continue
                sa[buf[s[d]]] = d
                buf[s[d]] += 1
            buf = sum_l.copy()
            sa[buf[s[n - 1]]] = n - 1
            buf[s[n - 1]] += 1
            for i in range(n):
                v = sa[i]
                if v >= 1 and not ls[v - 1]:
                    sa[buf[s[v - 1]]] = v - 1
                    buf[s[v - 1]] += 1
            buf = sum_l.copy()
            for i in range(n)[::-1]:
                v = sa[i]
                if v >= 1 and ls[v - 1]:
                    buf[s[v - 1] + 1] -= 1
                    sa[buf[s[v - 1] + 1]] = v - 1
            return sa

        if max(self.str, default=0) <= 255:
            return sa_is(self.str.copy(), 255)
        alphabet = sorted(set(self.str))
        rank = {value: i for i, value in enumerate(alphabet)}
        return sa_is([rank[value] for value in self.str], len(alphabet) - 1)

    def build_lcp(self) -> tuple[list[int], list[int]]:
        """
        Build LCP (Longest Common Prefix) array and rank array.
        Uses Kasai's algorithm which runs in O(n) time.

        Returns:
            tuple[list[int], list[int]]: A tuple containing:
                - LCP array: lcp[i] is the length of longest common prefix of
                  suffixes starting at arr[i] and arr[i+1]
                - Rank array: inverse of suffix array, rnk[arr[i]] = i

        Examples:
            >>> sa = SuffixArray("banana")
            >>> sa.lcp  # LCP array
            [1, 3, 0, 0, 2]
            >>> sa.rnk  # Rank array
            [3, 2, 5, 1, 4, 0]

        Time Complexity:
            O(n)
        """
        rnk = [0] * self.n
        for i in range(self.n):
            rnk[self.arr[i]] = i
        lcp = [0] * (self.n - 1)
        h = 0
        for i in range(self.n):
            if h > 0:
                h -= 1
            if rnk[i] == 0:
                continue
            j = self.arr[rnk[i] - 1]
            while j + h < self.n and i + h < self.n:
                if self.str[j + h] != self.str[i + h]:
                    break
                h += 1
            lcp[rnk[i] - 1] = h
        return lcp, rnk

    def get_lcp(self, l: int, r: int) -> int:
        """
        Get length of longest common prefix of suffixes starting at positions l and r.
        Uses Range Minimum Query on LCP array to compute result in O(1) time.

        Args:
            l (int): Starting position of first suffix, in [0, n].
            r (int): Starting position of second suffix, in [0, n].

        Returns:
            int: Length of longest common prefix. Position n is the empty suffix.

        Raises:
            IndexError: If either position is outside [0, n].

        Examples:
            >>> sa = SuffixArray("banana")
            >>> sa.get_lcp(1, 3)  # Length of LCP of "anana" and "ana"
            3

        Time Complexity:
            O(n log n) on the first call, then O(1)
        """
        if not (0 <= l <= self.n and 0 <= r <= self.n):
            raise IndexError('suffix position must be within [0, n]')
        if l == self.n or r == self.n: return 0
        if l == r: return self.n - l
        if self.rmq is None:
            self.rmq = SparseTable(self.lcp, min)
        l, r = self.rnk[l], self.rnk[r]
        if l > r: l, r = r, l
        return self.rmq.prod(l, r)


def count_distinct_substrings_by_sa(input_string: str) -> int:
    """
    Calculate the number of distinct substrings in a given string using suffix array.

    Args:
        input_string (str): Input string

    Returns:
        int: Number of distinct substrings

    Examples:
        >>> count_distinct_substrings_by_sa("banana")
        15

    Time Complexity:
        O(n) for byte-range characters; O(n + sigma log sigma) otherwise,
        where sigma is the number of distinct characters.

    Space Complexity:
        O(n)
    """
    sa = SuffixArray(input_string)
    n = len(input_string)
    total_substrings = n * (n + 1) // 2
    lcp_sum = sum(sa.lcp)
    return total_substrings - lcp_sum


def longest_common_substring(input_string_0: str, input_string_1: str) -> tuple[str, int, int, int, int]:
    """
    Find the longest common substring between two strings.

    Computes the longest substring that appears in both input strings using suffix array
    and LCP (Longest Common Prefix) array. The algorithm concatenates the two strings
    with a separator and uses the suffix array to efficiently find the longest match.

    Args:
        input_string_0: First string to compare
        input_string_1: Second string to compare

    Returns:
        A tuple containing:
            - The longest common substring (empty string if none exists)
            - Start position in input_string_0 (0 if no common substring)
            - End position in input_string_0 (0 if no common substring)
            - Start position in input_string_1 (0 if no common substring)
            - End position in input_string_1 (0 if no common substring)

    Examples:
        >>> longest_common_substring("banana", "ananas")
        ('anana', 1, 6, 0, 5)

        >>> longest_common_substring("abcdef", "xyz")
        ('', 0, 0, 0, 0)

        >>> longest_common_substring("programming", "grammars")
        ('gramm', 3, 8, 0, 5)

    Notes:
        - The separator is chosen outside the input alphabet. If every
          Unicode code point occurs, a suffix automaton is used instead.
        - If multiple longest common substrings exist, returns the first one found
        - The returned positions are 0-indexed and follow Python's slice convention
          where substring = string[start:end]

    Time Complexity:
        O(n + m + sigma log sigma), where n and m are the input lengths and
        sigma is the number of distinct characters. Byte-range input takes O(n + m).

    Space Complexity:
        O(n + m)
    """
    n = len(input_string_0)
    if not input_string_0 or not input_string_1:
        return ('', 0, 0, 0, 0)
    sep = chr(0)
    if sep in input_string_0 or sep in input_string_1:
        alphabet = set(input_string_0) | set(input_string_1)
        for code in range(0x110000):
            sep = chr(code)
            if sep not in alphabet:
                break
        else:
            return SuffixAutomaton(input_string_0).longest_common_substring(input_string_1)
    string = input_string_0 + sep + input_string_1
    sa = SuffixArray(string)
    best_len = 0
    best_s_pos = best_t_pos = -1

    for i in range(len(string) - 1):
        a, b = sa.arr[i], sa.arr[i + 1]
        if a == n or b == n:
            continue
        if (a < n) ^ (b < n):
            if sa.lcp[i] > best_len:
                best_len = sa.lcp[i]
                if a < n:
                    best_s_pos = a
                    best_t_pos = b - (n + 1)
                else:
                    best_s_pos = b
                    best_t_pos = a - (n + 1)

    if best_len == 0:
        return ('', 0, 0, 0, 0)

    return (input_string_0[best_s_pos:best_s_pos + best_len], best_s_pos, best_s_pos + best_len, best_t_pos, best_t_pos + best_len)


class SuffixAutomaton:
    """
    A class implementing suffix automaton for a single string.
    Provides efficient string processing capabilities including substring queries,
    distinct substring counting, and longest common substring computation.

    Attributes:
        next (list[dict[str, int]]): Transition table for each automaton state
        link (list[int]): Suffix link of each state
        length (list[int]): Maximum length represented by each state
        occurrence_count (list[int]): Online terminal counts, before suffix-link
            propagation. Use build_occurrence_counts() for total occurrences.
        last (int): Index of the current terminal state

    Args:
        string: Initial string used to build the automaton.

    Space Complexity:
        - O(n)

    Examples:
        >>> sam = SuffixAutomaton("banana")
        >>> sam.contains("ana")
        True
        >>> sam.count_distinct_substrings()
        15
    """
    def __init__(self, string: str = "") -> None:
        '''
        Initialize SuffixAutomaton with a string.

        Args:
            string (str): Input string to build suffix automaton for

        Returns:
            None.

        Time Complexity:
            - O(len(string)) amortized

        Examples:
            >>> sam = SuffixAutomaton("aba")
            >>> len(sam)
            4
        '''
        self.next: list[dict[str, int]] = [{}]
        self.link: list[int] = [-1]
        self.length: list[int] = [0]
        self.occurrence_count: list[int] = [0]
        self._first_pos: list[int] = [-1]
        self.last = 0
        for char in string:
            self.extend(char)

    def __len__(self) -> int:
        '''
        Return the number of states in the automaton.

        Returns:
            int: Number of states

        Time Complexity:
            - O(1)
        '''
        return len(self.next)

    def extend(self, char: str) -> int:
        """
        Extend the automaton by appending one character.

        Args:
            char (str): A string containing exactly one character.

        Returns:
            int: Index of the new terminal state

        Raises:
            ValueError: If char does not contain exactly one character.

        Time Complexity:
            - O(1) amortized

        Examples:
            >>> sam = SuffixAutomaton()
            >>> sam.extend("a")
            1
        """
        if len(char) != 1:
            raise ValueError('char must contain exactly one character')
        cur = len(self.next)
        self.next.append({})
        self.link.append(0)
        self.length.append(self.length[self.last] + 1)
        self.occurrence_count.append(1)
        self._first_pos.append(self.length[cur] - 1)

        p = self.last
        while p != -1 and char not in self.next[p]:
            self.next[p][char] = cur
            p = self.link[p]

        if p == -1:
            self.link[cur] = 0
        else:
            q = self.next[p][char]
            if self.length[p] + 1 == self.length[q]:
                self.link[cur] = q
            else:
                clone = len(self.next)
                self.next.append(self.next[q].copy())
                self.link.append(self.link[q])
                self.length.append(self.length[p] + 1)
                self.occurrence_count.append(0)
                self._first_pos.append(self._first_pos[q])
                while p != -1 and self.next[p].get(char) == q:
                    self.next[p][char] = clone
                    p = self.link[p]
                self.link[q] = clone
                self.link[cur] = clone

        self.last = cur
        return cur

    def transition(self, state: int, char: str) -> int:
        """
        Get the transition destination from a state by one character.

        Args:
            state (int): Source state
            char (str): Transition character

        Returns:
            int: Destination state, or -1 if the transition does not exist

        Raises:
            IndexError: If state is outside the allocated state range.
            ValueError: If char does not contain exactly one character.

        Time Complexity:
            - O(1) average

        Examples:
            >>> sam = SuffixAutomaton("ab")
            >>> sam.transition(0, "a")
            1
        """
        if not 0 <= state < len(self.next):
            raise IndexError('state index out of range')
        if len(char) != 1:
            raise ValueError('char must contain exactly one character')
        return self.next[state].get(char, -1)

    def contains(self, substring: str) -> bool:
        """
        Check whether a substring appears in the built string.

        Args:
            substring (str): Query substring

        Returns:
            bool: True if substring appears, otherwise False

        Time Complexity:
            - O(len(substring)) average

        Examples:
            >>> sam = SuffixAutomaton("banana")
            >>> sam.contains("nan")
            True
        """
        state = 0
        for char in substring:
            state = self.transition(state, char)
            if state == -1:
                return False
        return True

    def count_distinct_substrings(self) -> int:
        """
        Count the number of distinct substrings.

        Returns:
            int: Number of distinct substrings

        Time Complexity:
            - O(|states|)

        Examples:
            >>> sam = SuffixAutomaton("aba")
            >>> sam.count_distinct_substrings()
            5
        """
        total = 0
        for state in range(1, len(self.next)):
            total += self.length[state] - self.length[self.link[state]]
        return total

    def build_occurrence_counts(self) -> list[int]:
        """
        Compute end-position counts for each state without changing online counts.

        Repeated calls and further extensions are supported. The root count
        is the source length, counting the non-empty processed prefixes.

        Returns:
            list[int]: End-position count of each state

        Time Complexity:
            - O(|states| log |states|)

        Examples:
            >>> sam = SuffixAutomaton("aaa")
            >>> counts = sam.build_occurrence_counts()
            >>> counts[sam.transition(0, "a")]
            3
        """
        order = sorted(range(len(self.next)), key=self.length.__getitem__, reverse=True)
        counts = self.occurrence_count[:]
        for state in order:
            parent = self.link[state]
            if parent != -1:
                counts[parent] += counts[state]
        return counts

    def longest_common_substring(self, other: str) -> tuple[str, int, int, int, int]:
        """
        Find the longest common substring with another string.

        Args:
            other (str): String to compare against

        Returns:
            tuple[str, int, int, int, int]: A tuple containing:
                - The longest common substring
                - Start position in the source string
                - End position in the source string
                - Start position in the other string
                - End position in the other string

        Time Complexity:
            - O(len(other)) average

        Examples:
            >>> sam = SuffixAutomaton("banana")
            >>> sam.longest_common_substring("ananas")
            ('anana', 1, 6, 0, 5)
        """
        state = 0
        length = 0
        best_len = 0
        best_other_r = 0
        best_state = 0

        for i, char in enumerate(other):
            while state != 0 and char not in self.next[state]:
                state = self.link[state]
                length = self.length[state]
            nxt = self.next[state].get(char)
            if nxt is None:
                state = 0
                length = 0
                continue
            state = nxt
            length += 1
            if length > best_len:
                best_len = length
                best_other_r = i + 1
                best_state = state

        if best_len == 0:
            return ("", 0, 0, 0, 0)

        other_l = best_other_r - best_len
        self_r = self.first_pos(best_state) + 1
        self_l = self_r - best_len
        return (other[other_l:best_other_r], self_l, self_r, other_l, best_other_r)

    def first_pos(self, state: int) -> int:
        """
        Return one end position of substrings represented by a state.

        Args:
            state (int): Target state

        Returns:
            int: One end position in the source string, or -1 for the root.

        Raises:
            IndexError: If state is outside the allocated state range.

        Time Complexity:
            - O(1)

        Examples:
            >>> sam = SuffixAutomaton("banana")
            >>> sam.first_pos(sam.transition(0, "b"))
            0
        """
        if not 0 <= state < len(self.next):
            raise IndexError('state index out of range')
        return self._first_pos[state]


def count_distinct_substrings(input_string: str) -> int:
    """
    Calculate the number of distinct substrings in a given string.

    Args:
        input_string (str): Input string

    Returns:
        int: Number of distinct substrings

    Time Complexity:
        - O(len(input_string)) amortized

    Space Complexity:
        - O(len(input_string))

    Examples:
        >>> count_distinct_substrings("banana")
        15
    """
    return SuffixAutomaton(input_string).count_distinct_substrings()


class CompactSuffixAutomaton:
    """
    Memory-efficient suffix automaton for substring queries.

    Transitions are stored as linked arrays instead of one dictionary per state.
    This is useful when the source string is large and the main operation is
    ``contains`` rather than enumerating transitions.

    Args:
        string: Initial string used to build the automaton.

    Space Complexity:
        O(number of states + number of transitions).
    """
    def __init__(self, string: str = '') -> None:
        """
        Initialize the automaton.

        Args:
            string: Input string to build from.

        Returns:
            None.

        Time Complexity:
            O(len(string) * A) in the worst case, where ``A`` is the maximum
            out-degree scanned by a transition lookup.
        """
        self.length = array('i', [0])
        self.link = array('i', [-1])
        self.head = array('i', [-1])
        self.to = array('i')
        self.char = array('i')
        self.next = array('i')
        self.last = 0
        for ch in string:
            self.extend(ch)

    def __len__(self) -> int:
        """
        Return the number of states.

        Returns:
            Number of states.

        Time Complexity:
            O(1)
        """
        return len(self.length)

    def _new_state(self, length: int, link: int = 0) -> int:
        state = len(self.length)
        self.length.append(length)
        self.link.append(link)
        self.head.append(-1)
        return state

    def _find_edge(self, state: int, c: int) -> int:
        edge = self.head[state]
        while edge != -1:
            if self.char[edge] == c:
                return edge
            edge = self.next[edge]
        return -1

    def _add_edge(self, state: int, c: int, dest: int) -> None:
        self.char.append(c)
        self.to.append(dest)
        self.next.append(self.head[state])
        self.head[state] = len(self.to) - 1

    def _copy_transitions(self, src: int, dst: int) -> None:
        edge = self.head[src]
        while edge != -1:
            self._add_edge(dst, self.char[edge], self.to[edge])
            edge = self.next[edge]

    def transition(self, state: int, char: str | int) -> int:
        """
        Get the transition destination from a state by one character.

        Args:
            state: Source state.
            char: A single character or its Unicode code point in [0, 0x10ffff].

        Returns:
            Destination state, or ``-1`` if the transition does not exist.

        Raises:
            IndexError: If state is outside the allocated state range.
            ValueError: If char is not one character or a valid code point.

        Time Complexity:
            O(out-degree of ``state``).
        """
        if not 0 <= state < len(self.length):
            raise IndexError('state index out of range')
        if isinstance(char, str) and len(char) != 1:
            raise ValueError('char must contain exactly one character')
        c = ord(char) if isinstance(char, str) else char
        if not 0 <= c <= 0x10ffff:
            raise ValueError('code point must be within [0, 0x10ffff]')
        edge = self._find_edge(state, c)
        return -1 if edge == -1 else self.to[edge]

    def extend(self, char: str | int) -> int:
        """
        Extend the automaton by appending one character.

        Args:
            char: A single character or its Unicode code point in [0, 0x10ffff].

        Returns:
            Index of the new terminal state.

        Raises:
            ValueError: If char is not one character or a valid code point.

        Time Complexity:
            O(A) amortized in typical small-alphabet use, where ``A`` is the
            maximum scanned out-degree.
        """
        if isinstance(char, str) and len(char) != 1:
            raise ValueError('char must contain exactly one character')
        c = ord(char) if isinstance(char, str) else char
        if not 0 <= c <= 0x10ffff:
            raise ValueError('code point must be within [0, 0x10ffff]')
        cur = self._new_state(self.length[self.last] + 1)
        p = self.last
        while p != -1 and self._find_edge(p, c) == -1:
            self._add_edge(p, c, cur)
            p = self.link[p]

        if p == -1:
            self.link[cur] = 0
        else:
            q = self.to[self._find_edge(p, c)]
            if self.length[p] + 1 == self.length[q]:
                self.link[cur] = q
            else:
                clone = self._new_state(self.length[p] + 1, self.link[q])
                self._copy_transitions(q, clone)
                while p != -1:
                    edge = self._find_edge(p, c)
                    if edge == -1 or self.to[edge] != q:
                        break
                    self.to[edge] = clone
                    p = self.link[p]
                self.link[q] = clone
                self.link[cur] = clone

        self.last = cur
        return cur

    def contains(self, substring: str) -> bool:
        """
        Check whether a substring appears in the built string.

        Args:
            substring: Query substring.

        Returns:
            True if ``substring`` appears, otherwise False.

        Time Complexity:
            O(len(substring) * A), where ``A`` is the maximum scanned out-degree.
        """
        state = 0
        for ch in substring:
            state = self.transition(state, ch)
            if state == -1:
                return False
        return True
