#!/usr/bin/env python3

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import NamedTuple, TypeVar


CellT = TypeVar('CellT')

_DIRECTIONS4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_DIRECTIONS8 = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


class GridComponentsResult(NamedTuple):
    """
    Connected components of passable cells in a grid.

    Attributes:
        n: Number of connected components.
        group: ``group[r][c]`` is the component id of cell ``(r, c)``, or ``-1``
            if the cell is not passable.
        size: ``size[i]`` is the number of cells in component ``i``.

    Space Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.
    """

    n: int
    group: list[list[int]]
    size: list[int]


def grid_index(row: int, col: int, width: int) -> int:
    """
    Convert a grid coordinate to a flat index.

    Args:
        row: Row index.
        col: Column index.
        width: Number of columns.

    Returns:
        Flat index ``row * width + col``.

    Time Complexity:
        O(1)
    """
    return row * width + col


def grid_position(index: int, width: int) -> tuple[int, int]:
    """
    Convert a flat index to a grid coordinate.

    Args:
        index: Flat index.
        width: Number of columns.

    Returns:
        Pair ``(row, col)``.

    Time Complexity:
        O(1)
    """
    return divmod(index, width)


def grid_neighbors4(row: int, col: int, height: int, width: int) -> Iterator[tuple[int, int]]:
    """
    Iterate over 4-neighbor cells inside the grid.

    Args:
        row: Row index of the center cell.
        col: Column index of the center cell.
        height: Number of rows.
        width: Number of columns.

    Returns:
        Iterator of neighboring coordinates.

    Time Complexity:
        O(1)
    """
    for dr, dc in _DIRECTIONS4:
        nr = row + dr
        nc = col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def grid_neighbors8(row: int, col: int, height: int, width: int) -> Iterator[tuple[int, int]]:
    """
    Iterate over 8-neighbor cells inside the grid.

    Args:
        row: Row index of the center cell.
        col: Column index of the center cell.
        height: Number of rows.
        width: Number of columns.

    Returns:
        Iterator of neighboring coordinates.

    Time Complexity:
        O(1)
    """
    for dr, dc in _DIRECTIONS8:
        nr = row + dr
        nc = col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def grid_bfs(grid: Sequence[Sequence[CellT]], starts: Iterable[tuple[int, int]], passable: Callable[[CellT], bool] | None = None, *, diagonal: bool = False) -> list[list[int]]:
    """
    Return unweighted shortest distances on an implicit grid graph.

    Args:
        grid: Rectangular grid.
        starts: Starting cells for multi-source BFS.
        passable: Predicate deciding whether a cell can be entered. If omitted,
            every cell is passable.
        diagonal: If ``True``, use 8-neighbor adjacency. Otherwise, use
            4-neighbor adjacency.

    Returns:
        Distance grid. Unreachable or non-passable cells have distance ``-1``.

    Raises:
        ValueError: If ``grid`` is not rectangular, a start is outside the grid,
            or a start is not passable.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(hw)
    """
    height, width, ok = _passable_mask(grid, passable)
    dist = [[-1] * width for _ in range(height)]
    q: deque[tuple[int, int]] = deque()
    for row, col in starts:
        if not (0 <= row < height and 0 <= col < width):
            raise ValueError('start cell is outside the grid')
        if not ok[row][col]:
            raise ValueError('start cell is not passable')
        if dist[row][col] == -1:
            dist[row][col] = 0
            q.append((row, col))

    directions = _DIRECTIONS8 if diagonal else _DIRECTIONS4
    while q:
        row, col = q.popleft()
        nd = dist[row][col] + 1
        for dr, dc in directions:
            nr = row + dr
            nc = col + dc
            if 0 <= nr < height and 0 <= nc < width and ok[nr][nc] and dist[nr][nc] == -1:
                dist[nr][nc] = nd
                q.append((nr, nc))
    return dist


def grid_connected_components(grid: Sequence[Sequence[CellT]], passable: Callable[[CellT], bool] | None = None, *, diagonal: bool = False) -> GridComponentsResult:
    """
    Compute connected components of passable cells in an implicit grid graph.

    Args:
        grid: Rectangular grid.
        passable: Predicate deciding whether a cell can be entered. If omitted,
            every cell is passable.
        diagonal: If ``True``, use 8-neighbor adjacency. Otherwise, use
            4-neighbor adjacency.

    Returns:
        Connected component ids and component sizes.

    Raises:
        ValueError: If ``grid`` is not rectangular.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(hw)
    """
    height, width, ok = _passable_mask(grid, passable)
    group = [[-1] * width for _ in range(height)]
    sizes: list[int] = []
    directions = _DIRECTIONS8 if diagonal else _DIRECTIONS4
    for sr in range(height):
        for sc in range(width):
            if not ok[sr][sc] or group[sr][sc] != -1:
                continue
            group_id = len(sizes)
            group[sr][sc] = group_id
            q: deque[tuple[int, int]] = deque([(sr, sc)])
            size = 0
            while q:
                row, col = q.popleft()
                size += 1
                for dr, dc in directions:
                    nr = row + dr
                    nc = col + dc
                    if 0 <= nr < height and 0 <= nc < width and ok[nr][nc] and group[nr][nc] == -1:
                        group[nr][nc] = group_id
                        q.append((nr, nc))
            sizes.append(size)
    return GridComponentsResult(n=len(sizes), group=group, size=sizes)


def _passable_mask(grid: Sequence[Sequence[CellT]], passable: Callable[[CellT], bool] | None) -> tuple[int, int, list[list[bool]]]:
    height = len(grid)
    if height == 0:
        return 0, 0, []
    width = len(grid[0])
    ok: list[list[bool]] = []
    for row in grid:
        if len(row) != width:
            raise ValueError('grid must be rectangular')
        if passable is None:
            ok.append([True] * width)
        else:
            ok.append([passable(value) for value in row])
    return height, width, ok
