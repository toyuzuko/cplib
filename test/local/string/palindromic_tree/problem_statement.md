# Problem Statement

Given a string `S`, consider all of its distinct palindromic substrings.

A palindrome is a string that reads the same from left to right and from right to left. A substring is distinct if its character sequence is different from all other palindromic substrings.

For this problem, output the number of distinct palindromic substrings, the longest palindromic suffix of `S`, and the list of all distinct palindromic substrings with their occurrence counts.

## Input Format

```text
S
```

`S` may be empty.

## Output Format

Print the following:

1. The number of distinct palindromic substrings of `S`
2. The longest palindromic suffix of `S`
3. One line for each distinct palindromic substring, sorted by increasing length and then lexicographically

Each line in the last part must contain the palindrome itself and its occurrence count, separated by a single space.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `0 <= |S| <= LENGTH_MAX`
- Every character of `S` belongs to `ALPHABET`

## Notes

The bundled `naive.py` checks every substring and tests whether it is a
palindrome directly, so its worst-case time is `O(|S|^3)`. Under the
configurable bound, this is `O(LENGTH_MAX^3)`.
