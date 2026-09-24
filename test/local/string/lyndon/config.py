"""Configuration for the local Lyndon test."""

from __future__ import annotations

NUM_CASES = 100
TIMEOUT_SECONDS = 2.0
SPECIAL_CASE_RATE = 0.3
LENGTH_MAX = 10
ALPHABET = "abc"
SPECIAL_CASES: tuple[str, ...] = (
    "",
    "a",
    "aaaa",
    "ababab",
    "banana",
    "bbaaccaadd",
)
