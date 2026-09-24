from collections.abc import Callable, Sequence
from typing import TypeVar, cast

from cplib.tools.type import KeyT


T = TypeVar('T')


def _resolve_key(key: Callable[[T], KeyT] | None) -> Callable[[T], KeyT]:
    if key is not None:
        return key

    def identity(value: T) -> KeyT:
        return cast(KeyT, value)

    return identity


def insertion_sort_states(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> list[list[T]]:
    res = list(values)
    key_func = _resolve_key(key)
    states = [res.copy()]
    for i in range(1, len(res)):
        v = res[i]
        kv = key_func(v)
        j = i - 1
        while j >= 0 and kv < key_func(res[j]):
            res[j + 1] = res[j]
            j -= 1
        res[j + 1] = v
        states.append(res.copy())
    return states


def bubble_sort_count(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> tuple[list[T], int]:
    res = list(values)
    key_func = _resolve_key(key)
    count = 0
    flag = True
    while flag:
        flag = False
        for j in range(len(res) - 1, 0, -1):
            if key_func(res[j]) < key_func(res[j - 1]):
                res[j], res[j - 1] = res[j - 1], res[j]
                count += 1
                flag = True
    return res, count


def selection_sort_count(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> tuple[list[T], int]:
    res = list(values)
    key_func = _resolve_key(key)
    count = 0
    for i in range(len(res)):
        min_idx = i
        for j in range(i, len(res)):
            if key_func(res[j]) < key_func(res[min_idx]):
                min_idx = j
        if i != min_idx:
            res[i], res[min_idx] = res[min_idx], res[i]
            count += 1
    return res, count


def shell_sort_count(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> tuple[list[T], list[int], int]:
    n = len(values)
    gaps: list[int] = []
    h = 1
    while h <= n:
        gaps.append(h)
        h = h * 3 + 1
    gaps.reverse()

    res = list(values)
    key_func = _resolve_key(key)
    total = 0
    for gap in gaps:
        for i in range(gap, len(res)):
            v = res[i]
            kv = key_func(v)
            j = i - gap
            while j >= 0 and kv < key_func(res[j]):
                res[j + gap] = res[j]
                j -= gap
                total += 1
            res[j + gap] = v
    return res, gaps, total


def merge_sort_count(values: Sequence[T], key: Callable[[T], KeyT] | None = None) -> tuple[list[T], int]:
    res = list(values)
    n = len(res)
    if n <= 1:
        return res, 0
    tmp = res.copy()
    key_func = _resolve_key(key)

    def sort(left: int, right: int) -> int:
        if right - left <= 1:
            return 0
        mid = (left + right) >> 1
        count = sort(left, mid) + sort(mid, right)
        i = left
        j = mid
        k = left
        while i < mid and j < right:
            if key_func(res[j]) < key_func(res[i]):
                tmp[k] = res[j]
                j += 1
            else:
                tmp[k] = res[i]
                i += 1
            k += 1
        while i < mid:
            tmp[k] = res[i]
            i += 1
            k += 1
        while j < right:
            tmp[k] = res[j]
            j += 1
            k += 1
        res[left:right] = tmp[left:right]
        return count + right - left

    return res, sort(0, n)
