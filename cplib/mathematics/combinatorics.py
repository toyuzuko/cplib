#!/usr/bin/env python3

from bisect import bisect_left, bisect_right
from collections import Counter
from math import comb

from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod, polynomial_shift


def _prepare_fps(transform_size: int, mod: int) -> bool:
    # Newton iterations and polynomial shifts need transforms beyond the output length.
    if ((mod - 1) & -(mod - 1)) < transform_size:
        return False
    if ConvolutionMod.get_mod() != mod:
        ConvolutionMod.set_mod(mod)
    return True


def _stirling_recurrence(n: int, fixed_k: int | None, mod: int, first_kind: bool) -> list[int]:
    width = n if fixed_k is None else fixed_k
    row = [0] * (width + 1)
    row[0] = 1 % mod
    column = [row[width]]
    for i in range(1, n + 1):
        for j in range(min(i, width), 0, -1):
            coefficient = 1 - i if first_kind else j
            row[j] = (row[j - 1] + coefficient * row[j]) % mod
        row[0] = 0
        if fixed_k is not None:
            column.append(row[width])
    return row if fixed_k is None else column


def enumerate_partition_number(n: int) -> list[int]:
    """
    Calculate partition numbers from 0 to n using pentagonal number theorem.

    Args:
        n: Upper bound of partition numbers to calculate.

    Returns:
        [p(0), ..., p(n)] modulo FormalPowerSeriesMod.get_mod().

    Raises:
        ValueError: If n is negative.

    Notes:
        Uses Euler's pentagonal number theorem and formal power series under
        the prime modulus configured on FormalPowerSeriesMod. If the modulus
        does not support a sufficiently long NTT, uses the pentagonal recurrence.

    Examples:
        >>> enumerate_partition_number(5)
        [1, 1, 2, 3, 5, 7]

        p(0) = 1
        p(1) = 1 (1)
        p(2) = 2 (1+1, 2)
        p(3) = 3 (1+1+1, 1+2, 3)
        p(4) = 5 (1+1+1+1, 1+1+2, 1+3, 2+2, 4)
        p(5) = 7 (1+1+1+1+1, 1+1+1+2, 1+1+3, 1+2+2, 1+4, 2+3, 5)

    Time Complexity:
        O(n log n) with suitable NTT capacity; otherwise O(n sqrt(n)).

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` is the maximum index to enumerate.
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    coef = [0] * (n + 1)
    coef[0] = 1
    i = 1
    while (k := i * (3 * i - 1) // 2) <= n:
        coef[k] = -1 if i & 1 else 1
        if k + i <= n:
            coef[k + i] = coef[k]
        i += 1
    if not _prepare_fps(1 << n.bit_length(), mod):
        nonzero = [(j, c) for j, c in enumerate(coef) if j and c]
        result = [1 % mod] + [0] * n
        for i in range(1, n + 1):
            value = 0
            for j, c in nonzero:
                if j > i:
                    break
                value -= c * result[i - j]
            result[i] = value % mod
        return result
    return FormalPowerSeriesMod(coef).inv().coef


def enumerate_stirling_number_first(n: int, fixed_k: int | None) -> list[int]:
    """
    Enumerate Stirling numbers of the first kind.

    Computes signed Stirling numbers of the first kind s(n,k), which count the number
    of permutations of n elements with exactly k cycles, multiplied by (-1)^(n-k).

    Args:
        n: Nonnegative maximum index.
        fixed_k: If None, computes s(n,k) for all k from 0 to n.
                If specified, computes s(i,fixed_k) for all i from 0 to n.

    Returns:
        list[int]: Stirling numbers modulo FormalPowerSeriesMod._mod
        - If fixed_k is None: [s(n,0), s(n,1), ..., s(n,n)]
        - If fixed_k is specified: [s(0,fixed_k), s(1,fixed_k), ..., s(n,fixed_k)]

    Time Complexity:
        - fixed_k is None: O(n log^2 n) using polynomial shift
        - fixed_k is specified: O(n log n) using formal power series

        With insufficient NTT capacity: O(n**2) for a row, or
        O(n * fixed_k) for a fixed column, plus O(n) output initialization.

    Space Complexity:
        O(n)

    Complexity Notation:
        ``n`` is the maximum index to enumerate.

    Raises:
        ValueError: If n is negative.

    Notes:
        Uses the prime modulus configured on FormalPowerSeriesMod. If the NTT
        capacity is insufficient (including n >= mod), uses the recurrence
        without factorial division. Out-of-range fixed_k gives a zero column.
        - s(n,k) = 0 for k > n or k < 0
        - s(n,0) = 1 if n = 0, else 0
        - s(n,n) = 1 for all n >= 0
        - Recurrence: s(n+1,k) = s(n,k-1) - n*s(n,k)
        - When fixed_k is None, uses falling factorial x(x-1)...(x-n+1) expansion
        - When fixed_k is specified, uses (-log(1-x))^k/k! followed by the sign (-1)^(n-k)

    Examples:
        >>> # Get s(4,k) for k = 0,1,2,3,4
        >>> enumerate_stirling_number_first(4, None)
        [0, 998244347, 11, 998244347, 1]

        >>> # Get s(i,2) for i = 0,1,2,3,4
        >>> enumerate_stirling_number_first(4, 2)
        [0, 0, 1, 998244350, 11]
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    if fixed_k is not None:
        if fixed_k < 0 or fixed_k > n:
            return [0] * (n + 1)
        if fixed_k == 0:
            return [1 % mod] + [0] * n
    if not _prepare_fps(2 << n.bit_length(), mod):
        return _stirling_recurrence(n, fixed_k, mod, True)
    if fixed_k is None:
        t = 0
        f = FormalPowerSeriesMod([1])
        for i in range(n.bit_length())[::-1]:
            f = f * polynomial_shift(f, -t)
            t <<= 1
            if (n >> i) & 1:
                f = f * FormalPowerSeriesMod([-t, 1])
                t += 1
        return f.coef
    else:
        fac = [1] * (n + 1)
        ifac = [1] * (n + 1)
        for i in range(2, n + 1):
            fac[i] = fac[i - 1] * i % mod
        ifac[n] = pow(fac[n], -1, mod)
        for i in range(n - 1, 0, -1):
            ifac[i] = ifac[i + 1] * (i + 1) % mod
        ifac[0] = 1
        res = [0] * (n + 1)
        f = FormalPowerSeriesMod([1, -1] + [0] * (n - 1))
        f = f.log() * (-1)
        f = f ** fixed_k
        for i in range(fixed_k, n + 1):
            res[i] = f[i] * ifac[fixed_k] % mod * fac[i] % mod
            if (i + fixed_k) % 2 == 1:
                res[i] = (mod - res[i]) % mod
        return res


