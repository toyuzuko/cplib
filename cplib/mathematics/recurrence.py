#!/usr/bin/env python3

from cplib.mathematics.polynomial import FormalPowerSeriesMod, coefficient_of_rational_polynomial


def evaluate_linear_recurrence(coef: list[int], init: list[int], k: int) -> int:
    """
    Compute the k-th term of a linear recurrence using formal power series (Bostan–Mori).

    The sequence is defined by:
        a_i = c_0 * a_{i-1} + c_1 * a_{i-2} + ... + c_{n-1} * a_{i-n}
    where n = len(coef), init = [a_0, ..., a_{n-1}], and coef = [c_0, ..., c_{n-1}].

    Args:
        coef (list[int]): Recurrence coefficients [c_0, c_1, ..., c_{n-1}].
        init (list[int]): Initial terms [a_0, a_1, ..., a_{n-1}].
        k (int): Index of the term to compute (0-based).

    Returns:
        int: The value of a_k modulo FormalPowerSeriesMod.get_mod().
        An empty recurrence defines the identically zero sequence.

    Examples:
        >>> # Sequence defined by a_n = 2*a_{n-1} + 3*a_{n-2}
        >>> coef = [2, 3]
        >>> init = [1, 2]  # a_0=1, a_1=2
        >>> # Then a_2 = 2*2 + 3*1 = 7, a_3 = 2*7 + 3*2 = 20, a_4 = 2*20 + 3*7 = 61
        >>> evaluate_linear_recurrence(coef, init, 4)
        61

    Raises:
        ValueError: If the lengths differ or k is negative.

    Notes:
        Uses NTT under the configured prime modulus when capacity permits;
        otherwise polynomial multiplication uses a quadratic fallback.
        998244353 is recommended.

    Time Complexity:
        O(n log(n + 1) log(k + 2)) with NTT, otherwise O(n**2 log(k + 2)).

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n = len(coef) = len(init)``.
    """
    if len(coef) != len(init) or k < 0:
        raise ValueError('lengths must match and k must be non-negative')
    n = len(coef)
    if n == 0:
        return 0
    if k < n:
        return init[k] % FormalPowerSeriesMod.get_mod()
    f = FormalPowerSeriesMod(init)
    g = FormalPowerSeriesMod([1] + [-i for i in coef])
    f = (f * g).resize(n)
    return coefficient_of_rational_polynomial(f, g, k)


def enumerate_linear_recurrence(coef: list[int], init: list[int], k: int, m: int) -> list[int]:
    """
    Enumerate consecutive terms of a linear recurrence.

    The sequence is defined by:
        a_i = c_0 * a_{i-1} + c_1 * a_{i-2} + ... + c_{n-1} * a_{i-n}
    where ``n = len(coef)``, ``init = [a_0, ..., a_{n-1}]``, and
    ``coef = [c_0, ..., c_{n-1}]``.

    Args:
        coef: Recurrence coefficients [c_0, c_1, ..., c_{n-1}].
        init: Initial terms [a_0, a_1, ..., a_{n-1}].
        k: Starting index (0-based).
        m: Number of consecutive terms to enumerate.

    Returns:
        list[int]: Consecutive terms of the recurrence modulo
        ``FormalPowerSeriesMod.get_mod()``. An empty recurrence defines the
        identically zero sequence. If m is zero, returns an empty list.

    Examples:
        >>> enumerate_linear_recurrence([1, 1], [0, 1], 3, 5)
        [2, 3, 5, 8, 13]

    Raises:
        ValueError: If the lengths differ, k is negative, or m is negative.

    Notes:
        Uses NTT under the configured prime modulus when capacity permits;
        otherwise polynomial multiplication uses a quadratic fallback.
        998244353 is recommended.

    Time Complexity:
        Let ``d = len(coef)``. The current implementation runs in
        O((d + m) log(d + m + 1) log(k + 2)) with NTT, or at most
        O((d + m)**2 log(k + 2)) with quadratic polynomial operations.

    Space Complexity:
        ``O(d log(k + 2) + m)``. Denominators for the halving steps are
        retained until the reconstruction pass.

    Complexity Notation:
        ``d = len(coef) = len(init)`` and ``m`` is the number of output terms.
    """
    if len(coef) != len(init) or k < 0 or m < 0:
        raise ValueError('lengths must match and k and m must be non-negative')
    if m == 0:
        return []
    if not coef:
        return [0] * m
    mod = FormalPowerSeriesMod.get_mod()
    base = [x % mod for x in init]
    rec = [x % mod for x in coef]
    q = FormalPowerSeriesMod([1] + [(-x) % mod for x in rec]).trimmed()
    p = (FormalPowerSeriesMod(base) * q).resize(len(base))
    poly_part, p = p.divmod_poly(q)
    poly_values = poly_part.div_xk(k).resize(m).coef
    if len(q) == 1:
        return poly_values

    p = p.trimmed()
    d = len(q) - 1

    path: list[tuple[FormalPowerSeriesMod, int]] = []
    current_denom = q
    current_start = k
    while current_start > max(1, d):
        path.append((current_denom, current_start))
        denom_neg = FormalPowerSeriesMod([(-x) % mod if i & 1 else x for i, x in enumerate(current_denom.coef)])
        current_denom = (current_denom * denom_neg)[::2].resize(d + 1)
        parity = (current_start - d) & 1
        current_start = (current_start - d + parity) // 2

    inverse_block = (~current_denom.resize(current_start + d))[current_start:].resize(d)
    while path:
        current_denom, current_start = path.pop()
        denom_neg = FormalPowerSeriesMod([(-x) % mod if i & 1 else x for i, x in enumerate(current_denom.coef)])
        parity = (current_start - d) & 1
        lifted = FormalPowerSeriesMod([0] * (2 * d))
        for i in range(d):
            lifted[2 * i] = inverse_block[i]
        inverse_block = (denom_neg * lifted)[d - parity:].resize(d)

    kth_inverse_mod_q = (q * inverse_block).resize(d)
    shifted_numer = ((kth_inverse_mod_q * p) % q).resize(d)
    rational_values = (shifted_numer * ~q.resize(m)).resize(m).coef
    return [(poly_values[i] + rational_values[i]) % mod for i in range(m)]


