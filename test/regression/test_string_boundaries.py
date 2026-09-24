from collections import Counter
import itertools
import random
import unittest

from cplib.mathematics.convolution import ConvolutionMod
from cplib.string.hashing import DynamicRollingHashMersenneMod, RollingHashMersenneMod, find_2d_pattern
from cplib.string.matching import AhoCorasick, knuth_morris_pratt, wildcard_pattern_matching, z_algorithm
from cplib.string.palindrome import PalindromicTree, manacher
from cplib.string.period import duval, enumerate_runs, minimum_representation
from cplib.string.suffix import CompactSuffixAutomaton, SuffixArray, SuffixAutomaton, longest_common_substring, count_distinct_substrings_by_sa
from cplib.string.trie import Trie


class StringBoundariesTest(unittest.TestCase):
    def test_suffix_arrays_and_lcp_for_unicode(self) -> None:
        rng = random.Random(0)
        alphabet = 'ab\0\1\2あ😀\U0010ffff'
        for n in (0, 1, 2, 9, 10, 99, 100, 101, 200):
            for _ in range(10):
                s = ''.join(rng.choice(alphabet) for _ in range(n))
                sa = SuffixArray(s)
                expected = sorted(range(n), key=lambda i: s[i:])
                self.assertEqual(sa.arr, expected)
                for _ in range(40):
                    l, r = rng.randrange(n + 1), rng.randrange(n + 1)
                    common = 0
                    while max(l, r) + common < n and s[l + common] == s[r + common]:
                        common += 1
                    self.assertEqual(sa.get_lcp(l, r), common)
                for l, r in ((-1, 0), (0, n + 1)):
                    with self.assertRaises(IndexError):
                        sa.get_lcp(l, r)

    def test_automaton_positions_counts_and_extensions(self) -> None:
        rng = random.Random(0)
        for _ in range(140):
            source = ''.join(rng.choice('ab\0あ') for _ in range(rng.randrange(14)))
            sam = SuffixAutomaton(source)
            compact = CompactSuffixAutomaton(source)
            for suffix in ('', rng.choice('ab\0あ')):
                if suffix:
                    sam.extend(suffix)
                    compact.extend(ord(suffix))
                    source += suffix
                counts = Counter(source[l:r] for l in range(len(source)) for r in range(l + 1, len(source) + 1))
                self.assertEqual(sam.count_distinct_substrings(), len(counts))
                self.assertEqual(count_distinct_substrings_by_sa(source), len(counts))
                occurrences = sam.build_occurrence_counts()
                self.assertEqual(sam.build_occurrence_counts(), occurrences)
                for pattern, count in counts.items():
                    state = 0
                    for ch in pattern:
                        state = sam.transition(state, ch)
                    self.assertEqual(occurrences[state], count)
                    end = sam.first_pos(state) + 1
                    self.assertEqual(source[end - len(pattern):end], pattern)
                    self.assertTrue(compact.contains(pattern))
                for pattern in ('', 'x', source + 'x'):
                    self.assertEqual(sam.contains(pattern), pattern in source)
                    self.assertEqual(compact.contains(pattern), pattern in source)
            for automaton in (sam, compact):
                before = len(automaton)
                for invalid in ('', 'ab'):
                    with self.assertRaises(ValueError):
                        automaton.extend(invalid)
                self.assertEqual(len(automaton), before)

    def test_longest_common_substring_bounds_and_content(self) -> None:
        rng = random.Random(0)
        pairs = [('\0', '\0'), ('abbb', 'bb'), ('', '\0'), ('あ' * 120, 'あ' * 100)]
        pairs += [(''.join(rng.choice('ab\0あ') for _ in range(rng.randrange(15))), ''.join(rng.choice('ab\0あ') for _ in range(rng.randrange(15)))) for _ in range(220)]
        for s, t in pairs:
            best = max((r - l for l in range(len(s) + 1) for r in range(l, len(s) + 1) if s[l:r] in t), default=0)
            for result in (longest_common_substring(s, t), SuffixAutomaton(s).longest_common_substring(t)):
                value, l, r, a, b = result
                self.assertTrue(0 <= l <= r <= len(s))
                self.assertTrue(0 <= a <= b <= len(t))
                self.assertEqual(s[l:r], value)
                self.assertEqual(t[a:b], value)
                self.assertEqual(len(value), best)

    def test_matching_empty_patterns_and_convolution_state(self) -> None:
        rng = random.Random(0)
        original_mod = ConvolutionMod.get_mod()
        try:
            for mod in (2, 3, 998244353):
                ConvolutionMod.set_mod(mod)
                for _ in range(65):
                    text = ''.join(rng.choice('ab*\0あ') for _ in range(rng.randrange(18)))
                    pattern = ''.join(rng.choice('ab*\0あ') for _ in range(rng.randrange(len(text) + 1)))
                    expected = [all(a == b or a == '*' or b == '*' for a, b in zip(text[i:i + len(pattern)], pattern)) for i in range(len(text) - len(pattern) + 1)]
                    self.assertEqual(wildcard_pattern_matching(text, pattern), expected)
                    self.assertEqual(ConvolutionMod.get_mod(), mod)
                    self.assertEqual(knuth_morris_pratt(text, pattern), [i for i in range(len(text) - len(pattern) + 1) if text.startswith(pattern, i)])
                    z = []
                    for i in range(len(text)):
                        length = 0
                        while i + length < len(text) and text[length] == text[i + length]:
                            length += 1
                        z.append(length)
                    self.assertEqual(z_algorithm(text), z)
        finally:
            ConvolutionMod.set_mod(original_mod)

    def test_aho_and_trie_duplicate_empty_and_large_counts(self) -> None:
        rng = random.Random(0)
        for _ in range(80):
            words = [''.join(rng.choice('abc') for _ in range(rng.randrange(5))) for _ in range(rng.randrange(12))]
            ac = AhoCorasick()
            trie = Trie()
            counts: Counter[str] = Counter()
            for word in words:
                ac.insert(word)
                count = rng.choice((0, 1, 2, 10**20))
                node = trie.insert(word, count)
                self.assertEqual(trie.restore(node), word)
                counts[word] += count
            text = ''.join(rng.choice('abc') for _ in range(rng.randrange(15)))
            expected = Counter((i, pos) for i, word in enumerate(words) for pos in range(len(text) - len(word) + 1) if text.startswith(word, pos))
            for _ in range(2):
                ac.build()
                self.assertEqual(Counter(ac.search_ids(text)), expected)
                self.assertEqual(Counter(ac.search(text)), Counter((words[i], pos) for (i, pos), count in expected.items() for _ in range(count)))
            for word in words + ['', 'x']:
                self.assertEqual(trie.count(word), counts[word])
                self.assertEqual(trie.contains(word), counts[word] > 0)
                expected_count = sum(count for value, count in counts.items() if value.startswith(word))
                self.assertEqual(trie.prefix_count(word), expected_count)
                self.assertEqual(trie.starts_with(word), expected_count > 0)
            self.assertEqual(set(trie.dfs_order()), set(range(len(trie))))
            with self.assertRaises(ValueError):
                trie.insert('abA')
            with self.assertRaises(ValueError):
                trie.insert('a', -1)
            self.assertEqual(trie.prefix_count(''), sum(counts.values()))
        ac = AhoCorasick()
        with self.assertRaises(ValueError):
            ac.insert('abA')
        ac.insert('a')
        self.assertEqual(list(ac.search_ids('a')), [(0, 0)])
        with self.assertRaises(ValueError):
            list(ac.search('A'))

    def test_hash_compatibility_unicode_and_collision_rejection(self) -> None:
        rng = random.Random(0)
        mod = RollingHashMersenneMod.mod
        for base in (1, 3, 911382323, mod - 1):
            chars = list('a\0あA😀b')
            dynamic = DynamicRollingHashMersenneMod(''.join(chars), base)
            for _ in range(35):
                i = rng.randrange(len(chars))
                chars[i] = rng.choice('ab\0\1あ😀')
                dynamic.set_char(i, chars[i])
                source = ''.join(chars)
                static = RollingHashMersenneMod(source, base)
                for l in range(len(chars) + 1):
                    for r in range(l, len(chars) + 1):
                        expected = sum(ord(c) * pow(base, j, mod) for j, c in enumerate(chars[l:r])) % mod
                        self.assertEqual(static.get_hash(l, r), expected)
                        self.assertEqual(dynamic.get_hash(l, r), expected)
                        pattern = ''.join(rng.choice('ab\0あ') for _ in range(rng.randrange(4)))
                        self.assertEqual(static.search_substring(pattern, l, r), source.find(pattern, l, r))
                        self.assertEqual(dynamic.search_substring(pattern, l, r), source.find(pattern, l, r))
        for x, y in ((10**200, -10**150), (-1, -2), (mod, 1)):
            self.assertEqual(RollingHashMersenneMod.mul(x, y), x * y % mod)
        self.assertEqual(find_2d_pattern(['ab'], ['ba'], row_base=1, col_base=1), [])
        for _ in range(100):
            h, w, r, c = [rng.randrange(5) for _ in range(4)]
            grid = [''.join(rng.choice('ab\0あ') for _ in range(w)) for _ in range(h)]
            pattern = [''.join(rng.choice('ab\0あ') for _ in range(c)) for _ in range(r)]
            expected = [(i, j) for i in range(h - r + 1) for j in range(w - c + 1) if all(grid[i + k][j:j + c] == pattern[k] for k in range(r))] if h and w and r and c else []
            self.assertEqual(find_2d_pattern(grid, pattern, row_base=1, col_base=1), expected)

    def test_palindromes_and_periods_against_substrings(self) -> None:
        rng = random.Random(0)
        strings = [''.join(chars) for n in range(8) for chars in itertools.product('ab', repeat=n)]
        strings += [''.join(rng.choice('ab\0\1\2あ') for _ in range(rng.randrange(18))) for _ in range(120)]
        for s in strings:
            n = len(s)
            centers = [0] * max(0, 2 * n - 1)
            palindromes: Counter[str] = Counter()
            runs = set()
            for l in range(n):
                for r in range(l + 1, n + 1):
                    substring = s[l:r]
                    if substring == substring[::-1]:
                        palindromes[substring] += 1
                        centers[l + r - 1] = max(centers[l + r - 1], r - l)
                    p = next((p for p in range(1, r - l + 1) if all(s[i] == s[i - p] for i in range(l + p, r))), r - l)
                    if r - l >= 2 * p and (l == 0 or s[l - 1] != s[l - 1 + p]) and (r == n or s[r] != s[r - p]):
                        runs.add((p, l, r))
            self.assertEqual(manacher(s), centers)
            self.assertEqual(set(enumerate_runs(s)), runs)
            tree = PalindromicTree(s)
            counts = tree.build_occurrence_counts()
            self.assertEqual(tree.build_occurrence_counts(), counts)
            self.assertEqual({tree.palindrome(i): counts[i] for i in range(2, len(tree))}, dict(palindromes))
            factors = [s[l:r] for l, r in duval(s)]
            self.assertEqual(''.join(factors), s)
            self.assertTrue(all(a >= b for a, b in zip(factors, factors[1:])))
            self.assertTrue(all(all(word < word[i:] for i in range(1, len(word))) for word in factors))
            self.assertEqual(minimum_representation(s), min(range(n), key=lambda i: s[i:] + s[:i]) if n else 0)


if __name__ == '__main__':
    unittest.main()