def enumerate_stirling_number_second(n: int, fixed_k: int | None) -> list[int]:
    """
    Enumerate Stirling numbers of the second kind.

    Computes Stirling numbers of the second kind S(n,k), which count the number
    of ways to partition a set of n elements into exactly k non-empty subsets.

    Args:
        n: Nonnegative maximum index.
        fixed_k: If None, computes S(n,k) for all k from 0 to n.
                If specified, computes S(i,fixed_k) for all i from 0 to n.

    Returns:
        list[int]: Stirling numbers modulo FormalPowerSeriesMod._mod
        - If fixed_k is None: [S(n,0), S(n,1), ..., S(n,n)]
        - If fixed_k is specified: [S(0,fixed_k), S(1,fixed_k), ..., S(n,fixed_k)]

    Raises:
        ValueError: If n is negative.

    Notes:
        Uses the prime modulus configured on FormalPowerSeriesMod. If the NTT
        capacity is insufficient (including n >= mod), uses the recurrence
        without factorial division. Out-of-range fixed_k gives a zero column.
        - S(n,k) = 0 for k > n or k < 0
        - S(n,0) = 1 if n = 0, else 0
        - S(n,n) = 1 for all n >= 0
        - S(n,1) = 1 for all n >= 1
        - Recurrence: S(n+1,k) = k*S(n,k) + S(n,k-1)
        - When fixed_k is None, uses inclusion-exclusion principle
        - When fixed_k is specified, uses generating function (e^x - 1)^k/k!

    Examples:
        >>> # Get S(4,k) for k = 0,1,2,3,4
        >>> enumerate_stirling_number_second(4, None)
        [0, 1, 7, 6, 1]

        >>> # Get S(i,2) for i = 0,1,2,3,4
        >>> enumerate_stirling_number_second(4, 2)
        [0, 0, 1, 3, 7]

    Time Complexity:
        ``O(n log n)`` for both branches

        With insufficient NTT capacity: O(n**2) for a row, or
        O(n * fixed_k) for a fixed column, plus O(n) output initialization.

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` is the maximum index to enumerate.
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    if fixed_k is not None:
        if fixed_k < 0 or fixed_k > n:
            return [0] * (n + 1)
        if fixed_k == 0:
            return [1 % mod] + [0] * n
    if not _prepare_fps(2 << n.bit_length(), mod):
        return _stirling_recurrence(n, fixed_k, mod, False)
    fac = [1] * (n + 1)
    ifac = [1] * (n + 1)
    for i in range(2, n + 1):
        fac[i] = fac[i - 1] * i % mod
    ifac[n] = pow(fac[n], -1, mod)
    for i in range(n - 1, 0, -1):
        ifac[i] = ifac[i + 1] * (i + 1) % mod
    ifac[0] = 1
    if fixed_k is None:
        f = FormalPowerSeriesMod([pow(i, n, mod) * ifac[i] % mod for i in range(n + 1)])
        g = FormalPowerSeriesMod([ifac[i] * (1 - (i & 1) * 2) for i in range(n + 1)])
        return (f * g)[:n + 1].coef
    else:
        f = FormalPowerSeriesMod([0] + [ifac[i] for i in range(1, n + 1)]) # exp(x) - 1
        f = f ** fixed_k
        res = [0] * (n + 1)
        for i in range(fixed_k, n + 1):
            res[i] = f[i] * ifac[fixed_k] % mod * fac[i] % mod
        return res


def enumerate_bell_number(n: int) -> list[int]:
    """
    Enumerate Bell numbers from B(0) to B(n).

    Computes Bell numbers B(n), which count the number of ways to partition
    a set of n elements into any number of non-empty subsets.

    Args:
        n: Maximum index for Bell numbers to compute

    Returns:
        list[int]: Bell numbers [B(0), B(1), ..., B(n)] modulo FormalPowerSeriesMod._mod

    Raises:
        ValueError: If n is negative.

    Notes:
        Uses the prime modulus configured on FormalPowerSeriesMod. When NTT
        capacity is insufficient, evaluates the recurrence directly.
        - B(n) = sum over k of S(n,k), where S(n,k) are Stirling numbers of the second kind
        - B(0) = 1 (empty set has one partition)
        - B(1) = 1, B(2) = 2, B(3) = 5, B(4) = 15, B(5) = 52, ...
        - Exponential generating function: exp(exp(x) - 1)
        - Dobinski's formula: B(n) = (1/e) * sum_{k=0}^∞ k^n/k!
        - Bell's triangle recurrence: B(n+1) = sum_{k=0}^n C(n,k) * B(k)

    Examples:
        >>> enumerate_bell_number(5)
        [1, 1, 2, 5, 15, 52]

        >>> # B(4) = 15 partitions of {1,2,3,4}:
        >>> # {{1,2,3,4}}, {{1},{2,3,4}}, {{2},{1,3,4}}, ..., {{1},{2},{3},{4}}

    Time Complexity:
        O(n log n) with suitable NTT capacity; otherwise O(n**2).

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` is the maximum index to enumerate.
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    if not _prepare_fps(2 << n.bit_length(), mod):
        row = [1 % mod]
        result = row.copy()
        for _ in range(n):
            next_row = [row[-1]]
            for value in row:
                next_row.append((next_row[-1] + value) % mod)
            row = next_row
            result.append(row[0])
        return result
    fac = [1] * (n + 1)
    ifac = [1] * (n + 1)
    for i in range(2, n + 1):
        fac[i] = fac[i - 1] * i % mod
    ifac[n] = pow(fac[n], -1, mod)
    for i in range(n - 1, 0, -1):
        ifac[i] = ifac[i + 1] * (i + 1) % mod
    ifac[0] = 1
    f = FormalPowerSeriesMod([0] + [ifac[i] for i in range(1, n + 1)])  # exp(x) - 1
    f = f.exp()
    res = [f[i] * fac[i] % mod for i in range(n + 1)]
    return res


def enumerate_bernoulli_number(n: int) -> list[int]:
    """
    Enumerate Bernoulli numbers from B₀ to Bₙ.

    Computes Bernoulli numbers Bₙ, which are rational numbers that appear in
    Taylor series expansions of many functions and in Euler-Maclaurin formula.

    Args:
        n: Maximum index for Bernoulli numbers to compute

    Returns:
        list[int]: Bernoulli numbers [B₀, B₁, ..., Bₙ] modulo FormalPowerSeriesMod._mod

    Raises:
        ValueError: If n is negative. If n + 1 >= mod, the returned prefix
            includes a rational number without a modular denominator inverse.

    Notes:
        Uses the prime modulus configured on FormalPowerSeriesMod. When NTT
        capacity is insufficient, evaluates the recurrence directly.
        - B₀ = 1, B₁ = -1/2 ≡ (mod-1)/2 (mod), B₂ = 1/6, B₃ = 0, B₄ = -1/30, ...
        - For odd n > 1, Bₙ = 0
        - Uses exponential generating function: x/(e^x - 1) = Σ Bₙ x^n/n!
        - Implementation inverts the series Σ x^n/(n+1)! = (e^x - 1)/x
        - Returns numerator * inverse(denominator) modulo mod, not just numerators
        - Recurrence: Σ_{k=0}^n C(n+1,k) Bₖ = 0 for n ≥ 1

    Examples:
        >>> # First few Bernoulli numbers (as fractions):
        >>> # B₀ = 1, B₁ = -1/2, B₂ = 1/6, B₄ = -1/30, B₆ = 1/42
        >>> # Note: 499122176 ≡ -1/2 (mod 998244353)
        >>> #       166374059 ≡ 1/6 (mod 998244353), etc.
        >>> enumerate_bernoulli_number(6)
        [1, 499122176, 166374059, 0, 565671800, 0, 308980395]

    Time Complexity:
        O(n log n) with suitable NTT capacity; otherwise O(n**2 + n log mod).

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n`` is the maximum index to enumerate.
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    if n + 1 >= mod:
        raise ValueError('Bernoulli enumeration requires n + 1 < the prime modulus')
    if not _prepare_fps(2 << n.bit_length(), mod):
        result = [1]
        row = [1, 1]
        for i in range(1, n + 1):
            row.append(1)
            for j in range(i, 0, -1):
                row[j] = (row[j] + row[j - 1]) % mod
            value = -sum(row[j] * result[j] for j in range(i))
            result.append(value * pow(i + 1, -1, mod) % mod)
        return result
    fac = [1] * (n + 2)
    ifac = [1] * (n + 2)
    for i in range(2, n + 2):
        fac[i] = fac[i - 1] * i % mod
    ifac[n + 1] = pow(fac[n + 1], -1, mod)
    for i in range(n, 0, -1):
        ifac[i] = ifac[i + 1] * (i + 1) % mod
    ifac[0] = 1
    f = FormalPowerSeriesMod([ifac[i + 1] for i in range(n + 1)])
    f = f.inv()
    res = [f[i] * fac[i] % mod for i in range(n + 1)]
    return res


def count_four_sum(a: list[int], b: list[int], c: list[int], d: list[int], target: int) -> int:
    """
    Count quadruples with one element from each list whose sum is ``target``.

    Args:
        a: First list.
        b: Second list.
        c: Third list.
        d: Fourth list.
        target: Target sum.

    Returns:
        int: Number of quadruples ``(i, j, k, l)`` such that
        ``a[i] + b[j] + c[k] + d[l] == target``.

    Time Complexity:
        ``O(len(a) len(b) + len(c) len(d))`` expected

    Space Complexity:
        ``O(len(a) len(b))``
    """

    left = Counter(x + y for x in a for y in b)
    return sum(left[target - x - y] for x in c for y in d)


def count_subset_sums_with_size_in_range(values: list[int], size: int, lower: int, upper: int) -> int:
    """
    Count subsets of fixed size whose sum lies in a closed interval.

    Args:
        values: Input values.
        size: Number of selected elements.
        lower: Inclusive lower bound of the sum.
        upper: Inclusive upper bound of the sum.

    Returns:
        int: Number of subsets of cardinality ``size`` with sum in
        ``[lower, upper]``.

    Time Complexity:
        ``O(2^(n/2) log 2^(n/2))``, where ``n = len(values)``

    Space Complexity:
        ``O(2^(n/2))``
    """

    if size < 0 or size > len(values) or lower > upper:
        return 0

    def subset_sums_by_size(seq: list[int], max_size: int) -> list[list[int]]:
        groups: list[list[int]] = [[] for _ in range(max_size + 1)]
        groups[0].append(0)
        used = 0
        for x in seq:
            used += 1
            for cnt in range(min(max_size, used), 0, -1):
                groups[cnt].extend(s + x for s in groups[cnt - 1])
        return groups

    mid = len(values) // 2
    left = subset_sums_by_size(values[:mid], size)
    right = subset_sums_by_size(values[mid:], size)
    for sums in right:
        sums.sort()

    ans = 0
    for left_size, sums in enumerate(left):
        right_size = size - left_size
        if not 0 <= right_size < len(right):
            continue
        targets = right[right_size]
        for s in sums:
            ans += bisect_right(targets, upper - s) - bisect_left(targets, lower - s)
    return ans


class TwelvefoldWay:
    """
    Count distributions of balls into boxes under one twelvefold-way case.

    Args:
        distinguishable_balls: Whether balls are distinguishable.
        distinguishable_boxes: Whether boxes are distinguishable.
        restriction: One of ``'any'``, ``'at_most_one'``, or ``'at_least_one'``.
        mod: Positive modulus for the returned count, not necessarily prime.

    Notes:
        Changing the public mod attribute clears the cached factorial tables
        at the next count call. The counting configuration otherwise stays fixed.

    Space Complexity:
        ``O(n + k)`` for cached factorials and dynamic programming buffers.
    """

    ANY = 'any'
    AT_MOST_ONE = 'at_most_one'
    AT_LEAST_ONE = 'at_least_one'

    def __init__(self, distinguishable_balls: bool, distinguishable_boxes: bool, restriction: str = ANY, mod: int = 1_000_000_007) -> None:
        """Configure one of the twelve distributions of balls into boxes.

        Args:
            distinguishable_balls: Whether individual balls are labelled.
            distinguishable_boxes: Whether individual boxes are labelled.
            restriction: ANY, AT_MOST_ONE, or AT_LEAST_ONE per box.
            mod: Positive modulus, not necessarily prime.

        Returns:
            None.

        Raises:
            ValueError: If restriction is invalid or mod is not positive.

        Time Complexity:
            O(1).
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        if restriction not in (self.ANY, self.AT_MOST_ONE, self.AT_LEAST_ONE):
            raise ValueError("restriction must be 'any', 'at_most_one', or 'at_least_one'")
        self.distinguishable_balls = distinguishable_balls
        self.distinguishable_boxes = distinguishable_boxes
        self.restriction = restriction
        self.mod = mod
        self._cached_mod: int = mod
        self._fact = [1]
        self._inv_fact = [1]

    def _ensure_factorials(self, limit: int) -> bool:
        if limit < len(self._inv_fact):
            return True
        if limit >= self.mod:
            return False
        old = len(self._fact)
        self._fact.extend([1] * max(0, limit + 1 - old))
        for i in range(old, limit + 1):
            self._fact[i] = self._fact[i - 1] * i % self.mod
        try:
            inverse = pow(self._fact[limit], -1, self.mod)
        except ValueError:
            return False
        self._inv_fact = [1] * (limit + 1)
        self._inv_fact[limit] = inverse
        for i in range(limit, 0, -1):
            self._inv_fact[i - 1] = self._inv_fact[i] * i % self.mod
        return True

    def _comb(self, n: int, r: int) -> int:
        if r < 0 or r > n:
            return 0
        if not self._ensure_factorials(n):
            return comb(n, r) % self.mod
        return self._fact[n] * self._inv_fact[r] % self.mod * self._inv_fact[n - r] % self.mod

    def _perm(self, n: int, r: int) -> int:
        if r < 0 or r > n:
            return 0
        if not self._ensure_factorials(n):
            if r >= self.mod:
                return 0
            value = 1
            for i in range(n - r + 1, n + 1):
                value = value * i % self.mod
            return value
        return self._fact[n] * self._inv_fact[n - r] % self.mod

    def _stirling_second(self, n: int, k: int, at_most: bool = False) -> int:
        if at_most:
            k = min(k, n)
        if k < 0 or k > n:
            return 0
        dp = [0] * (k + 1)
        dp[0] = 1
        for i in range(1, n + 1):
            upper = min(i, k)
            for j in range(upper, 0, -1):
                dp[j] = (dp[j - 1] + j * dp[j]) % self.mod
            dp[0] = 0
        return sum(dp) % self.mod if at_most else dp[k]

    def _partition_at_most_parts(self, total: int, parts: int) -> int:
        if total < 0 or parts < 0:
            return 0
        dp = [0] * (total + 1)
        dp[0] = 1
        for part in range(1, min(parts, total) + 1):
            for s in range(part, total + 1):
                dp[s] = (dp[s] + dp[s - part]) % self.mod
        return dp[total]

    def count(self, n: int, k: int) -> int:
        """
        Count valid distributions of ``n`` balls into ``k`` boxes.

        Args:
            n: Number of balls.
            k: Number of boxes.

        Returns:
            Number of valid distributions modulo mod. Negative n or k gives
            zero. The empty distribution counts once before reduction modulo mod.

        Raises:
            ValueError: If mod has been changed to a nonpositive value.

        Time Complexity:
            O(n min(n, k)) for partitions/Stirling numbers. Labelled unrestricted
            assignments use O(log n); labelled surjections use O(k log n) plus
            factorial preparation. Other cases use factorial-table lookup after
            O(n + k) preparation. If a factorial is not invertible, combinations
            use math.comb followed by reduction (including its large-integer
            cost); permutations use O(n) modular multiplications.
        """
        if self.mod <= 0:
            raise ValueError('mod must be positive')
        if self.mod != self._cached_mod:
            self._fact = [1]
            self._inv_fact = [1]
            self._cached_mod = self.mod
        if n < 0 or k < 0 or self.mod == 1:
            return 0
        if k == 0:
            return int(n == 0)
        if n == 0:
            return int(self.restriction != self.AT_LEAST_ONE)
        if self.restriction == self.AT_LEAST_ONE and k > n:
            return 0

        if self.distinguishable_balls and self.distinguishable_boxes:
            if self.restriction == self.ANY:
                return pow(k, n, self.mod)
            if self.restriction == self.AT_MOST_ONE:
                return self._perm(k, n)
            ans = 0
            for empty in range(k + 1):
                term = self._comb(k, empty) * pow(k - empty, n, self.mod) % self.mod
                ans = (ans - term) % self.mod if empty & 1 else (ans + term) % self.mod
            return ans

        if not self.distinguishable_balls and self.distinguishable_boxes:
            if self.restriction == self.ANY:
                return self._comb(n + k - 1, k - 1) if k else int(n == 0)
            if self.restriction == self.AT_MOST_ONE:
                return self._comb(k, n)
            return self._comb(n - 1, k - 1) if n >= k and k > 0 else int(n == k == 0)

        if self.distinguishable_balls and not self.distinguishable_boxes:
            if self.restriction == self.ANY:
                return self._stirling_second(n, k, at_most=True)
            if self.restriction == self.AT_MOST_ONE:
                return int(n <= k)
            return self._stirling_second(n, k)

        if self.restriction == self.ANY:
            return self._partition_at_most_parts(n, k)
        if self.restriction == self.AT_MOST_ONE:
            return int(n <= k)
        return self._partition_at_most_parts(n - k, k) if n >= k else 0


def enumerate_montmort_number(n: int, mod: int) -> list[int]:
    """
    Enumerate Montmort numbers modulo ``mod``.

    This returns derangement counts ``!i`` for ``0 <= i <= n``.

    Args:
        n: Maximum size to enumerate.
        mod: Modulus used in the recurrence.

    Returns:
        list[int]: ``[!0, !1, ..., !n]`` modulo ``mod``.

    Raises:
        ValueError: If n is negative or mod is not positive.

    Time Complexity:
        - ``O(n)``

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the maximum index to enumerate.

    Examples:
        >>> enumerate_montmort_number(5, 10 ** 9 + 7)
        [1, 0, 1, 2, 9, 44]
    """
    if n < 0 or mod <= 0:
        raise ValueError('n must be nonnegative and mod positive')
    res = [0] * (n + 1)
    res[0] = 1 % mod
    if n >= 2:
        res[2] = 1 % mod
    for i in range(3, n + 1):
        res[i] = (i - 1) * (res[i - 1] + res[i - 2]) % mod
    return res


def count_all_subset_sums(arr: list[int], target: int) -> list[int]:
    """
    Count the number of subsets with each possible sum from 0 to target.

    For each sum s from 0 to target, counts how many subsets of arr have sum exactly s.
    Handles multisets (arrays with duplicate elements) correctly.

    Args:
        arr: List of non-negative integers (may contain duplicates)
        target: Maximum sum to consider

    Returns:
        list[int]: Array where result[i] is the number of subsets with sum i,
                  modulo FormalPowerSeriesMod._mod

    Raises:
        ValueError: If target or any input element is negative.

    Notes:
        - Counts distinguish input positions, including equal and zero values.
        - Zero elements multiply all counts by 2 each; values above target cannot
          contribute and are ignored. Modular counts need not be positive.
        - Uses the prime modulus configured on FormalPowerSeriesMod. If the NTT
          capacity is insufficient, uses ordinary subset-sum dynamic programming.
        - Uses generating function approach with formal power series
        - For multiset {a₁, a₂, ..., aₙ}, the generating function is:
          ∏(1 + x^{a_i}) = exp(∑ log(1 + x^{a_i}))
        - Efficiently handles duplicates by grouping equal elements

    Examples:
        >>> # Subsets: sum 0: {}, sum 1: {1}, sum 2: {2}, sum 3: {3}, {1,2},
        >>> #          sum 4: {1,3}, sum 5: {2,3}, sum 6: {1,2,3}
        >>> count_all_subset_sums([1, 2, 3], 6)
        [1, 1, 1, 2, 1, 1, 1]

        >>> # Subsets: sum 0: {}, sum 1: {1}, {1'}, sum 2: {2}, {1,1'},
        >>> #          sum 3: {1,2}, {1',2}, sum 4: {1,1',2}
        >>> count_all_subset_sums([1, 1, 2], 4)
        [1, 2, 2, 2, 1]

    Time Complexity:
        O(target log target + len(arr)) with suitable NTT capacity; otherwise
        O(len(arr) * target + len(arr)).

    Space Complexity:
        ``O(target)``

    Complexity Notation:
        ``target`` is the maximum subset sum retained in the output.
    """
    if target < 0 or any(x < 0 for x in arr):
        raise ValueError('target and elements must be nonnegative')
    mod = FormalPowerSeriesMod.get_mod()
    cnt = [0] * (target + 1)
    for x in arr:
        if x <= target:
            cnt[x] += 1
    if not _prepare_fps(2 << target.bit_length(), mod):
        result = [1 % mod] + [0] * target
        for x in arr:
            for total in range(target, x - 1, -1):
                result[total] = (result[total] + result[total - x]) % mod
        return result
    inv = [1] * (target + 1)
    for i in range(2, target + 1):
        inv[i] = mod - mod // i * inv[mod % i] % mod
    coef = [0] * (target + 1)
    for i in range(1, target + 1):
        for j in range(i, target + 1, i):
            coef[j] += inv[j // i] * cnt[i] * ((j // i & 1) * 2 - 1)
            coef[j] %= mod
    f = FormalPowerSeriesMod(coef)
    f = f.exp()
    multiplier = pow(2, cnt[0], mod)
    return [value * multiplier % mod for value in f.coef]
