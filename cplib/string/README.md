# cplib.string

`cplib.string` contains string algorithms and data structures.

## Modules

### `hashing.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `RollingHashMersenneMod` | class | `RollingHashMersenneMod(string: str, base: int = 911382323)` | A class implementing rolling hash with Mersenne prime modulo (2^61 - 1). | Space: O(n) in the constructor input size or configured capacity |
| `DynamicRollingHashMersenneMod` | class | `DynamicRollingHashMersenneMod(string: str, base: int = 911382323)` | A class implementing dynamic rolling hash with Mersenne prime modulo (2^61 - 1). | Space: O(n) in the constructor input size or configured capacity |
| `find_2d_pattern` | function | `find_2d_pattern(grid: Sequence[str], pattern: Sequence[str], row_base: int = 972663749, col_bas…` | Find all top-left positions where a 2D character pattern appears. | Time: O(HW + RC + K_h * C + K_v * R), where H * W is the grid size, R * C is the pattern size, and K_h and K_v are the numbers of horizontal and vertical hash candidates checked, respectively. |

### `matching.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `z_algorithm` | function | `z_algorithm(input_string: str) -> list[int]` | Compute Z-array using Z-algorithm. | Time: O(n) |
| `knuth_morris_pratt` | function | `knuth_morris_pratt(text: str, pattern: str) -> list[int]` | Find all occurrences of pattern in text using KMP algorithm. | Time: O(n + m), where n is ``len(text)`` and m is ``len(pattern)`` |
| `wildcard_pattern_matching` | function | `wildcard_pattern_matching(text: str, pattern: str) -> list[bool]` | Find all positions where pattern matches text with wildcard support. | Time: O(sigma * (n + m) log(n + m)), where sigma is the number of distinct non-``'*'`` characters appearing in ``text`` or ``pattern`` |
| `AhoCorasick` | class | `AhoCorasick()` | Aho-Corasick automaton for multi-pattern matching on lowercase ASCII. | Space: ``O(L + V * A + Z)``. |

### `palindrome.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `manacher` | function | `manacher(input_string: str) -> list[int]` | Compute longest palindrome lengths using Manacher's algorithm. | Time: O(n) |
| `PalindromicTree` | class | `PalindromicTree(string: str = '')` | Palindromic tree for distinct palindromic substrings. | Space: ``O(n)`` |
| `count_distinct_palindromes` | function | `count_distinct_palindromes(input_string: str) -> int` | Count distinct palindromic substrings of a string. | Time: ``O(len(input_string))`` amortized |

### `period.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `duval` | function | `duval(input_string: str) -> list[tuple[int, int]]` | Compute the Lyndon factorization of a string. | Time: ``O(n)`` |
| `lyndon_factorization` | function | `lyndon_factorization(input_string: str) -> list[str]` | Return the Lyndon factorization as substrings. | Time: ``O(n)`` |
| `minimum_representation` | function | `minimum_representation(input_string: str) -> int` | Return the index of the lexicographically minimum cyclic rotation. | Time: ``O(n)`` |
| `enumerate_runs` | function | `enumerate_runs(input_string: str) -> list[tuple[int, int, int]]` | Enumerate all maximal runs (tandem repeats) in a string. | Time: O(n log n), including suffix-array construction and LCP preprocessing. |

### `suffix.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SuffixArray` | class | `SuffixArray(string: str)` | A class implementing suffix array with SA-IS algorithm. | Space: O(n) after construction; O(n log n) after an LCP query builds the sparse table. |
| `count_distinct_substrings_by_sa` | function | `count_distinct_substrings_by_sa(input_string: str) -> int` | Calculate the number of distinct substrings in a given string using suffix array. | Time: O(n) for byte-range characters; O(n + sigma log sigma) otherwise, where sigma is the number of distinct characters. |
| `longest_common_substring` | function | `longest_common_substring(input_string_0: str, input_string_1: str) -> tuple[str, int, int, int,…` | Find the longest common substring between two strings. | Time: O(n + m + sigma log sigma), where n and m are the input lengths and sigma is the number of distinct characters. Byte-range input takes O(n + m). |
| `SuffixAutomaton` | class | `SuffixAutomaton(string: str = '')` | A class implementing suffix automaton for a single string. | Space: O(n) |
| `count_distinct_substrings` | function | `count_distinct_substrings(input_string: str) -> int` | Calculate the number of distinct substrings in a given string. | Time: O(len(input_string)) amortized |
| `CompactSuffixAutomaton` | class | `CompactSuffixAutomaton(string: str = '')` | Memory-efficient suffix automaton for substring queries. | Space: O(number of states + number of transitions). |

### `trie.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Trie` | class | `Trie()` | Trie for lowercase ASCII strings. | Space: ``O(V * A)``. |
