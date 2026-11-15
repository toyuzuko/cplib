#!/usr/bin/env python3

from collections.abc import Callable

from cplib.tools.type import KeyT


def monotone_minima(
    n_rows: int, n_cols: int, value: Callable[[int, int], KeyT]
) -> list[int]:
    """
    Find the leftmost minimum column of every row of a monotone matrix.

    The leftmost row-minimum indices must be nondecreasing with the row
    index. This precondition is not checked. A rectangular Monge matrix is
    sufficient, but total monotonicity is not required. Values need only
    support a consistent strict ordering via ``<``; equivalent values tie
    in favor of the smaller column index.

    All entries of the rectangular domain must be defined, and ``value``
    must return stable values independently of evaluation order. Rows are
    evaluated in divide-and-conquer order, not increasing order. In
    particular, this is not an online Monge-DP solver: a callback must not
    depend on earlier rows being solved first. Triangular or staircase
    domains are not implicitly supported. Padding invalid entries is safe
    only if the resulting full matrix still satisfies these preconditions.

    Args:
        n_rows: Number of rows, indexed from zero.
        n_cols: Number of columns, indexed from zero.
        value: Callback returning the entry at a row and column.

    Returns:
        Leftmost minimum column indices in row order. For zero rows,
        returns an empty list without calling ``value``.

    Raises:
        ValueError: If either dimension is negative, or there are positive
            rows but no columns.

    Time Complexity:
        O(n_rows + n_cols * log(n_rows + 1)) callback evaluations and
        comparisons, assuming each costs O(1).

    Space Complexity:
        O(n_rows) for the result and O(log(n_rows + 1)) auxiliary space.

    Examples:
        >>> monotone_minima(4, 5, lambda i, j: (i - j) ** 2)
        [0, 1, 2, 3]
        >>> monotone_minima(3, 4, lambda i, j: 0)
        [0, 0, 0]
        >>> monotone_minima(0, 0, lambda i, j: 0)
        []
    """
    if n_rows < 0 or n_cols < 0:
        raise ValueError('matrix dimensions must be non-negative')
    if not n_rows:
        return []
    if not n_cols:
        raise ValueError('positive rows require at least one column')

    result = [0] * n_rows
    stack = [(0, n_rows, 0, n_cols)]
    while stack:
        row_lo, row_hi, col_lo, col_hi = stack.pop()
        row = (row_lo + row_hi) // 2
        best_col = col_lo
        best_value = value(row, col_lo)
        for col in range(col_lo + 1, col_hi):
            candidate = value(row, col)
            if candidate < best_value:
                best_col = col
                best_value = candidate
        result[row] = best_col
        if row + 1 < row_hi:
            stack.append((row + 1, row_hi, best_col, col_hi))
        if row_lo < row:
            stack.append((row_lo, row, col_lo, best_col + 1))
    return result
