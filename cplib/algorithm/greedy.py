#!/usr/bin/env python3

import heapq
from collections.abc import Sequence
from functools import cmp_to_key


def maximum_profit(prices: Sequence[int]) -> int:
    """
    Return the maximum difference ``prices[j] - prices[i]`` for ``i < j``.

    Args:
        prices: Sequence of observed values in chronological order.

    Returns:
        Maximum obtainable difference by buying before selling.

    Raises:
        ValueError: If fewer than two prices are given.

    Time Complexity:
        O(n), where ``n = len(prices)``.

    Space Complexity:
        O(1)
    """
    if len(prices) < 2:
        raise ValueError('at least two prices are required')
    min_price = prices[0]
    best = prices[1] - prices[0]
    for i in range(1, len(prices)):
        price = prices[i]
        profit = price - min_price
        if profit > best:
            best = profit
        if price < min_price:
            min_price = price
    return best


def greedy_coin_count(coins: Sequence[int], amount: int) -> int:
    """
    Return the number of coins chosen by the standard greedy algorithm.

    This is optimal for canonical coin systems such as ``[25, 10, 5, 1]``. For
    arbitrary coin systems, use ``minimum_coin_count`` instead.

    Args:
        coins: Available positive coin values.
        amount: Target amount.

    Returns:
        Number of selected coins, or ``-1`` if the greedy remainder cannot be
        made exactly.

    Raises:
        ValueError: If ``amount`` is negative or a coin value is not positive.

    Time Complexity:
        O(n log n), where ``n = len(coins)``.

    Space Complexity:
        O(n)
    """
    if amount < 0:
        raise ValueError('amount must be non-negative')
    count = 0
    remaining = amount
    for coin in sorted(coins, reverse=True):
        if coin <= 0:
            raise ValueError('coin values must be positive')
        used, remaining = divmod(remaining, coin)
        count += used
    return count if remaining == 0 else -1


def fractional_knapsack(items: Sequence[tuple[int, int]], capacity: int) -> float:
    """
    Return the maximum value obtainable when items can be split.

    Args:
        items: Pairs ``(value, weight)`` for each item. Non-positive values
            need not be selected; all weights must be positive.
        capacity: Maximum total weight.

    Returns:
        Maximum obtainable value.

    Raises:
        ValueError: If ``capacity`` is negative or an item weight is not
            positive.

    Time Complexity:
        O(n log n), where ``n = len(items)``.

    Space Complexity:
        O(n)
    """
    if capacity < 0:
        raise ValueError('capacity must be non-negative')
    for _, weight in items:
        if weight <= 0:
            raise ValueError('item weights must be positive')

    def compare(a: tuple[int, int], b: tuple[int, int]) -> int:
        av, aw = a
        bv, bw = b
        left = av * bw
        right = bv * aw
        if left == right:
            return 0
        return -1 if left > right else 1

    total = 0.0
    remaining = capacity
    for value, weight in sorted(items, key=cmp_to_key(compare)):
        if remaining == 0 or value <= 0:
            break
        take = weight if weight <= remaining else remaining
        total += value * take / weight
        remaining -= take
    return total


def max_non_overlapping_intervals(intervals: Sequence[tuple[int, int]], *, allow_touch: bool = True) -> int:
    """
    Return the maximum number of non-overlapping intervals.

    Args:
        intervals: Pairs ``(start, end)``.
        allow_touch: If true, intervals ``[a, b)`` and ``[b, c)`` are
            compatible. If false, the next interval must start strictly after
            the previous one ends.

    Returns:
        Maximum selectable interval count.

    Time Complexity:
        O(n log n), where ``n = len(intervals)``.

    Space Complexity:
        O(n)
    """
    count = 0
    current_end: int | None = None
    for start, end in sorted(intervals, key=lambda interval: (interval[1], interval[0])):
        if current_end is None or (current_end <= start if allow_touch else current_end < start):
            count += 1
            current_end = end
    return count


def huffman_encoded_length(frequencies: Sequence[int]) -> int:
    """
    Return the minimum encoded length for Huffman coding.

    Args:
        frequencies: Non-negative symbol frequencies. Zero frequencies are
            ignored.

    Returns:
        Total number of bits in an optimal Huffman code. For a single symbol,
        the code length is treated as 1.

    Raises:
        ValueError: If any frequency is negative.

    Time Complexity:
        O(n log n), where ``n = len(frequencies)``.

    Space Complexity:
        O(n)
    """
    heap: list[int] = []
    for freq in frequencies:
        if freq < 0:
            raise ValueError('frequencies must be non-negative')
        if freq:
            heap.append(freq)
    if len(heap) == 0:
        return 0
    if len(heap) == 1:
        return heap[0]
    heapq.heapify(heap)
    total = 0
    while len(heap) >= 2:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        total += merged
        heapq.heappush(heap, merged)
    return total
