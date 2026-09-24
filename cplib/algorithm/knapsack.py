#!/usr/bin/env python3

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cmp_to_key
from typing import NamedTuple


class SubsetSumResult(NamedTuple):
    """
    Result of a subset-sum style meet-in-the-middle query.

    Attributes:
        total: Sum of the selected values.
        indices: Indices of the selected values in increasing order.

    Space Complexity:
        O(k), where ``k`` is the number of selected values.
    """

    total: int
    indices: list[int]


def _subset_sums_with_masks(values: Sequence[int], offset: int = 0) -> list[tuple[int, int]]:
    states = [(0, 0)]
    for i, value in enumerate(values):
        bit = 1 << (offset + i)
        states += [(total + value, mask | bit) for total, mask in states]
    return states


def _indices_from_mask(mask: int, n: int) -> list[int]:
    return [i for i in range(n) if (mask >> i) & 1]


def subset_sum_meet_in_the_middle(values: Sequence[int], target: int) -> SubsetSumResult | None:
    """
    Find one subset whose sum is exactly ``target``.

    Args:
        values: Input values. Negative values are allowed.
        target: Required sum.

    Returns:
        ``SubsetSumResult`` for one feasible subset, or ``None`` if no subset
        has sum ``target``.

    Time Complexity:
        O(n 2^(n/2))

    Space Complexity:
        O(2^(n/2))
    """
    n = len(values)
    mid = n // 2
    left = _subset_sums_with_masks(values[:mid])
    right = _subset_sums_with_masks(values[mid:], mid)
    right_by_sum: dict[int, int] = {}
    for total, mask in right:
        if total not in right_by_sum:
            right_by_sum[total] = mask
    for left_total, left_mask in left:
        right_mask = right_by_sum.get(target - left_total)
        if right_mask is not None:
            return SubsetSumResult(target, _indices_from_mask(left_mask | right_mask, n))
    return None


def maximum_subset_sum_at_most_meet_in_the_middle(values: Sequence[int], limit: int) -> SubsetSumResult | None:
    """
    Find a maximum-sum subset whose sum is at most ``limit``.

    Args:
        values: Input values. Negative values are allowed.
        limit: Upper bound on the selected sum.

    Returns:
        ``SubsetSumResult`` for one optimal subset, or ``None`` if every subset
        has sum greater than ``limit``.

    Time Complexity:
        O(n 2^(n/2))

    Space Complexity:
        O(2^(n/2))
    """
    n = len(values)
    mid = n // 2
    left = _subset_sums_with_masks(values[:mid])
    right = sorted(_subset_sums_with_masks(values[mid:], mid))
    right_sums = [total for total, _ in right]
    best_total: int | None = None
    best_mask = 0
    for left_total, left_mask in left:
        j = bisect_right(right_sums, limit - left_total) - 1
        if j < 0:
            continue
        total = left_total + right[j][0]
        if best_total is None or total > best_total:
            best_total = total
            best_mask = left_mask | right[j][1]
    if best_total is None:
        return None
    return SubsetSumResult(best_total, _indices_from_mask(best_mask, n))


@dataclass(slots=True)
class KnapsackItem:
    """One item description for unified knapsack solving.

    Attributes:
        weight: Non-negative item weight.
        value: Item value.
        count: Multiplicity of the item.
            - ``1`` for 0/1 knapsack
            - integer ``>= 0`` for bounded knapsack
            - ``-1`` for unbounded knapsack

    Space Complexity:
        ``O(1)``
    """

    weight: int
    value: int
    count: int = 1


class KnapsackResult(NamedTuple):
    """Result of a knapsack query with reconstruction.

    Attributes:
        value: Maximum obtainable total value.
        chosen: Chosen multiplicity for each original item.

    Space Complexity:
        ``O(n)``, where ``n`` is the number of original items.
    """

    value: int
    chosen: list[int]