def berlekamp_massey(sequence: list[int]) -> list[int]:
    """
    Compute minimal linear recurrence coefficients for a given integer sequence
    using the Berlekamp–Massey algorithm over the finite field defined by
    FormalPowerSeriesMod._mod (default = 998244353).

    The returned coefficients `coeffs` satisfy::

        a_n = -sum_{i=1}^L coeffs[i] * a_{n-i}  (mod M)

    where `M = FormalPowerSeriesMod._mod` and `coeffs[0] == 1`.

    Args:
        sequence (list[int]): Known terms of the sequence [a_0, a_1, ..., a_{n-1}].

    Returns:
        list[int]: Recurrence coefficients `coeffs` of length L+1, with `coeffs[0] == 1`.
        An empty or identically zero input returns [1].

    Notes:
        The configured modulus must be prime. The recurrence fits the supplied
        prefix; predicting later terms requires that the sequence really follows
        a recurrence of the inferred order. At least 2L known terms suffice
        for a sequence known to have recurrence order at most L.

    Examples:
        >>> sequence = [1, 2, 7, 20, 61]  # from a_n = 2*a_{n-1} + 3*a_{n-2}
        >>> coeffs = berlekamp_massey(sequence)
        >>> # Returns [1, M-2, M-3] because a_n = -(-2)*a_{n-1} - (-3)*a_{n-2}
        >>> print(coeffs)
        [1, 998244351, 998244350]

    Time Complexity:
        O(n^2)

    Space Complexity:
        O(n)

    Complexity Notation:
        ``n = len(sequence)``.
    """
    mod = FormalPowerSeriesMod.get_mod()
    prev_coeffs = [1]
    curr_coeffs = [1]
    degree = 0
    offset = 0
    last_discrepancy = 1

    for i, value in enumerate(sequence):
        offset += 1
        discrepancy = value % mod
        for j in range(1, degree + 1):
            discrepancy = (discrepancy + curr_coeffs[j] * sequence[i - j]) % mod
        if discrepancy == 0:
            continue
        temp_coeffs = curr_coeffs.copy()
        scale = discrepancy * pow(last_discrepancy, mod - 2, mod) % mod
        needed = len(prev_coeffs) + offset
        if len(curr_coeffs) < needed:
            curr_coeffs += [0] * (needed - len(curr_coeffs))
        for j in range(len(prev_coeffs)):
            curr_coeffs[j + offset] = (curr_coeffs[j + offset] - scale * prev_coeffs[j]) % mod
        if 2 * degree <= i:
            prev_coeffs = temp_coeffs
            degree = i + 1 - degree
            offset = 0
            last_discrepancy = discrepancy

    return curr_coeffs


def find_linear_recurrence(sequence: list[int]) -> list[int]:
    """
    Derive coefficients for direct evaluation of a linear recurrence from a given sequence.

    Uses berlekamp_massey to find the minimal recurrence in the form::

        a_n = -sum_{i=1..L} bm[i] * a_{n-i}  (mod M)

    Then converts to the common coefficient order for::

        a_n = c_0 * a_{n-1} + c_1 * a_{n-2} + ... + c_{L-1} * a_{n-L}

    Args:
        sequence (list[int]): Known terms of the sequence [a_0, a_1, ..., a_{n-1}].

    Returns:
        list[int]: Coefficients [c_0, c_1, ..., c_{L-1}] for use in direct
        recurrence evaluation. An empty or identically zero input returns [].

    Notes:
        Uses the prime modulus configured on FormalPowerSeriesMod. The result
        fits the given prefix; see berlekamp_massey for the conditions under
        which it determines later terms.

    Examples:
        >>> seq = [1, 2, 7, 20, 61]
        >>> # Recurrence a_n = 2*a_{n-1} + 3*a_{n-2}
        >>> find_linear_recurrence(seq)
        [2, 3]

    Time Complexity:
        ``O(n^2)``

    Space Complexity:
        ``O(n)``

    Complexity Notation:
        ``n = len(sequence)``.
    """
    bm = berlekamp_massey(sequence)
    mod = FormalPowerSeriesMod.get_mod()
    b = [-bm[i] % mod for i in range(1, len(bm))]
    return b
