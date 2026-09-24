#!/usr/bin/env python3

from collections.abc import Sequence


def solve_n_queens(n: int, fixed: Sequence[tuple[int, int]] = ()) -> tuple[int, ...] | None:
    """
    Return one N-Queens placement satisfying fixed queens.

    Args:
        n: Board size.
        fixed: Pre-placed queens as ``(row, column)`` pairs.

    Returns:
        A tuple ``cols`` where ``cols[row]`` is the queen column, or ``None`` if
        no placement exists.

    Raises:
        ValueError: If ``n`` is negative or a fixed queen is outside the board.

    Time Complexity:
        Exponential in ``n`` in the worst case.

    Space Complexity:
        O(n)
    """
    if n < 0:
        raise ValueError('n must be non-negative')
    fixed_col = [-1] * n
    for r, c in fixed:
        if not (0 <= r < n and 0 <= c < n):
            raise ValueError('fixed queen is outside the board')
        if fixed_col[r] != -1 and fixed_col[r] != c:
            return None
        fixed_col[r] = c

    fixed_cols = 0
    fixed_diag1 = 0
    fixed_diag2 = 0
    for r, c in enumerate(fixed_col):
        if c == -1:
            continue
        col_bit = 1 << c
        diag1_bit = 1 << (r + c)
        diag2_bit = 1 << (r - c + n - 1)
        if fixed_cols & col_bit or fixed_diag1 & diag1_bit or fixed_diag2 & diag2_bit:
            return None
        fixed_cols |= col_bit
        fixed_diag1 |= diag1_bit
        fixed_diag2 |= diag2_bit

    placement = [-1] * n
    for r, c in enumerate(fixed_col):
        if c != -1:
            placement[r] = c
    all_cols = (1 << n) - 1

    def dfs(row: int, cols: int, diag1: int, diag2: int) -> bool:
        if row == n:
            return True
        fixed_c = fixed_col[row]
        if fixed_c != -1:
            return dfs(row + 1, cols, diag1, diag2)
        candidates = all_cols & ~cols
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            c = bit.bit_length() - 1
            d1 = 1 << (row + c)
            d2 = 1 << (row - c + n - 1)
            if diag1 & d1 or diag2 & d2:
                continue
            placement[row] = c
            if dfs(row + 1, cols | bit, diag1 | d1, diag2 | d2):
                return True
            placement[row] = -1
        return False

    if dfs(0, fixed_cols, fixed_diag1, fixed_diag2):
        return tuple(placement)
    return None


def sliding_puzzle_distance(board: Sequence[int], height: int, width: int, target: Sequence[int] | None = None, max_distance: int | None = None) -> int:
    """
    Return the shortest solution length of a rectangular sliding puzzle.

    The blank tile must be represented by ``0``. The implementation uses IDA*
    with Manhattan-distance heuristic, so it is suitable for small sliding
    puzzles such as 8-puzzle and 15-puzzle.

    Args:
        board: Initial board in row-major order.
        height: Positive number of rows.
        width: Positive number of columns.
        target: Target board in row-major order. If omitted, the target is
            ``1, 2, ..., height * width - 1, 0``.
        max_distance: Optional non-negative upper bound on the allowed answer.

    Returns:
        The minimum number of moves, or ``-1`` if no solution is found within
        ``max_distance``.

    Raises:
        ValueError: If the board dimensions or tile sets are invalid, or
            ``max_distance`` is negative.

    Time Complexity:
        Exponential in the solution length in the worst case.

    Space Complexity:
        O((height * width)^2 + answer), including the distance table and
        recursion stack.
    """
    if height <= 0 or width <= 0:
        raise ValueError('height and width must be positive')
    if max_distance is not None and max_distance < 0:
        raise ValueError('max_distance must be non-negative')
    n = height * width
    start = list(board)
    if len(start) != n:
        raise ValueError('board size does not match height * width')
    goal = list(range(1, n)) + [0] if target is None else list(target)
    if len(goal) != n:
        raise ValueError('target size does not match height * width')
    if sorted(start) != sorted(goal):
        raise ValueError('board and target must contain the same tiles')
    if sorted(goal) != list(range(n)):
        raise ValueError('tiles must be 0, 1, ..., height * width - 1')
    if start == goal:
        return 0

    order = {tile: i for i, tile in enumerate(goal) if tile}
    values = [order[tile] for tile in start if tile]
    inversions = 0
    for i, x in enumerate(values):
        for y in values[i + 1:]:
            if x > y:
                inversions += 1
    if width & 1:
        if inversions & 1:
            return -1
    else:
        start_blank_from_bottom = height - (start.index(0) // width)
        goal_blank_from_bottom = height - (goal.index(0) // width)
        if (inversions + start_blank_from_bottom - goal_blank_from_bottom) & 1:
            return -1

    target_pos = [0] * n
    for i, tile in enumerate(goal):
        target_pos[tile] = i

    dist = [[0] * n for _ in range(n)]
    for tile in range(1, n):
        tr, tc = divmod(target_pos[tile], width)
        for pos in range(n):
            r, c = divmod(pos, width)
            dist[tile][pos] = abs(r - tr) + abs(c - tc)

    neighbors: list[list[int]] = [[] for _ in range(n)]
    for pos in range(n):
        r, c = divmod(pos, width)
        if r:
            neighbors[pos].append(pos - width)
        if r + 1 < height:
            neighbors[pos].append(pos + width)
        if c:
            neighbors[pos].append(pos - 1)
        if c + 1 < width:
            neighbors[pos].append(pos + 1)

    zero = start.index(0)
    heuristic = sum(dist[tile][pos] for pos, tile in enumerate(start) if tile)
    inf = 10 ** 18

    def dfs(zero_pos: int, previous_zero: int, depth: int, current_h: int, bound: int) -> int:
        estimate = depth + current_h
        if estimate > bound:
            return estimate
        if current_h == 0:
            return -1
        best_next = inf
        for next_zero in neighbors[zero_pos]:
            if next_zero == previous_zero:
                continue
            tile = start[next_zero]
            next_h = current_h + dist[tile][zero_pos] - dist[tile][next_zero]
            start[zero_pos], start[next_zero] = start[next_zero], start[zero_pos]
            result = dfs(next_zero, zero_pos, depth + 1, next_h, bound)
            start[zero_pos], start[next_zero] = start[next_zero], start[zero_pos]
            if result == -1:
                return -1
            if result < best_next:
                best_next = result
        return best_next

    bound = heuristic
    while True:
        if max_distance is not None and bound > max_distance:
            return -1
        result = dfs(zero, -1, 0, heuristic, bound)
        if result == -1:
            return bound
        if result == inf:
            return -1
        bound = result
