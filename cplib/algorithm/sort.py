#!/usr/bin/env python3

from collections.abc import Callable, Sequence
from typing import cast
from cplib.tools.type import T, KeyT


def _resolve_key(key: Callable[[T], KeyT] | None) -> Callable[[T], KeyT]:
    if key is not None:
        return key

    def identity(value: T) -> KeyT:
        return cast(KeyT, value)

    return identity


def insertion_sort(values: Sequence[T], key: Callable[[T], KeyT] | None = None, gap: int = 1) -> list[T]:
    """
    Return a copy sorted within each gap-spaced subsequence by insertion sort.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.
        gap: Step width for gapped insertion sort.

    Returns:
        Copy with each subsequence ``result[offset::gap]`` sorted. The whole
        result is sorted when ``gap == 1``.

    Raises:
        ValueError: If ``gap`` is not positive.

    Time Complexity:
        O(n + n^2 / gap) in the worst case, including the input copy.

    Space Complexity:
        O(n)
    """
    if gap <= 0:
        raise ValueError('gap must be positive')
    res = list(values)
    key_func = _resolve_key(key)
    for i in range(gap, len(res)):
        v = res[i]
        kv = key_func(v)
        j = i - gap
        while j >= 0 and kv < key_func(res[j]):
            res[j + gap] = res[j]
            j -= gap
        res[j + gap] = v
    return res