def bounded_knapsack_small_values(items: Sequence[KnapsackItem], capacity: int, *, window: int | None = None) -> int:
    """
    Return the bounded-knapsack optimum for small item values.

    This routine is intended for instances where item weights and multiplicities
    can be very large, but each item value is small. It computes a density-order
    greedy solution, then searches the bounded neighborhood of that solution by
    value-difference DP.

    Args:
        items: Bounded items. Each ``count`` must be non-negative.
        capacity: Non-negative total weight limit.
        window: Absolute value-difference window around the greedy solution. If
            omitted, ``4 * sum(item.value)`` over the positive-value,
            positive-weight items that fit individually is used. A smaller
            custom window may exclude the optimum.

    Returns:
        Maximum achievable total value with the default window. A custom
        window returns the best value found within that window.

    Raises:
        ValueError: If ``capacity``, an item weight, multiplicity, or
            ``window`` is negative.

    Time Complexity:
        O(n log n + n * (window + 1) + sum(item.value)) for retained items,
        where ``n`` is ``len(items)``. Integer arithmetic is treated as O(1).

    Space Complexity:
        O(n + window)
    """
    if window is not None and window < 0:
        raise ValueError('window must be non-negative')
    if capacity < 0:
        raise ValueError('capacity must be non-negative')
    filtered: list[KnapsackItem] = []
    base_value = 0
    for item in items:
        if item.weight < 0:
            raise ValueError('item weights must be non-negative')
        if item.count < 0:
            raise ValueError('item counts must be non-negative')
        if item.value <= 0:
            continue
        if item.count == 0:
            continue
        if item.weight == 0:
            base_value += item.value * item.count
        elif item.weight <= capacity:
            filtered.append(item)
    if not filtered:
        return base_value

    def compare(a: KnapsackItem, b: KnapsackItem) -> int:
        lhs = a.value * b.weight
        rhs = b.value * a.weight
        if lhs != rhs:
            return -1 if lhs > rhs else 1
        if a.weight != b.weight:
            return -1 if a.weight < b.weight else 1
        return 0

    sorted_items = sorted(filtered, key=cmp_to_key(compare))
    take: list[int] = []
    greedy_value = 0
    greedy_weight = 0
    remaining = capacity
    for item in sorted_items:
        count = min(item.count, remaining // item.weight)
        take.append(count)
        greedy_value += item.value * count
        weight = item.weight * count
        greedy_weight += weight
        remaining -= weight

    if window is None:
        window = 4 * sum(item.value for item in sorted_items)
    inf = capacity + sum(item.weight * item.count for item in sorted_items) + 1
    offset = window
    size = window * 2 + 1
    dp = [inf] * size
    dp[offset] = 0
    for item, base_count in zip(sorted_items, take):
        value = item.value
        weight = item.weight
        lower = -base_count
        upper = item.count - base_count
        ndp = [inf] * size
        for residue in range(value):
            q_min = -((window + residue) // value)
            q_max = (window - residue) // value
            que_q: list[int] = []
            que_v: list[int] = []
            head = 0
            add_q = q_min
            for q in range(q_min, q_max + 1):
                limit = min(q - lower, q_max)
                while add_q <= limit:
                    idx = offset + residue + add_q * value
                    if 0 <= idx < size and dp[idx] < inf:
                        candidate = dp[idx] - add_q * weight
                        while len(que_v) > head and que_v[-1] >= candidate:
                            que_v.pop()
                            que_q.pop()
                        que_q.append(add_q)
                        que_v.append(candidate)
                    add_q += 1
                expire = q - upper
                while head < len(que_q) and que_q[head] < expire:
                    head += 1
                if head < len(que_q):
                    idx = offset + residue + q * value
                    if 0 <= idx < size:
                        ndp[idx] = q * weight + que_v[head]
        dp = ndp

    best = greedy_value
    for delta in range(window + 1):
        if greedy_weight + dp[offset + delta] <= capacity:
            value = greedy_value + delta
            if value > best:
                best = value
    return base_value + best


def _knapsack_meet_in_the_middle(items: Sequence[tuple[int, int]], capacity: int) -> int:
    half = len(items) // 2
    left = items[:half]
    right = items[half:]
    left_states = [(0, 0)]
    for weight, value in left:
        size = len(left_states)
        for i in range(size):
            cur_weight, cur_value = left_states[i]
            next_weight = cur_weight + weight
            if next_weight <= capacity:
                left_states.append((next_weight, cur_value + value))
    left_states.sort()
    filtered: list[tuple[int, int]] = []
    best = -1
    for weight, value in left_states:
        if value > best:
            filtered.append((weight, value))
            best = value
    left_weights = [weight for weight, _ in filtered]
    right_states = [(0, 0)]
    for weight, value in right:
        size = len(right_states)
        for i in range(size):
            cur_weight, cur_value = right_states[i]
            next_weight = cur_weight + weight
            if next_weight <= capacity:
                right_states.append((next_weight, cur_value + value))
    ans = 0
    for weight, value in right_states:
        rem = capacity - weight
        j = bisect_right(left_weights, rem) - 1
        if j >= 0 and ans < value + filtered[j][1]:
            ans = value + filtered[j][1]
    return ans


def _knapsack_meet_in_the_middle_restore(items: Sequence[tuple[int, int, int, int]], capacity: int, item_count: int) -> KnapsackResult:
    half = len(items) // 2
    left = items[:half]
    right = items[half:]
    left_states = [(0, 0, 0)]
    for idx, (weight, value, _, _) in enumerate(left):
        size = len(left_states)
        bit = 1 << idx
        for i in range(size):
            cur_weight, cur_value, mask = left_states[i]
            next_weight = cur_weight + weight
            if next_weight <= capacity:
                left_states.append((next_weight, cur_value + value, mask | bit))
    left_states.sort()
    filtered: list[tuple[int, int, int]] = []
    best = -1
    for weight, value, mask in left_states:
        if value > best:
            filtered.append((weight, value, mask))
            best = value
    left_weights = [weight for weight, _, _ in filtered]
    best_value = 0
    best_left_mask = 0
    best_right_mask = 0
    right_states = [(0, 0, 0)]
    for idx, (weight, value, _, _) in enumerate(right):
        size = len(right_states)
        bit = 1 << idx
        for i in range(size):
            cur_weight, cur_value, mask = right_states[i]
            next_weight = cur_weight + weight
            if next_weight <= capacity:
                right_states.append((next_weight, cur_value + value, mask | bit))
    for weight, value, right_mask in right_states:
        rem = capacity - weight
        j = bisect_right(left_weights, rem) - 1
        if j >= 0 and best_value < value + filtered[j][1]:
            best_value = value + filtered[j][1]
            best_left_mask = filtered[j][2]
            best_right_mask = right_mask
    chosen = [0] * item_count
    for idx, (_, _, original, amount) in enumerate(left):
        if (best_left_mask >> idx) & 1:
            chosen[original] += amount
    for idx, (_, _, original, amount) in enumerate(right):
        if (best_right_mask >> idx) & 1:
            chosen[original] += amount
    return KnapsackResult(best_value, chosen)


def _knapsack_weight_dp(items: Sequence[tuple[int, int]], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    for weight, value in items:
        for cur in range(capacity, weight - 1, -1):
            cand = dp[cur - weight] + value
            if cand > dp[cur]:
                dp[cur] = cand
    return max(dp)


def _knapsack_value_dp(items: Sequence[tuple[int, int]], capacity: int) -> int:
    total_value = sum(value for _, value in items)
    inf = capacity + 1
    dp = [inf] * (total_value + 1)
    dp[0] = 0
    for weight, value in items:
        for cur in range(total_value, value - 1, -1):
            cand = dp[cur - value] + weight
            if cand < dp[cur]:
                dp[cur] = cand
    for value in range(total_value, -1, -1):
        if dp[value] <= capacity:
            return value
    return 0


def _knapsack_weight_dp_restore(items: Sequence[tuple[int, int, int, int]], capacity: int, item_count: int) -> KnapsackResult:
    neg_inf = -(1 << 60)
    dp = [neg_inf] * (capacity + 1)
    take = [bytearray(capacity + 1) for _ in range(len(items))]
    dp[0] = 0
    for idx, (weight, value, _, _) in enumerate(items):
        for cur in range(capacity, weight - 1, -1):
            cand = dp[cur - weight] + value
            if cand > dp[cur]:
                dp[cur] = cand
                take[idx][cur] = 1
    best_weight = 0
    for weight in range(1, capacity + 1):
        if dp[weight] > dp[best_weight]:
            best_weight = weight
    chosen = [0] * item_count
    cur = best_weight
    for idx in range(len(items) - 1, -1, -1):
        if take[idx][cur]:
            weight, _, original, amount = items[idx]
            chosen[original] += amount
            cur -= weight
    return KnapsackResult(dp[best_weight], chosen)


def _knapsack_value_dp_restore(items: Sequence[tuple[int, int, int, int]], capacity: int, item_count: int) -> KnapsackResult:
    total_value = sum(value for _, value, _, _ in items)
    inf = capacity + 1
    dp = [inf] * (total_value + 1)
    take = [bytearray(total_value + 1) for _ in range(len(items))]
    dp[0] = 0
    for idx, (weight, value, _, _) in enumerate(items):
        for cur in range(total_value, value - 1, -1):
            cand = dp[cur - value] + weight
            if cand < dp[cur]:
                dp[cur] = cand
                take[idx][cur] = 1
    best_value = 0
    for value in range(total_value, -1, -1):
        if dp[value] <= capacity:
            best_value = value
            break
    chosen = [0] * item_count
    cur = best_value
    for idx in range(len(items) - 1, -1, -1):
        if take[idx][cur]:
            _, value, original, amount = items[idx]
            chosen[original] += amount
            cur -= value
    return KnapsackResult(best_value, chosen)


def knapsack(items: Sequence[KnapsackItem], capacity: int, *, restore: bool = False, mitm_threshold: int = 40) -> int | KnapsackResult:
    """Return the maximum obtainable value under a weight limit.

    This is a unified entry point for several knapsack variants. Each item may
    be 0/1, bounded, or unbounded depending on ``count``.

    Internally the function converts the instance to an equivalent 0/1 problem
    and then chooses one of:

    - meet-in-the-middle for small item count
    - weight-based DP when the capacity side is smaller
    - value-based DP when the total value side is smaller

    Args:
        items: Items described by ``(weight, value, count)``.
        capacity: Non-negative total weight limit.
        restore: Whether to also return the number of times each original item
            is chosen.
        mitm_threshold: Use meet-in-the-middle when the expanded 0/1 item count
            is at most this threshold.

    Returns:
        Maximum achievable total value. When ``restore=True``, returns
        ``KnapsackResult(value, chosen)`` where ``chosen[i]`` is the chosen
        multiplicity of ``items[i]``.

    Raises:
        ValueError: If ``capacity`` or ``mitm_threshold`` is negative, an item
            has invalid weight or multiplicity, or positive-value unbounded
            zero-weight items make the optimum unbounded.

    Time Complexity:
        Meet-in-the-middle branch: ``O(m 2^(m/2))`` where ``m`` is the expanded
        0/1 item count. DP branches take ``O(m * min(capacity, total_value))``.

    Space Complexity:
        Meet-in-the-middle: ``O(2^ceil(m/2) + n)``. Value-only DP:
        ``O(m + n + min(capacity, total_value))``. Restoring DP:
        ``O(m + n + m * min(capacity, total_value))``, where ``n = len(items)``.

    Examples:
        >>> items = [KnapsackItem(weight=2, value=3, count=3), KnapsackItem(weight=3, value=4, count=-1)]
        >>> # The first item can be taken at most 3 times, and the second item can be taken any number of times.
        >>> # One optimal solution is to take the first item 2 times (weight 4, value 6) and the second item 2 times (weight 6, value 8),
        >>> # for a total weight of 10 and total value of 14.
        >>> knapsack(items, capacity=10, restore=True)
        KnapsackResult(value=14, chosen=[2, 2])
    """

    if capacity < 0:
        raise ValueError('capacity must be non-negative')
    if mitm_threshold < 0:
        raise ValueError('mitm_threshold must be non-negative')
    expanded: list[tuple[int, int]] = []
    expanded_restore: list[tuple[int, int, int, int]] = []
    base_value = 0
    base_chosen = [0] * len(items)
    for item_index, item in enumerate(items):
        weight = item.weight
        value = item.value
        count = item.count
        if weight < 0:
            raise ValueError('item weights must be non-negative')
        if count == 0:
            continue
        if count < -1:
            raise ValueError('item count must be -1 or non-negative')
        if weight == 0:
            if count == -1:
                if value > 0:
                    raise ValueError('positive-value zero-weight unbounded items make the optimum unbounded')
                continue
            if value > 0:
                base_value += value * count
                base_chosen[item_index] += count
            continue
        if weight > capacity or value <= 0:
            continue
        limit = capacity // weight if count == -1 else min(count, capacity // weight)
        take = 1
        while limit > 0:
            used = min(take, limit)
            entry = (weight * used, value * used)
            expanded.append(entry)
            expanded_restore.append((entry[0], entry[1], item_index, used))
            limit -= used
            take <<= 1
    if not expanded:
        return KnapsackResult(base_value, base_chosen) if restore else base_value
    if restore:
        if len(expanded_restore) <= mitm_threshold:
            result = _knapsack_meet_in_the_middle_restore(expanded_restore, capacity, len(items))
            chosen = [base_chosen[i] + result.chosen[i] for i in range(len(items))]
            return KnapsackResult(base_value + result.value, chosen)
        total_value = sum(value for _, value, _, _ in expanded_restore)
        if capacity <= total_value:
            result = _knapsack_weight_dp_restore(expanded_restore, capacity, len(items))
        else:
            result = _knapsack_value_dp_restore(expanded_restore, capacity, len(items))
        chosen = [base_chosen[i] + result.chosen[i] for i in range(len(items))]
        return KnapsackResult(base_value + result.value, chosen)
    if len(expanded) <= mitm_threshold:
        return base_value + _knapsack_meet_in_the_middle(expanded, capacity)
    total_value = sum(value for _, value in expanded)
    if capacity <= total_value:
        return base_value + _knapsack_weight_dp(expanded, capacity)
    return base_value + _knapsack_value_dp(expanded, capacity)
