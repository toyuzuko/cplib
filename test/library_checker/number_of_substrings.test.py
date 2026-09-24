# verification-helper: PROBLEM https://judge.yosupo.jp/problem/number_of_substrings

from cplib.string.suffix import count_distinct_substrings_by_sa as count_distinct_substrings


S = input()
print(count_distinct_substrings(S))