def bubble_sort(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> list[T]:
    """
    Return a stably sorted copy using bubble sort.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.

    Returns:
        Sorted copy.

    Time Complexity:
        O(n^2)

    Space Complexity:
        O(n)
    """
    res = list(values)
    key_func = _resolve_key(key)
    flag = True
    while flag:
        flag = False
        for j in range(len(res) - 1, 0, -1):
            if key_func(res[j]) < key_func(res[j - 1]):
                res[j], res[j - 1] = res[j - 1], res[j]
                flag = True
    return res


def selection_sort(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> list[T]:
    """
    Return a sorted copy using selection sort.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.

    Returns:
        Sorted copy.

    Time Complexity:
        O(n^2)

    Space Complexity:
        O(n)
    """
    res = list(values)
    key_func = _resolve_key(key)
    for i in range(len(res)):
        min_idx = i
        for j in range(i, len(res)):
            if key_func(res[j]) < key_func(res[min_idx]):
                min_idx = j
        if i != min_idx:
            res[i], res[min_idx] = res[min_idx], res[i]
    return res


def shell_sort(values: Sequence[T], key: Callable[[T], KeyT] | None = None, gaps: Sequence[int] | None = None) -> list[T]:
    """
    Return a sorted copy using shell sort.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.
        gaps: Gap sequence in execution order. If omitted, Knuth gaps are used.
            A final gap-1 pass is added if the sequence does not end in 1.

    Returns:
        Sorted copy.

    Raises:
        ValueError: If a gap is not positive.

    Time Complexity:
        O(n^2) for the default gaps. For custom gaps, a general upper bound is
        O(sum(n + n^2 / gap)), including the final gap-1 pass.

    Space Complexity:
        O(n + g), where g is the number of gaps.
    """
    n = len(values)
    if gaps is None:
        generated: list[int] = []
        h = 1
        while h <= n:
            generated.append(h)
            h = h * 3 + 1
        gaps_list = generated[::-1]
    else:
        gaps_list = list(gaps)
    if any(g <= 0 for g in gaps_list):
        raise ValueError('gaps must be positive')
    if not gaps_list or gaps_list[-1] != 1:
        gaps_list.append(1)
    res = list(values)
    for gap in gaps_list:
        res = insertion_sort(res, key=key, gap=gap)
    return res


def merge_sort(arr: list[T], cmp: Callable[[T, T], bool], threshold: int = 3) -> list[T]:
    """Return a stably sorted copy of ``arr`` using the given comparator.

    The implementation uses bottom-up merge sort and switches to insertion
    sort for small blocks controlled by ``threshold``.

    Args:
        arr: Input list.
        cmp: Comparator that returns true when the first argument should come
            before the second.
        threshold: Number of merge levels handled by insertion sort before the
            implementation switches to merging. Must be non-negative.

    Returns:
        Sorted copy of ``arr``.

    Raises:
        ValueError: If ``threshold`` is negative.

    Time Complexity:
        ``O(n log n)`` for a fixed threshold. In general,
        ``O(n log n + n * min(n, 2**threshold))``.

    Space Complexity:
        ``O(n)``

    Examples:
        >>> merge_sort([3, 1, 4, 1, 5, 9, 2, 6], lambda x, y: x < y)
        [1, 1, 2, 3, 4, 5, 6, 9]
        >>> # Sorted by string length.
        >>> merge_sort(['apple', 'banana', 'cherry'], lambda x, y: len(x) < len(y))
        ['apple', 'banana', 'cherry']
    """
    if threshold < 0:
        raise ValueError('threshold must be non-negative')
    n = len(arr)
    h = (n - 1).bit_length()
    res = arr.copy()
    tmp = arr.copy()
    for i in range(h):
        d = 1 << i
        if i == 0:
            for lt in range(0, n - 1, 2):
                if cmp(res[lt + 1], res[lt]):
                    res[lt], res[lt + 1] = res[lt + 1], res[lt]
        elif i < threshold:
            for lt in range(0, n, d * 2):
                rt = min(lt + d * 2, n)
                for j in range(lt + 1, rt):
                    k = j - 1
                    res_j = res[j]
                    while k >= lt and cmp(res_j, res[k]):
                        res[k + 1] = res[k]
                        k -= 1
                    res[k + 1] = res_j
        else:
            cur = 0
            for lt in range(0, n, d * 2):
                lt_end = rt = min(lt + d, n)
                rt_end = min(lt + 2 * d, n)
                while lt < lt_end and rt < rt_end:
                    if cmp(res[rt], res[lt]):
                        tmp[cur] = res[rt]
                        rt += 1
                    else:
                        tmp[cur] = res[lt]
                        lt += 1
                    cur += 1
                while lt < lt_end:
                    tmp[cur] = res[lt]
                    lt += 1
                    cur += 1
                while rt < rt_end:
                    tmp[cur] = res[rt]
                    rt += 1
                    cur += 1
            tmp, res = res, tmp
    return res


def intro_sort(values: Sequence[T], cmp: Callable[[T, T], bool], threshold: int = 16) -> list[T]:
    """
    Return a sorted copy using introsort with the given comparator.

    This implementation combines median-of-three Hoare quicksort, insertion
    sort for small ranges, and heapsort as a worst-case fallback. It is not
    stable.

    Args:
        values: Input sequence.
        cmp: Comparator that returns true when the first argument should come
            before the second.
        threshold: Ranges of this size or smaller are handled by insertion sort.

    Returns:
        Sorted copy of ``values``.

    Raises:
        ValueError: If ``threshold`` is not positive.

    Time Complexity:
        O(n log n) for a fixed threshold, where ``n = len(values)``. In
        general, O(n log n + n * min(n, threshold)).

    Space Complexity:
        O(n + log n).
    """
    if threshold <= 0:
        raise ValueError('threshold must be positive')

    res = list(values)
    n = len(res)
    if n <= 1:
        return res

    def insertion(left: int, right: int) -> None:
        for i in range(left + 1, right):
            value = res[i]
            j = i
            while j > left and cmp(value, res[j - 1]):
                res[j] = res[j - 1]
                j -= 1
            res[j] = value

    def greater(i: int, j: int) -> bool:
        return cmp(res[j], res[i])

    def sift_down(root: int, end: int, left: int) -> None:
        while True:
            child = left + ((root - left) << 1) + 1
            if child >= end:
                return
            if child + 1 < end and greater(child + 1, child):
                child += 1
            if not greater(child, root):
                return
            res[root], res[child] = res[child], res[root]
            root = child

    def heap_sort(left: int, right: int) -> None:
        for root in range(left + ((right - left) >> 1) - 1, left - 1, -1):
            sift_down(root, right, left)
        for end in range(right - 1, left, -1):
            res[left], res[end] = res[end], res[left]
            sift_down(left, end, left)

    def median_index(left: int, right: int) -> int:
        a = left
        b = (left + right) >> 1
        c = right - 1
        if cmp(res[b], res[a]):
            a, b = b, a
        if cmp(res[c], res[b]):
            b, c = c, b
        if cmp(res[b], res[a]):
            a, b = b, a
        return b

    def partition(left: int, right: int) -> int:
        pivot = res[median_index(left, right)]
        i = left
        j = right - 1
        while True:
            while cmp(res[i], pivot):
                i += 1
            while cmp(pivot, res[j]):
                j -= 1
            if i >= j:
                return j + 1
            res[i], res[j] = res[j], res[i]
            i += 1
            j -= 1

    stack = [(0, n, n.bit_length() << 1)]
    while stack:
        left, right, depth = stack.pop()
        while right - left > threshold:
            if depth == 0:
                heap_sort(left, right)
                left = right
                break
            depth -= 1
            mid = partition(left, right)
            if mid - left < right - mid:
                stack.append((mid, right, depth))
                right = mid
            else:
                stack.append((left, mid, depth))
                left = mid
        if right - left > 1:
            insertion(left, right)
    return res


def includes_sorted(values: Sequence[KeyT], targets: Sequence[KeyT]) -> bool:
    """
    Return whether sorted ``values`` contains all sorted ``targets``.

    Repeated elements are treated with multiplicity, matching the standard
    sorted range inclusion operation.

    Args:
        values: Sorted candidate container.
        targets: Sorted values to search for.

    Returns:
        True if every target can be matched in order, otherwise False.

    Time Complexity:
        O(n + m), where ``n = len(values)`` and ``m = len(targets)``.

    Space Complexity:
        O(1)
    """
    i = 0
    n = len(values)
    for target in targets:
        while i < n and values[i] < target:
            i += 1
        if i == n or target < values[i]:
            return False
        i += 1
    return True


def sorted_set_union(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]:
    """
    Return the union of two sorted unique sequences.

    Args:
        a: First sorted sequence without duplicates.
        b: Second sorted sequence without duplicates.

    Returns:
        Sorted list containing elements that appear in at least one sequence.

    Time Complexity:
        O(n + m), where ``n = len(a)`` and ``m = len(b)``.

    Space Complexity:
        O(n + m)
    """
    i = j = 0
    n = len(a)
    m = len(b)
    res: list[KeyT] = []
    while i < n and j < m:
        if a[i] < b[j]:
            res.append(a[i])
            i += 1
        elif b[j] < a[i]:
            res.append(b[j])
            j += 1
        else:
            res.append(a[i])
            i += 1
            j += 1
    res.extend(a[i:])
    res.extend(b[j:])
    return res


def sorted_set_intersection(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]:
    """
    Return the intersection of two sorted unique sequences.

    Args:
        a: First sorted sequence without duplicates.
        b: Second sorted sequence without duplicates.

    Returns:
        Sorted list containing elements that appear in both sequences.

    Time Complexity:
        O(n + m), where ``n = len(a)`` and ``m = len(b)``.

    Space Complexity:
        O(min(n, m))
    """
    i = j = 0
    n = len(a)
    m = len(b)
    res: list[KeyT] = []
    while i < n and j < m:
        if a[i] < b[j]:
            i += 1
        elif b[j] < a[i]:
            j += 1
        else:
            res.append(a[i])
            i += 1
            j += 1
    return res


def sorted_set_difference(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]:
    """
    Return the sorted set difference ``a - b``.

    Args:
        a: First sorted sequence without duplicates.
        b: Second sorted sequence without duplicates.

    Returns:
        Sorted list containing elements that appear in ``a`` but not in ``b``.

    Time Complexity:
        O(n + m), where ``n = len(a)`` and ``m = len(b)``.

    Space Complexity:
        O(n)
    """
    i = j = 0
    n = len(a)
    m = len(b)
    res: list[KeyT] = []
    while i < n and j < m:
        if a[i] < b[j]:
            res.append(a[i])
            i += 1
        elif b[j] < a[i]:
            j += 1
        else:
            i += 1
            j += 1
    res.extend(a[i:])
    return res


def sorted_set_symmetric_difference(a: Sequence[KeyT], b: Sequence[KeyT]) -> list[KeyT]:
    """
    Return the symmetric difference of two sorted unique sequences.

    Args:
        a: First sorted sequence without duplicates.
        b: Second sorted sequence without duplicates.

    Returns:
        Sorted list containing elements that appear in exactly one sequence.

    Time Complexity:
        O(n + m), where ``n = len(a)`` and ``m = len(b)``.

    Space Complexity:
        O(n + m)
    """
    i = j = 0
    n = len(a)
    m = len(b)
    res: list[KeyT] = []
    while i < n and j < m:
        if a[i] < b[j]:
            res.append(a[i])
            i += 1
        elif b[j] < a[i]:
            res.append(b[j])
            j += 1
        else:
            i += 1
            j += 1
    res.extend(a[i:])
    res.extend(b[j:])
    return res


def counting_sort(values: Sequence[int], max_value: int | None = None, min_value: int = 0) -> list[int]:
    """
    Return the sorted values using counting sort.

    Args:
        values: Input integer values.
        max_value: Maximum possible value. If omitted, it is computed from
            ``values``.
        min_value: Minimum possible value.

    Returns:
        Sorted list.

    Raises:
        ValueError: If ``min_value > max_value`` or a value is outside the
            configured range.

    Time Complexity:
        O(n + U), where ``U = max_value - min_value + 1``.

    Space Complexity:
        O(n + U)
    """
    if max_value is not None and min_value > max_value:
        raise ValueError('min_value must be at most max_value')
    if not values:
        return []
    if max_value is None:
        max_value = max(values)
    if min_value > max_value:
        raise ValueError('min_value must be at most max_value')
    counts = [0] * (max_value - min_value + 1)
    for value in values:
        if value < min_value or value > max_value:
            raise ValueError('value is outside the configured range')
        counts[value - min_value] += 1
    res: list[int] = []
    for i, count in enumerate(counts):
        if count:
            res.extend([i + min_value] * count)
    return res


def partition(values: Sequence[T], key: Callable[[T], KeyT] | None = None, left: int = 0, right: int | None = None) -> tuple[list[T], int]:
    """
    Return a copy partitioned by the last element as pivot.

    The half-open range ``[left, right)`` is partitioned in Lomuto style:
    elements whose key is at most the pivot key are moved before the pivot.
    Elements outside the range are left unchanged.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.
        left: Left boundary of the partition range, inclusive.
        right: Right boundary of the partition range, exclusive. If omitted, ``len(values)`` is used.

    Returns:
        Pair of the partitioned copy and the final pivot index.

    Raises:
        ValueError: If the range is empty or out of bounds.

    Time Complexity:
        O(len(values)), including the full input copy.

    Space Complexity:
        O(len(values))
    """
    if right is None:
        right = len(values)
    if not (0 <= left < right <= len(values)):
        raise ValueError('partition range must be non-empty and within values')
    key_func = _resolve_key(key)
    res = list(values)
    pivot_key = key_func(res[right - 1])
    i = left - 1
    for j in range(left, right - 1):
        if not (pivot_key < key_func(res[j])):
            i += 1
            res[i], res[j] = res[j], res[i]
    q = i + 1
    res[q], res[right - 1] = res[right - 1], res[q]
    return res, q


def quick_sort(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> list[T]:
    """
    Return a sorted copy using iterative Lomuto quicksort.

    This is an educational quicksort implementation whose pivot is always the
    last element of the current range. It is not stable.

    Args:
        values: Input sequence.
        key: Function used to extract comparison keys. If omitted, values are compared directly.

    Returns:
        Sorted copy.

    Time Complexity:
        Average O(n log n), worst-case O(n^2).

    Space Complexity:
        O(n)
    """
    res = list(values)
    key_func = _resolve_key(key)
    stack = [(0, len(res))]
    while stack:
        left, right = stack.pop()
        if right - left <= 1:
            continue
        pivot_key = key_func(res[right - 1])
        i = left - 1
        for j in range(left, right - 1):
            if not (pivot_key < key_func(res[j])):
                i += 1
                res[i], res[j] = res[j], res[i]
        q = i + 1
        res[q], res[right - 1] = res[right - 1], res[q]
        stack.append((q + 1, right))
        stack.append((left, q))
    return res


def minimum_cost_sort(values: Sequence[int]) -> int:
    """
    Return the minimum swap cost needed to sort values in ascending order.

    Swapping two elements with values ``x`` and ``y`` costs ``x + y``. This
    function assumes all values are distinct and non-negative.

    Args:
        values: Input values to sort.

    Returns:
        Minimum total swap cost.

    Raises:
        ValueError: If a value is negative or values are not distinct.

    Time Complexity:
        O(n log n), where ``n = len(values)``.

    Space Complexity:
        O(n)
    """
    n = len(values)
    if n <= 1:
        if n == 1 and values[0] < 0:
            raise ValueError('values must be non-negative')
        return 0
    if any(value < 0 for value in values):
        raise ValueError('values must be non-negative')
    if len(set(values)) != n:
        raise ValueError('values must be distinct')
    global_min = min(values)
    order = sorted(range(n), key=lambda i: (values[i], i))
    to = [0] * n
    for sorted_pos, original_pos in enumerate(order):
        to[original_pos] = sorted_pos

    visited = [False] * n
    res = 0
    for start in range(n):
        if visited[start]:
            continue
        cur = start
        cycle_len = 0
        cycle_sum = 0
        cycle_min = 0
        while not visited[cur]:
            visited[cur] = True
            value = values[cur]
            cycle_sum += value
            if cycle_len == 0 or value < cycle_min:
                cycle_min = value
            cycle_len += 1
            cur = to[cur]
        if cycle_len <= 1:
            continue
        direct = cycle_sum + (cycle_len - 2) * cycle_min
        via_global_min = cycle_sum + cycle_min + (cycle_len + 1) * global_min
        res += min(direct, via_global_min)
    return res
